from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from course_analytics.etl import read_raw_tables, transform_tables, validate_tables
from course_analytics.quality import DataQualityError


def test_raw_sample_data_passes_validation() -> None:
    tables = transform_tables(read_raw_tables(Path("data/raw")))
    validate_tables(tables)


def test_duplicate_department_id_fails_validation() -> None:
    tables = transform_tables(read_raw_tables(Path("data/raw")))
    duplicate = tables["departments"].iloc[[0]].copy()
    tables["departments"] = pd.concat([tables["departments"], duplicate], ignore_index=True)

    with pytest.raises(DataQualityError, match="duplicate"):
        validate_tables(tables)


def test_invalid_enrollment_status_fails_validation() -> None:
    tables = transform_tables(read_raw_tables(Path("data/raw")))
    tables["enrollments"].loc[0, "enrollment_status"] = "pending"

    with pytest.raises(DataQualityError, match="invalid values"):
        validate_tables(tables)
