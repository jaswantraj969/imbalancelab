"""Errors raised while loading and validating datasets."""


class DataValidationError(ValueError):
    """Base class for dataset loading/validation failures."""


class UnsupportedFormatError(DataValidationError):
    """The file extension is not a supported tabular format."""


class EmptyDatasetError(DataValidationError):
    """The dataset has no rows."""


class MissingColumnsError(DataValidationError):
    """Columns required by the schema are absent."""

    def __init__(self, missing: list[str]) -> None:
        self.missing = missing
        super().__init__(f"missing required columns: {missing}")


class NaNTargetError(DataValidationError):
    """The target column contains missing values."""

    def __init__(self, n_missing: int) -> None:
        self.n_missing = n_missing
        super().__init__(f"target column has {n_missing} missing value(s)")


class NonBinaryTargetError(DataValidationError):
    """The target does not have exactly two distinct values."""

    def __init__(self, values: list[object]) -> None:
        self.values = values
        shown = values[:10]
        super().__init__(
            f"target must have exactly 2 distinct values, found {len(values)}: {shown}"
        )


class PositiveLabelError(DataValidationError):
    """The declared positive label does not occur in the target."""


class DtypeMismatchError(DataValidationError):
    """A column's dtype does not match ``expected_dtypes``."""

    def __init__(self, mismatches: dict[str, str]) -> None:
        self.mismatches = mismatches
        super().__init__(f"dtype mismatch: {mismatches}")
