# JTTBH — Master Reference

**"Just Trying to be Helpful"** — personal productivity dashboard  
**Stack:** Python 3.10+ / Flask 3.0+ / MySQL 9.0+ / PyMySQL (no ORM)  
**Live:** https://jttbh.com | **Repo:** https://github.com/JasonRFrancis/JTTBH  
**Dev:** `python ./app/main.py` from project root  
**See also:** `SPECIFICATION.md` for feature details, routes, table schemas, and operations.

---

## Part A — Working With This Project

### A1. Workflow

- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions). Stop and re-plan if things go sideways.
- Use subagents to keep the main context window clean; offload research and parallel analysis.
- After ANY correction from the user: update `claude/LESSONS.md` with the pattern.
- Never mark a task complete without demonstrating it works (logs, tests, or browser test).
- When given a bug report: just fix it. Point at logs/errors, resolve them. Zero hand-holding required.
- **Before declaring template work complete:** verify every `{% block %}` name in the child template exists in `base.html`. Jinja2 silently discards non-matching blocks — CSS and JS will not load and no error is raised. Valid block names: `title`, `css`, `content`, `js`.

### A2. Task Management

1. Write plan to `claude/TODO.md` with checkable items.
2. Check in before starting implementation on anything non-trivial.
3. Mark items complete as you go.
4. Add results/lessons to `claude/LESSONS.md` when done.

### A3. Core Principles

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
| Insert-only data | User data tables use insert-only pattern (see §C2); exceptions: `user`, `svg`, `fitness_exercise`, `bookmark`, `bookmark_category`, `bookmark_category_item` |
| Progressive enhancement | Every page must work without CSS or JS enabled |
| Semantic HTML | `<article>`, `<section>`, `<nav>`, `<header>`, `<footer>` over `<div>` |
| Mobile-first | CSS written for mobile viewport first |

### B2. File & Naming Conventions

```
app/
  __init__.py          # app factory, Jinja2 globals, blueprint registration
  models/              # habit_model.py, todo_model.py …
  routes/              # one blueprint per feature: habit.py, todo.py …
  services/
    database.py        # db_manager singleton
    decorators.py      # login_required, permission_required_read/write, PERM_* constants
    timezone_utils.py  # user_today() → date in user's IANA timezone
  static/css/          # base.css + one per feature
  static/js/           # base.js + one per feature
  templates/           # flat — naming: [feature]_[page].html
migrations/            # YYYYMMDD_description.sql — must be idempotent
claude/                # scratch files, RESULTS.md, LESSONS.md, TODO.md
```

- Feature names are **singular**: `todo`, `habit`, `bookmark`, `chore`
- After the feature prefix, identifiers use camelCase: `todo_pushedForward`
- Templates, models, routes: **one folder deep only**

### B3. URL Structure

```
GET  /[username]/[area]/[view]/[params…]    → renders [area]_[view].html
POST /[username]/[area]/[action]/post/[id…] → mutates state, redirects (PRG)
```

Dates in URLs: ISO `YYYY-MM-DD`. POST action names: `create`, `update`, `delete`, `toggle`, `reorder`, `move`.

### B4. Route Inventory

