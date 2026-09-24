from sqlalchemy import create_engine, text

from app.config import settings
from app.models import Base


MIGRATIONS = [
    "ALTER TABLE submissions ADD COLUMN IF NOT EXISTS submission_type VARCHAR(20) DEFAULT 'typed'",
    "ALTER TABLE submissions ADD COLUMN IF NOT EXISTS source_filename VARCHAR(255)",
    "ALTER TABLE submissions ADD COLUMN IF NOT EXISTS source_file_path VARCHAR(512)",
    "ALTER TABLE submissions ADD COLUMN IF NOT EXISTS ocr_raw_text TEXT",
    "ALTER TABLE submissions ADD COLUMN IF NOT EXISTS ocr_confidence FLOAT",
    "ALTER TABLE submissions ADD COLUMN IF NOT EXISTS ocr_details TEXT",
    "ALTER TABLE submissions ADD COLUMN IF NOT EXISTS detailed_report TEXT",
    "ALTER TABLE questions ADD COLUMN IF NOT EXISTS marking_rubric TEXT",
    "ALTER TABLE questions ADD COLUMN IF NOT EXISTS key_concepts TEXT",
    "ALTER TABLE questions ADD COLUMN IF NOT EXISTS source_filename VARCHAR(255)",
    "ALTER TABLE questions ADD COLUMN IF NOT EXISTS source_file_path VARCHAR(512)",
    "ALTER TABLE questions ADD COLUMN IF NOT EXISTS ocr_raw_text TEXT",
    "ALTER TABLE questions ADD COLUMN IF NOT EXISTS generation_source VARCHAR(20) DEFAULT 'manual'",
]


def run_migrations():
    migration_url = settings.database_url_unpooled or settings.database_url
    migration_engine = create_engine(migration_url, pool_pre_ping=True)
    try:
        Base.metadata.create_all(bind=migration_engine)
        with migration_engine.begin() as conn:
            for statement in MIGRATIONS:
                conn.execute(text(statement))
    finally:
        migration_engine.dispose()
    print("Database migrations applied.")


if __name__ == "__main__":
    run_migrations()
