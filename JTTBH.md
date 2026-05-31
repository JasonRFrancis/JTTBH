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
- **Before declaring template work complete:** verify that every `{% block %}` name in the child template exists in `base.html`. Jinja2 silently discards blocks whose names don't match — CSS and JS will not load and no error will be raised. The only valid block names are: `title`, `css`, `content`, `js`.

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
    timezone_utils.py  # user_today() → date in user's IANA timezone; today_for_tz(tz_name)
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
| `admin_bp` | `/<u>/admin` | `GET /dashboard`, `GET /users`, `GET /log`, `GET /icons`, `GET /errors` |
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
| `fitness_bp` | `/<u>/fitness` | `GET /index`, `GET /log`, `GET /settings`, `GET /settings/<fitness_id>` |
| | | `POST /program/create/post`, `/program/activate/post/<id>`, `/program/delete/post/<id>` |
| | | `POST /program/exercise/create/post`, `/program/exercise/update/post/<program_id>`, `/program/exercise/delete/post/<program_id>` |
| | | `POST /exercise/create/post` (add new exercise to catalog) |
| | | `POST /log/set/post` (JSON), `/log/set/delete/post/<log_set_id>` (JSON), `/log/end/post/<log_id>` |
| | | `POST /weight/post` (JSON) |
| `triage_bp` | `/<u>/triage` | `GET /index` |
| `vacation_bp` | `/<u>/vacation` | `GET /index`, `POST /create/post`, `POST /delete/post/<vacation_id>` |
| `appointment_bp` | `/<u>/appointment` | `GET /index` |
| `podcast_bp` | `/<u>/podcast` | `GET /subscription`, `GET /list`, `GET /feed/<feed_id>.xml` |
| | | `POST /subscription/create/post`, `POST /list/create/post` |
| `chore_bp` | `/<u>/chore` | `GET /index` |
| `book_bp` | `/<u>/book` | `GET /index` |
| | | `POST /create/post`, `POST /update/post/<book_id>`, `POST /finish/post/<book_id>` |
| `media_bp` | `/<u>/media` | `GET /index`, `GET /detail/<media_id>`, `GET /settings`, `GET /search/json` |
| | | `POST /create/post`, `POST /update/post/<media_id>`, `POST /delete/post/<media_id>` |
| | | `POST /sync/post/<media_id>` — re-sync TMDB/RSS metadata for one item |
| | | `POST /episode/seen/post/<episode_id>` — toggle episode seen/unseen |
| | | `POST /steam/sync/post` — import Steam library as videogame items |
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
| `fitness_exercise` | Direct `UPDATE` | Reference/catalog data (not user data); shared across all users |

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
`id`, `habitID`, `entry` (date), `completed` (1 or NULL), `vacation`, `change_id` (varchar(36), UNIQUE — client-generated UUID per toggle for idempotency), `created`, `created_by`

**`todo`**  
`id`, `todoID`, `userID`, `title` (NULL = soft-deleted), `content` (TEXT), `due` (date), `list_type`, `list_name`, `position`, `completed` (datetime or NULL), `added` (date), `created`, `created_by`

**`project`**  
`id`, `projectID`, `userID`, `name` (NULL = soft-deleted), `description`, `status`, `position`, `created`, `created_by`

**`book`**  
`id`, `bookID`, `userID`, `title` (NULL = soft-deleted), `author`, `status` ENUM('reading','finished','abandoned'), `started` (date), `finished` (date), `notes` (TEXT), `created`, `created_by`

**`media`** — insert-only (title NULL = soft-deleted); uses `PERM_BOOK` (2048)  
`id`, `mediaID` (UUID), `userID`, `title` VARCHAR(500, NULL = soft-deleted), `kind` ENUM('book','movie','show','podcast','videogame','boardgame'), `creator` VARCHAR(255), `status` ENUM('want','in_progress','done','dismiss'), `rating` TINYINT (1–5), `review` TEXT, `external_id` VARCHAR(500) (TMDB int ID, RSS feed URL, or `steam:<appid>`), `cover_url` VARCHAR(500), `streaming` VARCHAR(255), `next_date` DATE (next episode/release date), `started` DATE, `finished` DATE, `created`, `created_by`

