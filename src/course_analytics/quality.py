from __future__ import annotations

import pandas as pd


PASSING_GRADES = {"A", "B", "C", "D"}
VALID_ENROLLMENT_STATUSES = {"completed", "withdrawn", "failed"}


class DataQualityError(ValueError):
    """Raised when source data fails a pipeline validation rule."""


def require_columns(frame: pd.DataFrame, table_name: str, columns: list[str]) -> None:
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise DataQualityError(f"{table_name} is missing required columns: {missing}")


def require_unique(frame: pd.DataFrame, table_name: str, column: str) -> None:
    duplicates = frame.loc[frame[column].duplicated(), column].tolist()
    if duplicates:
        raise DataQualityError(f"{table_name}.{column} has duplicate values: {duplicates}")


def require_foreign_key(
    child: pd.DataFrame,
    parent: pd.DataFrame,
    child_table: str,
    child_column: str,
    parent_column: str,
) -> None:
    missing = sorted(set(child[child_column].dropna()) - set(parent[parent_column].dropna()))
    if missing:
        raise DataQualityError(
            f"{child_table}.{child_column} contains values missing from {parent_column}: {missing}"
        )


def require_allowed_values(
    frame: pd.DataFrame, table_name: str, column: str, allowed_values: set[str]
) -> None:
    invalid = sorted(set(frame[column].dropna()) - allowed_values)
    if invalid:
        raise DataQualityError(f"{table_name}.{column} has invalid values: {invalid}")


def require_non_negative(frame: pd.DataFrame, table_name: str, column: str) -> None:
    invalid_count = int((frame[column] < 0).sum())
    if invalid_count:
        raise DataQualityError(f"{table_name}.{column} has {invalid_count} negative values")
