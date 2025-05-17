import sys
import os

# Додаємо шлях до каталогу dz7, щоб імпорти типу 'from models.base' працювали
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from models.base import Base
from config import DATABASE_URL


config = context.config
config.set_main_option('sqlalchemy.url', DATABASE_URL)

if config.config_file_name is not None:
    try:
        fileConfig(config.config_file_name)
    except KeyError:
        pass  # Вимикаємо логування, якщо немає handlers

connectable = engine_from_config(
    config.get_section(config.config_ini_section),
    prefix="sqlalchemy.",
    poolclass=pool.NullPool)

with connectable.connect() as connection:
    context.configure(
        connection=connection,
        target_metadata=Base.metadata
    )

    with context.begin_transaction():
        context.run_migrations()