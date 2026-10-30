# Working on XZY01 RTL Lab

- Latest user experiment constraint (2026-10-16): follow `FYP_FIXED_INPUT_RTL_RULES.md`. Preserve original task inputs and tests byte-for-byte; identical actual prompt content across models for each task; this new mainline uses one model call directly producing RTL, without candidate IR or feedback. Freeze and coordinator-review the finite new design before execution; preserve all historical evidence.

- Read README.md and ARCHITECTURE.md before editing the runner.
- Keep model generation, task/testbench definitions, scheduling and simulation adapters separable.
- Use Python 3.10+ standard library unless a dependency materially improves the experiment.
- Never expose credentials. Exclude machine-local configs, raw account logs, runs and generated binaries from Git.
- Treat generated RTL as untrusted input. Keep the fixed testbench and vector hashes independent of the generator.
- Never count offline fixtures or synthetic HTTP/commercial-tool tests as real model/EDA evidence.
- Existing ECE shared VDI: no SSH, no supported batch EDA service, no EDA scheduler. Export one-case manual scripts until new explicit school permission exists.
- Do not change an active experiment's source. Create a new run after code/task/tool changes.
- Run `python -m unittest -v test_lab test_batch test_dev` for meaningful runner changes. Synthesis tests require native Yosys in WSL/Linux or a native Windows installation.
- FSM study changes also require `test_fsm`; preserve its two-call cap, public/private checker separation, and no automatic retries after unknown outcomes.
- Keep dev10 source/split locks and adapted-benchmark labels. Never mix development tasks or near duplicates into the final set.
- Synthesis review must bind the original result and RTL hashes; never overwrite model output or silently repair baseline failures.
- Real Codex/API experiments consume account usage; keep concurrency/call caps explicit and preserve requested model IDs.
- Keep Chinese user documentation and evidence summaries accurate about what was actually executed.
