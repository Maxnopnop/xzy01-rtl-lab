# Findings — paired feedback study, 2026-10-01

- Previous frozen 48-turn study is complete at commit 186357a. Scores 7/8, 7/8, 8/8; all checked IRs were initially correct, so it did not test feedback-driven repair.
- One real erroneous IR exists at evidence/fsm48/jobs/m02__rt_sequence__table__s001/stage1/response.txt. It sends S4 on input 0 to S3 instead of S2. Preserve its exact bytes and provenance.
- Existing FSM interpreter handles data-only single-bit Moore FSMs, explicit reset, finite graph equivalence and timed pre/post-edge simulation.
- Existing guarded Codex CLI adapter uses ChatGPT login, disables tools and records usage. Existing batch subprocess cleanup and Yosys replay can be reused.
- Current account usage readout: 63% used in the available window; no credit purchase or reset is needed/authorized. This is account-wide, not experiment-specific.
- Repository is clean. Existing source/benchmark locks must remain unchanged. New development families and held-out tasks will live in a separate bank.
- User explicitly authorized autonomous completion, progressive scale-up, GitHub sync inherited from prior turns, and shutdown after verified completion; no intermediate confirmation is needed.
- Frozen bank contains four genuinely different new development behaviors and two held-out candidates. Candidate hold-out status is limited: offline verified and not model-used, but no external expert review or exhaustive similarity audit is claimed.
- Paired prompts differ only in computed public feedback. No fresh first-stage generation is charged in this conditional repair experiment; prior natural-IR provenance remains recorded.
