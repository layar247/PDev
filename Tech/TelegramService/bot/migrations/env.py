from logging.config import fileConfig
from sqlalchemy import create_engine
from database.models import Base
from alembic import context
import os

DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:megasecretpassword@db:5432/db")

config = context.config
fileConfig(config.config_file_name) if config.config_file_name else None
target_metadata = Base.metadata

def run_migrations_online():
    connectable = create_engine(DB_URL)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True
        )
        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()