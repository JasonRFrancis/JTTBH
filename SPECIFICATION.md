# SPECIFICATION.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Table of Contents

1. [Claude Instructions](#1-claude-instructions)
2. [Essential Commands](#2-essential-commands)
   1. [Development](#21-development)
   2. [Production Deployment](#22-production-deployment)
   3. [Database Management](#23-database-management)
3. [Project Overview](#3-project-overview)
4. [Current Site Features](#4-current-site-features)
   1. [Dashboard](#41-dashboard)
   2. [User Preferences](#42-user-preferences)
   3. [Habit Tracker](#43-habit-tracker)
   4. [Todo List](#44-todo-list)
   5. [Admin](#45-admin)
5. [Future Features](#5-future-features)
   1. [Show Tracker](#51-show-tracker)
   2. [Movie Tracker](#52-movie-tracker)
   3. [Project List](#53-project-list)
   4. [Bookmarks](#54-bookmarks)
   5. [Fitness Program](#55-fitness-program)
   6. [Triage](#56-triage)
   7. [Vacation Mode](#57-vacation-mode)
   8. [Appointments](#58-appointments)
   9. [Podcast Feed](#59-podcast-feed)
   10. [Household Chores](#510-household-chores)
   11. [Book Tracker](#511-book-tracker)
   12. [Daily Questions](#512-daily-questions)
   13. [Mood Tracker](#513-mood-tracker)
6. [Site Details](#6-site-details)
   1. [Habit Tracker Details](#61-habit-tracker-details)
   2. [Todo List Details](#62-todo-list-details)
7. [Architecture Overview](#7-architecture-overview)
   1. [Core Architectural Principles](#71-core-architectural-principles)
   2. [Naming Conventions](#72-naming-conventions)
   3. [Test-Driven Development](#73-test-driven-development)
   4. [Authentication Flow](#74-authentication-flow)
   5. [Database Architecture](#75-database-architecture)
   6. [Permission System](#76-permission-system)
8. [Configuration Management](#8-configuration-management)
   1. [Environment Structure](#81-environment-structure)
   2. [Database Configuration](#82-database-configuration)
9. [Technology Stack](#9-technology-stack)
   1. [Required Dependencies](#91-required-dependencies)
   2. [Not Allowed](#92-not-allowed)
10. [Error Handling Strategy](#10-error-handling-strategy)
    1. [User-Facing Errors (HTML)](#101-user-facing-errors-html)
    2. [API Errors (JSON)](#102-api-errors-json)
    3. [Server Errors](#103-server-errors)
11. [Performance Requirements](#11-performance-requirements)
    1. [Page Load Times](#111-page-load-times)
    2. [Database Optimization](#112-database-optimization)
    3. [Caching Strategy](#113-caching-strategy)
12. [Key Patterns](#12-key-patterns)
    1. [Template Pattern](#121-template-pattern)
    2. [Model Pattern](#122-model-pattern)
    3. [Route Pattern](#123-route-pattern)
    4. [REST Form Implementation](#124-rest-form-implementation)
    5. [Template Organization](#125-template-organization)
13. [Example Data Structures](#13-example-data-structures)
14. [Critical Implementation Details](#14-critical-implementation-details)
    1. [User Approval System](#141-user-approval-system)
    2. [Google API Integration](#142-google-api-integration)
    3. [Email Notifications](#143-email-notifications)
    4. [Key Integrations](#144-key-integrations)
15. [Database Migrations](#15-database-migrations)
    1. [Initial Setup](#151-initial-setup)
    2. [Schema Standards](#152-schema-standards)
    3. [Schema Updates](#153-schema-updates)
    4. [Migration Execution](#154-migration-execution)
16. [Testing Strategy](#16-testing-strategy)
    1. [Unit Tests](#161-unit-tests)
    2. [Integration Tests](#162-integration-tests)
    3. [Running Tests](#163-running-tests)
    4. [Test Data](#164-test-data)
17. [Claude Debugging](#17-claude-debugging)
18. [Development Workflow](#18-development-workflow)
19. [Production Deployment Checklist](#19-production-deployment-checklist)
    1. [Pre-Deployment](#191-pre-deployment)
    2. [Deployment Steps](#192-deployment-steps)
    3. [Post-Deployment](#193-post-deployment)
20. [File Structure Key Points](#20-file-structure-key-points)

## Outline

1. Claude Instructions
  1. Closely read these specifications
  2. Create any missing portions of the project's folder structure
  3. Implement the necessary files to conform to the specification
  4. Review `/schema.sql`
  5. Update `README.md` and `requirements.txt`
  6. In `/claude`, create `RESULTS.md` that outlines any challenges or ambiguities encountered during the implementation. Specify (with line numbers) places in the specification that caused implementation challenges. Recommend specific modifications to `SPECIFICATION.md` or `schema.sql`. In general, trust the philosophical decisions represented in this document.
2. Essential Commands
  1. Development
    ```bash
    # Run the development server
    python ./app/main.py

    # Switch between development and production environments
    ./config/switch_env.sh dev
    ./config/switch_env.sh prod
    ./config/switch_env.sh status
    ```
  2. Production Deployment
    ```bash
    # Initial production setup (run as jttbh user)
    ./config/setup_production.sh

    # Deploy updates
    ./config/deploy.sh

    # Quick server management
    ./config/quick_commands.sh status    # Check all services
    ./config/quick_commands.sh logs      # View recent logs
    ./config/quick_commands.sh restart   # Restart services
    ./config/quick_commands.sh backup    # Create manual backup
    ```
  3. Database Management
      ```bash
      # Connect to development database
      mysql -u jttbh -p jttbh

      # Connect to production database (via script)
      ./config/quick_commands.sh db

      # Import schema
      mysql -u jttbh -p jttbh < schema.sql
      ```
3. Project Overview
  1. `Just Trying to be Helpful` or `jttbh` is a site developed in Python Flask using a mysql database. Its primary purpose is to bring together the various streams of information and track the goals, habits, tasks, and projects that a person might want to manage in their life
  2. Hosting: This project is developed and tested locally and is deployed to jttbh.com, hosted on a `Linode` Ubuntu server
  3. Source Control: The source is hosted at `https://github.com/JasonRFrancis/JTTBH` and is deployed into production from that repository. The `main` branch is always production-ready
  4. Overall Organization: The project uses the following structure:
    ```
    jttbh/
    ├── venv/
    ├── app/
    │   ├── __init__.py
    │   ├── main.py
    │   ├── models/
    │   ├── routes/
    │   ├── services/
    │   ├── static/
    │   │   ├── css/
    │   │   ├── js/
    │   │   ├── fonts/
    │   │   └── images/
    │   └── templates/
    │       ├── admin.html
    │       ├── auth.html
    │       ├── base.html
    │       ├── index.html
    │       └── …
    ├── claude/
    ├── claude.md
    ├── config/
    │   ├── dev.py
    │   └── prod.py
    ├── requirements.txt
    ├── README.md
    ├── schema.sql
    ├── SPECIFICATION.md
    ├── test/
    ├── .gitignore
    └── .env
    ```
4. Current Site Features:
  1. Dashboard
    1. The primary view for the site is a dashboard which contains the current day's view of each of the site's relevant features
    2. The user should be able to see, at a glance, the most pressing tasks and indicate that they have been completed
    3. Each widget in the dashboard should contain a link to the more detailed view (contained in the `[area]` of the site)
  2. User Preferences
    1. Designated under `user` and tracked in the `user_preference` database table
    2. The user can set default and behavioral values for the various features of the site
    3. What preferences they can set will be determined by their permissions
  3. Habit Tracker
    1. Designated under the `habit` area using the `habit` database tables
    2. Allows the user to track daily habits
    3. Each day's habits can be presented in two different formats:
      1. As a 5x5 grid of icons (from the `svg` database table) that can be toggled on (completed) or off (incomplete)
      2. Or as a list of (max 25) icons with a label and an optional link to the activity in question
    4. The full view presents a calendar where each grid of icons represents a day, with the current day highlighted
      1. The calendar should include three weeks previous and one week in the future, rather than presenting the calendar month
      2. Habits can be marked as completed (or incomplete) regardless of where they appear on the calendar
    5. Each habit has an icon associated with it, a title, a brief description, and an optional action (stored as a URL, either through the `jttbh` site or linking to another site on the web)
    6. The user can designate what days of the week that habit is to be accomplished as well as its position in the grid
    7. The page calculates habit streaks (uninterrupted days that the habit has been marked as completed), as well as the proportion of the current day's habits that have been completed
    8. The site should also present a "heat map" view showing a grid of individual days where the intensity of the color indicates the proportion of habits completed that day (similar to the GitHub activity grid)
  4. Todo List
    1. Designated under the `todo` area using the `todo` database tables; patterned after teuxdeux.com
    2. Weekly view (top of page): Five lists covering the dates from yesterday until three days in the future. The current date (or the date designated in the URL) is in the second position
    3. Custom lists (bottom of page): Two groups:
      1. Planning: Four lists based on future periods: "Next Week", "This Month", "Next Month", and "Someday Soon"
      2. My Lists: Up to four lists that can be named in the site's preferences. Unnamed lists are not shown
    4. Each list element contains a text input, a checkbox, and options to delete or add details (contained in the `content` column in the table)
    5. List items can be reordered and moved to different lists
    6. The weekly list begins with 11 blank list items; custom lists begin with 5. Lists grow automatically as elements are filled in
    7. List item `title` and `content` text can be formatted using a basic flavor of Markdown
    8. Completed items: Persist on the list
    9. Daily rollover: The first time each day that the todo page is loaded, all incomplete items from the previous day are moved to the current day
      1. This only applies to the current-day list and the list from the previous day
      2. When a todo item is moved, a record is created in the `todo_pushedForward` table. That table should be checked on page load to determine whether the item should be moved
      3. If a todo item is to be moved, a new record is inserted into the `todo` table with the current day as the `due` date. The `created` and `created_by` fields should be updated. `added` represents the original due date for the item and is not updated
      4. This process is resilient to concurrency collisions; if a second request initiates a move, it will only result in duplicate (redundant) records in the table
    10. The current day can be adjusted using buttons that move forward or backward in time. A date picker allows the user to select the current day
    11. The user is provided a search option to search among todo items
    12. The dashboard version of the todo list contains the current day's items
  5. Admin
    1. Designated under the `admin` area; accessible only to users with `PERM_ADMIN` (bit 0, value 1)
    2. User Management: `GET /<username>/admin/users`
      1. Lists all users grouped by approval status (pending, approved, rejected)
      2. Pending users can be approved or rejected; approval grants default permissions (`read=8190, write=8190`)
      3. Approved users can have their permission bitvectors edited via a checkbox matrix
      4. Rejecting a user sets `approval_status='rejected'` and `active=0`
    3. Icon Management: `GET /<username>/admin/icons`
      1. Lists all SVG icons stored in the `svg` database table, rendered inline
      2. New icons can be added by pasting SVG markup into a textarea with a live preview
      3. Existing icons can be edited (name, description, SVG code) or deleted
      4. Unlike most tables, the `svg` table uses direct `UPDATE`/`DELETE` rather than the insert-only pattern, because `imageID` has a `UNIQUE KEY` constraint
      5. Routes:
        1. `POST /<username>/admin/icon/create/post` — insert new icon
        2. `POST /<username>/admin/icon/update/post/<image_id>` — update icon in place
        3. `POST /<username>/admin/icon/delete/post/<image_id>` — hard delete icon
    4. Access Log: `GET /<username>/admin/log`
      1. Shows the 200 most recent rows from the `log` table
      2. Columns displayed: id, username, resource (URL path), GET params, POST data, IP, timestamp
      3. The `log` table schema uses: `userid`, `username`, `resource`, `get`, `post`, `ip`, `user_agent`, `created`
5. Future Features
  1. Show Tracker
    1. Tracks the shows the user would like to watch
    2. Includes information (including links) to streaming services where those shows can be watched
    3. Uses API calls to an external service to track when shows are available or upcoming
  2. Movie Tracker
    1. Tracks movies the user has seen and would like to watch
    2. Thumbs-up or thumbs-down rating
    3. Includes the possibility for a short review
  3. Project List
    1. Designated under the `project` area using the `project` database tables
    2. A page that allows for tracking and brainstorming about longer-term projects
    3. Each project should contain a "Next step" indicating what the next action should be
    4. The project page should also allow for a "mood board" of resources and notes associated with the project
    5. It should be possible for the user to assign a project's "next step" to a list in the Todo resource
  4. Bookmarks
    1. Designated under the `bookmark` area; similar in functionality to pinboard.in
    2. Bookmarks can be added through form input or API
    3. By default, bookmarks are grouped by day and then by URL
    4. Bookmarks can be designated `read later`, added to a reference list, or tagged
    5. Each bookmark link in the list should also be accompanied by an option to open the link in a tab and remove it from the list
    6. A separate reference page lists any links added to the reference list. It should be possible to rearrange them, add a short description, and group them under headings
  5. Fitness Program
    1. The fitness program has a different set of exercises per day (weight machines at the gym and hand-weights at home)
    2. Some exercises should refer to an instructional video
    3. On any given day, the user should see the exercises with the recommended weight, sets, and reps, and be able to record progress
    4. Populate the list of exercises with the weight machines present in a typical gym
    5. Dashboard widget: Today's exercises
    6. Vacation mode: Option to skip workouts during vacation
  6. Triage
    1. Designated under `triage`; uses Google APIs to pull in the user's current gmail inbox and calendar items and allows the user to convert those to todo items
    2. API connections and permissions with Google will be set up separately; the Python code to connect to Google's APIs is needed
    3. The page lists the last three days of emails in the inbox, and allows conversion to todos. A button should populate a field with the subject line and content of the email for editing before adding as a todo to today's list
    4. The user should see a list of the next week's calendar events and push a button to convert them into todos
  7. Vacation Mode
    1. The user is presented with a simple calendar on which they can mark individual days when they will be on vacation
    2. This triggers vacation mode for those days
    3. If the days are marked retroactively, the page will perform any necessary recalculations
  8. Appointments
    1. Designated by `appointment`; based on the functionality of calendly.com
    2. Appointments can be blocked out (recurring or one-off) and then email invitations can be sent with a link to view the blocks and select an appointment
    3. The appointment selection page (used by someone accepting a proposed appointment) should not require authentication except for a key in the URL
    4. For now, compose the email and stub in sending it. Create the public booking page and the ability to create recurring blocks
  9. Podcast Feed
    1. Designated by `podcast`; a custom podcast XML feed subscribable by a podcast player
    2. The feed page needs to be accessible (no authentication required) by all popular podcast players
    3. Every user can create multiple feeds, kept in the `podcast` table and listed at `/[username]/podcast/subscription`
    4. A podcast is made up of subscriptions to "podcast lists" (groups of podcast episodes), stored in the `podcast_list` table and created at `/[username]/podcast/list`
    5. Rather than a recorded podcast, it is a collection of audio files from around the web that are linked to
  10. Household Chores
    1. Designated by `chore`; manages household chores with optional user assignment, scheduling, and completion reporting
    2. Users can be grouped into a household, stored in the `household` and `household_member` tables
    3. Chores (in the `chore` table) are organized into lists, associated with a household (stored in the `chore_list` table)
    4. Frequency is designated in the `chore_listItemDay` and `chore_listItemMonth` tables
    5. Chores become available to perform when they enter the `chore_assigned` table. They can be assigned by household members, or completed by the user (whether or not it was assigned)
  11. Book Tracker
    1. Designated by `book` and stored in the `book` table
    2. For now: a form to add a new book and a list of books with a way to indicate the user has finished reading it
  12. Daily Questions
    1. Part of the `journal` designation, stored in the `journal_answer` and `journal_question` tables
    2. Provides a prompt per day and allows the user to input a response
    3. Questions are provided in the `journal_question` table, indexed per day
    4. If the table has more than one question for the day, serve them all up with corresponding textarea boxes
  13. Mood Tracker
    1. Part of the `journal` designation, stored in the `journal_mood`, `journal_moodCategory`, and `journal_moodValue` tables
    2. Allows the user to capture their current mood across several categories
    3. If no categories exist, the user tracks their general mood. If no values exist, they track `happy` or `sad`
    4. Categories and values are set up in the user preferences area
    5. Values with a null categoryID are defaults that can be overridden for any category
6. Site Details: Detailed implementation instructions for the features of the site.
  1. Habit Tracker Details
    1. This feature is affected by vacation mode.
    2. Grid Position
      1. The 5x5 grid uses **row-major** encoding: `position = row * 5 + column`
      2. Examples:
         1. Top-left (0,0) = 0
         2. Top-right (0,4) = 4
         3. Bottom-left (4,0) = 20
         4. Bottom-right (4,4) = 24
      3. If a habit does not exist at a given position, that square in the grid is left blank and is not toggleable
      4. Multiple habits can occupy the same position in the grid, just not on the same day
      5. Position Picker (Settings page)
         1. Grid position is selected via a 5×5 grid of buttons, not a `<input type="number">`
         2. Positions occupied by another habit whose days overlap the currently selected days are marked **conflicted** (disabled, red tint)
         3. Positions occupied by another habit whose days do not overlap are marked **occupied** (yellow tint, still selectable)
         4. The picker refreshes conflict state via AJAX on every dayweek checkbox change
         5. Endpoint: `GET /<username>/habit/positions/json?dayweek=<int>&exclude=<habitID>`
            - `dayweek`: bitmask of the days being configured; a position is conflicted when `dayweek & other_habit.dayweek != 0`
            - `exclude`: habitID of the habit being edited, so its own position is not self-conflicting
            - Response: `{"positions": [{"position": 3, "habitID": "...", "name": "...", "dayweek": 62, "conflicted": true}, ...]}`
    3. Days of Week
      1. The `dayweek` field encodes which days a habit applies using a bitmask:
         ```
         | Day       | Bit | Value |
         |-----------|-----|-------|
         | Sunday    | 0   | 1     |
         | Monday    | 1   | 2     |
         | Tuesday   | 2   | 4     |
         | Wednesday | 3   | 8     |
         | Thursday  | 4   | 16    |
         | Friday    | 5   | 32    |
         | Saturday  | 6   | 64    |
         ```
      2. Common values:
         1. All days: 127
         2. Weekdays (Mon-Fri): 62
         3. Weekends (Sat-Sun): 65
      3. Check if habit applies today:
         ```python
         from datetime import datetime
         day_of_week = (datetime.today().weekday() + 1) % 7
         day_bit = 1 << day_of_week
         applies_today = bool(habit.dayweek & day_bit)
         ```
    4. Streaks
      1. Calculate uninterrupted completion streaks
      2. Calculate daily completion percentages
      3. Display GitHub-style heat map
      4. When vacation mode is enabled, streak calculations are paused for that period
      5. The user should be able to designate which habits are affected by vacation mode
    5. Vacation Mode
      1. Each habit has a `vacation_mode` TINYINT field:
        1. 1 = Paused during vacation
        2. 0 = Continues during vacation
      2. Streak calculation skips days that fall within vacation periods for habits with `vacation_mode=1`
    6. UI
      1. Settings page: Add vacation period
      2. Habit creation: Checkbox for "pause during vacation"
    7. Appropriate SVG icons can be selected from https://allsvgicons.com/. The SVG description should then be saved in the `svg` database table
    8. Prepopulate the list of habits with the following:
      ```
     | Habit                 | icon           | action |
     |-----------------------|----------------|--------|
     | Morning Prayer        | pray           |        |
     | Brain games           | knowledge      |        |
     | Morning Duolingo      | duolingo       |        |
     | Morning study         | scriptures     |        |
     | Record quote          | quote          |        |
     | Take pill             | pill           |        |
     | Plan day              | todo           |        |
     | Exercise              | exercise       |        |
     | Read book             | read           |        |
     | Family History        | genealogy      |        |
     | Record memories       | memory         |        |
     | Housework             | housework      |        |
     | Work on calling       | church         |        |
     | Record blood pressure | blood pressure |        |
     | Phone call            | phone          |        |
     | Inbox zero            | email          |        |
     | Check finances        | money          |        |
     | Evening Duolingo      | duolingo       |        |
     | Evening Prayer        | pray           |        |

      ```
  2. Todo List Details
    1. Custom List Configuration
      1. Route: `/[username]/settings`
      2. Permission: `PERM_DASHBOARD` (settings are cross-feature)
      3. Storage: `user_preference` table
      4. Preference keys:
         1. `todo_list1_name` (default: "List 1")
         2. `todo_list2_name` (default: "List 2")
         3. `todo_list3_name` (default: "List 3")
         4. `todo_list4_name` (default: "List 4")
    2. Markdown Syntax
      1. Supported (CommonMark subset):
         1. Header: `#text` or `##text`
         2. Bold: `**text**` or `__text__`
         3. Italic: `*text*` or `_text_`
         4. Links: `[text](url)`
         5. Lists: `- item` or `1. item`
         6. Code: `` `code` ``
      2. Not Supported:
         1. HTML tags
         2. Images
         3. Scripts
         4. Arbitrary attributes
    3. Markdown Rendering
      1. Display-view is rendered as the page is being drawn, content is updated with Javascript
      2. Server renders for initial page load (works without JS); client re-renders for live editing
      3. Libraries: python-markdown (server), markedjs (client)
      4. Rendering only in display-specific versions of todo items
      5. HTML tags are forbidden
    4. Search Scope
      1. Search across `title` field (primary)
      2. Search across `content` field (secondary)
7. Architecture Overview
  1. Core Architectural Principles
    1. REST
      1. Follows the principles outlined in Roy Fielding's dissertation
      2. Each resource is accessed through a unique URL
      3. URL Structure
        1. Pattern: `/[username]/[area]/[view or action]/[parameters]/[presentation]`
          1. `[username]`: Unique identifier for the user, selected by the user after access is approved
          2. `[area]`: Label for the site's specific feature (`todo`, `habit`, `triage`, `bookmark`, etc.)
          3. `[view or action]`: How the `[area]` is being presented. Corresponds with the template in `/templates/`. For example, `/[username]/todo/index` maps to `/templates/todo_index.html`. When processing a `POST`, the action describes how the state is being changed
          4. `[parameters]`: Arbitrary number of values delimited by `/`. Should be precise enough to describe the resource. Example: `/jason/todo/index/html/20250926-20250930/20250927/` displays todo lists from 26 Sep 2025 through 30 Sep 2025 with 27 Sep 2025 highlighted
          5. `[presentation]`: How data is transmitted to the user (`html`, `json`, or `pdf`). All `[view]` values should have templates for these three presentations
      4. URL Presentation Parameter
        1. If `[presentation]` is missing in a GET request, assume "html"
        2. `/jason/todo/index/html` - Correct
        3. `/jason/todo/index` - Assumes html
      5. Date Parameters
        1. Dates: Use ISO format with hyphens (`2025-09-27`)
        2. Date ranges: Use format `YYYY-MM-DD-YYYY-MM-DD`
        3. Always include separators (hyphens, underscores)
      6. HTTP Verbs and State
        1. Actions on resources are described by HTTP verbs (`GET`, `PUT`, `POST`, `DELETE`)
        2. Other than logging the user's behavior, `GET` never changes state
        3. Since HTTP only implements `GET` and `POST`, `PUT` and `DELETE` are implemented with `POST`
        4. Any verb that changes state redirects to `GET` once the action is complete and provides a status message (via Flask flash messages)
        5. With very few exceptions (the current date, for example), the state is entirely contained in the database, and the URL indexes into the database
        6. If the data model hasn't changed, each URL will produce a unique and consistent result
        7. If the data model has changed but a `[history]` value has been provided, the URL will always return a unique and consistent result
      7. Action Endpoints
        1. Action endpoints (POST/PUT/DELETE) do NOT follow the presentation pattern; `[action]` replaces `[view]` and `[presentation]` is "post"
        2. Pattern: `POST /[username]/[area]/[action]/post/[/[resourceID]]`
        3. Examples:
          1. `POST /jason/todo/create/post` - Create new todo
          2. `POST /jason/todo/toggle/post/<todoID>` - Toggle completion
          3. `POST /jason/todo/delete/post/<todoID>` - Soft delete
          4. `POST /jason/todo/update/post/<todoID>` - Update todo
          5. `POST /jason/todo/move/post/<todoID>|<listID>` - Move todo
        4. Response: Actions redirect to appropriate GET URL
          1. Success: Redirect to list view or detail view with flash message
          2. Error: Redirect back to form with error message
        5. Note: Browsers don't natively support PUT/DELETE, so we use POST with action names
    2. Access Control
      1. Users access resources by supplying URLs, and access control is managed using function decorators
      2. In nearly every instance (except the settings page), if a user has permission to access a resource, they are provided with the entire resource
      3. The URL should be sufficiently precise to describe a resource that requires elevated access
    3. Authentication Separated from Access Control
      1. Since every page is uniquely described by the URL and the `[username]` is a parameter, by default any user could see any other user's page by changing the URL
      2. Every access should be constrained by whether the user has appropriate permissions **and** the `[username]` field matches the current user's username (stored in session)
      3. This constraint is removed for admin users, who can access all other users' pages (including other admins)
    4. Model Architecture
      1. Uses direct raw SQL queries via `app/services/database.py` instead of ORM for performance and control
      2. Insert-Only Pattern
        1. Almost all tables deploy an insert-only, type-2 style architecture
        2. To update data: insert a new value
        3. To delete data: insert a null value
        4. Selecting the top (1) record ordered by `id DESC` will produce the current value
        5. To delete a record, insert a new row with the primary data field set to NULL:
          1. Todo: Set `title` to NULL
          2. Habit: Set `name` to NULL
          3. Project: Set `name` to NULL
      3. Insert-Only Concurrency
        1. Two simultaneous updates: Both INSERT succeed
        2. Latest state: Highest `id` value wins
        3. No data loss: Both updates preserved in history
        4. No locking needed: INSERT operations don't block
        5. Accept "last writer wins" behavior as documented. This doesn't happen much in practice, and the benefit outweighs the consequences
        6. Example:
          1. User A: Updates todo title at 10:00:00 (id=100)
          2. User B: Updates same todo at 10:00:01 (id=101)
          3. Current state: User B's update (id=101)
          4. History preserved: Both updates visible in audit
    5. Blueprint Organization: Routes organized in `/routes/` directory as Flask blueprints
    6. Model Layer: Entity models in `/models/` inherit from `BaseModel` and use raw SQL
    7. User Approval System: All new users require admin approval before accessing features
    8. Permission-Based Access: Granular feature permissions (todo, habit, triage, etc.)
    9. CSS and JS: All features have their own css and js files. Common `base.css` and `base.js` describe the minimum overall features
    10. Semantic HTML: No design frameworks. Prefer semantic HTML5 elements (`<article>`, `<section>`, `<nav>`, `<aside>`, `<header>`, `<footer>`) over generic `<div>` tags. Custom elements are allowed where they make sense (e.g., `<habit-grid>`, `<todo-list>`) but must have proper ARIA attributes and valid HTML5 (custom elements must have hyphen). Avoid excessive class attributes when semantic elements can convey meaning
      1. HTML markup should be elegant and descriptive. The HTML should not describe the appearance of the page, rather the structure of the data. Use the minimum markup required to structure the content and provide adequate accessibility information
      2. HTML and CSS: The goal is to first produce beautiful, semantic, functional vanilla and semantic HTML. That should be the first target. Subsequent instructions will address CSS and JavaScript layering
    11. Progressive enhancement: Every page must be legible and functional regardless of whether CSS or JavaScript are loaded. Every process must be accomplishable using HTML forms and HTTP verbs
    12. Mobile-first
    13. Vanilla JS
  2. Naming Conventions
    1. All primary features (todo, habit, book, etc.) use the singular (not plural) designation
    2. Any files, functions, or database tables that participate in a feature are prefixed with that designation and an underscore (e.g., `todo_index.py` or `habit_log.html`)
    3. After the underscore, further words use camelCase
    4. Templates, models, routes, etc. should be only one folder deep. The naming convention groups associated files
  3. Test-Driven Development
    1. Database is responsible for the state: Other than authentication and access control, all state is maintained in the database. Nothing in the view or controller changes unless the database changes
    2. Single-purpose functions: Functions perform a single transformation or a single action
    3. Idempotent functions: Only `/model` functions change state. Calling a function with the same parameters produces the same results every time
    4. Intermediary data representation: `/model` functions return a Python list of dictionaries. All control and view functions consume lists of dictionaries
    5. Synthetic data: With a single parameter change, the system should use synthetic data instead of database data. Synthetic data is described as lists of dictionaries in `/test/synthetic.py`. When testing, all other processes proceed normally, short-circuiting database calls
    6. pytest: The pytest framework runs unit tests. Results available in console, as JSON, or as a web page
    7. Unit tests: Every function should have associated unit tests with adequate range of values (including unexpected or illegal values). Tests are in `/test`. Visiting `/test` runs all tests; `/test/[feature]` tests individual features. All `/test` URLs are restricted to admin access
    8. Test coverage: `/test` pages should count functions per feature and indicate what additional tests are needed
  4. Authentication Flow
    1. OAuth Login Sequence
    1. Google OAuth 2.0 authentication via `/routes/auth.py`
    2. New users automatically set to `approval_status='pending'`
    3. Unapproved users redirected to `/pending-approval` page
    4. Admin approval via `/[username]/admin/users` interface
    5. Approved users get default feature permissions
    6. OAuth Token Management
      1. Store `access_token`, `refresh_token`, and `token_expires` in user table
      2. Before making Google API calls, check token expiration
      3. If expired, use `refresh_token` to obtain new `access_token`
      4. Update user table with new tokens
      5. If refresh fails, redirect to re-authentication
      6. For triage feature, tokens MUST include `gmail.readonly` and `calendar.readonly` scopes
    7. Google OAuth Setup (Production)
      1. Create OAuth 2.0 credentials:
        1. Go to: https://console.cloud.google.com/apis/credentials
        2. Create OAuth client ID (Web application)
        3. Authorized redirect URIs: `https://jttbh.com/auth/oauth2callback`
      2. Required scopes:
        1. `openid` (user authentication)
        2. `email` (user email)
        3. `profile` (user name)
        4. `https://www.googleapis.com/auth/gmail.readonly` (for triage)
        5. `https://www.googleapis.com/auth/calendar.readonly` (for triage)
      3. Environment variables:
        1. `GOOGLE_CLIENT_ID=<your_client_id>`
        2. `GOOGLE_CLIENT_SECRET=<your_client_secret>`
        3. `GOOGLE_REDIRECT_URI=https://jttbh.com/auth/oauth2callback`
      4. Implementation: See `routes/auth.py` lines 15-45 for production OAuth flow
  5. Database Architecture
    1. Primary Keys and Indexing
      1. Each table (except `user`) uses `id` as the primary key (auto-increment integer)
      2. Indexed as `id DESC` because the highest id grouped by the table's other keys is authoritative
    2. User Table Special Case
      1. The `user` table is an EXCEPTION to the insert-only pattern
      2. Uses `userID` (UUID) as sole PRIMARY KEY
      3. Updates are done via UPDATE statements, not INSERT
      4. This is necessary because `userID` must remain stable across sessions
      5. History of user changes is tracked in separate audit log
    3. UUIDs and Foreign Keys
      1. All other keys use UUID fields
      2. The `user` table contains a `username` (varchar(50)) and a `userid` (UUID) field
      3. The `userid` is the foreign key in all other tables
    4. Timestamps and Audit Fields
      1. Each table has `created` and `created_by` fields
      2. `created` contains a timestamp of when the record was inserted
      3. `created_by` includes the user identifier of who generated the state change
    5. Soft Deletes and Updates
      1. Inserts a new record instead of updating
      2. Inserts a null record instead of deleting
    6. Enum Table
      1. Numeric values that need labels appear in the `enum` table
      2. The `enum` table has a `namespace` field, then a list of `name`:`value` pairs
      3. `value` is numeric; `name` is varchar(max)
    7. Stages
      1. Most multi-stage processes can be described by a numeric `stage` field
      2. Stages are described in the `enum` table
      3. Higher numbers represent progress through the stages
      4. Stages of 100, 200, 300, etc. are preferable to 1, 2, 3 since they allow later adjustment and finer granularity
  6. Permission System
    1. Bitvector Storage
      1. Stored in `user_permission` table as two bitvector values: `read` and `write`
      2. Bit mapping reference is stored in the `user_permissionAccess` table
      3. `read` determines access to the resource; `write` determines whether values can be updated
      4. Users with `read` but not `write` see a read-only display (no form elements)
      5. Users with `read` but not `write` cannot submit a POST
      6. All users have permission to their own `settings` page
    2. Permission Bit Mapping
      ```
      | Bit | Value | Permission    | Description                         |
      |-----|-------|---------------|-------------------------------------|
      | 0   | 1     | Admin         | Admin functions                     |
      | 1   | 2     | Podcast       | Access podcast feed                 |
      | 2   | 4     | Appointment   | Scheduling                          |
      | 3   | 8     | Dashboard     | Dashboard view                      |
      | 4   | 16    | Todo          | Todo lists                          |
      | 5   | 32    | Habit         | Habit tracking                      |
      | 6   | 64    | Project       | Projects                            |
      | 7   | 128   | Triage        | Email/Calendar triage               |
      | 8   | 256   | Bookmark      | Bookmarks                           |
      | 9   | 512   | Fitness       | Fitness program                     |
      | 10  | 1024  | Chore         | Household chores (REQUIRED FEATURE) |
      | 11  | 2048  | Book          | Book tracker (REQUIRED FEATURE)     |
      | 12  | 4096  | Journal       | Daily questions & mood tracking     |
      ```
    3. Standard Permission Sets
      1. Admin: 4294967295 (All permissions)
      2. Default: 8190 (Bits 1-12: All features except admin)
        1. Calculation: 2 + 4 + 8 + 16 + 32 + 64 + 128 + 256 + 512 + 1024 + 2048 + 4096 = 8190
    4. Permission Examples by Feature
      1. Admin: `read` = can see permissions and other admin functions; `write` = can change permissions and other admin functions
      2. Podcast: `read` = can access a podcast feed; `write` = can create and edit a podcast feed
      3. Appointment: `read` = can see available appointments and sign up; `write` = can create appointment slots
      4. Dashboard: `read` = can access the dashboard; `write` = can rearrange and customize the dashboard
      5. Todo: `read` = can see todo list items; `write` = can check off, add, modify, and delete todo items
      6. Habit: `read` = can see habit items; `write` = can check off, create, modify, delete, and rearrange habit items
      7. Project: `read` = can see projects and items; `write` = can create, modify, and delete projects and items
      8. Triage: access requires `read` and `write` permissions
      9. Bookmark: `read` = can see bookmarks; `write` = can add, modify, and delete bookmarks
    5. Code Example
      ```python
      # Read access (GET routes)
      @todo_bp.route('/index/html')
      @permission_required_read(PERM_TODO)
      def index():
      # View only

      # Write access (POST routes)
      @todo_bp.route('/create', methods=['POST'])
      @permission_required_read(PERM_TODO)
      @permission_required_write(PERM_TODO)
      def create():
      # Can modify

      # Check permission
      if user.get_permissions() & TODO_ACCESS:
      # User has todo access
      ```
    6. Permission Requirements by Feature
      1. Dashboard: `PERM_DASHBOARD` (8)
      2. Todo: `PERM_TODO` (16)
      3. Habit: `PERM_HABIT` (32)
      4. Project: `PERM_PROJECT` (64)
      5. Fitness: `PERM_FITNESS` (512)
      6. Admin: `PERM_ADMIN` (1)
      7. Checked via decorators and template conditionals
      8. Admin can grant/revoke via `/[username]/admin/users` interface
8. Configuration Management
  1. Environment Structure
    1. Development: Uses `.env` file with MySQL localhost
    2. Production: Uses `.env.production` with production MySQL and email SMTP
    3. Config Classes: `config/` folder contains .py files with environment-aware configuration classes
  2. Database Configuration
    1. Development: MySQL on localhost (jttbh database)
    2. Production: MySQL on production server (jttbh database)
    3. Connection: Via `app/services/database.py` DatabaseManager class
9. Technology Stack
  1. Required Dependencies
    1. Python 3.10+
    2. Flask 3.0+
    3. MySQL 9.0+
    4. PyMySQL for database connection
    5. google-auth, google-auth-oauthlib, google-auth-httplib2 for OAuth
    6. google-api-python-client for Gmail/Calendar APIs
    7. pytest for testing
    8. gunicorn for production serving
    9. nginx for reverse proxy
  2. Not Allowed
    1. No ORM (use raw SQL only)
    2. No JavaScript frameworks (vanilla JS only)
    3. No CSS frameworks (custom CSS only)
10. Error Handling Strategy
  1. User-Facing Errors (HTML)
    1. Use Flask flash messages for form validation errors
    2. Display messages at the top of the page after redirect
    3. Provide clear, actionable error messages in plain language
    4. Categories: `error`, `warning`, `message`, `success`
  2. API Errors (JSON)
    1. Return consistent error format:
      ```json
      {
        "status": "error",
        "message": "Human-readable error message",
        "code": "ERROR_CODE",
        "details": {}
      }
      ```
    2. HTTP status codes: 400 (validation), 401 (unauthorized), 403 (forbidden), 404 (not found), 500 (server error)
  3. Server Errors
    1. Log all errors to database `log` table
    2. Show generic error page to user (don't expose internals)
    3. Email admin for critical errors (500-level)
    4. Include request context in logs (user, URL, parameters)
11. Performance Requirements
  1. Page Load Times
    1. Dashboard: < 500ms
    2. List views (todo, habit): < 300ms
    3. Form submissions: < 200ms
    4. API responses: < 100ms
  2. Database Optimization
    1. Use indexes on frequently queried fields (`userID`, date fields, `list_type`)
    2. Limit result sets to reasonable sizes (habits: 28 days, todos: current week + custom lists)
    3. Use connection pooling for database access
    4. Optimize insert-only queries with proper JOIN patterns
  3. Caching Strategy
    1. Cache user permissions in session (duration of session)
    2. Cache enum values in application memory (clear on app restart)
    3. No caching of dynamic data (todos, habits) - always fetch fresh from database
    4. Cache static assets (CSS, JS, images) with far-future expires headers
12. Key Patterns
  1. Template Pattern
    1. Separate templates for each `[presentation]` and for read-only vs full-featured versions of each resource
    2. Each HTML template is contained in a `<main>` tag with a class identifying the feature (e.g., `<main class="todo">`)
    3. The header is in a `<header>` tag
      1. User information, including a link to site preferences, is in a custom `<login>` tag in the header
    4. The footer is in a `<footer>` tag
      1. Site navigation should be in the footer
  2. Model Pattern
    ```python
    # All models inherit from BaseModel and use raw SQL
    class User(BaseModel):
        table_name = 'user'

        @classmethod
        def find_by_email(cls, email: str):
            query = "SELECT * FROM user WHERE email = %s"
            result = db_manager.execute_one(query, (email,))
            return cls(**result) if result else None
    ```
  3. Route Pattern
    ```python
    # Blueprint-based routes with decorators
    @main_bp.route('/dashboard')
    @login_required
    def dashboard():
        # Route logic using raw SQL via models
    ```
  4. REST Form Implementation:
    1. Since browsers only support GET and POST natively, all form mutations use POST:
      ```python
      # Create new resource
      @blueprint.route('/create/', methods=['POST'])
      def create():
          # Process form data
          # Insert to database
          flash('Resource created successfully', 'success')
          return redirect(url_for('resource.index'))

      # Update resource
      @blueprint.route('/update/', methods=['POST'])
      def update():
          # Process form data
          # Insert new record (insert-only pattern)
          flash('Resource updated successfully', 'success')
          return redirect(url_for('resource.view'))

      # Delete resource
      @blueprint.route('/delete/', methods=['POST'])
      def delete():
          # Insert null record (soft delete)
          flash('Resource deleted successfully', 'success')
          return redirect(url_for('resource.index'))
      ```
  5. Template Organization
    1. Flat structure in `/templates/` directory
    2. Naming convention: `[route]_[page].html` (e.g., `habit_form.html`)
    3. Base template with common layout and navigation
13. Example Data Structures
  1. Todo Item
    ```json
    {
      "todoID": "550e8400-e29b-41d4-a716-446655440000",
      "userID": "58ec8c11-e060-4367-93cf-91a6cc28db8c",
      "title": "Complete project proposal",
      "content": "Include budget section and timeline",
      "due": "2025-09-27",
      "list_type": "daily",
      "list_name": null,
      "position": 0,
      "completed": null,
      "added": "2025-09-25",
      "created": "2025-09-25T10:30:00",
      "created_by": "58ec8c11-e060-4367-93cf-91a6cc28db8c"
    }
    ```
  2. Habit
    ```json
    {
      "habitID": "660e8400-e29b-41d4-a716-446655440001",
      "userID": "58ec8c11-e060-4367-93cf-91a6cc28db8c",
      "name": "Morning Exercise",
      "description": "30 minutes of exercise",
      "action": "https://example.com/workout",
      "color": "#4CAF50",
      "icon": "exercise",
      "active": 1,
      "dayweek": 127,
      "position": 0,
      "created": "2025-09-01T08:00:00",
      "created_by": "58ec8c11-e060-4367-93cf-91a6cc28db8c"
    }
    ```
  3. Habit Entry
    ```json
    {
      "habitID": "660e8400-e29b-41d4-a716-446655440001",
      "entry": "2025-09-27",
      "completed": 1,
      "vacation": 0,
      "created": "2025-09-27T07:30:00",
      "created_by": "58ec8c11-e060-4367-93cf-91a6cc28db8c"
    }
    ```
  4. Project
    ```json
    {
      "projectID": "770e8400-e29b-41d4-a716-446655440002",
      "userID": "58ec8c11-e060-4367-93cf-91a6cc28db8c",
      "name": "Website Redesign",
      "description": "Modernize company website with new branding",
      "next_step": "Create wireframes for homepage",
      "position": 0,
      "created": "2025-09-15T14:00:00",
      "created_by": "58ec8c11-e060-4367-93cf-91a6cc28db8c"
    }
    ```
14. Critical Implementation Details
  1. User Approval System
    1. New users created with `approved=False`, `approval='pending'`
    2. Admin notifications created automatically for new signups
    3. Approval/rejection sends email notifications to users
    4. Default permissions granted upon approval
  2. Google API Integration
    1. OAuth scopes: `gmail.readonly`, `calendar.readonly` for triage features
    2. Credentials stored in `google_credentials` JSON field
    3. API access via `app/services/google_services.py` GoogleServicesManager
  3. Email Notifications
    1. Admin alerts for new user signups
    2. User notifications for approval/rejection
    3. Permission change notifications
    4. SMTP configuration via environment variables
  4. Key Integrations
    1. Google APIs: Gmail (readonly) and Calendar (readonly) for triage functionality
    2. Email System: SMTP notifications for user approval workflow
    3. TVDB API: Television database for media tracking features
15. Database Migrations
  1. Initial Setup
    1. Create database: `CREATE DATABASE jttbh CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`
    2. Run schema: `mysql -u jttbh -p jttbh < schema.sql`
    3. Verify tables: `SHOW TABLES;`
  2. Schema Standards
    1. String default values MUST use single quotes, not backticks
    2. Prefer ENUM for status fields with fixed values
    3. All schema changes must be tested with `mysql < schema.sql`
  3. Schema Updates
    1. All schema changes must be in `/migrations/YYYYMMDD_description.sql`
    2. Migrations must be idempotent (safe to run multiple times)
    3. Include both forward migration and rollback instructions
    4. Example migration file structure:
       ```sql
       -- Migration: Add vacation_mode field to habit table
       -- Date: 2025-09-27
       -- Author: jason

       -- Forward migration
       ALTER TABLE habit ADD COLUMN vacation_mode TINYINT(1) DEFAULT 1
         COMMENT 'Whether this habit is affected by vacation mode';

       -- Rollback (comment out, for reference)
       -- ALTER TABLE habit DROP COLUMN vacation_mode;
       ```
  4. Migration Execution
    ```bash
    # Apply migration
    mysql -u jttbh -p jttbh < migrations/20250927_add_vacation_mode.sql

    # Verify
    mysql -u jttbh -p jttbh -e "DESCRIBE habit;"
    ```
16. Testing Strategy
  1. Unit Tests
    1. Every model method must have unit tests
    2. Test with synthetic data from `/test/synthetic.py`
    3. Test edge cases: empty lists, null values, invalid inputs
    4. Target: 80% code coverage minimum
  2. Integration Tests
    1. Test full request/response cycle for each route
    2. When testing queries, use test cases in the production database (designated by a `-` as the first character of the identifier, i.e., `"userID": "-58ec8c11-e060-4367-93cf-91a6cc28db8c"`)
    3. Test authentication and permission decorators
    4. Test all HTTP verbs (GET, POST)
  3. Running Tests
    ```bash
    # All tests with coverage
    pytest --cov=app --cov-report=html

    # Specific test file
    pytest test/test_todo.py -v

    # Specific test function
    pytest test/test_todo.py::test_create_todo -v

    # Via web interface (admin only)
    # Visit: /test or /test/todo or /test/habit
    ```
  4. Test Data
    1. Synthetic data defined in `/test/synthetic.py`
    2. Functions to get/filter/manipulate test data
    3. Covers all major entities: users, todos, habits, projects, etc.
    4. Use synthetic data flag to bypass database calls
17. Claude Debugging
  1. If there is a need to create additional files for the purpose of debugging, those should be created in the `/claude` folder. They will be culled when no longer useful.
18. Development Workflow
  1. Read SPECIFICATION.md: Comprehensive system reference
  2. Use environment switcher: `./config/switch_env.sh dev` for development
  3. Database changes: Create migration scripts in `/migrations/`
  4. Follow patterns: Raw SQL, blueprint routes, flat templates
  5. Run unit tests: `pytest` or visit `/test` route
  6. Test manually: Check most recent changes
  7. Deploy: Use deployment scripts for production updates
19. Production Deployment Checklist
  1. Pre-Deployment
    1. [ ] All tests passing (`pytest`)
    2. [ ] Database migrations ready and tested
    3. [ ] Environment variables set in `.env.production`
    4. [ ] `SECRET_KEY` is cryptographically random (not default)
    5. [ ] `DEBUG = False` in production config
    6. [ ] HTTPS configured (Let's Encrypt/Certbot)
    7. [ ] Database backups configured (automated daily)
    8. [ ] Error logging configured (file-based or external service)
  2. Deployment Steps
    1. [ ] Backup production database: `./config/quick_commands.sh backup`
    2. [ ] Pull latest code: `git pull origin main`
    3. [ ] Activate virtual environment: `source venv/bin/activate`
    4. [ ] Install dependencies: `pip install -r requirements.txt`
    5. [ ] Run migrations: `mysql -u jttbh -p jttbh < migrations/latest.sql`
    6. [ ] Restart application: `./config/quick_commands.sh restart`
    7. [ ] Verify services: `./config/quick_commands.sh status`
    8. [ ] Test key features: Dashboard, Todos, Habits
    9. [ ] Monitor logs: `./config/quick_commands.sh logs`
  3 Post-Deployment
    1. [ ] Monitor error logs for 24 hours
    2. [ ] Verify backup was created
    3. [ ] Test from external network
    4. [ ] Verify SSL certificate is valid
20. File Structure Key Points
  1. `/app/routes/`: Flask blueprints for different application areas
  2. `/app/models/`: Data models using raw SQL via BaseModel
  3. `/app/services/`: Core utilities (database, email, Google APIs, decorators)
  4. `/app/templates/`: Flat structure with `[route]_[page].html` naming
  5. `/migrations/`: Database migration scripts
  6. Configuration files: Multiple environment-specific configs and deployment scripts
21. Errors encountered
  1. I get this error when I try to run the application:  
     ```
    File                                         
    "/Users/jason/Documents/JTTBH/./app/main.py", line 6, in <module>                                 
    from app import create_app                                                                    
    ModuleNotFoundError: No module named 'app'    
    ```
  2. 127.0.0.1:5000 works, but localhost:5000 doesn't. After logging in, the site redirects to localhost
  3. After logging in, the application returns this error:
    ```
    InsecureTransportError
    oauthlib.oauth2.rfc6749.errors.InsecureTransportError: (insecure_transport) OAuth 2 MUST utilize https.
    ```
  4. After first vising the todo page, the application returns this error:
    ```
    UndefinedError
    jinja2.exceptions.UndefinedError: 'timedelta' is undefined
    ```