**`media_episode`** — direct UPDATE for `seen` (not insert-only)  
`id`, `episodeID` (UUID, UNIQUE KEY), `mediaID` (FK), `title` VARCHAR(500), `season` SMALLINT (NULL for podcasts), `episode_number` SMALLINT, `air_date` DATE, `seen` TINYINT DEFAULT 0, `description` TEXT, `external_id` VARCHAR(500) (TMDB episode ID or RSS guid), `created`, `created_by`

**`user_preference`** — key-value store; current row = highest `id` per `(userID, preference)`  
`id`, `userID`, `preference` (key string), `value` VARCHAR(500), `created`, `created_by`  
Known keys: `timezone`, `steam_api_key`, `steam_id`, `todo_list1_name` … `todo_list4_name`  
⚠ `value` was VARCHAR(100) before migration `20260529_user_preference_value_size.sql`.

**`fitness_bodyWeight`**  
`id`, `weightID` (UUID), `userID`, `weight` DECIMAL(5,1), `unit` ENUM('lbs','kg') DEFAULT 'lbs', `recorded` (date), `created`, `created_by`  
One entry per date per user; latest `id` wins for same `(userID, recorded)`.

**`fitness_program`**  
`id`, `programID`, `fitnessID` (FK), `day_of_week` (0=Sun…6=Sat), `exerciseID` (FK, NULL = soft-deleted), `order_index`, `recommended_sets`, `recommended_reps`, `recommended_weight`, `notes` (setup/adjustment notes), `location` ENUM('gym','home','other'), `recommended_duration` INT (minutes, cardio), `recommended_speed` DECIMAL(4,2) (mph, cardio), `recommended_incline` DECIMAL(4,1) (degrees, cardio), `created`

**`fitness_logSet`**  
`id`, `logSetID` (UUID), `logID` (FK), `exerciseID` (FK, NULL = soft-deleted), `set_number`, `actual_weight` DECIMAL(6,1), `actual_reps` INT, `notes`, `duration_minutes` INT (cardio), `speed` DECIMAL(4,2) (cardio), `incline` DECIMAL(4,1) (cardio), `created`, `created_by`

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
- Session keys set on login: `user_id`, `username`, `perm_read`, `perm_write`, `timezone`
- `session.permanent = True` is set at login; `PERMANENT_SESSION_LIFETIME = 604800` (7 days) in both `config/dev.py` and `config/prod.py`
- `timezone` is loaded from `user_preference` table (key `'timezone'`); defaults to `'UTC'` if absent; refreshed immediately in session when user saves timezone preference
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
| Admin (dashboard) | Implemented | `admin_bp` | `admin_dashboard.html` |
| Admin (users) | Implemented | `admin_bp` | `admin_users.html` |
| Admin (icons) | Implemented | `admin_bp` | `admin_icons.html` |
| Admin (log) | Implemented | `admin_bp` | `admin_log.html` |
| Admin (errors) | Implemented | `admin_bp` | `admin_errors.html` |
| User settings | Implemented | `user_bp` | `user_settings.html` |
| Project | Implemented | `project_bp` | `project_index.html`, `project_view.html` |
| Media Tracker | Implemented | `media_bp` | `media_index.html`, `media_detail.html`, `media_settings.html` |
| Book (legacy) | Implemented | `book_bp` | `book_index.html` |
| Journal | Implemented | `journal_bp` | `journal_index.html`, `journal_questions.html`, `journal_mood_settings.html` |
| Bookmark | Implemented | `bookmark_bp` | `bookmark_index.html`, `bookmark_read_later.html` |
| Fitness | Implemented | `fitness_bp` | `fitness_index.html`, `fitness_log.html`, `fitness_settings.html` |
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
- Admin nav: **Dashboard | Users | Icons | Log | Errors** — consistent across all five admin pages.
- Footer "Admin" link points to `admin.dashboard`.
- **Dashboard page** (`GET /dashboard`):
  - Stat cards: total users (+ pending count), requests today / last 7 days / all-time
  - Server health: uptime, load average (1/5/15 min), memory %, disk % — read from `/proc/` on Linux; shows "Linux only" message on macOS dev
  - 30-day request volume bar chart — vanilla JS Canvas, data embedded as JSON in `data-labels`/`data-values` attributes
  - Top 15 pages table (last 30 days, static assets excluded)
  - Content counts: media by kind, todos, habits
