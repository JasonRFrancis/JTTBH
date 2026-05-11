# JTTBH — Master Reference

**"Just Trying to be Helpful"** — personal productivity dashboard  
**Stack:** Python 3.10+ / Flask 3.0+ / MySQL 9.0+ / PyMySQL (no ORM)  
**Live:** https://jttbh.com | **Repo:** https://github.com/JasonRFrancis/JTTBH  
**Dev:** `python ./app/main.py` from project root

---

## Part A — Working With This Project

### A1. Workflow

- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions). Stop and re-plan if things go sideways — don't keep pushing.
- Use subagents to keep the main context window clean; offload research and parallel analysis.
- After ANY correction from the user: update `claude/LESSONS.md` with the pattern.
- Never mark a task complete without demonstrating it works (logs, tests, or browser test).
- For non-trivial changes: pause and ask "is there a more elegant way?"
- When given a bug report: just fix it. Point at logs/errors, resolve them. Zero hand-holding required.

### A2. Task Management

1. Write plan to `claude/TODO.md` with checkable items.
2. Check in before starting implementation on anything non-trivial.
3. Mark items complete as you go.
4. Add results/lessons to `claude/TODO.md` and `claude/LESSONS.md` when done.

### A3. Core Principles

- **Simplicity first.** Minimum code that solves the problem. Nothing speculative.
- **Surgical changes.** Touch only what the task requires. Don't "improve" adjacent code.
- **No laziness.** Find root causes. No temporary fixes or workarounds.
- **No ORM.** Raw SQL only via `db_manager`.
- **No JS frameworks.** Vanilla JS only.
- **No CSS frameworks.** Custom CSS only.

---

## Part B — Architecture

### B1. Immutable Technical Rules

| Rule | Detail |
|------|--------|
| No bitwise `&` in Jinja2 | Use `bitand(a, b)` global. `&` raises `TemplateSyntaxError`. |
| GET never mutates | Only POST changes state (except request logging) |
| PRG pattern | Every POST redirects to a GET; outcomes communicated via `flash()` |
| Permission decorators | Every route: `@login_required` + `@permission_required_read` (+ write for mutations) |
| Username ownership | Routes must verify `username == session['username']` unless the user is admin |
| Insert-only data | User data tables use insert-only pattern (see §C2); exceptions: `user`, `svg` |
| Progressive enhancement | Every page must work without CSS or JS enabled |
| Semantic HTML | `<article>`, `<section>`, `<nav>`, `<header>`, `<footer>` over `<div>` |
| Mobile-first | CSS written for mobile viewport first |

### B2. File & Naming Conventions

```
app/
  __init__.py          # app factory, Jinja2 globals, blueprint registration
  main.py              # entry point
  models/              # one file per feature: habit_model.py, todo_model.py …
  routes/              # one blueprint per feature: habit.py, todo.py …
  services/
    database.py        # db_manager singleton
    decorators.py      # login_required, permission_required_read/write, PERM_* constants
    email_service.py
    google_services.py
  static/
    css/               # base.css + one per feature (habit.css, admin.css …)
    js/                # base.js + one per feature
  templates/           # flat — naming: [feature]_[page].html
config/
  dev.py / prod.py
migrations/            # YYYYMMDD_description.sql — must be idempotent
test/
  synthetic.py         # in-memory test data
  test_*.py
claude/                # scratch files, RESULTS.md, LESSONS.md, TODO.md
schema.sql
```

**Naming rules:**
- Feature names are **singular**: `todo`, `habit`, `book`, `bookmark`, `chore`
- Files: `[feature]_model.py`, `[feature].py` (routes), `[feature]_[page].html`
- After the feature prefix, identifiers use camelCase: `todo_pushedForward`
- Templates, models, routes: **one folder deep only** (no subdirectories)

### B3. URL Structure

```
GET  /[username]/[area]/[view]/[params…]    → renders [area]_[view].html
POST /[username]/[area]/[action]/post/[id…] → mutates state, redirects (PRG)
```

