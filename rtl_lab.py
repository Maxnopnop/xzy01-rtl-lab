"""Small, standard-library-only RTL generation and simulation experiment runner."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from urllib.parse import urlsplit
import uuid

ROOT = Path(__file__).resolve().parent
SCHEMA = 1
MAX_LOG = 2 * 1024 * 1024
SYSTEM_PROMPT = """Implement the given digital circuit in synthesizable SystemVerilog.
Return only one complete module in a single ```systemverilog code block.
Use exactly the specified module name and ports. Do not provide a testbench.
No includes, preprocessor directives, strings, hierarchical references, extra
modules, simulation system tasks, file IO, or attributes. Only $signed,
$unsigned and $clog2 system functions are permitted. Do not use delays.
The independent evaluator will supply all input stimuli and check outputs."""


class LabError(Exception):
    def __init__(self, status, stage, message):
        self.status, self.stage, self.message = status, stage, message
        super().__init__(message)


def utc():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def redact(text, secret=""):
    if secret:
        text = text.replace(secret, "[REDACTED]")
        # Also remove escaped variants in a JSON response.
        text = text.replace(json.dumps(secret)[1:-1], "[REDACTED]")
    return text


def write_text(path, value, secret=""):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(redact(value, secret), encoding="utf-8")


def write_json(path, value, secret=""):
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n", secret)


def clean_env():
    # Pass only OS/tool runtime necessities to generated-code subprocesses.
    names = {"PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP", "TMPDIR",
             "HOME", "USERPROFILE", "LANG", "LC_ALL", "LD_LIBRARY_PATH"}
    env = {k: v for k, v in os.environ.items() if k.upper() in names}
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def kill_tree(proc):
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=10, check=False)
    else:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    if proc.poll() is None:
        proc.kill()
    proc.wait(timeout=10)


def run_process(command, cwd, timeout, env=None):
    """Bound wall time and captured output; reap the process tree on timeout."""
    start = time.monotonic()
    kwargs = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    proc = subprocess.Popen(command, cwd=cwd, env=env or clean_env(),
                            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, **kwargs)
    chunks = {"stdout": bytearray(), "stderr": bytearray()}
    overflow = threading.Event()

    def drain(stream, name):
        while True:
            piece = stream.read(8192)
            if not piece:
                break
            room = MAX_LOG - len(chunks[name])
            chunks[name].extend(piece[:max(0, room)])
            if len(piece) > room:
                overflow.set()
        stream.close()

    readers = [threading.Thread(target=drain, args=(getattr(proc, name), name), daemon=True)
               for name in chunks]
    for reader in readers:
        reader.start()
    timed_out = False
    killed = False
    try:
        while proc.poll() is None:
            if time.monotonic() - start > timeout or overflow.is_set():
                timed_out = time.monotonic() - start > timeout
                kill_tree(proc)
                killed = True
                break
            time.sleep(0.02)
    except BaseException:
        kill_tree(proc)
        raise
    finally:
        for reader in readers:
            reader.join(timeout=5)
    return {"command": [str(x) for x in command], "returncode": proc.returncode,
            "elapsed_seconds": round(time.monotonic() - start, 4), "timeout": timed_out,
            "output_limit": overflow.is_set(), "killed": killed, "pid": proc.pid,
            **{key: bytes(value).decode("utf-8", errors="replace") for key, value in chunks.items()}}


def save_process(folder, stage, result, secret=""):
    write_text(folder / f"{stage}.stdout.log", result["stdout"], secret)
    write_text(folder / f"{stage}.stderr.log", result["stderr"], secret)
    write_json(folder / f"{stage}.json", {k: v for k, v in result.items() if k not in ("stdout", "stderr")}, secret)


def resolve_tool(override, name):
    candidate = override or shutil.which(name)
    if not candidate and os.name == "nt":
        p = Path("D:/iverilog/bin") / (name + ".exe")
        candidate = str(p) if p.is_file() else None
    if not candidate or not Path(candidate).is_file():
        raise LabError("ENV_ERROR", "environment", f"Executable not found: {name}")
    return str(Path(candidate).resolve())


def inspect_tools(args, folder):
    found = {}
    for name in ("iverilog", "vvp"):
        exe = resolve_tool(getattr(args, name), name)
        result = run_process([exe, "-V"], folder, 10)
        save_process(folder, name + "_version", result)
        if result["timeout"] or result["returncode"] != 0:
            raise LabError("ENV_ERROR", "environment", f"Cannot execute {name} -V")
        found[name] = {"path": exe, "sha256": digest(Path(exe).read_bytes()),
                       "version": (result["stdout"] + result["stderr"]).splitlines()[0]}
    return found


def extract_rtl(raw, module):
    if len(raw.encode("utf-8")) > 128 * 1024:
        raise LabError("EXTRACTION_ERROR", "extraction", "RTL response exceeds 128 KiB")
    fences = re.findall(r"```([^\n]*)\n(.*?)```", raw, re.S)
    if fences:
        if len(fences) != 1 or fences[0][0].strip().lower() not in ("", "verilog", "systemverilog", "sv"):
            raise LabError("EXTRACTION_ERROR", "extraction", "Expected exactly one RTL code block")
        source = fences[0][1].strip() + "\n"
    else:
        source = raw.strip() + "\n"
    # Remove comments for inspection, not for the saved/compiled source.
    tokens = re.sub(r'//[^\n]*|/\*.*?\*/', ' ', source, flags=re.S)
    modules = re.findall(r"\bmodule\s+(\w+)", tokens)
    if modules != [module] or len(re.findall(r"\bendmodule\b", tokens)) != 1:
        raise LabError("RTL_REJECTED", "policy", "Expected only the specified DUT module")
    if not re.match(r"\s*module\b", tokens) or not re.search(r"\bendmodule\s*$", tokens):
        raise LabError("RTL_REJECTED", "policy", "Unexpected text outside DUT module")
    if any(x in tokens for x in ('`', '"', '\\', '(*', '*)')):
        raise LabError("RTL_REJECTED", "policy", "Directives, strings, escaped names and attributes are unsupported")
    if re.search(r"\b(?:bind|force|release|defparam|program|interface|package|extern|primitive|config)\b", tokens):
        raise LabError("RTL_REJECTED", "policy", "Unsupported construct or hierarchy modification")
    if re.search(r"\b(?:tb|__lab_\w*)\b|[A-Za-z_]\w*\s*\.", tokens):
        raise LabError("RTL_REJECTED", "policy", "Hierarchical evaluator access is prohibited")
    if any(x not in ("$signed", "$unsigned", "$clog2") for x in re.findall(r"\$[A-Za-z_][\w$]*", tokens)):
        raise LabError("RTL_REJECTED", "policy", "Simulation/file/system tasks are prohibited in DUT")
    return source


