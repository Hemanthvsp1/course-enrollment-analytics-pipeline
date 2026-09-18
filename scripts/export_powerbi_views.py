from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


POWERBI_TABLES = [
    "report_enrollment_trends",
    "report_capacity_utilization",
    "report_pass_rates",
    "report_department_performance",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export Power BI-ready report CSV files.")
    parser.add_argument("--tables-dir", default="data/processed/tables")
    parser.add_argument("--output-dir", default="data/processed/powerbi")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tables_dir = Path(args.tables_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for table_name in POWERBI_TABLES:
        source_path = tables_dir / f"{table_name}.csv"
        if not source_path.exists():
            raise FileNotFoundError(f"Run scripts/run_pipeline.py first. Missing {source_path}")
        frame = pd.read_csv(source_path)
        frame.to_csv(output_dir / f"{table_name}.csv", index=False)

    print(f"Power BI extracts written to {output_dir}")


if __name__ == "__main__":
    main()
