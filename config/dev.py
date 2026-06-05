"""
JTTBH Development Configuration
=================================
Used when ``FLASK_ENV=development`` (the default).

Values are read from environment variables (loaded from .env by the app
factory).  The hard-coded defaults are only used when a variable is absent.

**Never use these values in production.**
"""

import os


class DevelopmentConfig:
    # ------------------------------------------------------------------ #
    # Flask core                                                           #
    # ------------------------------------------------------------------ #
    DEBUG      = True
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # ------------------------------------------------------------------ #
    # MySQL                                                                #
    # ------------------------------------------------------------------ #
    MYSQL_HOST     = os.environ.get('MYSQL_HOST',     'localhost')
    MYSQL_PORT     = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_USER     = os.environ.get('MYSQL_USER',     'jttbh')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'jttbh')
    # Support both MYSQL_DB and MYSQL_DATABASE env var names
    MYSQL_DB       = os.environ.get('MYSQL_DB') or os.environ.get('MYSQL_DATABASE', 'jttbh')

    # ------------------------------------------------------------------ #
    # Google OAuth 2.0                                                     #
    # ------------------------------------------------------------------ #
    GOOGLE_CLIENT_ID     = os.environ.get('GOOGLE_CLIENT_ID',     '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    GOOGLE_REDIRECT_URI  = os.environ.get('GOOGLE_REDIRECT_URI',  'http://127.0.0.1:5000/auth/oauth2callback')

    # Allow OAuth over plain HTTP in development (localhost only)
    OAUTHLIB_INSECURE_TRANSPORT = '1'

    # ------------------------------------------------------------------ #
    # SMTP / Email                                                         #
    # ------------------------------------------------------------------ #
    # Support both SMTP_HOST and SMTP_SERVER env var names
    SMTP_HOST     = os.environ.get('SMTP_HOST') or os.environ.get('SMTP_SERVER', '')
    SMTP_PORT     = int(os.environ.get('SMTP_PORT', 587))
    # Support both SMTP_USER and SMTP_USERNAME env var names
    SMTP_USER     = os.environ.get('SMTP_USER') or os.environ.get('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
    # Support both SMTP_FROM and FROM_EMAIL env var names
    SMTP_FROM     = os.environ.get('SMTP_FROM') or os.environ.get('FROM_EMAIL', '')
    ADMIN_EMAIL   = os.environ.get('ADMIN_EMAIL', '')

    # ------------------------------------------------------------------ #
    # Session                                                              #
    # ------------------------------------------------------------------ #
    # ------------------------------------------------------------------ #
    # External APIs                                                        #
    # ------------------------------------------------------------------ #
    TMDB_API_KEY       = os.environ.get('TMDB_API_KEY', '')
    IMPORT_API_KEY     = os.environ.get('IMPORT_API_KEY', '')

    # ------------------------------------------------------------------ #
    # File uploads                                                         #
    # ------------------------------------------------------------------ #
    _BASE_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    UPLOAD_FOLDER  = os.path.join(_BASE_DIR, 'app', 'static', 'uploads', 'recipes')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

    SESSION_COOKIE_SECURE   = False   # Allow HTTP cookies in development
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 604800  # 7 days in seconds