def judge_simulation(result, receipt, expected_checks, nonce):
    if result["timeout"]:
        return "TIMEOUT", "Simulation wall timeout"
    if result["output_limit"]:
        return "SIM_ERROR", "Simulation output limit exceeded"
    lines = receipt.strip().splitlines()
    if len(lines) != 1:
        return "SIM_ERROR", "Missing or multiple evaluator completion receipts"
    match = re.fullmatch(r"RTL_LAB_V1 ([0-9a-f]+) checks=(\d+) errors=(\d+)", lines[0])
    if not match or match[1] != nonce or int(match[2]) != expected_checks:
        return "SIM_ERROR", "Invalid receipt, nonce or executed-check count"
    if int(match[3]) > 0:
        return "FUNCTION_FAIL", f"Independent testbench found {match[3]} mismatches"
    if result["returncode"] != 0:
        return "SIM_ERROR", "Nonzero simulator exit despite zero-error receipt"
    return "PASS", f"Independent testbench completed all {expected_checks} checks"


def validate_endpoint(base, allow_anonymous, key):
    parsed = urlsplit(base)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise LabError("ENV_ERROR", "api_config", "Set a valid LLM_BASE_URL ending in /v1")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise LabError("ENV_ERROR", "api_config", "Endpoint must not contain credentials, query or fragment")
    local = parsed.hostname in ("localhost", "127.0.0.1", "::1")
    if parsed.scheme == "http" and not local:
        raise LabError("ENV_ERROR", "api_config", "Remote endpoints require HTTPS")
    if not key and not allow_anonymous:
        raise LabError("ENV_ERROR", "api_config", "Set the chosen API key environment variable, or explicitly use --allow-anonymous")
    return base.rstrip("/") + "/chat/completions"