- `[presentation]` (`html`/`json`) is optional on GET; default is `html`
- Dates in URLs: ISO format `YYYY-MM-DD`; date ranges: `YYYY-MM-DD-YYYY-MM-DD`
- POST action describes the mutation: `create`, `update`, `delete`, `toggle`, `reorder`, `move`

**Examples:**
```
GET  /jason/todo/index
GET  /jason/todo/index/2025-09-27
POST /jason/todo/create/post
POST /jason/todo/toggle/post/<todoID>
POST /jason/todo/delete/post/<todoID>
```

### B4. Complete Route Inventory

| Blueprint | URL prefix | Defined routes |
|-----------|-----------|----------------|
| `auth_bp` | `/auth` | `GET /login`, `GET /login/google`, `GET /oauth2callback`, `GET /logout`, `GET /pending-approval` |
| `dashboard_bp` | `/<u>/dashboard` | `GET /index`, `GET /index/json` |
| `admin_bp` | `/<u>/admin` | `GET /users`, `GET /log`, `GET /icons` |
| | | `POST /users/approve/post/<user_id>`, `POST /users/reject/post/<user_id>`, `POST /users/permissions/post/<user_id>` |
| | | `POST /icon/create/post`, `POST /icon/update/post/<image_id>`, `POST /icon/delete/post/<image_id>` |
| `user_bp` | `/<u>` | `GET /settings`, `POST /settings/post` |
| `todo_bp` | `/<u>/todo` | `GET /index`, `GET /index/jump`, `GET /index/<date_str>`, `GET /search`, `GET /search/<path:query>` |
| | | `POST /create/post`, `POST /toggle/post/<todo_id>`, `POST /update/post/<todo_id>`, `POST /delete/post/<todo_id>`, `POST /move/post/<todo_id>`, `POST /reorder/post` |
| `habit_bp` | `/<u>/habit` | `GET /index`, `GET /index/<date_str>`, `GET /heatmap`, `GET /settings`, `GET /settings/<habit_id>` |
| | | `GET /positions/json?dayweek=<int>&exclude=<habitID>` — returns occupied positions with conflict flags |
| | | `POST /toggle/post/<habit_id>/<date_str>`, `POST /create/post`, `POST /update/post/<habit_id>`, `POST /delete/post/<habit_id>`, `POST /reorder/post` |
| `project_bp` | `/<u>/project` | `GET /index`, `GET /view/<project_id>` |
| | | `POST /create/post`, `POST /update/post/<project_id>`, `POST /delete/post/<project_id>`, `POST /resource/create/post/<project_id>`, `POST /resource/delete/post/<resource_id>`, `POST /send_to_todo/post/<project_id>` |
| `bookmark_bp` | `/<u>/bookmark` | `GET /index`, `GET /read-later` |
| | | `POST /create/post`, `POST /read/post/<bookmark_id>` |
| `fitness_bp` | `/<u>/fitness` | `GET /index`, `GET /log` |
| `triage_bp` | `/<u>/triage` | `GET /index` |
| `vacation_bp` | `/<u>/vacation` | `GET /index`, `POST /create/post`, `POST /delete/post/<vacation_id>` |
| `appointment_bp` | `/<u>/appointment` | `GET /index` |
| `podcast_bp` | `/<u>/podcast` | `GET /subscription`, `GET /list`, `GET /feed/<feed_id>.xml` |
| | | `POST /subscription/create/post`, `POST /list/create/post` |
| `chore_bp` | `/<u>/chore` | `GET /index` |
| `book_bp` | `/<u>/book` | `GET /index` |
| | | `POST /create/post`, `POST /update/post/<book_id>`, `POST /finish/post/<book_id>` |
| `journal_bp` | `/<u>/journal` | `GET /index`, `GET /index/<date_str>`, `GET /questions`, `GET /mood/settings` |
| | | `POST /answer/post/<question_id>`, `POST /mood/post`, `POST /question/create/post`, `POST /mood/category/create/post`, `POST /mood/value/create/post` |

---

## Part C — Data Layer

### C1. Permission System

Stored as two bitvectors (`read`, `write`) in `user_permission`. Current = row with highest `id` per `userID`.