- **Users page** (`GET /users`): Three sections: Pending Approval, Approved Users, Rejected. Pending shows approve/reject buttons. Approved shows permission bitmask badges + "Edit Permissions" toggle form + "Revoke" button. Rejected shows approve button only.
- **Icons page** (`GET /icons`): Add form (name, description, SVG code textarea with live preview) + grid of existing icons with inline edit/delete per icon.
- **Log page** (`GET /log`): Up to 500 `log` rows with filter controls (resource substring, username, date range). Below the table: journalctl full output (last 150 lines) when available. Filter state shown in URL query params; "Clear" link appears when any filter is active.
- **Errors page** (`GET /errors`): `journalctl -u jttbh -p err -n 500 --no-pager` output — priority `err` and above (error, critical, alert, emergency). Displayed in a dark scrollable `<pre>` with a red left border. Shows an explanatory message when journalctl is unavailable (macOS dev).
- SVG icons are stored as raw SVG text in `svg.svg`; rendered with `{{ icon.svg | safe }}`.

### E4. Todo

- Items grouped by `list_type` and `list_name`.
- Date navigation: `GET /index/<YYYY-MM-DD>` shows items due on that date; `GET /index/jump` redirects to today.
- `list_type` distinguishes major sections (e.g. work, personal, someday).
- Items can be moved between dates (`move/post`) and reordered within a list (`reorder/post`).
- Completed items show with strikethrough; `completed` column stores datetime of completion (not a boolean).

### E5. Habit

- Index shows 28 days of habit grids; each day shows today's applicable habits in a 5×5 grid.
- Toggle marks a habit as done/undone for a specific date.
- Heatmap shows historical completion data (GitHub-style grid).
- Settings page lists all habits; clicking one opens edit form for that habit.
- `vacation_mode` = habit is paused during vacation periods.
- **Shared positions:** Multiple habits can occupy the same grid position if their `dayweek` bitmasks don't overlap. `get_grid_for_date` picks the applying habit for each position on a given day. Habits that don't apply on a day render as empty cells — they are not shown as inactive.
- **Position picker:** The settings form uses a 5×5 grid of buttons (not a number input) for selecting a grid position. Positions occupied by another habit with overlapping days are marked `conflicted` (disabled, red). Positions occupied on non-overlapping days are marked `occupied` (yellow, still selectable). The picker updates via AJAX on every dayweek checkbox change using `GET /positions/json`; the `exclude` param omits the habit being edited so its own position is not self-conflicting. **Creating a habit requires an explicit position selection** — the hidden `position` field starts empty and the server rejects empty submissions with a flash error.
- **Reorder (Settings):** The "Grid Layout" 5×5 drag interface has been replaced with a flat position list. Each row shows position badge, color, name, day schedule, and a **Swap** button. Click Swap on two habits to exchange their position numbers; click Save Positions to batch-POST to `POST /reorder/post` (page reloads after 600 ms).
- **Toggle AJAX:** Habit cell toggle uses optimistic UI — the checkbox state updates immediately, then a fire-and-forget POST is sent with `X-Requested-With: XMLHttpRequest`, `Content-Type: application/x-www-form-urlencoded`, and `body: change_id=<uuid>`. A 10-second polling loop (`GET /habit/index/json`) reconciles server truth with the DOM. Cells with an in-flight POST are skipped by the reconciler until their `change_id` appears in the poll response, at which point the pending flag is cleared. `change_id` is a client-generated `crypto.randomUUID()` stored in `habit_entry.change_id` (UNIQUE); the model pre-checks for duplicate UUIDs to handle retries without double-toggling.
- **Dashboard widget:** Today's habit grid (`<habit-grid>`) is embedded in the dashboard using the same markup and JS as the index page. `habit.css` and `habit.js` are loaded on the dashboard when the user has `PERM_HABIT`. The `habit-grid` and `habit-cell` CSS rules are top-level (not scoped to `main.habit`) so they render inside the dashboard's `<section class="habit">` widget.
- **CSS scoping:** `main.habit, section.habit { … }` — the habit stylesheet applies to both the habit feature's main page and the dashboard widget section.