def generate(args, folder, payload, secret):
    endpoint = validate_endpoint(args.base_url, args.allow_anonymous, secret)
    write_json(folder / "api_request.json", {"endpoint": endpoint, "payload": payload}, secret)
    env = clean_env()
    # This secret is never in argv, the request JSON or simulation environment.
    env["RTL_LAB_API_SECRET"] = secret
    result = run_process([sys.executable, str(ROOT / "api_worker.py"),
                          str(folder / "api_request.json"), str(args.api_timeout)],
                         folder, args.api_timeout, env)
    save_process(folder, "api", result, secret)
    if result["timeout"]:
        raise LabError("API_ERROR", "api_timeout", "API wall timeout; no automatic retry")
    if result["output_limit"]:
        raise LabError("API_ERROR", "api", "API response output limit exceeded")
    try:
        envelope = json.loads(result["stdout"])
    except (ValueError, TypeError):
        raise LabError("API_ERROR", "api", "API worker did not produce valid JSON") from None
    if result["returncode"] != 0 or not envelope.get("ok"):
        raise LabError("API_ERROR", "api", str(envelope.get("error", "API request failed")))
    raw_body = envelope["body"]
    write_text(folder / "api_response.raw.json", raw_body, secret)
    try:
        body = json.loads(raw_body)
        choices = body["choices"]
        if len(choices) != 1:
            raise ValueError()
        raw = choices[0]["message"]["content"]
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError()
    except (ValueError, KeyError, TypeError):
        raise LabError("API_ERROR", "api", "Expected one nonempty choices[0].message.content string") from None
    write_text(folder / "model_output.raw.txt", raw, secret)
    if choices[0].get("finish_reason") == "length":
        raise LabError("EXTRACTION_ERROR", "extraction", "Model output hit its token limit; retained for inspection")
    return raw, {"response_model": body.get("model"), "response_id": body.get("id"),
                 "usage": body.get("usage"), "finish_reason": choices[0].get("finish_reason"),
                 "http_status": envelope.get("http_status")}


