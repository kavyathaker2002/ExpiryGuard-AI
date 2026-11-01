import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

# Load project-root environment values before routes or AI clients are imported.
# Existing process environment values take precedence over values in .env.
load_dotenv(dotenv_path=Path(__file__).resolve().parent / '.env', override=False)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE = os.path.join(BASE_DIR, 'instance', 'expiryguard.db')
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', '0') == '1'
    PERMANENT_SESSION_LIFETIME = 86400 * 7  # 7 days
    MAX_IMAGE_BYTES = 8 * 1024 * 1024
    MAX_CONTENT_LENGTH = 9 * 1024 * 1024
