import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'data'
UPLOAD_DIR = BASE_DIR / 'uploads'
EXPORT_CACHE_DIR = BASE_DIR / 'export_cache'
DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)
EXPORT_CACHE_DIR.mkdir(exist_ok=True)


def _normalize_database_url(url: str) -> str:
    """Normalize database URL for SQLAlchemy compatibility."""
    if not url:
        return url
    
    # Handle Railway's postgres:// format (convert to postgresql://)
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    
    # Convert to SQLAlchemy compatible format with psycopg driver (v3)
    if url.startswith('postgresql://') and not url.startswith('postgresql+psycopg://'):
        url = url.replace('postgresql://', 'postgresql+psycopg://', 1)
    
    return url


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'replace-me-before-production')
    APP_ENV = os.getenv('APP_ENV', os.getenv('FLASK_ENV', 'development'))
    BASE_URL = os.getenv('BASE_URL', 'http://127.0.0.1:5000')
    SQLALCHEMY_DATABASE_URI = _normalize_database_url(
        os.getenv('DATABASE_URL', f'sqlite:///{(DATA_DIR / "swimdiary.db").as_posix()}')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    ALLOW_FREE_EXPORTS = os.getenv('ALLOW_FREE_EXPORTS', 'false').lower() == 'true'
    ALLOW_DEV_VIP = os.getenv('ALLOW_DEV_VIP', 'true').lower() == 'true'

    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '')
    STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')
    STRIPE_PRICE_MONTHLY = os.getenv('STRIPE_PRICE_MONTHLY', '')
    STRIPE_PRICE_YEARLY = os.getenv('STRIPE_PRICE_YEARLY', '')

    STORAGE_BACKEND = os.getenv('STORAGE_BACKEND', 'local')
    R2_ACCOUNT_ID = os.getenv('R2_ACCOUNT_ID', '')
    R2_ACCESS_KEY_ID = os.getenv('R2_ACCESS_KEY_ID', '')
    R2_SECRET_ACCESS_KEY = os.getenv('R2_SECRET_ACCESS_KEY', '')
    R2_BUCKET = os.getenv('R2_BUCKET', '')
    R2_ENDPOINT = os.getenv('R2_ENDPOINT', '')
    R2_PUBLIC_BASE_URL = os.getenv('R2_PUBLIC_BASE_URL', '')


class ProductionConfig(Config):
    APP_ENV = 'production'
    ALLOW_DEV_VIP = False
