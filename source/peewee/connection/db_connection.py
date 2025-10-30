'''
Database connection module to prevent circular imports.
This module establishes the database connection and makes it available to other modules.
'''

from librepy.peewee.sdbc_peewee import SDBCPostgresqlDatabase
from librepy.utils.db_config_manager import DatabaseConfigManager
from librepy.peewee.db_model.base_model import database_proxy
from librepy.pybrex.values import pybrex_logger

logger = pybrex_logger(__name__)
db_config_manager = DatabaseConfigManager()


def _create_database_instance():
    logger.debug("Creating new database instance")
    connection_params = db_config_manager.get_connection_params()
    if not connection_params or not connection_params.get("database"):
        logger.info("No database configuration found, prompting user for configuration")
        if not db_config_manager.prompt_configuration():
            from librepy.peewee.connection.db_exceptions import DBCanceledException
            raise DBCanceledException("Database configuration canceled by user")
        connection_params = db_config_manager.get_connection_params()
        if not connection_params or not connection_params.get("database"):
            raise Exception("Database configuration failed - no valid connection parameters available.")
    logger.debug(f"Creating database connection to {connection_params['database']} at {connection_params['host']}:{connection_params['port']}")
    return SDBCPostgresqlDatabase(
        connection_params["database"],
        user=connection_params.get("user"),
        password=connection_params.get("password"),
        host=connection_params.get("host"),
        port=connection_params.get("port"),
        autoconnect=False,
    )


def get_database_connection(force_reinitialize: bool = False):
    if database_proxy.obj is None or force_reinitialize:
        logger.debug("Initializing database connection and binding models")
        db_instance = _create_database_instance()
        database_proxy.initialize(db_instance)
        _bind_models_to_db(database_proxy.obj)
        logger.debug("Database connection and model binding completed")
    else:
        logger.debug("Using existing database connection")
    return database_proxy.obj


def _bind_models_to_db(db):
    logger.debug("Binding models to database")
    import inspect
    from librepy.app.data import model as app_models
    from librepy.peewee.db_model.base_model import BaseModel

    # Dynamically find all classes that inherit from BaseModel
    models = []
    for name, obj in inspect.getmembers(app_models, inspect.isclass):
        if obj is not BaseModel and issubclass(obj, BaseModel):
            models.append(obj)
            logger.debug(f"Found model class: {obj.__name__}")

    logger.debug(f"Found {len(models)} model classes to bind")

    for model in models:
        # Force the model to use the actual database instance instead of proxy
        model._meta.database = db
        logger.debug(f"Bound model {model.__name__} to database: {type(model._meta.database).__name__}")
    logger.info(f"Successfully bound {len(models)} models to database")


def reinitialize_database_connection():
    # Force reload configuration from disk to pick up any changes
    db_config_manager.reload_config()
    db = get_database_connection(force_reinitialize=True)
    _bind_models_to_db(db)
    return db
