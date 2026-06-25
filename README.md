# Private Java SMP — Website

A Minecraft community website built with Flask featuring a screenshot gallery, user authentication, VIP ranks, a server shop, and server join information.

---

## Table of Contents

- [Tech Stack](#tech-stack)
- [Backend Structure](#backend-structure)
- [Database Models](#database-models)
- [Routes Reference](#routes-reference)
- [Running Locally](#running-locally)
- [Environment Variables](#environment-variables)
- [File Uploads](#file-uploads)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web Framework | Flask |
| ORM | Flask-SQLAlchemy |
| Auth | Flask-Login + Werkzeug password hashing |
| Forms | Flask-WTF |
| Database | PostgreSQL |
| Frontend | Jinja2 templates, Bootstrap 5, Babel (React Virtual DOM) |
| Server | Gunicorn |

---

## Backend Structure

```
/
├── main.py                  # Entry point — imports app from app.py
├── app.py                   # App factory, config, login manager, all routes
├── models.py                # SQLAlchemy ORM models (User, Image, Comment)
├── forms.py                 # Flask-WTF form definitions
├── utils.py                 # Helper functions (file validation, formatting)
│
├── static/
│   ├── css/style.css        # Minecraft-themed custom styles
│   ├── js/script.js         # Client-side JS (copy IP, image preview, etc.)
│   ├── js/react/            # React Virtual DOM components (via Babel standalone)
│   │   ├── gallery.jsx      # Gallery grid component
│   │   ├── comments.jsx     # Comments component
│   │   └── profile.jsx      # Profile component
│   ├── uploads/             # User-uploaded images (auto-created)
│   └── images/
│       ├── vip/             # VIP rank badge images
│       └── favicon.ico      # Site favicon (logo.webp)
│
├── templates/
│   ├── base.html            # Base layout (navbar, footer, scripts)
│   ├── index.html           # Homepage (server info, VIP, gallery, shop)
│   ├── upload.html          # Image upload form
│   ├── image_detail.html    # Single image view + comments
│   ├── login.html           # Login page
│   ├── register.html        # Registration page
│   ├── profile.html         # User profile page
│   ├── edit_profile.html    # Edit profile form
│   ├── search_results.html  # Search results
│   └── category.html        # Category-filtered gallery
│
└── migrations/
    ├── run_migration.py     # Manual migration runner script
    └── db_update.sql        # SQL for schema changes
```

### Key Files Explained

**`main.py`** — The gunicorn entry point. Just one line:
```python
from app import app
```

**`app.py`** — Does everything at startup:
- Creates the Flask app and sets `SECRET_KEY` from env
- Applies `ProxyFix` middleware for correct HTTPS URL generation behind a proxy
- Connects to PostgreSQL via `DATABASE_URL`
- Initialises Flask-Login and sets the login redirect route
- Runs `db.create_all()` to auto-create tables if they don't exist
- Seeds sample data if the database is empty
- Defines all route handlers

**`models.py`** — Three SQLAlchemy models with relationships.

**`forms.py`** — WTForms classes for registration, login, upload, comments, and profile editing with CSRF protection.

**`utils.py`** — Shared helpers: allowed file extension check, category slug extraction, human-readable date formatting.

---

## Database Models

### `User`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer | Primary key |
| `username` | String(64) | Unique, required |
| `email` | String(120) | Unique, required |
| `password_hash` | String(256) | Werkzeug hashed |
| `profile_pic` | String(255) | Path to avatar |
| `bio` | Text | Optional |
| `minecraft_username` | String(64) | Optional |

### `Image`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer | Primary key |
| `title` | String(128) | Required |
| `description` | Text | Optional |
| `category` | String(64) | e.g. Builds, Redstone |
| `filename` | String(256) | Stored filename |
| `filepath` | String(512) | URL path to file |
| `uploader` | String(64) | Display name |
| `user_id` | Integer | FK → `user.id` |

### `Comment`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer | Primary key |
| `image_id` | Integer | FK → `image.id` |
| `username` | String(64) | Display name |
| `text` | Text | Required |
| `user_id` | Integer | FK → `user.id` |

---

## Routes Reference

### Authentication
| Method | Route | Description |
|---|---|---|
| GET/POST | `/register` | New user sign-up |
| GET/POST | `/login` | User login |
| GET | `/logout` | End session |

### Gallery
| Method | Route | Description |
|---|---|---|
| GET | `/` | Homepage with gallery |
| GET/POST | `/upload` | Upload image (login required) |
| GET | `/image/<id>` | Image detail + comments |
| GET/POST | `/image/<id>/comment` | Post a comment (login required) |
| GET | `/category/<category>` | Filter by category |
| GET | `/search?q=...` | Full-text search |

### Profiles
| Method | Route | Description |
|---|---|---|
| GET | `/profile` | Current user's profile |
| GET | `/user/<id>` | Public profile view |
| GET/POST | `/profile/edit` | Edit bio, Minecraft username, avatar |
| GET/POST | `/profile/change_password` | Update password |

---

## Running Locally

### 1. Prerequisites

- Python 3.11+
- PostgreSQL running locally (or a connection string to a remote DB)

### 2. Clone and install dependencies

```bash
git clone <your-repo-url>
cd <repo-folder>
pip install -r requirements.txt
```

### 3. Set environment variables

Create a `.env` file in the project root (or export them in your shell):

```env
DATABASE_URL=postgresql://user:password@localhost:5432/your_db_name
SESSION_SECRET=any-random-secret-string
```

> If you use a `.env` file, install `python-dotenv` and add `load_dotenv()` to the top of `main.py`, or export them manually before running.

### 4. Create the database

Make sure your PostgreSQL database exists, then the app will auto-create all tables on first run via `db.create_all()`.

```bash
# Example: create the database in psql
createdb your_db_name
```

### 5. Run the development server

```bash
python main.py
```

Or with gunicorn (matches the production command):

```bash
gunicorn --bind 0.0.0.0:5000 --reload main:app
```

Then open `http://localhost:5000` in your browser.

### 6. (Optional) Run database migrations manually

If you need to apply schema changes to an existing database:

```bash
python migrations/run_migration.py
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | Full PostgreSQL connection string |
| `SESSION_SECRET` | Yes | Flask session signing key — use a long random string |

---

## File Uploads

- Uploaded images are saved to `static/uploads/`
- Allowed formats: `png`, `jpg`, `jpeg`, `gif`, `webp`
- Maximum upload size: **16 MB**
- The `uploads/` directory is created automatically on first run if it doesn't exist

---

## Notes

- The React components in `static/js/react/` use **Babel standalone** (compiled in the browser). This is fine for development but the console will show a warning about precompiling for production — this is expected and harmless.
- The server IP (`private-java-smp.aternos.me:40115`) is hardcoded in the templates and can be changed in `templates/base.html` and `templates/index.html`.
- VIP rank badge images live in `static/images/vip/`.
