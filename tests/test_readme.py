"""The README's library quickstart must run as written."""

import re
from pathlib import Path

import pytest

from conftest import make_imbalanced_frame

README = Path(__file__).resolve().parents[1] / "README.md"


def test_readme_library_quickstart_runs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    match = re.search(
        r"## Quickstart: library\n\n```python\n(.*?)```", README.read_text("utf-8"), re.S
    )
    assert match, "library quickstart block not found"
    monkeypatch.chdir(tmp_path)
    make_imbalanced_frame(n=300).to_csv("my_data.csv", index=False)
    namespace: dict[str, object] = {}
    exec(compile(match.group(1), "README-quickstart", "exec"), namespace)  # noqa: S102
    reports = list((tmp_path / "runs").glob("*/report/report.md"))
    assert len(reports) == 1
    assert (tmp_path / "holdout.json").is_file()
    assert (reports[0].parent.parent / "final_evaluation.json").is_file()
