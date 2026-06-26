# Private Java SMP — Website

A Minecraft community website built with Flask featuring a screenshot gallery, user authentication, admin panel, direct messaging, group chat, VIP ranks, server shop, and server join functionality.

---

## Table of Contents

- [Tech Stack](#tech-stack)
- [Backend Structure](#backend-structure)
- [Database Models](#database-models)
- [Routes Reference](#routes-reference)
- [Running Locally](#running-locally)
- [Environment Variables](#environment-variables)
- [File Uploads](#file-uploads)
- [Admin Panel](#admin-panel)
- [Content Moderation](#content-moderation)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web Framework | Flask |
| ORM | Flask-SQLAlchemy |
| Auth | Flask-Login + Werkzeug password hashing |
| Forms & CSRF | Flask-WTF + CSRFProtect |
| Database | PostgreSQL |
| Frontend | Jinja2 templates, Bootstrap 5, React (via Babel standalone) |
| Server | Gunicorn |

---

## Backend Structure

```
/
├── main.py                    # Entry point — imports app from app.py
├── app.py                     # App factory, config, all routes
├── models.py                  # SQLAlchemy ORM models
├── forms.py                   # Flask-WTF form definitions
├── utils.py                   # File validation, category helpers
├── profanity.py               # Bad-word filter (used on uploads, comments, messages)
│
├── static/
│   ├── css/style.css          # Minecraft-themed custom styles
│   ├── js/script.js           # Client-side JS (copy IP, image preview)
│   ├── js/react/              # React Virtual DOM components (Babel standalone)
│   │   ├── gallery.jsx        # Gallery grid component
│   │   ├── comments.jsx       # Comments display component
│   │   └── profile.jsx        # Profile component
│   ├── uploads/               # User-uploaded images (auto-created on startup)
│   └── images/
│       ├── vip/               # VIP rank badge images (vip_gold.png, vip_bronze.png)
│       ├── logo.webp          # Site logo
│       └── favicon.ico        # Site favicon
│
├── templates/
│   ├── base.html              # Base layout (navbar, footer, scripts)
│   ├── index.html             # Homepage (server info, VIP ranks, gallery, shop)
│   ├── upload.html            # Image upload form
│   ├── image.html             # Single image view + comments
│   ├── search.html            # Search results
│   ├── category.html          # Category-filtered gallery
│   ├── 403.html               # 403 Forbidden page
│   ├── 404.html               # 404 Not Found page
│   ├── auth/
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── profile.html
│   │   ├── edit_profile.html
│   │   └── change_password.html
│   ├── messages/
│   │   ├── inbox.html         # DM inbox + new message user list
│   │   ├── conversation.html  # 1-on-1 private chat
│   │   └── group_chat.html    # Server-wide group chat
│   └── admin/
│       └── dashboard.html     # Admin panel (IP, images, comments, users)
│
└── migrations/
    ├── run_migration.py        # Manual migration runner
    └── db_update.sql           # SQL schema changes
```

### Key Files

**`main.py`** — One line: `from app import app`. Used by gunicorn.

**`app.py`** — Does everything at startup:
- Creates the Flask app, applies CSRF protection, applies `ProxyFix`
- Connects to PostgreSQL via `DATABASE_URL`
- Initialises Flask-Login
- Runs `db.create_all()` to auto-create any missing tables
- Seeds the default server IP into `server_config` if not present
- Defines all route handlers

**`profanity.py`** — Regex-based bad-word filter. `contains_profanity(text)` returns `True` if the text contains a banned word. Applied to image titles/descriptions, comments, and all chat messages before saving.

---

## Database Models

### `ServerConfig`
Stores key/value configuration (e.g. the server IP). Editable by admins through the admin panel.

| Column | Type | Notes |
|---|---|---|
| `id` | Integer | Primary key |
| `key` | String(64) | Unique config key |
| `value` | String(256) | Config value |

### `User`
| Column | Type | Notes |
|---|---|---|
| `id` | String(36) | UUID primary key |
| `username` | String(50) | Unique, required |
| `email` | String(120) | Unique, required |
| `password_hash` | String(256) | Werkzeug hashed |
| `profile_pic` | String(255) | Path to avatar |
| `bio` | Text | Optional |
| `minecraft_username` | String(50) | Optional |
| `is_admin` | Boolean | Default False; first registered user gets True |
| `created_at` | DateTime | Auto-set |

### `Image`
| Column | Type | Notes |
|---|---|---|
| `id` | String(36) | UUID primary key |
| `title` | String(100) | Required |
| `description` | Text | Required |
| `category` | String(50) | e.g. Builds, Redstone |
| `filename` | String(255) | Stored filename |
| `filepath` | String(255) | `/static/uploads/<uuid>.<ext>` |
| `uploaded_at` | DateTime | Auto-set |
| `uploader` | String(50) | Display name |
| `user_id` | String(36) | FK → `users.id` |

### `Comment`
| Column | Type | Notes |
|---|---|---|
| `id` | String(36) | UUID primary key |
| `image_id` | String(36) | FK → `images.id` |
| `username` | String(50) | Display name |
| `text` | Text | Required |
| `created_at` | DateTime | Auto-set |
| `user_id` | String(36) | FK → `users.id` |

### `DirectMessage`
| Column | Type | Notes |
|---|---|---|
| `id` | String(36) | UUID primary key |
| `sender_id` | String(36) | FK → `users.id` |
| `receiver_id` | String(36) | FK → `users.id` |
| `text` | Text | Required |
| `created_at` | DateTime | Auto-set |
| `is_read` | Boolean | Default False; marked True when recipient opens conversation |

### `GroupMessage`
| Column | Type | Notes |
|---|---|---|
| `id` | String(36) | UUID primary key |
| `sender_id` | String(36) | FK → `users.id` |
| `text` | Text | Required |
| `created_at` | DateTime | Auto-set |

---

## Routes Reference

### Public
| Method | Route | Description |
|---|---|---|
| GET | `/` | Homepage — server info, VIP ranks, gallery, shop |
| GET | `/image/<id>` | Image detail page with comments |
| GET | `/category/<name>` | Gallery filtered by category |
| GET | `/search?q=...` | Search images by title, description, category |

### Authentication
| Method | Route | Description |
|---|---|---|
| GET/POST | `/register` | Sign up (first user auto-gets admin) |
| GET/POST | `/login` | Log in |
| GET | `/logout` | Log out |

### Gallery
| Method | Route | Description |
|---|---|---|
| GET/POST | `/upload` | Upload image — login required, profanity checked |
| GET/POST | `/image/<id>` | View image; POST submits a comment |

### Profiles
| Method | Route | Description |
|---|---|---|
| GET | `/profile` | Current user's profile |
| GET | `/user/<id>` | Another user's public profile |
| GET/POST | `/profile/edit` | Edit bio, Minecraft username, avatar |
| GET/POST | `/profile/change_password` | Change password |

### Messaging (login required)
| Method | Route | Description |
|---|---|---|
| GET | `/messages` | Inbox — existing conversations + all users to DM |
| GET/POST | `/messages/<user_id>` | 1-on-1 private chat; POST sends a message |
| GET/POST | `/chat` | Server-wide group chat; POST sends a message |

### Admin (admin only)
| Method | Route | Description |
|---|---|---|
| GET | `/admin` | Dashboard — images, comments, users, IP |
| POST | `/admin/set-ip` | Update the server IP stored in DB |
| POST | `/admin/delete/image/<id>` | Delete image + file from disk |
| POST | `/admin/delete/comment/<id>` | Delete a comment |
| POST | `/admin/toggle-admin/<user_id>` | Grant or revoke admin for a user |

---

## Running Locally

### 1. Prerequisites

- Python 3.11+
- PostgreSQL running locally (or a remote connection string)

### 2. Clone and install dependencies

```bash
git clone <your-repo-url>
cd <repo-folder>
pip install -r requirements.txt
```

### 3. Set environment variables

Create a `.env` file or export in your shell:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/your_db_name
SESSION_SECRET=any-long-random-string
```

### 4. Create the database and run migrations

```bash
# Create DB (if it doesn't exist)
createdb your_db_name

# The app auto-creates all tables on first startup via db.create_all()
# For adding columns to an existing DB, run:
python migrations/run_migration.py
```

### 5. Start the server

```bash
# Development
python main.py

# Production-style (matches the deployment command)
gunicorn --bind 0.0.0.0:5000 --reload main:app
```

Open `http://localhost:5000` in your browser.

**First registered account is automatically made admin.**

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | Full PostgreSQL connection string |
| `SESSION_SECRET` | Yes | Flask session signing key — use a long random string |

---

## File Uploads

- Saved to `static/uploads/` (created automatically on startup)
- Allowed formats: `png`, `jpg`, `jpeg`, `gif`, `webp`
- Maximum size: **16 MB**
- Stored with a UUID filename to avoid collisions
- Filepath stored in DB as `/static/uploads/<uuid>.<ext>` (absolute URL path)

---

## Admin Panel

Access at `/admin` — requires an account with `is_admin = True`.

**Features:**
- **Server IP tab** — change the IP shown site-wide (stored in DB, not hardcoded)
- **Images tab** — view all uploads with previews; delete any image (also removes file from disk)
- **Comments tab** — view all comments; delete inappropriate ones
- **Users tab** — view all accounts; grant or revoke admin privileges

**How to become admin:**
- The first account ever registered is automatically granted admin
- Existing accounts can be promoted by another admin via the Users tab
- Or run directly: `UPDATE users SET is_admin = TRUE WHERE username = 'yourname';`

---

## Content Moderation

`profanity.py` provides a regex word-list filter applied **before saving** to:
- Image titles and descriptions (upload rejected if triggered)
- Comments (comment rejected if triggered)
- Direct messages and group chat messages (message rejected if triggered)

To add or remove banned words, edit the `BAD_WORDS` list in `profanity.py`.

---

## Notes

- The Babel standalone warning in the browser console (`You are using the in-browser Babel transformer…`) is expected — the React components compile in-browser for development convenience. It does not affect functionality.
- Server IP is stored in the `server_config` database table and injected into every template via a Flask context processor — changing it in the admin panel updates it everywhere instantly.
- The navbar shows **Messages**, **Group Chat**, and (for admins) **Admin Panel** only when logged in.
