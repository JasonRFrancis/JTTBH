# JTTBH - Just Trying to be Helpful

A personal productivity platform built with Python Flask and MySQL that brings together various streams of information to help you track goals, habits, tasks, and projects.

## Features

### Core Features
- **Dashboard** - Unified view of daily tasks, habits, and priorities
- **Todo List** - TeuxDeux-inspired task management with automatic push-forward of incomplete items
- **Habit Tracker** - 5x5 grid for daily habits with streak calculations and GitHub-style heat map
- **Vacation Mode** - Pause habit streaks during vacation periods
- **Project Management** - Long-term project tracking with mood boards and next steps
- **Bookmarks** - Pinboard.in style bookmark management with tagging and reference list
- **Book Tracker** - Reading list with status workflow (to-read, reading, finished)
- **Fitness Program** - Exercise tracking with programs, logs, sets, and reps
- **Podcast Feed** - Podcast subscription management with RSS feed generation
- **Household Chores** - Recurring chore tracking with bitmask scheduling
- **Daily Journal** - Daily questions, answers, and mood tracking with categories
- **Admin Panel** - User approval workflow and permission management
- **Settings** - User preferences with insert-only storage

### Features Requiring External API Setup
- **Triage** - Gmail and Calendar integration for inbox processing (requires Google OAuth scopes)
- **Appointments** - Calendly-style appointment scheduling with public booking page (requires email integration)

See `/claude/RESULTS.md` for implementation details and known issues.

## Architecture

### Core Principles
- **RESTful URLs**: `/[username]/[area]/[view]/[presentation]/[parameters]`
- **Insert-Only Database**: Type-2 slowly changing dimensions for full audit history
- **Semantic HTML**: No CSS frameworks, progressive enhancement
- **Raw SQL**: Direct PyMySQL queries, no ORM
- **Permission System**: Granular bitvector-based access control
- **Mobile-First**: Responsive design from ground up

### Technology Stack
- **Backend**: Python 3.10+, Flask 3.0+
- **Database**: MySQL 9.0+ with insert-only pattern
- **Authentication**: Google OAuth 2.0
- **Frontend**: Semantic HTML5, vanilla JavaScript, custom CSS

## Quick Start

### Prerequisites
- Python 3.10 or higher
- MySQL 9.0 or higher
- Google OAuth credentials (for authentication and triage features)

### Initial Setup

1. **Clone and navigate to repository**
   ```bash
   cd /path/to/JTTBH
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up database**
   ```bash
   # Create database and user
   mysql -u root -p -e "CREATE DATABASE jttbh CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
   mysql -u root -p -e "CREATE USER 'jttbh'@'localhost' IDENTIFIED BY 'your_password';"
   mysql -u root -p -e "GRANT ALL PRIVILEGES ON jttbh.* TO 'jttbh'@'localhost';"
   mysql -u root -p -e "FLUSH PRIVILEGES;"

   # Import schema
   mysql -u jttbh -p jttbh < schema.sql
   ```

5. **Configure environment**
   ```bash
   # Create .env file
   cat > .env << EOF
   # Database Configuration
   DB_HOST=localhost
   DB_USER=jttbh
   DB_PASSWORD=your_password
   DB_NAME=jttbh

   # Flask Configuration
   FLASK_ENV=development
   SECRET_KEY=your-secret-key-change-in-production
   PORT=5000

   # Google OAuth (optional for development)
   GOOGLE_CLIENT_ID=your_client_id
   GOOGLE_CLIENT_SECRET=your_client_secret
   GOOGLE_REDIRECT_URI=http://localhost:5000/auth/oauth2callback
   EOF
   ```

6. **Run development server**
   ```bash
   python ./app/main.py
   ```

   Application available at `http://localhost:5000`

## Development Commands

```bash
# Run development server
python ./app/main.py

# Switch environments
./config/switch_env.sh dev
./config/switch_env.sh prod
./config/switch_env.sh status

# Database management
mysql -u jttbh -p jttbh                    # Connect to database
mysql -u jttbh -p jttbh < schema.sql       # Import/reimport schema
```

## Production Deployment

### Production Setup

```bash
# Initial production setup (run as jttbh user)
./config/setup_production.sh

# Deploy updates
./config/deploy.sh

# Server management
./config/quick_commands.sh status    # Check all services
./config/quick_commands.sh logs      # View recent logs
./config/quick_commands.sh restart   # Restart services
./config/quick_commands.sh backup    # Create manual backup
./config/quick_commands.sh db        # Connect to production database
```

### Production Checklist

Before deploying to production:

