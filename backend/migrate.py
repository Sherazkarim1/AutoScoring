import json

from sqlalchemy import text

from app.database import engine


MIGRATIONS = [
    "ALTER TABLE submissions ADD COLUMN IF NOT EXISTS submission_type VARCHAR(20) DEFAULT 'typed'",
    "ALTER TABLE submissions ADD COLUMN IF NOT EXISTS source_filename VARCHAR(255)",
    "ALTER TABLE submissions ADD COLUMN IF NOT EXISTS source_file_path VARCHAR(512)",
    "ALTER TABLE submissions ADD COLUMN IF NOT EXISTS ocr_raw_text TEXT",
    "ALTER TABLE submissions ADD COLUMN IF NOT EXISTS ocr_confidence FLOAT",
    "ALTER TABLE submissions ADD COLUMN IF NOT EXISTS ocr_details TEXT",
    "ALTER TABLE submissions ADD COLUMN IF NOT EXISTS detailed_report TEXT",
]


def run_migrations():
    with engine.begin() as conn:
        for statement in MIGRATIONS:
            conn.execute(text(statement))
    print("Database migrations applied.")


if __name__ == "__main__":
    run_migrations()
