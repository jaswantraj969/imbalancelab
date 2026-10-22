"""Load CSV/Parquet files and validate them against a :class:`DatasetSchema`."""

import hashlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.api import types as ptypes

from imbalancelab.data.errors import (
    DtypeMismatchError,
    EmptyDatasetError,
    MissingColumnsError,
    NaNTargetError,
    NonBinaryTargetError,
    PositiveLabelError,
    UnsupportedFormatError,
)
from imbalancelab.data.schema import DatasetSchema

SUPPORTED_SUFFIXES = (".csv", ".parquet", ".pq")
_CHUNK = 1 << 20


@dataclass(frozen=True)
class LoadedDataset:
    """A validated dataset.

    ``frame`` holds the data as loaded (the target column is never modified). ``y`` is the
    derived binary target: 1 for ``schema.positive_label``, 0 otherwise.
    """

    frame: pd.DataFrame
    y: np.ndarray
    schema: DatasetSchema
    sha256: str
    source_path: Path
    positive_label_coerced: bool = False
    notes: tuple[str, ...] = ()

    @property
    def n_rows(self) -> int:
        return len(self.frame)

    @property
    def feature_columns(self) -> list[str]:
        return self.schema.feature_columns(list(self.frame.columns))

    def features(self) -> pd.DataFrame:
        return self.frame[self.feature_columns]


def sha256_file(path: Path) -> str:
    """SHA-256 hex digest of the file's bytes."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as fh:
        while chunk := fh.read(_CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def read_table(path: Path) -> pd.DataFrame:
    """Read a CSV or Parquet file into a DataFrame."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise UnsupportedFormatError(
            f"unsupported file type {suffix!r}; expected one of {SUPPORTED_SUFFIXES}"
        )
    if suffix == ".csv":
        try:
            return pd.read_csv(path, low_memory=False)
        except pd.errors.EmptyDataError as exc:
            raise EmptyDatasetError(f"{path.name} contains no data") from exc
    return pd.read_parquet(path)


def load_dataset(path: Path | str, schema: DatasetSchema) -> LoadedDataset:
    """Load ``path`` and validate it against ``schema``.

    Raises a :class:`~imbalancelab.data.errors.DataValidationError` subclass on failure.
    """
    path = Path(path)
    frame = read_table(path)
    sha = sha256_file(path)
    notes: list[str] = []

    if len(frame) == 0:
        raise EmptyDatasetError(f"{path.name} has no rows")
    missing = [c for c in schema.required_columns() if c not in frame.columns]
    if missing:
        raise MissingColumnsError(missing)

    frame = _apply_expected_dtypes(frame, schema, notes)
    frame = _coerce_time_column(frame, schema, notes)

    target = frame[schema.target]
    n_nan = int(target.isna().sum())
    if n_nan:
        raise NaNTargetError(n_nan)
    values = list(pd.unique(target))
    if len(values) != 2:
        raise NonBinaryTargetError(values)

    is_positive, coerced = _match_positive_label(target, schema.positive_label)
    if coerced:
        notes.append(
            f"positive_label {schema.positive_label!r} matched target values by string "
            "comparison (type differs from the stored target)"
        )
    y = is_positive.to_numpy(dtype=np.int8)
    return LoadedDataset(
        frame=frame,
        y=y,
        schema=schema,
        sha256=sha,
        source_path=path,
        positive_label_coerced=coerced,
        notes=tuple(notes),
    )


def _match_positive_label(target: pd.Series, label: object) -> tuple[pd.Series, bool]:
    try:
        exact = target == label
    except TypeError:
        exact = pd.Series(False, index=target.index)
    exact = exact.fillna(False).astype(bool)
    if exact.any():
        return exact, False
    as_str = target.astype(str) == str(label)
    if as_str.any():
        return as_str.astype(bool), True
    observed = [str(v) for v in pd.unique(target)]
    raise PositiveLabelError(
        f"positive_label {label!r} not found in target values {observed} "
        "(also tried string comparison)"
    )


def _is_integer_valued(series: pd.Series) -> bool:
    if ptypes.is_integer_dtype(series):
        return True
    if ptypes.is_float_dtype(series):
        values = series.dropna().to_numpy()
        return bool(np.all(np.mod(values, 1) == 0))
    return False


def _apply_expected_dtypes(
    frame: pd.DataFrame, schema: DatasetSchema, notes: list[str]
) -> pd.DataFrame:
    if not schema.expected_dtypes:
        return frame
    frame = frame.copy()
    mismatches: dict[str, str] = {}
    for col, expected in schema.expected_dtypes.items():
        series = frame[col]
        actual = str(series.dtype)
        if expected == "numeric":
            if not ptypes.is_numeric_dtype(series) or ptypes.is_bool_dtype(series):
                mismatches[col] = f"expected numeric, got {actual}"
        elif expected == "boolean":
            if not ptypes.is_bool_dtype(series):
                observed = set(series.dropna().unique().tolist())
                if not observed <= {0, 1}:
                    mismatches[col] = f"expected boolean, got {actual}"
        elif expected == "categorical":
            if ptypes.is_datetime64_any_dtype(series) or (
                ptypes.is_float_dtype(series) and not _is_integer_valued(series)
            ):
                mismatches[col] = f"expected categorical, got {actual}"
            elif ptypes.is_numeric_dtype(series) and not ptypes.is_bool_dtype(series):
                frame[col] = pd.Series(
                    [str(int(v)) if pd.notna(v) else np.nan for v in series],
                    index=series.index,
                    dtype=object,
                )
                notes.append(f"column {col!r}: integer codes converted to categorical strings")
        elif expected == "datetime":
            converted = _to_datetime(series)
            if converted is None:
                mismatches[col] = f"expected datetime, got {actual}"
            elif converted is not series:
                frame[col] = converted
                notes.append(f"column {col!r}: parsed as datetime")
    if mismatches:
        raise DtypeMismatchError(mismatches)
    return frame


def _to_datetime(series: pd.Series) -> pd.Series | None:
    if ptypes.is_datetime64_any_dtype(series):
        return series
    if ptypes.is_numeric_dtype(series) or ptypes.is_bool_dtype(series):
        return None
    try:
        return pd.to_datetime(series, errors="raise", format="mixed")
    except (ValueError, TypeError):
        return None


def _coerce_time_column(
    frame: pd.DataFrame, schema: DatasetSchema, notes: list[str]
) -> pd.DataFrame:
    col = schema.time_column
    if col is None or col in schema.expected_dtypes:
        return frame
    series = frame[col]
    if ptypes.is_datetime64_any_dtype(series) or (
        ptypes.is_numeric_dtype(series) and not ptypes.is_bool_dtype(series)
    ):
        return frame
    converted = _to_datetime(series)
    if converted is None:
        raise DtypeMismatchError({col: f"time column must be datetime or numeric, got {series.dtype}"})
    frame = frame.copy()
    frame[col] = converted
    notes.append(f"time column {col!r}: parsed as datetime")
    return frame
