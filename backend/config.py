import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# PostgreSQL — дефолты работают из коробки с дефолтной установкой PostgreSQL.
# Если нужно поменять — задай переменные окружения (см. README), а не меняй этот файл.
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "oshop_db")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

DATABASE_URL = (
    f"postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

# JWT — секретный ключ для подписи токенов.
# В продакшне задаётся через переменную окружения SECRET_KEY.
# Дефолт — только для локальной разработки / пет-проекта.
SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key_change_in_production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Дефолтный админ — создаётся при первом запуске setup_db.py
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# Flask
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev_flask_secret_change_in_production")