### E6. Fitness

**Three exercise types** — stored in `fitness_exercise.type` ENUM(`'strength'`, `'cardio'`, `'done'`):

| Type | Tracks | Log form |
|------|--------|----------|
| `strength` | weight (lbs), reps, machine adjustment (notes) | Inline entry row: lbs × reps + adj field |
| `cardio` | duration (min), speed (mph), incline (°), adjustment (notes) | Inline entry row: 4 inputs |
| `done` | completion only (no numeric data) | Direct POST on button press — no form row |

**Programs:**
- A user can have multiple fitness programs (`fitness` table); only one is `active` at a time.
- Each program has a weekly schedule: exercises assigned per `day_of_week` (0=Sun … 6=Sat) in `fitness_program`.
- `fitness_program.notes` = machine setup/adjustment note (pre-populated into the log entry row).
- `fitness_program` is insert-only (update = select + insert new row, same `programID`).

**Index page (`fitness_index.html`):**
- Shows today's exercises for the active program and today's location.
- Each exercise article has a `<template class="prefill-data">` with last session's values; JS reads these for pre-filling entry rows.
- Strength/cardio: "+ Set" / "+ Log" button clones a `<template>` row; confirm (✓) POSTs to `POST /log/set/post` (JSON), cancel (×) removes the row.
- Done: "✓ Mark Done" button directly POSTs to `POST /log/set/post` (JSON); no form row shown.
- Logged sets are shown read-only with a delete (×) button per row.
- Body weight form at top of page; saves to `fitness_bodyWeight` via `POST /weight/post` (JSON).

**Prefill behavior (strength):** Pre-fills weight/reps/notes from previous session's first set for that exercise; falls back to program's recommended values. After confirming a set, the prefill template is updated with just-logged values so the next set inherits them.

**Set logging routes (all return JSON `{"status": "ok", "logSetID": "..."}`):**
- `POST /log/set/post` — creates a `fitness_logSet` row; also creates a `fitness_log` row for today if none exists.
- `POST /log/set/delete/post/<log_set_id>` — deletes `fitness_logSet` row.
- `POST /log/end/post/<log_id>` — sets `fitness_log.end_time = NOW()`.

**Settings page (`fitness_settings.html`):**
- Program list with activate/delete; "+ New Program" form.
- Day-tab schedule editor: 7 tabs (Sun–Sat), each showing exercises for that day with edit (inline `<details>`) and remove buttons.
- Edit form pre-fills location, notes, sets/reps/weight (strength) or duration/speed/incline (cardio), video URL.
- "+ Add exercise" form per day; exercise `<select>` uses `data-type` to show/hide strength vs cardio fields via JS.
- Exercise catalog section at bottom: "+ New Exercise" form (name, type select, muscle group, equipment select, description, video URL).

