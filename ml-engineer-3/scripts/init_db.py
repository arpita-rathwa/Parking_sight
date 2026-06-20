"""Create the ML-platform tables. In prod this is an Alembic migration owned by
Backend; for the demo it's create_all."""

from common.db import init_db

if __name__ == "__main__":
    init_db()
    print("ML-platform tables created.")
