# Task Plan: Paired feedback study and bounded scale-up

## Goal
Complete a reproducible paired-feedback experiment, expand to new FSM task families, verify and sync all results, then perform the user-authorized normal Windows shutdown.

## Finish line and constraints
- Stage A: 32 new model turns: 2 models x 4 fixed erroneous IRs x 2 feedback conditions x 2 repeats.
- Stage B: 64 new turns on 8 fixed erroneous IRs from 4 new development families; identical pairing. Total hard cap 96 new turns, concurrency 2, no paid-credit purchase/reset, no automatic model retries.
- Freeze all tasks, faults, public feedback, private tests, conditions and source before generation. Escalate scale only after Stage A completes without infrastructure/checker inconsistencies; do not condition expansion on a positive effect.
- Build 2 additional held-out task families and lock them before running either stage. Offline oracle checks are allowed; no model evaluation or tuning on held-out tasks this round.
- Every accepted DUT receives Icarus specification/IR tests and independent Yosys synthesis. Distinguish real recorded error from deliberate injected faults.
- Complete meaningful tests, evidence/hash verification, Chinese findings, GitHub push and successful CI. Finish does NOT mean a positive research result or a finished FYP.
- Shutdown only after these checks and clean synchronization. Use normal shutdown without force-closing unsaved applications; record the result and completion state before scheduling it. No school SSH, batch EDA, or messages.

## Current Phase
Phase 2: Offline verification

## Next Step
Finish full regression, commit frozen protocol/code/bank, then start Stage A without further source edits.

## Phases
1. Bank, fixed split and experimental protocol — complete
2. Paired single-call runner and offline regression — in_progress
3. Stage A 32-turn paired study — pending
4. Stage B 64-turn expansion — pending
5. Synthesis, analysis, literature and evidence verification — pending
6. GitHub/CI, final archive and authorized shutdown — pending

## Loop checklist
- [x] Define finish line, deliverables and constraints.
- [x] Set finite budget and stopping gates.
- [ ] Execute, verify and record each phase.
- [ ] Deliver evidence and state research limits.

## Errors
- Read-only `shutdown.exe /?` returned Windows error 203 instead of help. The shutdown executable and PowerShell Stop-Computer cmdlet exist. Use an independently verified non-force shutdown path at the final gate; no shutdown has been attempted yet.