| Blueprint | URL prefix | Key routes |
|-----------|-----------|------------|
| `auth_bp` | `/auth` | `GET /login`, `GET /oauth2callback`, `GET /logout` |
| `dashboard_bp` | `/<u>/dashboard` | `GET /index`, `GET /index/json` |
| `admin_bp` | `/<u>/admin` | `GET /dashboard`, `/users`, `/log`, `/icons`, `/errors` + POST mutations |
| `user_bp` | `/<u>` | `GET /settings`, `POST /settings/post` |
| `todo_bp` | `/<u>/todo` | `GET /index[/<date_str>]`, `GET /search`, `POST /create|toggle|update|delete|move|reorder/post` |
| `habit_bp` | `/<u>/habit` | `GET /index[/<date>]`, `/heatmap`, `/settings[/<id>]`, `GET /positions/json` · `POST /toggle|create|update|delete|reorder/post` |
| `project_bp` | `/<u>/project` | `GET /index`, `GET /view/<id>` · `POST /create|update|delete/post`, `/resource/create|delete/post`, `/send_to_todo/post/<id>` |
| `bookmark_bp` | `/<u>/bookmark` | `GET /index`, `/archive`, `/read-later`, `/category/<id>`, `/items/json` · full POST suite (create, update, archive, favorite, delete, bulk-delete, category CRUD + reorder) |
| `fitness_bp` | `/<u>/fitness` | `GET /index`, `/log`, `/settings` · `POST /program/*`, `/exercise/create/post`, `/log/set/post` (JSON), `/weight/post` (JSON) |
| `media_bp` | `/<u>/media` | `GET /index`, `/detail/<id>`, `/settings`, `/search/json` · `POST /create|update|delete|sync/post`, `/episode/seen/post/<id>`, `/steam/sync/post` |
| `journal_bp` | `/<u>/journal` | `GET /index[/<date>]`, `/questions`, `/mood/settings` · `POST /answer|mood|question/create/post` |
| `study_bp` | `/<u>/study` | `GET /index[/<date>]`, `/collections`, `/collection/<id>`, `/feed.xml` (public RSS) · `POST /collection|source /create|update|delete/post`, `/subscribe|unsubscribe|subscription/update/post`, `/source/complete/post/<id>` |
| `quote_bp` | `/<u>/quote` | `GET /index`, `/add` · `POST /create|update|delete/post` |
| `recipe_bp` | `/<u>/recipe` | `GET /index`, `/detail/<id>`, `/add`, `/edit/<id>` · `POST /extract/post` (JSON), `/create\|update\|delete/post`, `/image/add/post/<id>`, `/image/delete/post/<image_id>`, `/pdf/post` |
| `triage_bp` | `/<u>/triage` | `GET /index` (stubbed) |
| `vacation_bp` | `/<u>/vacation` | `GET /index` · `POST /create|delete/post` |
| `appointment_bp` | `/<u>/appointment` | `GET /index` (stubbed) |
| `chore_bp` | `/<u>/chore` | `GET /index` (stubbed) |
| `book_bp` | `/<u>/book` | `GET /index` · `POST /create|update|finish/post` (legacy) |

---

## Part C — Data Layer

### C1. Permission System

| Bit | Value | Constant | Feature |
|-----|-------|----------|---------|
| 0 | 1 | `PERM_ADMIN` | Admin |
| 1 | 2 | `PERM_PODCAST` | Podcast feed (blueprint removed; bit reserved) |
| 2 | 4 | `PERM_APPOINTMENT` | Scheduling |
| 3 | 8 | `PERM_DASHBOARD` | Dashboard |
| 4 | 16 | `PERM_TODO` | Todo |
| 5 | 32 | `PERM_HABIT` | Habit |
| 6 | 64 | `PERM_PROJECT` | Projects |
| 7 | 128 | `PERM_TRIAGE` | Triage |
| 8 | 256 | `PERM_BOOKMARK` | Bookmarks |
| 9 | 512 | `PERM_FITNESS` | Fitness |
| 10 | 1024 | `PERM_CHORE` | Chores |
| 11 | 2048 | `PERM_BOOK` | Media/Book tracker |
| 12 | 4096 | `PERM_JOURNAL` | Journal/mood |
| 13 | 8192 | `PERM_STUDY` | Study |
| 14 | 16384 | `PERM_QUOTE` | Quotes |
| 15 | 32768 | `PERM_RECIPE` | Recipe tracker |

**Default on approval:** `read = write = 32766` (bits 1–14; admin bit 0 and Recipe bit 15 excluded)

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

**In templates:** `has_perm(bit)` / `has_write_perm(bit)`

### C2. Database Patterns

#### Insert-only (default for user data)

```python
# Read current state
SELECT col FROM thing t
WHERE t.thingID = %s
  AND t.id = (SELECT MAX(t2.id) FROM thing t2 WHERE t2.thingID = t.thingID)
  AND t.name IS NOT NULL   -- NULL sentinel = soft-deleted

# Update: INSERT new row, same thingID
# Delete: INSERT row with sentinel column = NULL
```

