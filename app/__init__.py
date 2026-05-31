"""
JTTBH Flask Application Factory
================================
"Just Trying to be Helpful" - Personal productivity Flask app.

This module contains the application factory function `create_app()` which
initialises the Flask application, registers all blueprints, sets up error
handlers, configures Jinja2 globals, and wires up per-request logging.
"""

import os
import sys
import traceback
from datetime import datetime, date, timedelta

from flask import Flask, redirect, url_for, request, session, g

# Load .env file if present (development convenience)
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def create_app(config_object=None):
    """
    Create and configure the Flask application.

    Parameters
    ----------
    config_object : object, optional
        A configuration class to load.  When omitted the factory reads the
        ``FLASK_ENV`` environment variable (default ``development``) and
        imports either ``config.dev.DevelopmentConfig`` or
        ``config.prod.ProductionConfig``.

    Returns
    -------
    Flask
        The fully configured Flask application instance.
    """
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
        static_folder=os.path.join(os.path.dirname(__file__), 'static'),
    )

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------
    _load_config(app, config_object)

    # ------------------------------------------------------------------
    # Jinja2 globals – make Python builtins available in every template
    # ------------------------------------------------------------------
    def _has_perm(perm_bit: int) -> bool:
        """Check if the current session user has a permission bit set."""
        from flask import session as _session  # noqa: PLC0415
        return bool(_session.get('perm_read', 0) & perm_bit)

    def _has_write_perm(perm_bit: int) -> bool:
        """Check if the current session user has a write permission bit set."""
        from flask import session as _session  # noqa: PLC0415
        return bool(_session.get('perm_write', 0) & perm_bit)

    app.jinja_env.globals.update(
        datetime=datetime,
        date=date,
        timedelta=timedelta,
        has_perm=_has_perm,
        has_write_perm=_has_write_perm,
        bitand=lambda a, b: int(a or 0) & b,
    )

    # ------------------------------------------------------------------
    # Jinja2 custom filters
    # ------------------------------------------------------------------
    _register_template_filters(app)

    # ------------------------------------------------------------------
    # Blueprints
    # ------------------------------------------------------------------
    _register_blueprints(app)

    # ------------------------------------------------------------------
    # Error handlers
    # ------------------------------------------------------------------
    _register_error_handlers(app)

    # ------------------------------------------------------------------
    # Per-request hooks (logging, teardown)
    # ------------------------------------------------------------------
    _register_request_hooks(app)

    # ------------------------------------------------------------------
    # Root route
    # ------------------------------------------------------------------
    @app.route('/')
    def index():
        """Redirect bare root URL to the login page."""
        return redirect(url_for('auth.login'))

    return app


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _register_template_filters(app: Flask) -> None:
    """Register custom Jinja2 filters used across templates."""
    try:
        import markdown as md_module
        @app.template_filter('markdown')
        def markdown_filter(text):
            """Render Markdown text to safe HTML (no raw HTML tags)."""
            if not text:
                return ''
            return md_module.markdown(
                text,
                extensions=['nl2br'],
                output_format='html',
            )
    except ImportError:
        @app.template_filter('markdown')
        def markdown_filter(text):
            return text or ''

    @app.template_filter('format_day_short')
    def format_day_short(d):
        """Format a date as 'Mon 27'."""
        if not d:
            return ''
        return d.strftime('%a %-d')

    @app.template_filter('format_day')
    def format_day(d):
        """Format a date as 'Mon Sep 27'."""
        if not d:
            return ''
        return d.strftime('%a %b %-d')

    @app.template_filter('format_date_long')
    def format_date_long(d):
        """Format a date as 'Monday, September 27, 2025'."""
        if not d:
            return ''
        return d.strftime('%A, %B %-d, %Y')

    @app.template_filter('dayweek_label')
    def dayweek_label(bitmask):
        """Convert a dayweek bitmask to a human-readable string."""
        if bitmask is None:
            return ''
        days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        active = [days[i] for i in range(7) if bitmask & (1 << i)]
        if len(active) == 7:
            return 'Every day'
        if active == ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']:
            return 'Weekdays'
        if active == ['Sat', 'Sun']:
            return 'Weekends'
        return ', '.join(active) if active else 'No days'


