# Commit map (history rewrite before publication)

The history was rewritten with `git filter-repo` before the repository was made public (decision
D38 in [PROJECT_STATUS.md](PROJECT_STATUS.md)). Every commit received a new hash. Author and commit
dates are unchanged. Use this table to translate hashes quoted in older notes, CI run pages
or release notes created before the rewrite.

Updated 2026-10-24 (decision D39): hashes changed a second time when commit-message
co-author trailers were removed. The **New** column shows the current hashes. File contents and
dates are unchanged.

| Old | New | Date (author) | Subject |
|---|---|---|---|
| `03ead06` | `b66dfe2` | 2026-10-22T12:35:27+05:00 | T0: project skeleton, tooling, plan |
| `5fbb139` | `0f85dac` | 2026-10-22T12:47:18+05:00 | Plan amendments: invariant 7, lock file, CI, pyarrow |
| `fdc15f3` | `4ba075c` | 2026-10-22T12:53:07+05:00 | M1: data loading, schema validation, profiling |
| `d906960` | `2e00973` | 2026-10-22T12:57:07+05:00 | M2: outer holdout, inner CV, cross-boundary duplicates, pipeline builder |
| `58c6241` | `4caed82` | 2026-10-22T12:58:37+05:00 | M3: metrics with explicit undefined cases |
| `9e207a5` | `f7da970` | 2026-10-22T13:02:20+05:00 | M4: experiment runner, baselines, file-based run records |
| `7ce0891` | `189a2b2` | 2026-10-22T13:05:52+05:00 | M5: OOF threshold analysis with provenance guard; one-shot final evaluation |
| `68a5647` | `ce31187` | 2026-10-22T13:12:35+05:00 | M6: evidence-based audit report (Markdown + HTML) from run records |
| `a9ff54e` | `6bf1a32` | 2026-10-22T13:17:07+05:00 | M7: FastAPI endpoints over a library workflow layer |
| `45706fc` | `58769d0` | 2026-10-22T13:25:29+05:00 | M8: Streamlit frontend as a pure API client |
| `b250b9a` | `6fbaf2d` | 2026-10-22T13:29:18+05:00 | M9: model persistence with integrity check; inference endpoint |
| `91c6f54` | `ea39d3e` | 2026-10-22T13:41:26+05:00 | M10: README, case study on mammography from real run records, smoke script |
| `855c023` | `fc1dd90` | 2026-10-22T13:45:55+05:00 | Final report for supervisor review |
| `e727ca4` | `6711d8c` | 2026-10-22T14:46:55+05:00 | T-R1: duplicate-aware splitting, honest two-run case study, RF determinism, UI evidence |
| `924b401` | `4b5c299` | 2026-10-22T14:49:06+05:00 | T-R1: review packet entry and revised final report |
| `01a9d51` | `94f17ca` | 2026-10-22T15:17:11+05:00 | T-R2: bootstrap CIs, evaluation coverage, cluster analysis, protocol history, ODbL notices |
| `573b2ba` | `f71f568` | 2026-10-22T15:17:54+05:00 | T-R2: review packet entry and regenerated final report |
| `f96c85a` | `30a0d77` | 2026-10-23T00:37:57+05:00 | T-R3: calibration disclosure, paired bootstrap, recall scope, httpx2, process docs moved |
| `0e9574e` | `7c4e8f3` | 2026-10-23T00:42:49+05:00 | T-R3: review packet entry and regenerated final report |
| `e840915` | `bd47d26` | 2026-10-23T01:03:43+05:00 | T-R5: test-scoring history in report/API/UI; persistence, API-exposure and threshold docs |
| `43a32aa` | `c1b3ec1` | 2026-10-23T01:08:35+05:00 | T-R5: review packet entry |
| `4298219` | `e60384d` | 2026-10-23T22:49:09+05:00 | Release prep: MIT LICENSE, README summary/badge/headline/licence, scrub local paths in logs |

## Second rewrite (D39): first-rewrite hash → current hash

