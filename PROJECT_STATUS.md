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

## Decisions

- **D1 (plan amendment):** added invariant 7 (outer holdout once per dataset; test scored once)
  and the M2/M4/M5/tooling amendments to IMPLEMENTATION_PLAN.md.
- **D2:** `python-multipart` added as a runtime dependency. FastAPI requires it for the
  multipart upload in `POST /datasets` (M7).
- **D3:** `requirements-lock.txt` is a *universal* lock (`uv pip compile --universal
  --python-version 3.11`), so one file serves both CI versions. numpy is resolved to 2.4.x on
  3.11 and 2.5.x on 3.12+ via environment markers.

## Last updated

2026-10-22 — T0 (Implementation Engineer)
