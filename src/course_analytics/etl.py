from __future__ import annotations

from pathlib import Path

import pandas as pd

from course_analytics.quality import (
    DataQualityError,
    VALID_ENROLLMENT_STATUSES,
    require_allowed_values,
    require_columns,
    require_foreign_key,
    require_non_negative,
    require_unique,
)


RAW_TABLES = {
    "departments": ["department_id", "department_code", "department_name", "college"],
    "instructors": ["instructor_id", "first_name", "last_name", "department_id"],
    "courses": ["course_id", "course_code", "course_title", "department_id", "credits"],
    "terms": ["term_id", "term_code", "term_name", "start_date", "end_date"],
    "sections": ["section_id", "course_id", "term_id", "instructor_id", "section_number", "capacity"],
    "enrollments": ["enrollment_id", "student_id", "section_id", "enrollment_status", "enrolled_date"],
    "grades": ["enrollment_id", "letter_grade", "numeric_grade"],
}

LOAD_ORDER = [
    "departments",
    "instructors",
    "courses",
    "terms",
    "sections",
    "enrollments",
    "grades",
]


def read_raw_tables(source_dir: Path) -> dict[str, pd.DataFrame]:
    tables: dict[str, pd.DataFrame] = {}
    for table_name, columns in RAW_TABLES.items():
        path = source_dir / f"{table_name}.csv"
        if not path.exists():
            raise FileNotFoundError(f"Missing source file: {path}")
        frame = pd.read_csv(path)
        require_columns(frame, table_name, columns)
        tables[table_name] = frame[columns].copy()
    return tables


