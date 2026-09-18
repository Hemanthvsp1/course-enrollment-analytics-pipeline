# Course Enrollment & Department Analytics Pipeline

This project analyzes university course enrollment, capacity, grades, and department performance across academic terms. It takes raw academic records, cleans and validates them with Python, loads them into a PostgreSQL-ready relational model, and produces SQL reports and Power BI-ready datasets for dashboard analysis.

The goal is to answer practical academic planning questions:

- Which departments are growing or declining across terms?
- Which courses are close to capacity or underutilized?
- How do pass rates vary by course, department, and term?
- Which departments have the strongest overall performance?

## Project Overview

Universities often store enrollment, course, grade, and department data in separate files or systems. This pipeline brings those records together into a clean analytics layer that can support reporting, dashboarding, and ad hoc SQL analysis.

The project includes:

- A Python ETL pipeline for cleaning and validating raw CSV files
- A PostgreSQL schema with relational constraints and analytics views
- SQL reports for enrollment trends, capacity utilization, pass rates, and department performance
- Power BI-ready CSV exports for building dashboard visuals
- A documented dashboard plan and data dictionary
- Automated tests for key data quality checks

## Tech Stack

- **Python**: ETL, data cleaning, validation, and report export
- **Pandas**: CSV processing and reporting table creation
- **SQL / PostgreSQL**: Relational schema, constraints, and analytics views
- **Power BI**: Dashboard design and reporting layer
- **Pytest**: Data quality test coverage
- **Docker**: Optional local PostgreSQL setup

## Data Used

The sample dataset represents a simplified academic enrollment system with:

- Departments and colleges
- Instructors
- Course catalog records
- Academic terms
- Course sections and capacity
- Student enrollments
- Letter and numeric grades

The data is intentionally small enough to review easily, while still supporting realistic analytics workflows across multiple terms and departments.

## Key Analytics Outputs

The pipeline produces reporting tables for:

| Output | Purpose |
| --- | --- |
| `report_enrollment_trends.csv` | Tracks active enrollments, withdrawals, and average grades by term and department. |
| `report_capacity_utilization.csv` | Compares enrolled students against section capacity by course and term. |
| `report_pass_rates.csv` | Calculates pass rates, failed student counts, and average grades by course. |
| `report_department_performance.csv` | Summarizes department-level enrollment, pass rate, average grade, and capacity utilization. |

These outputs can be loaded directly into Power BI or queried from PostgreSQL views.

## Dashboard Concept

The Power BI dashboard is designed around four pages:

1. **Enrollment Overview**: term-over-term enrollment trends and department comparisons
2. **Capacity & Demand**: courses with high or low capacity utilization
3. **Pass Rate Analysis**: pass rates and average grades by course and department
4. **Department Performance**: department-level KPIs across enrollment, grades, and utilization

The full dashboard specification is available in [docs/powerbi_dashboard_spec.md](docs/powerbi_dashboard_spec.md).

## How the Pipeline Works

1. Raw CSV files are read from `data/raw/`.
2. Python standardizes text values, dates, IDs, grades, and enrollment statuses.
3. Data quality checks validate required columns, primary keys, foreign keys, grade ranges, and allowed status values.
4. Cleaned tables and analytics-ready report tables are written to `data/processed/tables/`.
5. Optional PostgreSQL loading creates normalized staging tables and reusable analytics views.
6. Power BI extracts are generated in `data/processed/powerbi/`.

## Repository Structure

```text
course-enrollment-analytics-pipeline/
  data/raw/                 Sample academic source data
  data/processed/           Generated cleaned tables and Power BI extracts
  docs/                     Data dictionary and dashboard documentation
  scripts/                  Pipeline and export commands
  sql/schema.sql            PostgreSQL schema and analytics views
  sql/reports/              SQL reporting queries
  src/course_analytics/     Python ETL and validation code
  tests/                    Data quality tests
```

## Quick Start

Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the ETL pipeline:

```bash
python scripts/run_pipeline.py --source-dir data/raw --output-dir data/processed
```

Generate Power BI-ready extracts:

```bash
python scripts/export_powerbi_views.py --tables-dir data/processed/tables --output-dir data/processed/powerbi
```

Run tests:

```bash
pytest
```

## Optional PostgreSQL Setup

Start a local PostgreSQL database with Docker:

```bash
docker compose up -d
```

Create a local environment file:

```bash
cp .env.example .env
```

Load the cleaned data into PostgreSQL:

```bash
python scripts/run_pipeline.py --source-dir data/raw --load-postgres
```

After loading PostgreSQL, run the included SQL reports:

```bash
psql "$DATABASE_URL" -f sql/reports/department_performance.sql
```

## PostgreSQL Analytics Views

The database schema creates reusable views in the `analytics` schema:

- `analytics.v_enrollment_trends`
- `analytics.v_capacity_utilization`
- `analytics.v_pass_rates`
- `analytics.v_department_performance`

These views can be connected directly to Power BI through the PostgreSQL connector.

## Data Quality Checks

The pipeline validates:

- Required columns in each source file
- Duplicate primary keys
- Missing foreign key relationships
- Invalid enrollment statuses
- Invalid letter grades
- Numeric grades outside the 0-100 range
- Negative course credits or section capacity

These checks help ensure that the reporting layer is built on consistent, trustworthy data.