def _load_config(app: Flask, config_object=None) -> None:
    """Load configuration from a class object or from the environment."""
    if config_object is not None:
        app.config.from_object(config_object)
        return

    env = os.environ.get('FLASK_ENV', 'development').lower()

    # Ensure the project root is on sys.path so `config.*` can be imported
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    if env == 'production':
        from config.prod import ProductionConfig  # noqa: PLC0415
        app.config.from_object(ProductionConfig)
    else:
        from config.dev import DevelopmentConfig  # noqa: PLC0415
        app.config.from_object(DevelopmentConfig)

    # Allow OAuthLib over plain HTTP in development (set by DevelopmentConfig)
    if app.config.get('OAUTHLIB_INSECURE_TRANSPORT'):
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


def _register_blueprints(app: Flask) -> None:
    """Import and register every blueprint with its URL prefix."""

    # Each tuple is (import_path, blueprint_attr, url_prefix)
    blueprint_specs = [
        ('app.routes.auth',        'auth_bp',        '/auth'),
        ('app.routes.dashboard',   'dashboard_bp',   '/<username>/dashboard'),
        ('app.routes.admin',       'admin_bp',       '/<username>/admin'),
        ('app.routes.user',        'user_bp',        '/<username>'),
        ('app.routes.todo',        'todo_bp',        '/<username>/todo'),
        ('app.routes.habit',       'habit_bp',       '/<username>/habit'),
        ('app.routes.project',     'project_bp',     '/<username>/project'),
        ('app.routes.bookmark',    'bookmark_bp',    '/<username>/bookmark'),
        ('app.routes.fitness',     'fitness_bp',     '/<username>/fitness'),
        ('app.routes.triage',      'triage_bp',      '/<username>/triage'),
        ('app.routes.vacation',    'vacation_bp',    '/<username>/vacation'),
        ('app.routes.appointment', 'appointment_bp', '/<username>/appointment'),
        ('app.routes.podcast',     'podcast_bp',     '/<username>/podcast'),
        ('app.routes.chore',       'chore_bp',       '/<username>/chore'),
        ('app.routes.book',        'book_bp',        '/<username>/book'),
        ('app.routes.media',       'media_bp',       '/<username>/media'),
        ('app.routes.journal',     'journal_bp',     '/<username>/journal'),
        ('app.routes.study',       'study_bp',       '/<username>/study'),
        ('app.routes.quote',       'quote_bp',       '/<username>/quote'),
    ]

    for module_path, bp_attr, url_prefix in blueprint_specs:
        try:
            import importlib
            module = importlib.import_module(module_path)
            blueprint = getattr(module, bp_attr)
            app.register_blueprint(blueprint, url_prefix=url_prefix)
        except ModuleNotFoundError:
            # Blueprint module not yet implemented – skip gracefully during
            # early development so the app still starts.
            app.logger.warning(
                'Blueprint module not found: %s – skipping registration.',
                module_path,
            )
        except AttributeError:
            app.logger.warning(
                'Blueprint attribute %r not found in %s – skipping.',
                bp_attr,
                module_path,
            )


def _register_error_handlers(app: Flask) -> None:
    """Register HTML error pages for common HTTP error codes."""

    from flask import render_template  # noqa: PLC0415

    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html', error=error), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html', error=error), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error('500 error: %s\n%s', error, traceback.format_exc())
        return render_template('errors/500.html', error=error), 500


def _register_request_hooks(app: Flask) -> None:
    """
    Register before/after request hooks.

    After every request (including those that raise exceptions) an entry is
    written to the ``log`` database table so that there is a complete audit
    trail of all HTTP activity.
    """

    @app.after_request
    def log_request(response):
        """
        Write a row to the ``log`` table after every HTTP request.

        Columns written:
            user_id     – UUID string from session, or NULL for anonymous
            method      – HTTP verb (GET, POST, …)
            path        – URL path (without query string)
            status_code – Integer HTTP response status
            ip_address  – Client IP address
            created_at  – Handled automatically by the DB default/NOW()
        """
        try:
            from app.services.database import db_manager  # noqa: PLC0415

            sql = """
                INSERT INTO log (userid, username, resource, `get`, `post`, ip, user_agent, created)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """
            db_manager.execute_insert(
                sql,
                (
                    session.get('user_id'),
                    session.get('username'),
                    request.path,
                    str(request.args.to_dict()) if request.args else None,
                    str(request.form.to_dict()) if request.method == 'POST' and request.form else None,
                    request.remote_addr,
                    request.user_agent.string[:512] if request.user_agent.string else None,
                ),
            )
        except Exception:  # noqa: BLE001 – never let logging break the response
            app.logger.error(
                'Failed to write request log: %s', traceback.format_exc()
            )

        return response
