"""
JTTBH Production Configuration
================================
All sensitive values are read exclusively from environment variables.
The application will start with empty strings for unconfigured keys,
but will not function correctly until every variable is set.

Set these in your hosting environment (systemd unit, Docker env file,
AWS Parameter Store, etc.) – never commit real values to source control.
"""

import os


class ProductionConfig:
    # ------------------------------------------------------------------ #
    # Flask core                                                           #
    # ------------------------------------------------------------------ #
    DEBUG = False

    # REQUIRED – generate a strong random key, e.g.:
    #   python -c "import secrets; print(secrets.token_hex(32))"
    SECRET_KEY = os.environ.get('SECRET_KEY', '')

    # ------------------------------------------------------------------ #
    # MySQL                                                                #
    # ------------------------------------------------------------------ #
    MYSQL_HOST     = os.environ.get('MYSQL_HOST',     'localhost')
    MYSQL_PORT     = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_USER     = os.environ.get('MYSQL_USER',     '')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_DB       = os.environ.get('MYSQL_DB',       'jttbh')

    # ------------------------------------------------------------------ #
    # Google OAuth 2.0                                                     #
    # ------------------------------------------------------------------ #
    GOOGLE_CLIENT_ID     = os.environ.get('GOOGLE_CLIENT_ID',     '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    GOOGLE_REDIRECT_URI  = os.environ.get(
        'GOOGLE_REDIRECT_URI',
        'https://yourdomain.com/auth/oauth2callback',
    )

    # MUST be absent (or '0') in production – OAuth requires HTTPS
    OAUTHLIB_INSECURE_TRANSPORT = '0'

    # ------------------------------------------------------------------ #
    # SMTP / Email                                                         #
    # ------------------------------------------------------------------ #
    SMTP_HOST     = os.environ.get('SMTP_HOST',     '')
    SMTP_PORT     = int(os.environ.get('SMTP_PORT', 587))
    SMTP_USER     = os.environ.get('SMTP_USER',     '')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
    SMTP_FROM     = os.environ.get('SMTP_FROM',     '')
    ADMIN_EMAIL   = os.environ.get('ADMIN_EMAIL',   '')

    # ------------------------------------------------------------------ #
    # External APIs                                                        #
    # ------------------------------------------------------------------ #
    TMDB_API_KEY = os.environ.get('TMDB_API_KEY', '')

    # ------------------------------------------------------------------ #
    # Session                                                              #
    # ------------------------------------------------------------------ #
    SESSION_COOKIE_SECURE   = True    # Require HTTPS for session cookies
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 604800  # 7 days in seconds
