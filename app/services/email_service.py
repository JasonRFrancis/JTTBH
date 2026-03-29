"""
JTTBH Email Service
====================
Provides a simple SMTP-based email service with three high-level helpers:

    email_service.send_email(to, subject, body, html_body=None)
    email_service.send_approval_notification(user_email, username, approved)
    email_service.send_admin_alert(subject, message)

Configuration is read from environment variables.  If any required variable is
missing or SMTP is unreachable, the service logs a warning and silently skips
sending rather than crashing the application.

Environment variables
---------------------
    SMTP_HOST       Hostname of the SMTP server  (e.g. smtp.gmail.com)
    SMTP_PORT       Port number                  (default: 587)
    SMTP_USER       SMTP authentication username
    SMTP_PASSWORD   SMTP authentication password
    SMTP_FROM       "From" address used in sent mail
    ADMIN_EMAIL     Destination address for admin alerts
"""

import os
import sys
import smtplib
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


# ---------------------------------------------------------------------------
# EmailService
# ---------------------------------------------------------------------------

class EmailService:
    """
    Thin SMTP email sender.

    All public methods are deliberately tolerant of misconfiguration: if the
    SMTP settings are absent or a connection error occurs, a warning is printed
    to stderr and the method returns ``False`` instead of raising.
    """

    def __init__(self):
        """Read SMTP configuration from environment variables."""
        self._host     = os.environ.get('SMTP_HOST', '')
        self._port     = int(os.environ.get('SMTP_PORT', 587))
        self._user     = os.environ.get('SMTP_USER', '')
        self._password = os.environ.get('SMTP_PASSWORD', '')
        self._from     = os.environ.get('SMTP_FROM', '')
        self._admin    = os.environ.get('ADMIN_EMAIL', '')

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _is_configured(self) -> bool:
        """Return True only when all required SMTP fields are present."""
        return bool(self._host and self._user and self._password and self._from)

    def _build_message(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: str | None = None,
    ) -> MIMEMultipart:
        """
        Construct a MIME message.

        If ``html_body`` is provided the message is sent as
        ``multipart/alternative`` with both plain-text and HTML parts so that
        mail clients can display whichever they prefer.
        """
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = self._from
        msg['To']      = to

        # Plain-text part is always included as the fallback
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        if html_body:
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        return msg

    def _send(self, to: str, msg: MIMEMultipart) -> bool:
        """
        Open an SMTP connection, authenticate, and deliver ``msg``.

        Returns
        -------
        bool
            ``True`` on success, ``False`` on any failure.
        """
        try:
            with smtplib.SMTP(self._host, self._port, timeout=10) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(self._user, self._password)
                server.sendmail(self._from, [to], msg.as_string())
            return True
        except smtplib.SMTPException as exc:
            print(
                f'[EmailService] SMTP error sending to {to!r}: {exc}\n'
                f'{traceback.format_exc()}',
                file=sys.stderr,
            )
            return False
        except OSError as exc:
            print(
                f'[EmailService] Network error sending to {to!r}: {exc}',
                file=sys.stderr,
            )
            return False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: str | None = None,
    ) -> bool:
        """
        Send an email message.

        Parameters
        ----------
        to : str
            Recipient email address.
        subject : str
            Email subject line.
        body : str
            Plain-text body.
        html_body : str, optional
            HTML body.  When provided, the message is sent as
            ``multipart/alternative``.

        Returns
        -------
        bool
            ``True`` if the message was delivered, ``False`` otherwise.
        """
        if not self._is_configured():
            print(
                '[EmailService] SMTP not configured – skipping send_email.',
                file=sys.stderr,
            )
            return False

        msg = self._build_message(to, subject, body, html_body)
        return self._send(to, msg)

    def send_approval_notification(
        self,
        user_email: str,
        username: str,
        approved: bool,
    ) -> bool:
        """
        Notify a user that their account registration was approved or rejected.

        Parameters
        ----------
        user_email : str
            The user's email address.
        username : str
            The user's chosen username.
        approved : bool
            ``True`` if the account was approved, ``False`` if rejected.

        Returns
        -------
        bool
            ``True`` if the notification was delivered.
        """
        if approved:
            subject = 'Your JTTBH account has been approved'
            body = (
                f'Hi {username},\n\n'
                'Good news – your JTTBH account has been approved.\n'
                'You can now log in at /auth/login.\n\n'
                'Just Trying to be Helpful'
            )
            html_body = (
                f'<p>Hi <strong>{username}</strong>,</p>'
                '<p>Good news – your JTTBH account has been <strong>approved</strong>.</p>'
                '<p>You can now <a href="/auth/login">log in</a>.</p>'
                '<p><em>Just Trying to be Helpful</em></p>'
            )
        else:
            subject = 'Your JTTBH account registration'
            body = (
                f'Hi {username},\n\n'
                'Unfortunately your JTTBH account registration was not approved.\n'
                'Please contact the administrator if you believe this is an error.\n\n'
                'Just Trying to be Helpful'
            )
            html_body = (
                f'<p>Hi <strong>{username}</strong>,</p>'
                '<p>Unfortunately your JTTBH account registration was '
                '<strong>not approved</strong>.</p>'
                '<p>Please contact the administrator if you believe this is an error.</p>'
                '<p><em>Just Trying to be Helpful</em></p>'
            )

        return self.send_email(user_email, subject, body, html_body)

    def send_admin_alert(self, subject: str, message: str) -> bool:
        """
        Send an alert email to the configured administrator address.

        Parameters
        ----------
        subject : str
            Email subject line.
        message : str
            Plain-text alert body.

        Returns
        -------
        bool
            ``True`` if the alert was delivered.
        """
        if not self._admin:
            print(
                '[EmailService] ADMIN_EMAIL not configured – skipping admin alert.',
                file=sys.stderr,
            )
            return False

        return self.send_email(self._admin, f'[JTTBH Alert] {subject}', message)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

#: Shared EmailService instance.  Import in route modules as:
#:
#:     from app.services.email_service import email_service
email_service = EmailService()
