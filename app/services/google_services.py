"""
JTTBH Google Services
======================
Provides Gmail and Google Calendar integration via the Google API client
libraries.  OAuth 2.0 tokens are persisted in the ``user`` table so users
only need to authorise once.

    google_services.get_gmail_messages(user_id, days=3)   -> list[dict]
    google_services.get_calendar_events(user_id, days=7)  -> list[dict]
    google_services.refresh_token_if_needed(user_id)      -> bool
    google_services.get_credentials(user_id)              -> Credentials | None

OAuth 2.0 scopes requested
---------------------------
    openid
    https://www.googleapis.com/auth/userinfo.email
    https://www.googleapis.com/auth/userinfo.profile
    https://www.googleapis.com/auth/gmail.readonly
    https://www.googleapis.com/auth/calendar.readonly

Environment variables
---------------------
    GOOGLE_CLIENT_ID      OAuth 2.0 client ID from Google Cloud Console
    GOOGLE_CLIENT_SECRET  OAuth 2.0 client secret
    GOOGLE_REDIRECT_URI   Callback URI registered in Google Cloud Console
"""

import os
import sys
import traceback
from datetime import datetime, timezone, timedelta

# Google API imports – guarded so the app still starts even if the packages
# have not been installed yet (useful during initial project setup).
try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    _GOOGLE_AVAILABLE = True
except ImportError:
    _GOOGLE_AVAILABLE = False
    print(
        '[GoogleServices] google-auth or google-api-python-client not installed. '
        'Google features will be unavailable.',
        file=sys.stderr,
    )


# ---------------------------------------------------------------------------
# Scopes
# ---------------------------------------------------------------------------

SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar.readonly',
]


# ---------------------------------------------------------------------------
# GoogleServicesManager
# ---------------------------------------------------------------------------

