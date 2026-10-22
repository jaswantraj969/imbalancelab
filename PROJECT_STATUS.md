# Project Status

Status values: `not started` · `in progress` · `done` (engineer's acceptance criteria pass) ·
`verified` (only the supervisor sets this, after review).

| Milestone | Description | Status | Evidence |
|---|---|---|---|
| M0 | Skeleton, tooling, plan | done | [REVIEW_PACKET.md](REVIEW_PACKET.md) (T0) |
| M1 | Data loading, schema validation, profiling | not started | — |
| M2 | Splitting + leakage-safe pipeline builder | not started | — |
| M3 | Metrics module incl. edge cases | not started | — |
| M4 | Experiment runner, baselines, run records | not started | — |
| M5 | Threshold analysis (OOF/validation only) | not started | — |
| M6 | Evidence-based audit report | not started | — |
| M7 | FastAPI endpoints | not started | — |
| M8 | Streamlit frontend (via API only) | not started | — |
| M9 | Model persistence + inference endpoint | not started | — |
| M10 | Docs + case study from real results | not started | — |

## Known issues

- Plan step "tree -L 3" substituted with `find` (no `tree` binary in Git Bash on this machine); see REVIEW_PACKET.md T0 deviations.

## Last updated

2026-10-22 — T0 (Implementation Engineer)
