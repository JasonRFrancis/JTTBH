"""
Report Routes
=============
User-facing bug report / feature request submission. Open to any logged-in
user (no permission bit) — it's a feedback channel, not a gated feature.

URL patterns
------------
GET  /<username>/report
GET  /<username>/report/create
POST /<username>/report/create/post
"""

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.models.error_report_model import ErrorReportModel
from app.services.decorators import login_required

report_bp = Blueprint('report', __name__)

_VALID_TYPES = ('bug_report', 'feature_request')


@report_bp.route('')
@login_required
def index(username: str):
    """List the current user's own submitted reports, newest first."""
    reports = ErrorReportModel.get_all(userID=session['user_id'])
    return render_template(
        'report_index.html',
        username=username,
        area='report',
        reports=reports,
    )


@report_bp.route('/create')
@login_required
def create_form(username: str):
    """Render the bug report / feature request submission form."""
    return render_template('report_create.html', username=username, area='report')


@report_bp.route('/create/post', methods=['POST'])
@login_required
def create(username: str):
    """Validate and insert a new bug report or feature request."""
    type_ = request.form.get('type', '').strip()
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip() or None

    if type_ not in _VALID_TYPES or not title:
        flash('Please choose a type and enter a title.', 'error')
        return redirect(url_for('report.create_form', username=username))

    ErrorReportModel.create(
        type_,
        title,
        description=description,
        userID=session['user_id'],
        username=username,
        url=request.referrer,
        created_by=session['user_id'],
    )
    flash('Thanks — your report has been submitted.', 'success')
    return redirect(url_for('report.index', username=username))
