import hashlib

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from imbalancelab.data import (
    DatasetSchema,
    DtypeMismatchError,
    EmptyDatasetError,
    MissingColumnsError,
    NaNTargetError,
    NonBinaryTargetError,
    PositiveLabelError,
    UnsupportedFormatError,
    load_dataset,
)


def _schema(**kw: object) -> DatasetSchema:
    base: dict[str, object] = {"target": "label", "positive_label": "yes"}
    base.update(kw)
    return DatasetSchema.model_validate(base)


def test_load_csv_derives_binary_target_without_mutating(write_csv, imbalanced_frame) -> None:
    path = write_csv(imbalanced_frame)
    ds = load_dataset(path, _schema(id_column="row_id"))
    assert ds.n_rows == len(imbalanced_frame)
    np.testing.assert_array_equal(ds.y, (imbalanced_frame["label"] == "yes").to_numpy())
    assert ds.y.dtype == np.int8
    assert set(ds.frame["label"].unique()) == {"yes", "no"}  # original target untouched
    assert ds.sha256 == hashlib.sha256(path.read_bytes()).hexdigest()
    assert "row_id" not in ds.feature_columns and "label" not in ds.feature_columns
    assert list(ds.features().columns) == ds.feature_columns
    assert not ds.positive_label_coerced


def test_load_parquet(write_csv, imbalanced_frame) -> None:
    path = write_csv(imbalanced_frame, "data.parquet")
    ds = load_dataset(path, _schema())
    assert ds.n_rows == len(imbalanced_frame)
    assert int(ds.y.sum()) == int((imbalanced_frame["label"] == "yes").sum())


def test_unsupported_format(tmp_path) -> None:
    path = tmp_path / "data.xlsx"
    path.write_bytes(b"x")
    with pytest.raises(UnsupportedFormatError):
        load_dataset(path, _schema())


def test_empty_file_and_header_only(tmp_path, write_csv) -> None:
    empty = tmp_path / "empty.csv"
    empty.write_text("")
    with pytest.raises(EmptyDatasetError):
        load_dataset(empty, _schema())
    header_only = write_csv(pd.DataFrame({"label": [], "x": []}), "hdr.csv")
    with pytest.raises(EmptyDatasetError):
        load_dataset(header_only, _schema())


def test_missing_columns(write_csv) -> None:
    path = write_csv(pd.DataFrame({"x": [1, 2]}))
    with pytest.raises(MissingColumnsError) as exc:
        load_dataset(path, _schema(group_column="g", split_strategy="group"))
    assert exc.value.missing == ["label", "g"]


def test_nan_target(write_csv) -> None:
    path = write_csv(pd.DataFrame({"label": ["yes", None, "no"], "x": [1, 2, 3]}))
    with pytest.raises(NaNTargetError) as exc:
        load_dataset(path, _schema())
    assert exc.value.n_missing == 1


@pytest.mark.parametrize("labels", [["a", "b", "c"], ["yes", "yes"]])
def test_non_binary_target(write_csv, labels) -> None:
    path = write_csv(pd.DataFrame({"label": labels, "x": range(len(labels))}))
    with pytest.raises(NonBinaryTargetError):
        load_dataset(path, _schema())


def test_absent_positive_label(write_csv) -> None:
    path = write_csv(pd.DataFrame({"label": ["a", "b"], "x": [1, 2]}))
    with pytest.raises(PositiveLabelError):
        load_dataset(path, _schema(positive_label="yes"))


def test_positive_label_string_coercion_is_recorded(write_csv) -> None:
    path = write_csv(pd.DataFrame({"label": [0, 1, 0, 1], "x": [1, 2, 3, 4]}))
    ds = load_dataset(path, _schema(positive_label="1"))
    assert ds.positive_label_coerced
    assert any("string comparison" in n for n in ds.notes)
    np.testing.assert_array_equal(ds.y, [0, 1, 0, 1])


def test_numeric_positive_label_exact(write_csv) -> None:
    path = write_csv(pd.DataFrame({"label": [-1, 1, -1, 1], "x": [1, 2, 3, 4]}))
    ds = load_dataset(path, _schema(positive_label=1))
    assert not ds.positive_label_coerced
    np.testing.assert_array_equal(ds.y, [0, 1, 0, 1])


def test_dtype_mismatch(write_csv) -> None:
    frame = pd.DataFrame({"label": ["yes", "no"], "x": ["a", "b"], "f": [0.5, 1.5]})
    path = write_csv(frame)
    with pytest.raises(DtypeMismatchError) as exc:
        load_dataset(path, _schema(expected_dtypes={"x": "numeric", "f": "categorical"}))
    assert set(exc.value.mismatches) == {"x", "f"}


def test_dtype_coercions(write_csv) -> None:
    frame = pd.DataFrame(
        {
            "label": ["yes", "no", "no"],
            "code": [10, 20, None],
            "when": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "flag": [0, 1, 1],
            "num": [1.0, 2.0, 3.0],
        }
    )
    path = write_csv(frame)
    ds = load_dataset(
        path,
        _schema(
            expected_dtypes={
                "code": "categorical",
                "when": "datetime",
                "flag": "boolean",
                "num": "numeric",
            }
        ),
    )
    assert ds.frame["code"].tolist()[:2] == ["10", "20"]
    assert pd.isna(ds.frame["code"].iloc[2])
    assert pd.api.types.is_datetime64_any_dtype(ds.frame["when"])
    assert len(ds.notes) == 2


def test_dtype_boolean_and_datetime_mismatch(write_csv) -> None:
    path = write_csv(pd.DataFrame({"label": ["yes", "no"], "b": [3, 4], "d": [1.5, 2.5]}))
    with pytest.raises(DtypeMismatchError) as exc:
        load_dataset(path, _schema(expected_dtypes={"b": "boolean", "d": "datetime"}))
    assert set(exc.value.mismatches) == {"b", "d"}
    path2 = write_csv(pd.DataFrame({"label": ["yes", "no"], "d": ["x", "y"]}), "d2.csv")
    with pytest.raises(DtypeMismatchError):
        load_dataset(path2, _schema(expected_dtypes={"d": "datetime"}))


def test_time_column_parsed_or_rejected(write_csv, imbalanced_frame) -> None:
    path = write_csv(imbalanced_frame)
    ds = load_dataset(path, _schema(time_column="ts", split_strategy="temporal"))
    assert pd.api.types.is_datetime64_any_dtype(ds.frame["ts"])
    bad = write_csv(pd.DataFrame({"label": ["yes", "no"], "ts": ["x", "y"]}), "bad.csv")
    with pytest.raises(DtypeMismatchError):
        load_dataset(bad, _schema(time_column="ts", split_strategy="temporal"))
    numeric = write_csv(pd.DataFrame({"label": ["yes", "no"], "ts": [1, 2]}), "num.csv")
    assert load_dataset(numeric, _schema(time_column="ts")).frame["ts"].tolist() == [1, 2]


def test_schema_validation() -> None:
    with pytest.raises(ValidationError):
        _schema(split_strategy="group")
    with pytest.raises(ValidationError):
        _schema(split_strategy="temporal")
    with pytest.raises(ValidationError):
        _schema(id_column="label")
    with pytest.raises(ValidationError):
        _schema(id_column="a", group_column="a")
    with pytest.raises(ValidationError):
        _schema(unknown_field=1)
    schema = _schema(id_column="i", expected_dtypes={"x": "numeric"})
    assert schema.required_columns() == ["label", "i", "x"]
    assert schema.feature_columns(["i", "x", "label", "z"]) == ["x", "z"]