| Bit | Value | Constant | Feature |
|-----|-------|----------|---------|
| 0 | 1 | `PERM_ADMIN` | Admin functions |
| 1 | 2 | `PERM_PODCAST` | Podcast feed |
| 2 | 4 | `PERM_APPOINTMENT` | Scheduling |
| 3 | 8 | `PERM_DASHBOARD` | Dashboard |
| 4 | 16 | `PERM_TODO` | Todo lists |
| 5 | 32 | `PERM_HABIT` | Habit tracking |
| 6 | 64 | `PERM_PROJECT` | Projects |
| 7 | 128 | `PERM_TRIAGE` | Email/Calendar triage |
| 8 | 256 | `PERM_BOOKMARK` | Bookmarks |
| 9 | 512 | `PERM_FITNESS` | Fitness |
| 10 | 1024 | `PERM_CHORE` | Household chores |
| 11 | 2048 | `PERM_BOOK` | Book tracker |
| 12 | 4096 | `PERM_JOURNAL` | Journal/mood |

**Default on approval:** `read = write = 8190` (bits 1–12 set; admin bit 0 excluded)

**Decorator usage:**
```python
from app.services.decorators import (
    login_required, permission_required_read, permission_required_write, PERM_TODO
)

@blueprint.route('/index')
@login_required
@permission_required_read(PERM_TODO)
def index(username: str): ...

@blueprint.route('/create/post', methods=['POST'])
@login_required
@permission_required_read(PERM_TODO)
@permission_required_write(PERM_TODO)
def create(username: str): ...
```

**In templates:** `has_perm(bit)` checks `session.perm_read`; `has_write_perm(bit)` checks `session.perm_write`.

### C2. Database Patterns

#### Insert-only (all user data tables by default)

```python
# Current state — always use MAX(id) subquery
SELECT col1, col2
FROM thing t
WHERE t.thingID = %s
  AND t.id = (SELECT MAX(t2.id) FROM thing t2 WHERE t2.thingID = t.thingID)
  AND t.name IS NOT NULL          -- IS NOT NULL filters soft-deletes

# Update → INSERT new row, same thingID, changed field values
INSERT INTO thing (thingID, userID, name, ..., created, created_by)
VALUES (%s, %s, %s, ..., NOW(), %s)

# Soft delete → INSERT row with sentinel column = NULL
INSERT INTO thing (thingID, userID, name, ...) VALUES (%s, %s, NULL, ...)
```

**Sentinel columns (set to NULL to soft-delete):**

| Table | Sentinel |
|-------|---------|
| `todo` | `title` |
| `habit` | `name` |
| `project` | `name` |

#### Exceptions to insert-only

| Table | Pattern | Reason |
|-------|---------|--------|
| `user` | Direct `UPDATE` | `userID` is UUID PK (stable); `approval_status`, `active`, tokens must be updated in-place |
| `svg` | Direct `UPDATE`/`DELETE` | Reference data, not user data; `imageID` has `UNIQUE KEY` constraint |

#### `db_manager` API

```python
from app.services.database import db_manager

db_manager.execute_query(sql, params)   # → list[dict]
db_manager.execute_one(sql, params)     # → dict | None
db_manager.execute_insert(sql, params)  # → int (lastrowid)
db_manager.execute_update(sql, params)  # → int (rowcount) — also for DELETE
```

All params must be tuples. Never interpolate values into SQL strings.

### C3. Key Table Schemas

Every insert-only table has: `id` (INT PK auto-increment), `<Entity>ID` (UUID varchar(36)), `userID` (FK varchar(36)), `created` (datetime), `created_by` (UUID varchar(36)).

**`user`** — UPDATE pattern, not insert-only  
`userID` (UUID PK), `google_id`, `email`, `name`, `username`, `approval_status` ENUM('pending','approved','rejected'), `active` TINYINT, `admin` TINYINT, `access_token`, `refresh_token`, `token_expires`, `created`, `created_by`