def evaluate(args, suite, spec, index, tools, secret):
    folder = suite / f"{index:03d}_{spec['id']}"
    folder.mkdir()
    start = time.monotonic()
    row = {"schema": SCHEMA, "task": spec["id"], "sample": index,
           "mode": args.mode, "source_label": args.label or {"offline": "OFFLINE_FIXTURE", "live": "LIVE_API", "codex": "LIVE_CODEX_CHATGPT"}[args.mode],
           "requested_model": args.model if args.mode != "offline" else None,
           "live_api_success": False, "started_utc": utc(), "directory": folder.name,
           "expected_checks": spec["checks"]}
    payload = {"model": args.model, "messages": [
        {"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": spec["spec"]}],
        "stream": False, args.token_field: args.max_output_tokens}
    for name in ("temperature", "seed"):
        if getattr(args, name) is not None:
            payload[name] = getattr(args, name)
    row["sampling"] = {k: v for k, v in payload.items() if k not in ("messages", "model")}
    if args.mode == "codex":
        row["sampling"] = {"reasoning_effort": args.codex_reasoning, "temperature": None, "seed": None,
                           "max_output_tokens": None, "note": "Codex CLI defaults; see codex_request.json"}
        payload = {"model": args.model, "prompt": SYSTEM_PROMPT + "\n\n" + spec["spec"],
                   "note": "Exact CLI prompt and arguments are saved in codex_request.json and codex.json"}
    write_json(folder / "prompt.json", {"mode": args.mode, "request": payload}, secret)
    write_json(folder / "spec.json", spec, secret)
    try:
        if args.mode == "live":
            raw, api_meta = generate(args, folder, payload, secret)
            row.update(api_meta)
            row["live_api_success"] = True
        elif args.mode == "codex":
            from codex_adapter import generate as generate_codex
            raw, codex_meta = generate_codex(args, folder, spec)
            row.update(codex_meta)
        else:
            source_path = Path(args.rtl_dir) / (spec["id"] + ".sv")
            row["offline_source"] = str(source_path.resolve())
            if not source_path.is_file():
                raise LabError("ENV_ERROR", "offline_input", f"Missing fixture: {spec['id']}.sv")
            if source_path.stat().st_size > 128 * 1024:
                raise LabError("EXTRACTION_ERROR", "extraction", "Offline input exceeds 128 KiB")
            raw = source_path.read_text(encoding="utf-8-sig")
            write_text(folder / "model_output.raw.txt", raw, secret)
        rtl = extract_rtl(raw, spec["module"])
        write_text(folder / "dut.sv", rtl, secret)
        row["rtl_sha256"] = digest((folder / "dut.sv").read_bytes())
        tb_bytes = (ROOT / "tasks" / (spec["id"] + "_tb.sv")).read_bytes()
        if digest(tb_bytes) != spec["tb_sha256"]:
            raise LabError("ENV_ERROR", "testbench", "Fixed testbench differs from manifest hash")
        (folder / "testbench.sv").write_bytes(tb_bytes)
        row["testbench_sha256"] = digest(tb_bytes)
        for name, expected in spec.get("assets", {}).items():
            if Path(name).name != name:
                raise LabError("ENV_ERROR", "testbench", "Invalid asset path")
            data = (ROOT / "tasks" / name).read_bytes()
            if digest(data) != expected:
                raise LabError("ENV_ERROR", "testbench", "Test vector hash changed")
            (folder / name).write_bytes(data)
        from backends import BACKENDS
        row.update(BACKENDS[getattr(args, "backend", "icarus")]().evaluate(folder, spec, tools, args, secret))
    except LabError as exc:
        row.update(status=exc.status, stage=exc.stage, message=exc.message)
    except (OSError, UnicodeError) as exc:
        row.update(status="ENV_ERROR", stage="io", message=type(exc).__name__)
    except KeyboardInterrupt:
        row.update(status="INTERRUPTED", stage="interrupted", message="User interrupted; child process cleaned up")
    row["elapsed_seconds"] = round(time.monotonic() - start, 4)
    row["finished_utc"] = utc()
    write_json(folder / "result.json", row, secret)
    return row


def summarize(suite, rows, secret=""):
    counts = {status: sum(r["status"] == status for r in rows) for status in sorted({r["status"] for r in rows})}
    result = {"schema": SCHEMA, "generated_utc": utc(), "counts": counts, "total": len(rows),
              "note": "Offline fixtures are not LLM benchmark results. Denominator includes all recorded samples.",
              "live_api_successes": sum(r.get("live_api_success", False) for r in rows),
              "codex_generation_successes": sum(r.get("codex_generation_success", False) for r in rows), "results": rows}
    write_json(suite / "summary.json", result, secret)
    fields = ["task", "sample", "mode", "source_label", "requested_model", "response_model", "status",
              "stage", "message", "live_api_success", "codex_generation_success", "expected_checks", "compile_seconds", "simulate_seconds",
              "elapsed_seconds", "directory", "rtl_sha256", "testbench_sha256"]
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    write_text(suite / "summary.csv", buffer.getvalue(), secret)


