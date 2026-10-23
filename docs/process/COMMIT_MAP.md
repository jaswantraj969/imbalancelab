# Commit map (history rewrite before publication)

The history was rewritten with `git filter-repo` before the repository was made public (decision
D38 in [PROJECT_STATUS.md](PROJECT_STATUS.md)). Every commit received a new hash. Author and commit
dates are unchanged. Use this table to translate hashes quoted in older notes, CI run pages
or release notes created before the rewrite.

| Old | New | Date (author) | Subject |
|---|---|---|---|
| `03ead06` | `d314ffd` | 2026-10-22T12:35:27+05:00 | T0: project skeleton, tooling, plan |
| `5fbb139` | `30ba02a` | 2026-10-22T12:47:18+05:00 | Plan amendments: invariant 7, lock file, CI, pyarrow |
| `fdc15f3` | `61796ba` | 2026-10-22T12:53:07+05:00 | M1: data loading, schema validation, profiling |
| `d906960` | `7d090fb` | 2026-10-22T12:57:07+05:00 | M2: outer holdout, inner CV, cross-boundary duplicates, pipeline builder |
| `58c6241` | `0f2a707` | 2026-10-22T12:58:37+05:00 | M3: metrics with explicit undefined cases |
| `9e207a5` | `680141c` | 2026-10-22T13:02:20+05:00 | M4: experiment runner, baselines, file-based run records |
| `7ce0891` | `c1c0863` | 2026-10-22T13:05:52+05:00 | M5: OOF threshold analysis with provenance guard; one-shot final evaluation |
| `68a5647` | `40013a7` | 2026-10-22T13:12:35+05:00 | M6: evidence-based audit report (Markdown + HTML) from run records |
| `a9ff54e` | `25e87da` | 2026-10-22T13:17:07+05:00 | M7: FastAPI endpoints over a library workflow layer |
| `45706fc` | `cf84f51` | 2026-10-22T13:25:29+05:00 | M8: Streamlit frontend as a pure API client |
| `b250b9a` | `1f0f4bd` | 2026-10-22T13:29:18+05:00 | M9: model persistence with integrity check; inference endpoint |
| `91c6f54` | `43c8cac` | 2026-10-22T13:41:26+05:00 | M10: README, case study on mammography from real run records, smoke script |
| `855c023` | `188d109` | 2026-10-22T13:45:55+05:00 | Final report for supervisor review |
| `e727ca4` | `9a28c93` | 2026-10-22T14:46:55+05:00 | T-R1: duplicate-aware splitting, honest two-run case study, RF determinism, UI evidence |
| `924b401` | `28bc061` | 2026-10-22T14:49:06+05:00 | T-R1: review packet entry and revised final report |
| `01a9d51` | `4544ca3` | 2026-10-22T15:17:11+05:00 | T-R2: bootstrap CIs, evaluation coverage, cluster analysis, protocol history, ODbL notices |
| `573b2ba` | `fcad5d9` | 2026-10-22T15:17:54+05:00 | T-R2: review packet entry and regenerated final report |
| `f96c85a` | `bd51d15` | 2026-10-23T00:37:57+05:00 | T-R3: calibration disclosure, paired bootstrap, recall scope, httpx2, process docs moved |
| `0e9574e` | `ffdccce` | 2026-10-23T00:42:49+05:00 | T-R3: review packet entry and regenerated final report |
| `e840915` | `c11399f` | 2026-10-23T01:03:43+05:00 | T-R5: test-scoring history in report/API/UI; persistence, API-exposure and threshold docs |
| `43a32aa` | `9457290` | 2026-10-23T01:08:35+05:00 | T-R5: review packet entry |
| `4298219` | `b2d9510` | 2026-10-23T22:49:09+05:00 | Release prep: MIT LICENSE, README summary/badge/headline/licence, scrub local paths in logs |
