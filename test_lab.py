"""Regression tests. HTTP fixtures below are MOCKS, never real LLM outputs."""
import argparse
from contextlib import redirect_stdout
import ctypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import os
from pathlib import Path
import sys
import threading
import time
import unittest
import uuid

import rtl_lab as lab

OUT = Path(os.environ.get("RTL_LAB_TEST_OUT", str(lab.ROOT / "test-results"))).resolve() / uuid.uuid4().hex[:12]
OUT.mkdir(parents=True)


def pid_alive(pid):
    if os.name == "nt":
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.restype = ctypes.c_void_p
        kernel.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
        kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        handle = kernel.OpenProcess(0x100000, 0, pid)
        if not handle:
            return False
        try:
            return kernel.WaitForSingleObject(handle, 0) == 258
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        # Linux killed grandchildren may briefly remain zombies until reaped.
        stat = Path(f"/proc/{pid}/stat")
        if stat.exists() and stat.read_text().split()[2] == "Z":
            return False
        return True
    except ProcessLookupError:
        return False


class Regression(unittest.TestCase):
    def test_codex_missing_executable_as_script(self):
        target = OUT / "codex_missing_executable"
        result = lab.run_process([sys.executable, str(lab.ROOT / 'rtl_lab.py'),
            '--mode', 'codex', '--model', 'gpt-5.6-sol', '--task', 'adder8',
            '--codex-executable', str(OUT / 'not-a-codex-executable'), '--out', str(target)], OUT, 20)
        self.assertEqual(result['returncode'], 1)
        self.assertNotIn('Traceback', result['stderr'])
        data = json.loads(next(target.glob('*/summary.json')).read_text())
        self.assertEqual(data['counts'], {'ENV_ERROR': 1})
        self.assertEqual(data['codex_generation_successes'], 0)

    def test_offline_matrix(self):
        matrix = [
            ("correct", "all", ["PASS"] * 20),
            ("wrong", "all", ["FUNCTION_FAIL"] * 20),
            ("syntax_error", "adder8", ["COMPILE_FAIL"]),
            ("timeout", "adder8", ["TIMEOUT"]),
            ("fake_pass", "adder8", ["RTL_REJECTED"]),
            ("carry_bug", "adder8", ["FUNCTION_FAIL"]),
            ("unknown", "adder8", ["FUNCTION_FAIL"]),
            ("async_reset", "counter4", ["FUNCTION_FAIL"]),
            ("reset_priority", "counter4", ["FUNCTION_FAIL"]),
            ("saturate", "counter4", ["FUNCTION_FAIL"]),
            ("encoder_zero", "encoder4", ["FUNCTION_FAIL"]),
        ]
        evidence = []
        for group, task, expected in matrix:
            with self.subTest(group=group):
                target = OUT / "offline" / group
                with redirect_stdout(io.StringIO()):
                    code = lab.main(["--rtl-dir", str(lab.ROOT / "examples" / group),
                                     "--task", task, "--out", str(target), "--sim-timeout", "1"])
                summary_path = next(target.glob("*/summary.json"))
                data = json.loads(summary_path.read_text(encoding="utf-8"))
                actual = [r["status"] for r in data["results"]]
                evidence.append({"fixture": group, "expected": expected, "actual": actual,
                                 "summary": str(summary_path.relative_to(OUT)), "matched": expected == actual})
                lab.write_json(OUT / "offline_matrix.json", evidence)
                self.assertEqual(actual, expected)
                self.assertEqual(code, 0 if group == "correct" else 1)
                self.assertEqual(data["live_api_successes"], 0)
                if group == "timeout":
                    stage = json.loads(next(target.glob("*/*/simulate.json")).read_text())
                    self.assertTrue(stage["killed"])
                    self.assertFalse(pid_alive(stage["pid"]))

    def test_verdict_protocol(self):
        good = {"timeout": False, "output_limit": False, "returncode": 0, "stdout": "PASS"}
        cases = [("", "SIM_ERROR"), ("PASS", "SIM_ERROR"),
                 ("RTL_LAB_V1 abc checks=2 errors=0", "PASS"),
                 ("RTL_LAB_V1 abc checks=1 errors=0", "SIM_ERROR"),
                 ("RTL_LAB_V1 stale checks=2 errors=0", "SIM_ERROR"),
                 ("RTL_LAB_V1 abc checks=2 errors=1", "FUNCTION_FAIL"),
                 ("RTL_LAB_V1 abc checks=2 errors=0\nPASS", "SIM_ERROR")]
        for receipt, expected in cases:
            with self.subTest(receipt=receipt):
                self.assertEqual(lab.judge_simulation(good, receipt, 2, "abc")[0], expected)
        self.assertEqual(lab.judge_simulation({**good, "returncode": 1}, cases[2][0], 2, "abc")[0], "SIM_ERROR")
        self.assertEqual(lab.judge_simulation({**good, "timeout": True}, cases[2][0], 2, "abc")[0], "TIMEOUT")

    def test_extraction_and_policy(self):
        source = (lab.ROOT / "examples/correct/adder8.sv").read_text(encoding="utf-8")
        self.assertIn("module adder8", lab.extract_rtl("Here is RTL.\n```verilog\n" + source + "```", "adder8"))
        bad = ["```verilog\n" + source + "```\n```verilog\n" + source + "```",
               source + "module tb; endmodule", source.replace("endmodule", "$finish; endmodule"),
               source.replace("endmodule", "initial tb.errors = 0; endmodule"),
               source.replace("endmodule", '`include "other.sv"\nendmodule'),
               source.replace("endmodule", 'initial $system("echo bad"); endmodule')]
        for raw in bad:
            with self.subTest(raw=raw[-60:]):
                with self.assertRaises(lab.LabError):
                    lab.extract_rtl(raw, "adder8")

    def test_environment_failure_recorded(self):
        target = OUT / "missing_tools"
        with redirect_stdout(io.StringIO()):
            code = lab.main(["--iverilog", str(OUT / "missing-executable"), "--out", str(target)])
        self.assertEqual(code, 1)
        data = json.loads(next(target.glob("*/summary.json")).read_text())
        self.assertEqual(data["counts"], {"ENV_ERROR": 1})

    def test_unconfigured_live_recorded(self):
        target = OUT / "unconfigured_live"
        with redirect_stdout(io.StringIO()):
            code = lab.main(["--mode", "live", "--model", "", "--out", str(target)])
        self.assertEqual(code, 1)
        data = json.loads(next(target.glob("*/summary.json")).read_text())
        self.assertEqual(data["counts"], {"ENV_ERROR": 1})
        self.assertEqual(data["live_api_successes"], 0)

    def test_unique_runs(self):
        target = OUT / "uniqueness"
        for _ in range(2):
            with redirect_stdout(io.StringIO()):
                self.assertEqual(lab.main(["--task", "encoder4", "--out", str(target)]), 0)
        self.assertEqual(len(list(target.glob("*/summary.json"))), 2)

    def test_timeout_cleans_process_tree(self):
        # Real parent/child processes, not a mocked cleanup call.
        code = "import subprocess,sys,time; p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); print(p.pid,flush=True); time.sleep(30)"
        result = lab.run_process([sys.executable, "-c", code], OUT, 0.8)
        lab.save_process(OUT, "process_tree_timeout", result)
        self.assertTrue(result["timeout"])
        self.assertTrue(result["killed"])
        self.assertFalse(pid_alive(result["pid"]))
        self.assertFalse(pid_alive(int(result["stdout"].strip())))

    def test_output_limit(self):
        result = lab.run_process([sys.executable, "-c", "import sys; sys.stdout.write('x'*4000000)"], OUT, 5)
        self.assertTrue(result["output_limit"])
        self.assertLessEqual(len(result["stdout"]), lab.MAX_LOG)

    def test_endpoint_policy(self):
        for endpoint in ("", "http://example.org/v1", "https://key@example.org/v1", "https://example.org/v1?key=hidden"):
            with self.assertRaises(lab.LabError):
                lab.validate_endpoint(endpoint, True, "")
        with self.assertRaises(lab.LabError):
            lab.validate_endpoint("https://example.org/v1", False, "")
        self.assertEqual(lab.validate_endpoint("http://127.0.0.1:11434/v1/", True, ""), "http://127.0.0.1:11434/v1/chat/completions")

    def test_mock_http_transport(self):
        fixture = (lab.ROOT / "examples/correct/adder8.sv").read_text(encoding="utf-8")
        secret = "SYNTHETIC_TEST_SECRET_" + uuid.uuid4().hex
        observed = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                observed.append({"path": self.path, "auth_ok": self.headers.get("Authorization") == "Bearer " + secret,
                                 "request": json.loads(self.rfile.read(int(self.headers["Content-Length"])))})
                case = self.path.split('/')[1]
                status = 401 if case == "auth_fail" else 302 if case == "redirect" else 200
                if case == "slow":
                    time.sleep(1)
                self.send_response(status)
                if case == "redirect":
                    self.send_header("Location", "/should-never-be-called")
                self.end_headers()
                body = {"model": "MOCK_NOT_LLM", "choices": [{"message": {"content": fixture + "\n// " + secret},
                          "finish_reason": "length" if case == "truncated" else "stop"}], "usage": {"total_tokens": 1}}
                raw = b"not json" if case == "invalid" else json.dumps(body).encode()
                try:
                    self.wfile.write(raw)
                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                    pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        folder = OUT / "MOCK_HTTP_NOT_REAL_LLM"
        folder.mkdir()
        lab.write_text(folder / "NOTICE.txt", "LOCAL SYNTHETIC HTTP TRANSPORT TEST ONLY. No real model or paid API was called.\n")
        try:
            for case in ("ok", "auth_fail", "invalid", "truncated", "slow", "redirect"):
                with self.subTest(case=case):
                    dest = folder / case
                    dest.mkdir()
                    args = argparse.Namespace(base_url=f"http://127.0.0.1:{server.server_port}/{case}/v1",
                                              allow_anonymous=False, api_timeout=0.3 if case == "slow" else 5)
                    payload = {"model": "MOCK_NOT_LLM", "messages": [{"role": "user", "content": "TEST_ONLY"}], "max_tokens": 128}
                    if case == "ok":
                        raw, meta = lab.generate(args, dest, payload, secret)
                        self.assertIn("module adder8", raw)
                        self.assertEqual(meta["response_model"], "MOCK_NOT_LLM")
                    else:
                        with self.assertRaises(lab.LabError) as caught:
                            lab.generate(args, dest, payload, secret)
                        self.assertEqual(caught.exception.status, "EXTRACTION_ERROR" if case == "truncated" else "API_ERROR")
                    for path in dest.iterdir():
                        self.assertNotIn(secret, path.read_text(encoding="utf-8"))
            self.assertEqual(len(observed), 6)
            self.assertTrue(all(x["auth_ok"] for x in observed))
            lab.write_json(folder / "observed_requests_without_credentials.json", observed)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Regression)
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    report = stream.getvalue()
    lab.write_text(OUT / "unittest.log", report)
    lab.write_json(OUT / "test_summary.json", {"tests_run": result.testsRun, "failures": len(result.failures),
                   "errors": len(result.errors), "successful": result.wasSuccessful(), "python": sys.version,
                   "platform": sys.platform, "http_tests": "LOCAL MOCK ONLY; not a real LLM", "completed_utc": lab.utc()})
    print(report)
    print("Evidence: " + str(OUT))
    raise SystemExit(0 if result.wasSuccessful() else 1)
