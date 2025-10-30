# MIGRATION_NAME = "001_initial"

from librepy.pybrex.values import APP_NAME
from librepy.app.data.model import (
    TrainingSession,
    Teacher
)

MIGRATION_NAME = "001_initial"
APPLICATION_SCHEMA = APP_NAME

def run_migration(database, logger):
    try:
        logger.info(f"Running migration: {MIGRATION_NAME}")

        # Ensure application schema exists and is in the search_path for this session
        database.execute_sql(f"CREATE SCHEMA IF NOT EXISTS {APPLICATION_SCHEMA};")
        database.execute_sql(f"SET search_path TO {APPLICATION_SCHEMA}, public;")

        # Bind the models to the current database instance (defensive)
        models = [
            TrainingSession,
            Teacher
        ]

        # Save and temporarily override the database binding for these models
        original_dbs = {}
        for m in models:
            original_dbs[m] = m._meta.database
            m._meta.database = database

        try:
            with database.atomic():
                database.create_tables(models)
        finally:
            # Restore original database bindings
            for m in models:
                m._meta.database = original_dbs[m]

        logger.info("Migration completed successfully")
        return True
    except Exception as exc:
        logger.error(f"Migration failed: {exc}")
        return False