**`log`** — append-only, written by after-request hook  
`id`, `userid` (lowercase, not `userID`), `username`, `resource` (URL path), `get` (query params dict), `post` (form data dict), `ip`, `user_agent`, `created`  
⚠ No `method`, `path`, `status_code`, or `ip_address` columns.

**`svg`** — UPDATE/DELETE pattern, not insert-only  
`id`, `imageID` (UUID, UNIQUE KEY), `name`, `description`, `svg` (TEXT), `created`, `created_by`

**`user_permission`**  
`id`, `userID`, `read` (INT bitvector), `write` (INT bitvector), `created`, `created_by`  
Current row = highest `id` per `userID`.

**`habit`**  
`id`, `habitID`, `userID`, `name` (NULL = soft-deleted), `description`, `action` (URL string), `color` (hex), `icon` (name ref → `svg.name`), `active`, `dayweek` (INT bitmask, see §E2), `position` (0–24, 5×5 grid), `vacation_mode`, `created`, `created_by`

**`habit_entry`**  
`id`, `habitID`, `entry` (date), `completed` (1 or NULL), `vacation`, `created`, `created_by`

**`todo`**  
`id`, `todoID`, `userID`, `title` (NULL = soft-deleted), `content` (TEXT), `due` (date), `list_type`, `list_name`, `position`, `completed` (datetime or NULL), `added` (date), `created`, `created_by`

**`project`**  
`id`, `projectID`, `userID`, `name` (NULL = soft-deleted), `description`, `status`, `position`, `created`, `created_by`

**`book`**  
`id`, `bookID`, `userID`, `title` (NULL = soft-deleted), `author`, `status` ENUM('reading','finished','abandoned'), `started` (date), `finished` (date), `notes` (TEXT), `created`, `created_by`

---

## Part D — Application Layer

### D1. Code Patterns

#### Model (`app/models/thing_model.py`)
```python
from app.services.database import db_manager
import uuid

class ThingModel:
    @staticmethod
    def get_things(user_id: str) -> list[dict]:
        return db_manager.execute_query("""
            SELECT t.thingID, t.name, ...
            FROM thing t
            WHERE t.userID = %s
              AND t.id = (SELECT MAX(t2.id) FROM thing t2 WHERE t2.thingID = t.thingID)
              AND t.name IS NOT NULL
            ORDER BY t.position
        """, (user_id,))

    @staticmethod
    def create(user_id: str, name: str) -> str:
        thing_id = str(uuid.uuid4())
        db_manager.execute_insert(
            "INSERT INTO thing (thingID, userID, name, created, created_by) VALUES (%s,%s,%s,NOW(),%s)",
            (thing_id, user_id, name, user_id),
        )
        return thing_id
```

#### Route blueprint (`app/routes/thing.py`)
```python
from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from app.services.decorators import login_required, permission_required_read, permission_required_write, PERM_THING

thing_bp = Blueprint('thing', __name__)

@thing_bp.route('/index')
@login_required
@permission_required_read(PERM_THING)
def index(username: str):
    items = ThingModel.get_things(session['user_id'])
    return render_template('thing_index.html', username=username, area='thing', items=items)

@thing_bp.route('/create/post', methods=['POST'])
@login_required
@permission_required_read(PERM_THING)
@permission_required_write(PERM_THING)
def create(username: str):
    name = request.form.get('name', '').strip()
    if not name:
        flash('Name is required.', 'error')
        return redirect(url_for('thing.index', username=username))
    ThingModel.create(session['user_id'], name)
    flash(f'"{name}" created.', 'success')
    return redirect(url_for('thing.index', username=username))
```

#### Template (`app/templates/thing_index.html`)
```html
{% extends "base.html" %}
{% block title %}Things{% endblock %}
{% block css %}<link rel="stylesheet" href="{{ url_for('static', filename='css/thing.css') }}">{% endblock %}

{% block content %}
<header>
  <h1>Things</h1>
  <nav aria-label="Thing navigation">…</nav>
</header>
<section aria-labelledby="section-heading">
  <h2 id="section-heading">…</h2>
  …
</section>
{% endblock %}

{% block js %}<script src="{{ url_for('static', filename='js/thing.js') }}" defer></script>{% endblock %}
```

