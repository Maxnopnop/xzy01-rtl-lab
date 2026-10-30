# Legacy regression impact audit

No model calls. The three failures and one error are assertions within two legacy HTTP tests, not four independent experiment faults.

1. test_lab mock HTTP ok: RemoteDisconnected rather than success.
2. truncated: API_ERROR instead of EXTRACTION_ERROR because no response reached extraction.
3. observed requests: 0 instead of 6.
4. batch call-cap fixture: 0 instead of 1 (does not demonstrate exceeding cap).

Controlled loopback reproduction with original api_worker.py and rtl_lab.clean_env: automatic urllib proxy discovery gives 0 server requests and RemoteDisconnected; disabling discovery only in an isolated diagnostic child gives exactly 1 server request and HTTP 200. Proxy discovery sees http/https and does not bypass 127.0.0.1. No persistent proxy, source or frozen file changed.

Current continuation uses direct-api-v1 transport.py http.client with explicit route, not legacy api_worker.py or rtl_lab.generate. Its frozen extractor is loaded as selected AST definitions only; it does not call the old HTTP client. Parent/source/input/route hashes and local preflight verified. All 240 payloads, grouped into 80 task/condition/sample triples, equal after removing only model. All 197 previous HTTP worker receipts had 180.5s timeout (180 request + .5 worker allowance); remaining path unchanged. Total batch deadline removal affects scheduling, not per-request token/timeout/prompt parameters.

Conclusion: these legacy test failures do not block the reviewed remaining 43 slots or establish a three-model prompt bias. They remain real legacy proxy-isolation defects, not a fully green general suite. Provider failures remain possible. Slots83 and197 are service failures, not RTL mistakes; full-sample and paired-available analyses must separate these missing outcomes and task eligibility labels. Different run times/upstream state remain uncontrolled. No guarantee of hidden provider internals or RAG gains.