class GoogleServicesManager:
    """
    Handles OAuth 2.0 token lifecycle and wraps Gmail / Calendar API calls.

    Tokens are stored in the ``user`` table columns:
        access_token    – current OAuth access token
        refresh_token   – long-lived refresh token
        token_expires   – DATETIME when the access token expires

    All public methods return empty lists / ``False`` / ``None`` on error
    rather than raising, so callers can degrade gracefully.
    """

    def __init__(self):
        self._client_id     = os.environ.get('GOOGLE_CLIENT_ID', '')
        self._client_secret = os.environ.get('GOOGLE_CLIENT_SECRET', '')
        self._redirect_uri  = os.environ.get(
            'GOOGLE_REDIRECT_URI',
            'http://127.0.0.1:5000/auth/oauth2callback',
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _is_configured(self) -> bool:
        """Return True only when OAuth credentials are present."""
        return bool(self._client_id and self._client_secret)

    def _get_user_token_row(self, user_id: str) -> dict | None:
        """Fetch token columns for a user from the database."""
        try:
            from app.services.database import db_manager  # noqa: PLC0415
            return db_manager.execute_one(
                'SELECT access_token, refresh_token, token_expires '
                'FROM user WHERE userID = %s',
                (user_id,),
            )
        except Exception:  # noqa: BLE001
            print(
                f'[GoogleServices] DB error fetching token for user {user_id}:\n'
                f'{traceback.format_exc()}',
                file=sys.stderr,
            )
            return None

    def _save_tokens(
        self,
        user_id: str,
        access_token: str,
        refresh_token: str | None,
        expires_at: datetime | None,
    ) -> None:
        """Persist refreshed tokens back to the database."""
        try:
            from app.services.database import db_manager  # noqa: PLC0415
            # Only update refresh_token when Google returns a new one
            if refresh_token:
                db_manager.execute_update(
                    'UPDATE user '
                    'SET access_token = %s, refresh_token = %s, token_expires = %s '
                    'WHERE userID = %s',
                    (access_token, refresh_token, expires_at, user_id),
                )
            else:
                db_manager.execute_update(
                    'UPDATE user '
                    'SET access_token = %s, token_expires = %s '
                    'WHERE userID = %s',
                    (access_token, expires_at, user_id),
                )
        except Exception:  # noqa: BLE001
            print(
                f'[GoogleServices] DB error saving tokens for user {user_id}:\n'
                f'{traceback.format_exc()}',
                file=sys.stderr,
            )

    def _build_credentials(self, row: dict) -> 'Credentials | None':
        """Construct a google.oauth2.credentials.Credentials object from a DB row."""
        if not _GOOGLE_AVAILABLE:
            return None
        if not row or not row.get('access_token'):
            return None

        # token_expires may be stored as a datetime or None
        expiry = row.get('token_expires')
        if isinstance(expiry, str):
            try:
                expiry = datetime.fromisoformat(expiry)
            except ValueError:
                expiry = None

        creds = Credentials(
            token=row['access_token'],
            refresh_token=row.get('refresh_token'),
            token_uri='https://oauth2.googleapis.com/token',
            client_id=self._client_id,
            client_secret=self._client_secret,
            scopes=SCOPES,
        )
        if expiry:
            # Credentials expects a timezone-aware datetime
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
            creds.expiry = expiry

        return creds

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_credentials(self, user_id: str) -> 'Credentials | None':
        """
        Return valid OAuth credentials for the given user, refreshing if needed.

        Parameters
        ----------
        user_id : str
            The user's UUID from the ``user`` table.

        Returns
        -------
        Credentials | None
            A valid ``google.oauth2.credentials.Credentials`` instance, or
            ``None`` if no tokens are stored or if refresh fails.
        """
        if not _GOOGLE_AVAILABLE or not self._is_configured():
            return None

        row = self._get_user_token_row(user_id)
        if not row:
            return None

        creds = self._build_credentials(row)
        if creds is None:
            return None

        # Refresh the token if it has expired or is about to expire
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                self._save_tokens(
                    user_id,
                    creds.token,
                    creds.refresh_token,
                    creds.expiry,
                )
            except Exception:  # noqa: BLE001
                print(
                    f'[GoogleServices] Token refresh failed for user {user_id}:\n'
                    f'{traceback.format_exc()}',
                    file=sys.stderr,
                )
                return None

        return creds

    def refresh_token_if_needed(self, user_id: str) -> bool:
        """
        Refresh the stored access token if it is expired.

        Parameters
        ----------
        user_id : str
            The user's UUID.

        Returns
        -------
        bool
            ``True`` if the token is valid (possibly after refresh),
            ``False`` if refresh failed or no token exists.
        """
        creds = self.get_credentials(user_id)
        return creds is not None and creds.valid

    def get_gmail_messages(self, user_id: str, days: int = 3) -> list[dict]:
        """
        Return a list of recent Gmail message summaries.

        Only messages received in the last ``days`` days are returned.
        Each dict contains:
            id          – Gmail message ID
            thread_id   – Gmail thread ID
            subject     – Email subject (decoded)
            from        – Sender address
            date        – Received date string
            snippet     – Short preview text from Gmail

        Parameters
        ----------
        user_id : str
            The user's UUID.
        days : int
            Look-back window in days (default: 3).

        Returns
        -------
        list[dict]
            Message summaries, newest first.  Empty list on any error.
        """
        if not _GOOGLE_AVAILABLE:
            return []

        creds = self.get_credentials(user_id)
        if not creds:
            return []

        try:
            service = build('gmail', 'v1', credentials=creds, cache_discovery=False)

            # Build a date-range query
            after_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime('%Y/%m/%d')
            query = f'after:{after_date}'

            result = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=50,
            ).execute()

            messages_meta = result.get('messages', [])
            messages = []

            for meta in messages_meta:
                msg_detail = service.users().messages().get(
                    userId='me',
                    id=meta['id'],
                    format='metadata',
                    metadataHeaders=['Subject', 'From', 'Date'],
                ).execute()

                headers = {
                    h['name']: h['value']
                    for h in msg_detail.get('payload', {}).get('headers', [])
                }

                messages.append({
                    'id':        msg_detail.get('id', ''),
                    'thread_id': msg_detail.get('threadId', ''),
                    'subject':   headers.get('Subject', '(no subject)'),
                    'from':      headers.get('From', ''),
                    'date':      headers.get('Date', ''),
                    'snippet':   msg_detail.get('snippet', ''),
                })

            return messages

        except Exception:  # noqa: BLE001
            print(
                f'[GoogleServices] Gmail API error for user {user_id}:\n'
                f'{traceback.format_exc()}',
                file=sys.stderr,
            )
            return []

    def get_calendar_events(self, user_id: str, days: int = 7) -> list[dict]:
        """
        Return upcoming Google Calendar events for the next ``days`` days.

        Each dict contains:
            id          – Calendar event ID
            summary     – Event title
            start       – Start datetime string (ISO 8601)
            end         – End datetime string (ISO 8601)
            location    – Location string (may be empty)
            description – Event description (may be empty)
            all_day     – True if this is an all-day event

        Parameters
        ----------
        user_id : str
            The user's UUID.
        days : int
            How many days ahead to look (default: 7).

        Returns
        -------
        list[dict]
            Events ordered by start time.  Empty list on any error.
        """
        if not _GOOGLE_AVAILABLE:
            return []

        creds = self.get_credentials(user_id)
        if not creds:
            return []

        try:
            service = build('calendar', 'v3', credentials=creds, cache_discovery=False)

            now       = datetime.now(timezone.utc)
            time_min  = now.isoformat()
            time_max  = (now + timedelta(days=days)).isoformat()

            result = service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime',
                maxResults=100,
            ).execute()

            events = []
            for item in result.get('items', []):
                start = item.get('start', {})
                end   = item.get('end', {})

                # All-day events use 'date'; timed events use 'dateTime'
                all_day    = 'date' in start and 'dateTime' not in start
                start_val  = start.get('dateTime', start.get('date', ''))
                end_val    = end.get('dateTime', end.get('date', ''))

                events.append({
                    'id':          item.get('id', ''),
                    'summary':     item.get('summary', '(no title)'),
                    'start':       start_val,
                    'end':         end_val,
                    'location':    item.get('location', ''),
                    'description': item.get('description', ''),
                    'all_day':     all_day,
                })

            return events

        except Exception:  # noqa: BLE001
            print(
                f'[GoogleServices] Calendar API error for user {user_id}:\n'
                f'{traceback.format_exc()}',
                file=sys.stderr,
            )
            return []


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

#: Shared GoogleServicesManager instance.  Import in route modules as:
#:
#:     from app.services.google_services import google_services
google_services = GoogleServicesManager()