### D2. Jinja2 Globals & Filters

**Globals available in all templates:**

| Name | Type | Value |
|------|------|-------|
| `datetime` | class | `datetime.datetime` |
| `date` | class | `datetime.date` |
| `timedelta` | class | `datetime.timedelta` |
| `has_perm(bit)` | fn | True if `session.perm_read & bit` |
| `has_write_perm(bit)` | fn | True if `session.perm_write & bit` |
| `bitand(a, b)` | fn | `int(a or 0) & b` |

**Filters:** `markdown`, `format_day_short` (→ "Mon 27"), `format_day` (→ "Mon Sep 27"), `format_date_long` (→ "Monday, September 27, 2025"), `dayweek_label` (bitmask → "Weekdays")

**⚠ Never use `&` in `{% %}` blocks.** Jinja2 raises `TemplateSyntaxError: unexpected char '&'`.
```html
{# Wrong #} {% if habit.dayweek and (habit.dayweek | int) & bit %}
{# Right  #} {% if bitand(habit.dayweek, bit) %}
```

### D3. Authentication Flow

- Google OAuth 2.0 only — `app/routes/auth.py`
- Scopes: `openid`, `userinfo.email`, `userinfo.profile`, `gmail.readonly`, `calendar.readonly`
- OAuth callback: `GET /auth/oauth2callback`
- After callback: look up user by `google_id`
  - Not found → create user with `approval_status='pending'`, redirect to `/auth/pending-approval`
  - `pending` → redirect to `/auth/pending-approval`
  - `rejected` → flash error, redirect to `/auth/login`
  - `approved` → populate session, redirect to `/<username>/dashboard/index`
- Session keys set on login: `user_id`, `username`, `perm_read`, `perm_write`
- Redirect URI (production): `https://jttbh.com/auth/oauth2callback` — must match Google Cloud Console **exactly**
- Dev: set `OAUTHLIB_INSECURE_TRANSPORT=1` in `.env`
- Requires `cryptography` package (PyMySQL + MySQL 8+ `caching_sha2_password`)

### D4. Error Handling

- User-facing: `flash(message, category)` — categories: `error`, `warning`, `message`, `success`
- JSON endpoints: `{"status": "error", "message": "...", "code": "...", "details": {}}`
- All requests logged to `log` table via `@app.after_request` hook in `app/__init__.py`
- Error templates: `app/templates/errors/403.html`, `404.html`, `500.html`
- Never let logging failures break the response (errors are caught and printed to app.logger)

---

## Part E — Features

### E1. Feature Status

| Feature | Status | Blueprint | Templates |
|---------|--------|-----------|-----------|
| Auth | Implemented | `auth_bp` | `auth.html`, `pending_approval.html` |
| Dashboard | Implemented | `dashboard_bp` | `dashboard_index.html` |
| Todo | Implemented | `todo_bp` | `todo_index.html`, `todo_search.html`, `_todo_item.html` |
| Habit | Implemented | `habit_bp` | `habit_index.html`, `habit_heatmap.html`, `habit_settings.html` |
| Admin (users) | Implemented | `admin_bp` | `admin_users.html` |
| Admin (icons) | Implemented | `admin_bp` | `admin_icons.html` |
| Admin (log) | Implemented | `admin_bp` | `admin_log.html` |
| User settings | Implemented | `user_bp` | `user_settings.html` |
| Project | Implemented | `project_bp` | `project_index.html`, `project_view.html` |
| Book | Implemented | `book_bp` | `book_index.html` |
| Journal | Implemented | `journal_bp` | `journal_index.html`, `journal_questions.html`, `journal_mood_settings.html` |
| Bookmark | Implemented | `bookmark_bp` | `bookmark_index.html`, `bookmark_read_later.html` |
| Fitness | Stubbed | `fitness_bp` | `fitness_index.html`, `fitness_log.html` |
| Triage | Stubbed | `triage_bp` | `triage_index.html` |
| Vacation | Implemented (read + create) | `vacation_bp` | `vacation_index.html` |
| Appointment | Stubbed | `appointment_bp` | `appointment_index.html` |
| Podcast | Implemented | `podcast_bp` | `podcast_subscription.html`, `podcast_list.html`, `podcast_feed.xml` |
| Chore | Stubbed (read-only) | `chore_bp` | `chore_index.html` |