def positive(value):
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise argparse.ArgumentTypeError("must be finite and positive")
    return value


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mode", choices=("offline", "live", "codex"), default="offline")
    p.add_argument("--rtl-dir", default=str(ROOT / "examples" / "correct"))
    p.add_argument("--task", default="all")
    p.add_argument("--samples", type=int, default=1)
    p.add_argument("--out", default=str(ROOT / "runs"))
    p.add_argument("--label", default="")
    p.add_argument("--iverilog", default=os.environ.get("IVERILOG"))
    p.add_argument("--vvp", default=os.environ.get("VVP"))
    p.add_argument("--model", default=os.environ.get("LLM_MODEL", ""))
    p.add_argument("--base-url", default=os.environ.get("LLM_BASE_URL", ""))
    p.add_argument("--api-key-env", default="LLM_API_KEY")
    p.add_argument("--allow-anonymous", action="store_true")
    p.add_argument("--codex-executable", default=None)
    p.add_argument("--codex-reasoning", choices=("low", "medium", "high", "xhigh", "max", "ultra"), default="low")
    p.add_argument("--temperature", type=float, default=None)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--max-output-tokens", type=int, default=2048)
    p.add_argument("--token-field", choices=("max_tokens", "max_completion_tokens"), default="max_tokens")
    p.add_argument("--api-timeout", type=positive, default=90)
    p.add_argument("--compile-timeout", type=positive, default=10)
    p.add_argument("--sim-timeout", type=positive, default=5)
    args = p.parse_args(argv)
    if args.samples < 1 or args.max_output_tokens < 1 or (args.temperature is not None and (not math.isfinite(args.temperature) or not 0 <= args.temperature <= 2)):
        p.error("samples/tokens must be positive; temperature must be finite in [0, 2]")
    secret = os.environ.get(args.api_key_env, "")
    suite = Path(args.out).resolve() / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_") + uuid.uuid4().hex[:10])
    suite.mkdir(parents=True)
    write_text(suite / "RUN_MODE.txt", args.mode.upper() + {"offline": " — supplied RTL, no model call\n", "live": " — configured HTTP API; inspect per-sample provenance\n", "codex": " — real Codex CLI generation using existing ChatGPT login\n"}[args.mode])
    rows = []
    try:
        tools = inspect_tools(args, suite)
        manifest = json.loads((ROOT / "tasks" / "manifest.json").read_text(encoding="utf-8"))
        write_json(suite / "environment.json", {"python": sys.version, "python_executable": sys.executable,
                   "platform": sys.platform, "tools": tools, "manifest_sha256": digest((ROOT / "tasks" / "manifest.json").read_bytes()),
                   "runner_sha256": digest(Path(__file__).read_bytes()), "api_worker_sha256": digest((ROOT / "api_worker.py").read_bytes())})
        if args.mode != "offline" and not args.model:
            raise LabError("ENV_ERROR", "api_config", "Set LLM_MODEL or --model; no default paid model is selected")
        # Validate before recording an endpoint anywhere.
        if args.mode == "live":
            validate_endpoint(args.base_url, args.allow_anonymous, secret)
        for spec in manifest:
            if args.task not in ("all", spec["id"]):
                continue
            for _ in range(args.samples):
                row = evaluate(args, suite, spec, len(rows) + 1, tools, secret)
                rows.append(row)
                summarize(suite, rows, secret)
                print(f"{row['task']}: {row['status']} ({row['mode']})")
                if row["status"] == "INTERRUPTED":
                    break
            if rows and rows[-1]["status"] == "INTERRUPTED":
                break
    except LabError as exc:
        rows.append({"task": "__preflight__", "mode": args.mode, "status": exc.status,
                     "stage": exc.stage, "message": exc.message, "live_api_success": False})
    except (OSError, ValueError) as exc:
        rows.append({"task": "__preflight__", "mode": args.mode, "status": "ENV_ERROR",
                     "stage": "environment", "message": type(exc).__name__, "live_api_success": False})
    summarize(suite, rows, secret)
    print("Results: " + str(suite))
    return 0 if rows and all(r["status"] == "PASS" for r in rows) else 1


if __name__ == "__main__":
    # Let adapters share this module's exception class when launched as a script.
    sys.modules.setdefault("rtl_lab", sys.modules[__name__])
    raise SystemExit(main())
