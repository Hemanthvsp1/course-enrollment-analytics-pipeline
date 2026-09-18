from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from course_analytics.config import load_settings
from course_analytics.etl import run_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean, validate, and load course analytics data.")
    parser.add_argument("--source-dir", default="data/raw")
    parser.add_argument("--output-dir", default="data/processed")
    parser.add_argument("--load-postgres", action="store_true")
    parser.add_argument("--schema-path", default="sql/schema.sql")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = load_settings(args.source_dir, args.output_dir)
    database_url = settings.database_url if args.load_postgres else None
    if args.load_postgres and not database_url:
        raise SystemExit("DATABASE_URL is required when --load-postgres is used")

    tables = run_pipeline(
        source_dir=settings.source_dir,
        output_dir=settings.output_dir,
        database_url=database_url,
        schema_path=Path(args.schema_path),
    )
    print(f"Pipeline complete. Wrote {len(tables)} tables to {settings.output_dir / 'tables'}")


if __name__ == "__main__":
    main()
