from alembic import context
from sqlalchemy import create_engine

from app.core.config import settings
from app.database.connection import Base
from app import models  # noqa: F401  (imports the models so Alembic can see them)

target_metadata = Base.metadata


def run_migrations():
    engine = create_engine(settings.database_url)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


run_migrations()