### E2. Habit — Day-of-Week Bitmask

`habit.dayweek` is an INT where each bit represents a day:

| Day | Bit position | Value |
|-----|-------------|-------|
| Sunday | 0 | 1 |
| Monday | 1 | 2 |
| Tuesday | 2 | 4 |
| Wednesday | 3 | 8 |
| Thursday | 4 | 16 |
| Friday | 5 | 32 |
| Saturday | 6 | 64 |

Common values: all days = 127, weekdays = 62, weekends = 65

```python
day_of_week = (date.weekday() + 1) % 7   # Python weekday(): Mon=0 → we want Sun=0
day_bit = 1 << day_of_week
applies = bool(habit['dayweek'] & day_bit)
```

**Grid positions:** 5×5 row-major grid. `position = row * 5 + col`. Range 0–24.

### E3. Admin

- All admin routes require `PERM_ADMIN` read (and write for mutations).
- Admin nav: **Users | Icons | Log** — consistent across all three admin pages.
- **Users page:** Three sections: Pending Approval, Approved Users, Rejected. Pending shows approve/reject buttons. Approved shows permission bitmask badges + "Edit Permissions" toggle form + "Revoke" button. Rejected shows approve button only.
- **Icons page:** Add form (name, description, SVG code textarea with live preview) + grid of existing icons with inline edit/delete per icon.
- **Log page:** Table of last 200 `log` rows: id, user, resource, GET params, POST params, IP, time.
- SVG icons are stored as raw SVG text in `svg.svg`; rendered with `{{ icon.svg | safe }}`.

### E4. Todo

- Items grouped by `list_type` and `list_name`.
- Date navigation: `GET /index/<YYYY-MM-DD>` shows items due on that date; `GET /index/jump` redirects to today.
- `list_type` distinguishes major sections (e.g. work, personal, someday).
- Items can be moved between dates (`move/post`) and reordered within a list (`reorder/post`).
- Completed items show with strikethrough; `completed` column stores datetime of completion (not a boolean).

### E5. Habit

- Index shows today's habits in a 5×5 grid layout; each cell is a habit card.
- Toggle marks a habit as done/undone for a specific date.
- Heatmap shows historical completion data (GitHub-style grid).
- Settings page lists all habits; clicking one opens edit form for that habit.
- `vacation_mode` = habit is paused during vacation periods.
- **Position picker:** The settings form uses a 5×5 grid of buttons (not a number input) for selecting a grid position. Positions occupied by another habit with overlapping days are marked `conflicted` (disabled, red). Positions occupied on non-overlapping days are marked `occupied` (yellow, still selectable). The picker updates via AJAX on every dayweek checkbox change using `GET /positions/json`; the `exclude` param omits the habit being edited so its own position is not self-conflicting.

---

## Part F — Operations

### F1. Security Requirements

- **SQL injection:** All queries use parameterized statements via `db_manager`. Never interpolate user input into SQL.
- **XSS:** Jinja2 auto-escapes all template variables. `| safe` is allowed only for SVG content stored in the database (`icon.svg | safe`), which is admin-controlled input.
- **CSRF:** All state-changing actions are POST with form submission. Google OAuth handles its own state parameter.
- **Session fixation:** Flask's `session.clear()` on logout.
- **Authorization:** Every route verifies ownership (`username == session['username']`) before serving data. Admin routes additionally require `PERM_ADMIN`.
- **OAuth tokens:** `access_token`, `refresh_token` stored in `user` table. Never logged or emitted to templates.
- **Secrets:** `.env` is gitignored. Never commit tokens, passwords, or OAuth credentials.
- **Password storage:** No passwords — authentication is Google OAuth only.
- **File uploads:** Not currently supported. If added, validate MIME type and store outside web root.

