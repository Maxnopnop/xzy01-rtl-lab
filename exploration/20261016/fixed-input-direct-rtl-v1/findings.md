# Findings
Rules read: FYP_FIXED_INPUT_RTL_RULES.md, AGENTS.md, validation/R1BC_RULE_REVIEW_20261016.md.
Five R1b supported families: rt_sequence, sticky_alarm, event_parity, request_delay, debounce3. Historical R1b/R1c generation is not pure direct RTL. All original evidence preserved.
Actual system/user content and wrapping must match across models; backend-added prompt remains an execution blocker unless evidenced.
request_delay has following-cycle wording risk: original reference phase0->1->2(q=1)->3, no prompt clarification added. Icarus/vvp current executable hashes match archived versions; current Yosys executable and service support remain unverified.
