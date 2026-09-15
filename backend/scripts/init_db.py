"""Initialize the PostgreSQL schema for the application."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db_session import create_all_tables


if __name__ == "__main__":
    if create_all_tables():
        print("Database tables created successfully.")
    else:
        sys.exit(1)