### F2. Configuration & Environment

| Env var | Required | Purpose |
|---------|----------|---------|
| `FLASK_ENV` | Yes | `development` or `production` |
| `SECRET_KEY` | Yes | Flask session signing key — use a long random string |
| `MYSQL_HOST` | Yes | Database hostname |
| `MYSQL_PORT` | No | Default 3306 |
| `MYSQL_USER` | Yes | Database user |
| `MYSQL_PASSWORD` | Yes | Database password |
| `MYSQL_DB` | Yes | Database name |
| `GOOGLE_CLIENT_ID` | Yes | OAuth app client ID |
| `GOOGLE_CLIENT_SECRET` | Yes | OAuth app client secret |
| `GOOGLE_REDIRECT_URI` | Yes | Must match Google Cloud Console exactly (`https://jttbh.com/auth/oauth2callback` in prod) |
| `OAUTHLIB_INSECURE_TRANSPORT` | Dev only | Set to `1` to allow OAuth over HTTP in development |
| `SMTP_HOST` | Yes | Email server host |
| `SMTP_PORT` | Yes | Email server port |
| `SMTP_USER` | Yes | Email sender address |
| `SMTP_PASSWORD` | Yes | Email sender password |
| `SMTP_FROM` | Yes | From address in approval emails |
| `ADMIN_EMAIL` | Yes | Recipient for admin alerts |

### F3. Infrastructure

- **Server:** Linode Ubuntu, nginx + gunicorn
- **User:** `jttbh` (not root); deploy path: `/home/jttbh/JTTBH/`
- **Systemd:** `jttbh.service` runs gunicorn; managed with `systemctl start/stop/restart/status jttbh`
- **Nginx:** Config at `/etc/nginx/sites-available/jttbh`, symlinked to `sites-enabled/`; default site must be removed
- **File permissions:** `chmod 755 /home/jttbh` and `chmod -R 755 app/static` required for nginx to serve static files
- **Python env:** virtualenv at `/home/jttbh/JTTBH/venv/`
- **Logs:** `journalctl -u jttbh -n 50 --no-pager`
- **Deploy:** `git pull && pip install -r requirements.txt && systemctl restart jttbh`

### F4. Testing

- Framework: `pytest`
- Synthetic data: `test/synthetic.py` — lists of dicts, bypasses DB
- Integration tests use test-user IDs prefixed with `-` (e.g. `-58ec8c11-…`) so they can be identified and cleaned up
- Run: `pytest --cov=app --cov-report=html`
- Target: 80% coverage minimum
- Never mock the database — integration tests must hit a real DB (or use synthetic data designed to match the real schema exactly)

---

## Part G — Known Issues & Decisions Log

### G1. Resolved Schema Issues

All previously documented schema issues have been fixed in `schema.sql`:

| Issue | Table | Fix applied |
|-------|-------|-------------|
| FK referenced wrong table name | `book` | Now references `user` (singular) |
| `UNIQUE KEY` blocked insert-only | `book.bookID` | Changed to plain `KEY` |
| `created_by` was wrong type | `podcast` | Changed to `varchar(36)` |
| Missing UUID column | `vacation` | `vacationID varchar(36)` added |
| `NOT NULL` blocked soft-delete | `project.name` | Changed to `DEFAULT NULL` |
| Column name typo | `podcast_episode.episodeID` | Corrected spelling |

### G2. Design Decisions

- **Insert-only pattern:** Preserves full audit history; every state change is a new row. Deletions are soft (NULL sentinel). Exceptions (`user`, `svg`) are documented in §C2.
- **No ORM:** Direct SQL gives full control over query shape and avoids N+1 issues.
- **Google OAuth only:** Eliminates password management entirely; single sign-on for admin.
- **Flat template directory:** Keeps template lookup simple; feature prefixes prevent name collisions.
- **`bitand()` Jinja2 global:** Workaround for Jinja2 rejecting the `&` operator in `{% %}` blocks.
- **Admin `user_permission` is append-only:** Each permission change creates a new row, providing a full audit trail of who changed what and when.
