"""Regenerate the case-study files omitted from git and check their SHA-256 against the record.

    python scripts/verify_case_study_hashes.py

For each exported run in docs/case_study/<label>/ this:
  1. loads the dataset CSV (downloading it via run_case_study.download if missing) and checks
     its SHA-256 against run.json;
  2. checks the committed holdout.json against the recorded test-index SHA-256;
  3. re-runs CV with the run's config.json on that holdout in a temporary directory;
  4. compares the SHA-256 of the regenerated fold_indices.json and oof_predictions.parquet with
     OMITTED_FILES.json, and the canonical fold-index hash with run.json.
Exit code 0 only if every check passes.
"""

import hashlib
import json
import sys
import tempfile
from pathlib import Path

import imbalancelab.workflow  # noqa: F401  (ensures the package imports before running)
from imbalancelab.data.loader import load_dataset
from imbalancelab.data.schema import DatasetSchema
from imbalancelab.evaluation.config import ExperimentConfig
from imbalancelab.evaluation.runner import run_experiment
from imbalancelab.splitting.splits import Holdout, indices_sha256
from imbalancelab.tracking.records import RunRecord

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_case_study import download  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(export: Path, csv: Path) -> bool:
    run = json.loads((export / "run.json").read_text())
    omitted = json.loads((export / "OMITTED_FILES.json").read_text())
    ok = True

    def check(label: str, got: str, want: str) -> None:
        nonlocal ok
        good = got == want
        ok &= good
        print(
            f"  [{'OK' if good else 'MISMATCH'}] {label}: {got}" + ("" if good else f" != {want}")
        )

    print(f"{export.name}: run {run['run_id']}")
    schema = DatasetSchema.model_validate(run["dataset"]["schema"])
    dataset = load_dataset(csv, schema)
    check("dataset sha256", dataset.sha256, run["dataset"]["sha256"])
    holdout = Holdout.load(export / "holdout.json")
    check("test-index sha256", indices_sha256(holdout.test_idx), run["holdout"]["test_sha256"])
    config = ExperimentConfig.model_validate_json((export / "config.json").read_text())
    with tempfile.TemporaryDirectory() as tmp:
        result = run_experiment(dataset, holdout, config, Path(tmp), run_id="regenerated")
        regenerated = RunRecord(result.run_dir)
        check(
            "fold-index canonical sha256",
            regenerated.run["cv"]["fold_indices_sha256"],
            run["cv"]["fold_indices_sha256"],
        )
        for name, meta in omitted.items():
            check(f"{name} file sha256", sha256(result.run_dir / name), meta["sha256"])
        committed = json.loads((export / "summary.json").read_text())
        check(
            "summary.json content",
            hashlib.sha256(json.dumps(regenerated.summary, sort_keys=True).encode()).hexdigest(),
            hashlib.sha256(json.dumps(committed, sort_keys=True).encode()).hexdigest(),
        )
    return ok


def main() -> int:
    csv = ROOT / "data" / "raw" / "mammography.csv"
    if not csv.is_file():
        try:
            _, csv = download(ROOT / "data" / "raw" / "imblearn")
        except OSError as exc:
            print(f"ENVIRONMENT LIMITATION: dataset download failed: {exc}", file=sys.stderr)
            return 2
    exports = sorted(p for p in (ROOT / "docs" / "case_study").iterdir() if p.is_dir())
    results = [verify(export, csv) for export in exports]
    print("ALL CHECKS PASSED" if all(results) else "SOME CHECKS FAILED")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
