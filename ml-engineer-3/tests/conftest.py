"""Pytest bootstrap: force demo/local config before any app module is imported,
so tests never touch S3/Postgres and imports can sit at the top of test files.
"""

import os

os.environ.setdefault("STORAGE_BACKEND", "local")
os.environ.setdefault("DATABASE_URL", "sqlite:///./_test.db")
os.environ.setdefault("LOCAL_STORAGE_DIR", "./_test_storage")