- [ ] Set secure `SECRET_KEY` in environment
- [ ] Configure production database credentials
- [ ] Set up HTTPS/SSL certificates (Let's Encrypt recommended)
- [ ] Configure Google OAuth credentials for production domain
- [ ] Set `FLASK_ENV=production`
- [ ] Configure email SMTP settings
- [ ] Set up automated database backups
- [ ] Review `/claude/RESULTS.md` for feature completion status

### Google OAuth Setup (Production)

1. **Create OAuth credentials**
   - Go to: https://console.cloud.google.com/apis/credentials
   - Create OAuth client ID (Web application)
   - Authorized redirect URIs: `https://jttbh.com/auth/oauth2callback`

2. **Required scopes**
   - `openid` - User authentication
   - `email` - User email
   - `profile` - User name
   - `https://www.googleapis.com/auth/gmail.readonly` - For triage (optional)
   - `https://www.googleapis.com/auth/calendar.readonly` - For triage (optional)

3. **Environment variables**
   ```bash
   GOOGLE_CLIENT_ID=your_client_id
   GOOGLE_CLIENT_SECRET=your_client_secret
   GOOGLE_REDIRECT_URI=https://jttbh.com/auth/oauth2callback
   ```

**Note**: Gmail/Calendar scopes require Google OAuth verification which can take 2-4 weeks. Basic authentication works without these scopes.

## Project Structure

```
jttbh/
├── app/
│   ├── __init__.py              # Flask application factory (17 blueprints)
│   ├── main.py                  # Entry point
│   ├── models/                  # Data models (15 files, insert-only pattern)
│   │   ├── base.py              # BaseModel with insert-only support
│   │   ├── user.py              # User model (exception: uses UPDATE)
│   │   ├── todo.py, habit.py, project.py, bookmark.py, book.py
│   │   ├── fitness.py, appointment.py, podcast.py, chore.py
│   │   ├── journal.py, triage.py, vacation.py, household.py
│   │   └── user_preference.py
│   ├── routes/                  # Flask blueprints (17 files)
│   │   ├── main.py, auth.py, admin.py, settings.py
│   │   ├── todo.py, habit.py, project.py, bookmark.py, book.py
│   │   ├── fitness.py, appointment.py, podcast.py, chore.py
│   │   ├── journal.py, triage.py, vacation.py
│   │   └── test.py              # Admin pytest runner
│   ├── services/                # Core utilities
│   │   ├── database.py          # PyMySQL connection manager
│   │   ├── decorators.py        # Authentication & permissions
│   │   ├── email.py             # SMTP email notifications
│   │   ├── google_services.py   # Google API integration
│   │   └── logging.py           # Request logging
│   ├── static/
│   │   ├── css/                 # 16 mobile-first stylesheets
│   │   └── js/                  # 9 vanilla JS files
│   └── templates/               # 34 HTML templates (flat structure)
├── claude/
│   └── RESULTS.md               # Schema issues, spec ambiguities, decisions
├── config/                      # Deployment scripts and configuration
├── test/                        # Unit tests and synthetic data
├── schema.sql                   # Database schema (~40 tables)
├── SPECIFICATION.md             # Complete project specification
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Key Features Documentation

### Insert-Only Pattern

All tables (except `user`) use an insert-only pattern for data versioning:

- **Updates**: Insert new row with updated values
- **Deletes**: Insert new row with primary field set to NULL
- **Current state**: MAX(id) for each entity
- **History**: All rows provide complete audit trail

See SPECIFICATION.md lines 273-290 for detailed documentation.

### Permission System

Granular permissions using bitvectors:

| Bit | Value | Permission  | Description              |
|-----|-------|-------------|--------------------------|
| 0   | 1     | Admin       | Administrative functions  |
| 1   | 2     | Podcast     | Podcast feed management   |
| 2   | 4     | Appointment | Appointment scheduling    |
| 3   | 8     | Dashboard   | Dashboard access          |
| 4   | 16    | Todo        | Todo lists                |
| 5   | 32    | Habit       | Habit tracking            |
| 6   | 64    | Project     | Project management        |
| 7   | 128   | Triage      | Email/Calendar triage     |
| 8   | 256   | Bookmark    | Bookmark management       |
| 9   | 512   | Fitness     | Workout tracking          |
| 10  | 1024  | Chore       | Household chore tracking  |
| 11  | 2048  | Book        | Book tracker              |
| 12  | 4096  | Journal     | Daily journal/questions   |

**Default permissions for approved users**: 8190 (all except admin)

### Authentication Flow

1. User authenticates via Google OAuth
2. New users start with `approval_status='pending'`
3. Admin approves users via `/[username]/admin/users`
4. Approved users receive default permissions
5. Permissions can be customized per user

### URL Pattern

URLs follow RESTful pattern: `/[username]/[area]/[view]/[presentation]/[parameters]`

Examples:
- `/jason/todo/index/html` - Todo list in HTML
- `/jason/habit/index/html` - Habit calendar
- `/jason/todo/search/html?q=meeting` - Search todos
- `POST /jason/todo/create/post` - Create new todo
- `POST /jason/habit/toggle/post/<habitID>/<date>` - Toggle habit

Presentation parameter defaults to `html` if omitted (SPEC line 239).

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific feature tests
pytest test/test_todo.py
pytest test/test_habit.py

# Via web interface (admin only)
http://localhost:5000/test
```

## Required Features Status

See `/claude/RESULTS.md` for complete implementation status.

### Implemented
- Dashboard, Todo (with push-forward), Habit (streaks and heat map), Vacation mode
- Project, Bookmark (with reference list), Book, Fitness, Podcast, Chore, Journal
- Insert-only database pattern, Permission bitvector system, Google OAuth
- Admin user approval workflow, User preferences/settings

### Requires External Credentials
- **Triage** - Scaffolded; requires Google Gmail/Calendar API scopes
- **Appointments** - Scaffolded; requires SMTP email configuration

### Not Implemented
- **Show Tracker** and **Movie Tracker** - No schema tables exist (SPEC Sections 5.1, 5.2)
- **PDF presentation** - HTML and JSON only; PDF deferred (SPEC line 287)

## Documentation

- **SPECIFICATION.md** - Complete project specification and architecture
- **/claude/RESULTS.md** - Implementation notes, ambiguities, and recommendations
- **schema.sql** - Database schema with insert-only pattern

## Contributing

This is a personal project. For coding standards and architectural patterns, refer to SPECIFICATION.md.

## License

Private project - All rights reserved.

## Contact

Jason Francis - jason.r.francis@gmail.com

Repository: https://github.com/JasonRFrancis/JTTBH