Sentinel columns: `todo.title`, `habit.name`, `project.name`, `study_collection.name`, `study_source.title`, `recipe.title`

**Exceptions** (direct UPDATE/DELETE): `user`, `svg`, `fitness_exercise`, `bookmark`, `bookmark_category`, `bookmark_category_item`, `study_subscription`, `study_completion`, `recipe_image`

#### `db_manager` API

```python
from app.services.database import db_manager

db_manager.execute_query(sql, params)   # → list[dict]
db_manager.execute_one(sql, params)     # → dict | None
db_manager.execute_insert(sql, params)  # → int (lastrowid)
db_manager.execute_update(sql, params)  # → int (rowcount) — also for DELETE
```

All params must be tuples. Never interpolate values into SQL strings.

### C3. Schema Gotchas

**`project`** — has `next_step TEXT` (not `status`). Confirmed from production.

**`log`** — full column list: `id`, `userid`, `username`, `area`, `resource`, `presentation`, `parameters`, `history`, `get`, `post`, `ip`, `user_agent`, `created`. No `method`, `path`, `status_code`, or `ip_address`.

**`study_subscription`** — has many extended columns beyond the basics: `filter_author`, `filter_category`, `sort_order` ENUM(`'natural'`,`'newest'`,`'oldest'`), `limit_count`, `start_offset`, `repeat`, `use_personal_schedule`, `name`. No `UNIQUE(userID, collectionID)` constraint — only `UNIQUE(subscriptionID)`.

**`fitness_exercise.type`** — ENUM in production is `('machine','hand_weight','bodyweight','cardio','video')`, NOT `('strength','cardio','done')` as described in some notes. Schema.sql matches production.

**`habit_entry.change_id`** — client-generated UUID per toggle; UNIQUE prevents duplicate processing on retry. Model must pre-check for duplicate UUIDs.

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
            SELECT t.thingID, t.name
            FROM thing t
            WHERE t.userID = %s
              AND t.id = (SELECT MAX(t2.id) FROM thing t2 WHERE t2.thingID = t.thingID)
              AND t.name IS NOT NULL
            ORDER BY t.position
        """, (user_id,))
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
    return render_template('thing_index.html', username=username, area='thing')
```

#### Template (`app/templates/thing_index.html`)
```html
{% extends "base.html" %}
{% block title %}Things{% endblock %}
{% block css %}<link rel="stylesheet" href="{{ url_for('static', filename='css/thing.css') }}">{% endblock %}
{% block content %}
<header><h1>Things</h1></header>
{% endblock %}
{% block js %}<script src="{{ url_for('static', filename='js/thing.js') }}" defer></script>{% endblock %}
```

### D2. Jinja2 Globals & Filters

| Name | Usage |
|------|-------|
| `datetime`, `date`, `timedelta` | Python datetime classes |
| `has_perm(bit)` | True if `session.perm_read & bit` |
| `has_write_perm(bit)` | True if `session.perm_write & bit` |
| `bitand(a, b)` | `int(a or 0) & b` — use instead of `&` in `{% %}` blocks |

**Filters:** `markdown`, `format_day_short` (→ "Mon 27"), `format_day` (→ "Mon Sep 27"), `format_date_long`, `dayweek_label`

**⚠ Never use `&` in `{% %}` blocks** — raises `TemplateSyntaxError`. Use `bitand(a, b)`.

### D3. Session Keys & Auth

Session keys set on login: `user_id`, `username`, `perm_read`, `perm_write`, `timezone`  
`session.permanent = True`; lifetime = 7 days (`PERMANENT_SESSION_LIFETIME = 604800`)  
`timezone` from `user_preference` key `'timezone'`; defaults to `'UTC'`

### D4. Error Handling

- User-facing: `flash(message, category)` — categories: `error`, `warning`, `message`, `success`
- JSON endpoints: `{"status": "error", "message": "...", "code": "...", "details": {}}`
- All requests logged to `log` table via `@app.after_request` hook in `app/__init__.py`
- Never let logging failures break the response