**`fitness_exercise` table** (direct UPDATE, not insert-only — reference/catalog data):
`exerciseID` (UUID), `name`, `type` ENUM(`'strength'`,`'cardio'`,`'done'`) DEFAULT `'strength'`, `muscle_group`, `equipment_type` ENUM(`'weight_machine'`,`'hand_weight'`,`'bodyweight'`,`'cable'`,`'other'`), `description`, `video_url`, `created`, `created_by`

**`fitness` table** (user's fitness profile):
`id`, `fitnessID` (UUID), `userID`, `name`, `description`, `active` TINYINT, `created`, `created_by`

**`fitness_log` table** (one row per workout session):
`id`, `logID` (UUID), `fitnessID` (FK), `userID`, `log_date` (date), `location` ENUM(`'gym'`,`'home'`,`'other'`), `start_time` (datetime), `end_time` (datetime or NULL), `created`, `created_by`

### E7. Media Tracker

Tracks media consumption across six kinds: **show**, **movie**, **podcast**, **book**, **videogame**, **boardgame**. Uses `PERM_BOOK` (2048). Blueprint: `media_bp` at `/<username>/media`.

**Kinds and statuses:**

| Kind | Label | External data source |
|------|-------|----------------------|
| `show` | Shows | TMDB (`/3/search/tv`, `/3/tv/<id>`, `/3/tv/<id>/season/<n>`) |
| `movie` | Movies | TMDB (`/3/search/movie`, `/3/movie/<id>`) |
| `podcast` | Podcasts | RSS feed URL (stored as `external_id`) |
| `book` | Books | Manual entry |
| `videogame` | Video Games | Steam API or manual entry |
| `boardgame` | Board Games | Manual entry |

Statuses: `want`, `in_progress`, `done`, `dismiss`

**Index page** — groups by kind (KIND_ORDER: show → movie → podcast → book → videogame → boardgame), then by status within each kind. Add form has TMDB autocomplete for show/movie (debounced, fires after 400 ms), hidden for other kinds. Podcast title/creator/cover auto-populated from RSS feed on create.

**Detail page** — cover image, metadata (creator, status, rating 1–5, review, streaming, next release date). Edit form. Episode list for shows (grouped by season, each with a seen/unseen toggle) and podcasts (flat list).

**Settings page** — Steam library sync form: `steam_api_key` and `steam_id` (17-digit), saved to `user_preference`. Submit imports the full Steam library: games with `playtime_forever > 0` → `in_progress`; unplayed → `want`. Skips games already present (matched by `external_id = 'steam:<appid>'`). Reports imported / already present / failed counts; first error text included in flash if any failures.

**TMDB integration** (`app/services/tmdb.py`):
- `TMDB_API_KEY` from `app.config['TMDB_API_KEY']` (env var)
- `search(query, kind)` — typeahead suggestions
- `show_details(tmdb_id)` → streaming, next_date, cover_url, season count
- `show_season(tmdb_id, season)` → episode list
- `movie_details(tmdb_id)` → cover_url, next_date (sequel release)

**Steam integration** (`app/services/steam.py`):
- `get_owned_games(api_key, steam_id)` → list of `{appid, name, playtime_forever, cover_url}`
- Cover URL: `https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/header.jpg`
- Credentials stored in `user_preference` (`steam_api_key`, `steam_id`); `value` column is VARCHAR(500)

**Model** (`app/models/media_model.py`) — module-level functions (not a class):
- `get_all(user_id)`, `get_one(user_id, media_id)`, `create(...)`, `update(user_id, media, **overrides)`, `soft_delete(user_id, media_id)`
- `get_episodes(media_id)`, `upsert_episode(...)` (preserves `seen` on update via external_id lookup), `set_seen(episode_id, seen)`

**Podcast field note:** The existing `podcast_bp` generates RSS *production* feeds (audio file collections). The media tracker's podcast support is *consumer-side* — subscribing to external RSS feeds to track episodes. These are entirely separate features.

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
| `TMDB_API_KEY` | Yes (for media) | TMDB API key for show/movie search and metadata sync |

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
