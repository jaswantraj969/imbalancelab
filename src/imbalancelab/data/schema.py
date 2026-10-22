"""Declarative dataset schema."""

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

SplitStrategy = Literal["stratified", "group", "temporal"]
ExpectedDtype = Literal["numeric", "categorical", "datetime", "boolean"]
Label = str | int | float | bool


class DatasetSchema(BaseModel):
    """Describes a binary classification dataset.

    ``positive_label`` is the raw target value that denotes the positive (minority) class.
    ``split_strategy`` decides how the outer holdout and the inner CV folds are built.
    """

    model_config = ConfigDict(extra="forbid")

    target: str = Field(min_length=1)
    positive_label: Label
    id_column: str | None = None
    group_column: str | None = None
    time_column: str | None = None
    expected_dtypes: dict[str, ExpectedDtype] = Field(default_factory=dict)
    split_strategy: SplitStrategy = "stratified"
    # group rows with identical feature values so no duplicate cluster crosses a split boundary
    duplicate_groups: bool = False

    @model_validator(mode="after")
    def _check_consistency(self) -> Self:
        if self.split_strategy == "group" and self.group_column is None:
            raise ValueError("split_strategy='group' requires group_column")
        if self.split_strategy == "temporal" and self.time_column is None:
            raise ValueError("split_strategy='temporal' requires time_column")
        if self.split_strategy == "temporal" and self.duplicate_groups:
            raise ValueError("duplicate_groups is not supported with split_strategy='temporal'")
        special = [
            c for c in (self.id_column, self.group_column, self.time_column) if c is not None
        ]
        if self.target in special:
            raise ValueError("target column cannot also be an id/group/time column")
        if len(special) != len(set(special)):
            raise ValueError("id/group/time columns must be distinct")
        return self

    def special_columns(self) -> list[str]:
        """Target plus any id/group/time columns: never used as model features."""
        cols = [self.target]
        for c in (self.id_column, self.group_column, self.time_column):
            if c is not None:
                cols.append(c)
        return cols

    def required_columns(self) -> list[str]:
        """Columns that must exist in the data."""
        return list(dict.fromkeys([*self.special_columns(), *self.expected_dtypes]))

    def feature_columns(self, columns: list[str]) -> list[str]:
        """Feature columns, in data order: everything except the special columns."""
        special = set(self.special_columns())
        return [c for c in columns if c not in special]