def transform_tables(tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    cleaned = {name: frame.copy() for name, frame in tables.items()}

    for name, frame in cleaned.items():
        for column in frame.select_dtypes(include="object").columns:
            frame[column] = frame[column].astype(str).str.strip()

    cleaned["departments"]["department_code"] = cleaned["departments"]["department_code"].str.upper()
    cleaned["courses"]["course_code"] = cleaned["courses"]["course_code"].str.upper()
    cleaned["enrollments"]["enrollment_status"] = cleaned["enrollments"]["enrollment_status"].str.lower()
    cleaned["grades"]["letter_grade"] = cleaned["grades"]["letter_grade"].str.upper()

    for table_name in ["departments", "instructors", "courses", "terms", "sections", "enrollments"]:
        id_column = next(column for column in cleaned[table_name].columns if column.endswith("_id"))
        cleaned[table_name][id_column] = cleaned[table_name][id_column].astype(int)

    cleaned["courses"]["credits"] = cleaned["courses"]["credits"].astype(int)
    cleaned["sections"]["capacity"] = cleaned["sections"]["capacity"].astype(int)
    cleaned["grades"]["enrollment_id"] = cleaned["grades"]["enrollment_id"].astype(int)
    cleaned["grades"]["numeric_grade"] = cleaned["grades"]["numeric_grade"].astype(float)

    for date_column in ["start_date", "end_date"]:
        cleaned["terms"][date_column] = pd.to_datetime(cleaned["terms"][date_column]).dt.date
    cleaned["enrollments"]["enrolled_date"] = pd.to_datetime(
        cleaned["enrollments"]["enrolled_date"]
    ).dt.date

    return cleaned


def validate_tables(tables: dict[str, pd.DataFrame]) -> None:
    unique_keys = {
        "departments": "department_id",
        "instructors": "instructor_id",
        "courses": "course_id",
        "terms": "term_id",
        "sections": "section_id",
        "enrollments": "enrollment_id",
    }
    for table_name, column in unique_keys.items():
        require_unique(tables[table_name], table_name, column)

    require_unique(tables["departments"], "departments", "department_code")
    require_unique(tables["courses"], "courses", "course_code")
    require_unique(tables["grades"], "grades", "enrollment_id")

    require_foreign_key(
        tables["instructors"], tables["departments"], "instructors", "department_id", "department_id"
    )
    require_foreign_key(
        tables["courses"], tables["departments"], "courses", "department_id", "department_id"
    )
    require_foreign_key(tables["sections"], tables["courses"], "sections", "course_id", "course_id")
    require_foreign_key(tables["sections"], tables["terms"], "sections", "term_id", "term_id")
    require_foreign_key(
        tables["sections"], tables["instructors"], "sections", "instructor_id", "instructor_id"
    )
    require_foreign_key(
        tables["enrollments"], tables["sections"], "enrollments", "section_id", "section_id"
    )
    require_foreign_key(
        tables["grades"], tables["enrollments"], "grades", "enrollment_id", "enrollment_id"
    )

    require_allowed_values(
        tables["enrollments"],
        "enrollments",
        "enrollment_status",
        VALID_ENROLLMENT_STATUSES,
    )
    require_allowed_values(tables["grades"], "grades", "letter_grade", {"A", "B", "C", "D", "F"})
    require_non_negative(tables["courses"], "courses", "credits")
    require_non_negative(tables["sections"], "sections", "capacity")

    invalid_grades = tables["grades"].query("numeric_grade < 0 or numeric_grade > 100")
    if not invalid_grades.empty:
        raise DataQualityError("grades.numeric_grade must be between 0 and 100")


def build_reporting_tables(tables: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    fact = (
        tables["enrollments"]
        .merge(tables["sections"], on="section_id", how="left")
        .merge(tables["courses"], on="course_id", how="left")
        .merge(tables["departments"], on="department_id", how="left")
        .merge(tables["terms"], on="term_id", how="left")
        .merge(tables["grades"], on="enrollment_id", how="left")
    )
    fact["is_enrolled"] = fact["enrollment_status"].isin(["completed", "failed"]).astype(int)
    fact["is_passed"] = fact["letter_grade"].isin(["A", "B", "C", "D"]).astype(int)
    fact["is_failed"] = (fact["letter_grade"] == "F").astype(int)
    fact["is_withdrawn"] = (fact["enrollment_status"] == "withdrawn").astype(int)
    fact["capacity_utilization"] = fact["is_enrolled"] / fact["capacity"]

    trend = (
        fact.groupby(["term_id", "term_name", "department_code"], as_index=False)
        .agg(
            enrolled_students=("is_enrolled", "sum"),
            withdrawals=("is_withdrawn", "sum"),
            average_grade=("numeric_grade", "mean"),
        )
        .sort_values(["term_id", "department_code"])
    )
    trend["average_grade"] = trend["average_grade"].round(2)

    capacity = (
        fact.groupby(
            ["term_id", "term_name", "department_code", "course_code", "course_title", "section_id"],
            as_index=False,
        )
        .agg(enrolled_students=("is_enrolled", "sum"), capacity=("capacity", "max"))
        .sort_values(["term_id", "department_code", "course_code"])
    )
    capacity["capacity_utilization_pct"] = (
        capacity["enrolled_students"] / capacity["capacity"] * 100
    ).round(2)

    pass_rates = (
        fact[fact["enrollment_status"].isin(["completed", "failed"])]
        .groupby(["term_id", "term_name", "department_code", "course_code"], as_index=False)
        .agg(
            graded_enrollments=("enrollment_id", "count"),
            passed_students=("is_passed", "sum"),
            failed_students=("is_failed", "sum"),
            average_grade=("numeric_grade", "mean"),
        )
    )
    pass_rates["pass_rate_pct"] = (
        pass_rates["passed_students"] / pass_rates["graded_enrollments"] * 100
    ).round(2)
    pass_rates["average_grade"] = pass_rates["average_grade"].round(2)

    department_performance = (
        fact.groupby(["term_id", "term_name", "department_code", "department_name", "college"], as_index=False)
        .agg(
            sections_offered=("section_id", "nunique"),
            active_enrollments=("is_enrolled", "sum"),
            withdrawals=("is_withdrawn", "sum"),
            passed_students=("is_passed", "sum"),
            average_grade=("numeric_grade", "mean"),
        )
    )
    department_capacity = (
        capacity.groupby(["term_id", "department_code"], as_index=False)
        .agg(total_capacity=("capacity", "sum"))
    )
    department_performance = department_performance.merge(
        department_capacity, on=["term_id", "department_code"], how="left"
    )
    department_performance["pass_rate_pct"] = (
        department_performance["passed_students"] / department_performance["active_enrollments"] * 100
    ).round(2)
    department_performance["average_grade"] = department_performance["average_grade"].round(2)
    department_performance["capacity_utilization_pct"] = (
        department_performance["active_enrollments"]
        / department_performance["total_capacity"]
        * 100
    ).round(2)

    return {
        "fact_enrollment_outcomes": fact,
        "report_enrollment_trends": trend,
        "report_capacity_utilization": capacity,
        "report_pass_rates": pass_rates,
        "report_department_performance": department_performance,
    }


def write_processed_tables(tables: dict[str, pd.DataFrame], output_dir: Path) -> None:
    table_dir = output_dir / "tables"
    table_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in tables.items():
        frame.to_csv(table_dir / f"{name}.csv", index=False)


def load_postgres(tables: dict[str, pd.DataFrame], database_url: str, schema_path: Path) -> None:
    try:
        from sqlalchemy import create_engine, text
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "PostgreSQL loading requires SQLAlchemy. Install project dependencies with "
            "`pip install -r requirements.txt` or `pip install -e .`."
        ) from exc

    engine = create_engine(database_url)
    schema_sql = schema_path.read_text(encoding="utf-8")
    with engine.begin() as connection:
        connection.execute(text(schema_sql))
        for table_name in reversed(LOAD_ORDER):
            connection.execute(text(f"TRUNCATE TABLE staging.{table_name} RESTART IDENTITY CASCADE"))
        for table_name in LOAD_ORDER:
            tables[table_name].to_sql(
                table_name,
                connection,
                schema="staging",
                if_exists="append",
                index=False,
                method="multi",
            )


def run_pipeline(
    source_dir: Path,
    output_dir: Path,
    database_url: str | None = None,
    schema_path: Path | None = None,
) -> dict[str, pd.DataFrame]:
    raw_tables = read_raw_tables(source_dir)
    cleaned = transform_tables(raw_tables)
    validate_tables(cleaned)
    reporting = build_reporting_tables(cleaned)
    write_processed_tables(cleaned | reporting, output_dir)
    if database_url:
        if schema_path is None:
            raise ValueError("schema_path is required when loading PostgreSQL")
        load_postgres(cleaned, database_url, schema_path)
    return cleaned | reporting
