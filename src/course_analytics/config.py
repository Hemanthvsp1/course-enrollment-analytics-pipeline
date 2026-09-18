from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv() -> None:
        return None


@dataclass(frozen=True)
class Settings:
    database_url: str | None
    source_dir: Path
    output_dir: Path


def load_settings(source_dir: str, output_dir: str) -> Settings:
    load_dotenv()
    return Settings(
        database_url=os.getenv("DATABASE_URL"),
        source_dir=Path(source_dir),
        output_dir=Path(output_dir),
    )