The co-author trailers were removed from commit messages on 2026-10-24, so every commit got
a new hash again. File contents and dates did not change. CI runs, release notes and
D38 text written between the two rewrites cite the first-rewrite hashes below. The last row
is a commit-message reword of the D39 commit itself.

| First rewrite | Current | Date (author) | Subject |
|---|---|---|---|
| `d314ffd` | `b66dfe2` | 2026-10-22T12:35:27+05:00 | T0: project skeleton, tooling, plan |
| `30ba02a` | `0f85dac` | 2026-10-22T12:47:18+05:00 | Plan amendments: invariant 7, lock file, CI, pyarrow |
| `61796ba` | `4ba075c` | 2026-10-22T12:53:07+05:00 | M1: data loading, schema validation, profiling |
| `7d090fb` | `2e00973` | 2026-10-22T12:57:07+05:00 | M2: outer holdout, inner CV, cross-boundary duplicates, pipeline builder |
| `0f2a707` | `4caed82` | 2026-10-22T12:58:37+05:00 | M3: metrics with explicit undefined cases |
| `680141c` | `f7da970` | 2026-10-22T13:02:20+05:00 | M4: experiment runner, baselines, file-based run records |
| `c1c0863` | `189a2b2` | 2026-10-22T13:05:52+05:00 | M5: OOF threshold analysis with provenance guard; one-shot final evaluation |
| `40013a7` | `ce31187` | 2026-10-22T13:12:35+05:00 | M6: evidence-based audit report (Markdown + HTML) from run records |
| `25e87da` | `6bf1a32` | 2026-10-22T13:17:07+05:00 | M7: FastAPI endpoints over a library workflow layer |
| `cf84f51` | `58769d0` | 2026-10-22T13:25:29+05:00 | M8: Streamlit frontend as a pure API client |
| `1f0f4bd` | `6fbaf2d` | 2026-10-22T13:29:18+05:00 | M9: model persistence with integrity check; inference endpoint |
| `43c8cac` | `ea39d3e` | 2026-10-22T13:41:26+05:00 | M10: README, case study on mammography from real run records, smoke script |
| `188d109` | `fc1dd90` | 2026-10-22T13:45:55+05:00 | Final report for supervisor review |
| `9a28c93` | `6711d8c` | 2026-10-22T14:46:55+05:00 | T-R1: duplicate-aware splitting, honest two-run case study, RF determinism, UI evidence |
| `28bc061` | `4b5c299` | 2026-10-22T14:49:06+05:00 | T-R1: review packet entry and revised final report |
| `4544ca3` | `94f17ca` | 2026-10-22T15:17:11+05:00 | T-R2: bootstrap CIs, evaluation coverage, cluster analysis, protocol history, ODbL notices |
| `fcad5d9` | `f71f568` | 2026-10-22T15:17:54+05:00 | T-R2: review packet entry and regenerated final report |
| `bd51d15` | `30a0d77` | 2026-10-23T00:37:57+05:00 | T-R3: calibration disclosure, paired bootstrap, recall scope, httpx2, process docs moved |
| `ffdccce` | `7c4e8f3` | 2026-10-23T00:42:49+05:00 | T-R3: review packet entry and regenerated final report |
| `c11399f` | `bd47d26` | 2026-10-23T01:03:43+05:00 | T-R5: test-scoring history in report/API/UI; persistence, API-exposure and threshold docs |
| `9457290` | `c1b3ec1` | 2026-10-23T01:08:35+05:00 | T-R5: review packet entry |
| `b2d9510` | `e60384d` | 2026-10-23T22:49:09+05:00 | Release prep: MIT LICENSE, README summary/badge/headline/licence, scrub local paths in logs |
| `9679bbc` | `eee1a66` | 2026-10-23T23:04:13+05:00 | Remap commit-hash references after history rewrite; add COMMIT_MAP.md and decision D38 |
| `14faaa2` | `f7d91fa` | 2026-10-23T23:31:26+05:00 | Docs: publish from fresh repository (D38); CI evidence from the new repository |
| `f2dc2d4` | `566d673` | 2026-10-24T00:17:55+05:00 | Update commit-hash references; add D39 |
