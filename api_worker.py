"""Isolated, bounded Chat Completions HTTP request. No SDK or automatic retries."""
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never forward Authorization to a redirected destination.
        return None


def main():
    secret = os.environ.get("RTL_LAB_API_SECRET", "")
    config = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if secret:
        headers["Authorization"] = "Bearer " + secret
    request = urllib.request.Request(config["endpoint"],
        data=json.dumps(config["payload"]).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=float(sys.argv[2])) as response:
            raw = response.read(1024 * 1024 + 1)
            if len(raw) > 1024 * 1024:
                raise ValueError("response size limit")
            result = {"ok": True, "http_status": response.status, "body": raw.decode("utf-8")}
    except urllib.error.HTTPError as exc:
        # Do not echo response bodies/headers, which may contain credentials.
        result = {"ok": False, "error": f"HTTP {exc.code}; no retry; check endpoint, credentials and model compatibility"}
    except Exception as exc:
        result = {"ok": False, "error": type(exc).__name__ + "; request failed; no retry"}
    text = json.dumps(result, ensure_ascii=False)
    if secret:
        text = text.replace(secret, "[REDACTED]").replace(json.dumps(secret)[1:-1], "[REDACTED]")
    print(text)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
