# Private Java SMP — Website

A Minecraft community website built with Flask. Features a screenshot gallery, user authentication, admin panel, real-time AJAX messaging (DMs + group chat), shop system, VIP ranks, Discord integration, and PWA support.

**Server IP:** `private-java-smp.aternos.me:40115`  
**Discord:** https://discord.gg/XFphHZujM  
**Made by:** SkipScaped

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web Framework | Flask |
| ORM | Flask-SQLAlchemy |
| Auth | Flask-Login + Werkzeug password hashing |
| Forms & CSRF | Flask-WTF + CSRFProtect |
| Database | PostgreSQL |
| Frontend | Jinja2 templates, Bootstrap 5, React (Babel standalone) |
| Messaging | AJAX fetch + server-side poll (no page reloads) |
| Server | Gunicorn |

---

## Features

- **Gallery** — upload screenshots, browse by category, comment on images
- **User accounts** — register/login, profile pics, bio, Minecraft username
- **Direct Messages** — real-time 1-on-1 chat via AJAX polling (no page reload)
- **Group Chat** — server-wide chat room, same seamless AJAX experience
- **Shop** — admin-managed categories & products; players click Discord to purchase
- **VIP Ranks** — displayed on the homepage
- **Admin Panel** — manage images, comments, users, server IP, and the shop
- **Profanity filter** — applied to uploads, comments, and all chat messages
- **PWA** — installable on mobile via service worker
- **Mobile responsive** — Bootstrap 5 grid throughout

---

## Backend Structure

```
/
├── main.py                    # Entry point — imports app from app.py
├── app.py                     # App factory, config, all routes
├── models.py                  # SQLAlchemy ORM models
├── forms.py                   # Flask-WTF form definitions
├── utils.py                   # File validation, category helpers
├── profanity.py               # Bad-word filter
│
├── static/
│   ├── css/style.css          # Minecraft-themed custom styles
│   ├── js/script.js           # Client-side JS (copy IP, image preview)
│   ├── js/react/              # React components (Babel standalone)
│   │   ├── gallery.jsx
│   │   ├── comments.jsx
│   │   └── profile.jsx
│   ├── uploads/               # User-uploaded images (auto-created)
│   └── images/
│       ├── vip/               # VIP rank badge images
│       ├── logo.webp
│       └── favicon.ico
│
├── templates/
│   ├── base.html              # Base layout (navbar, footer, scripts)
│   ├── index.html             # Homepage
│   ├── shop.html              # Public shop page
│   ├── upload.html
│   ├── image.html
│   ├── search.html
│   ├── category.html
│   ├── 403.html / 404.html
│   ├── auth/
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── profile.html
│   │   ├── edit_profile.html
│   │   └── change_password.html
│   ├── messages/
│   │   ├── inbox.html
│   │   ├── conversation.html  # AJAX DM chat (no page reload)
│   │   └── group_chat.html    # AJAX group chat (no page reload)
│   └── admin/
│       ├── dashboard.html
│       └── shop.html          # Admin shop management
│
└── migrations/
    ├── run_migration.py
    └── db_update.sql
```

---

## Database Models

### `User`
| Column | Type | Notes |
|---|---|---|
| `id` | String(36) | UUID primary key |
| `username` | String(50) | Unique |
| `email` | String(120) | Unique |
| `password_hash` | String(256) | Werkzeug hashed |
| `profile_pic` | String(255) | Avatar path |
| `bio` | Text | Optional |
| `minecraft_username` | String(50) | Optional |
| `is_admin` | Boolean | First registered user auto-gets True |
| `created_at` | DateTime | Auto-set |

### `Image`
| Column | Type | Notes |
|---|---|---|
| `id` | String(36) | UUID primary key |
| `title` | String(100) | Required |
| `description` | Text | Required |
| `category` | String(50) | e.g. Builds |
| `filename` | String(255) | Stored filename |
| `filepath` | String(255) | `/static/uploads/<uuid>.<ext>` |
| `uploaded_at` | DateTime | Auto-set |
| `uploader` | String(50) | Display name |
| `user_id` | String(36) | FK → `users.id` |

### `Comment`
| Column | Type | Notes |
|---|---|---|
| `id` | String(36) | UUID PK |
| `image_id` | String(36) | FK → `images.id` |
| `username` | String(50) | Display name |
| `text` | Text | Required |
| `created_at` | DateTime | Auto-set |
| `user_id` | String(36) | FK → `users.id` |

### `DirectMessage`
| Column | Type | Notes |
|---|---|---|
| `id` | String(36) | UUID PK |
| `sender_id` | String(36) | FK → `users.id` |
| `receiver_id` | String(36) | FK → `users.id` |
| `text` | Text | Required |
| `created_at` | DateTime | Auto-set |
| `is_read` | Boolean | Marked True when recipient polls |

### `GroupMessage`
| Column | Type | Notes |
|---|---|---|
| `id` | String(36) | UUID PK |
| `sender_id` | String(36) | FK → `users.id` |
| `text` | Text | Required |
| `created_at` | DateTime | Auto-set |

### `ShopCategory`
| Column | Type | Notes |
|---|---|---|
| `id` | String(36) | UUID PK |
| `name` | String(100) | Required |
| `description` | Text | Optional |
| `image_path` | String(255) | Optional banner |
| `created_at` | DateTime | Auto-set |

### `ShopProduct`
| Column | Type | Notes |
|---|---|---|
| `id` | String(36) | UUID PK |
| `category_id` | String(36) | FK → `shop_categories.id` |
| `name` | String(100) | Required |
| `description` | Text | Optional |
| `price` | String(50) | e.g. `$5.00` or `Free` |
| `image_path` | String(255) | Optional |
| `in_stock` | Boolean | Default True |
| `created_at` | DateTime | Auto-set |

---

## Routes Reference

### Public
| Method | Route | Description |
|---|---|---|
| GET | `/` | Homepage |
| GET | `/image/<id>` | Image detail + comments |
| GET | `/category/<name>` | Gallery filtered by category |
| GET | `/search?q=...` | Search images |
| GET | `/shop` | Public shop page |

### Auth
| Method | Route | Description |
|---|---|---|
| GET/POST | `/register` | Sign up (first user auto-gets admin) |
| GET/POST | `/login` | Log in |
| GET | `/logout` | Log out |
| GET/POST | `/profile/edit` | Edit profile |
| GET/POST | `/profile/change_password` | Change password |

### Messaging (login required)
| Method | Route | Description |
|---|---|---|
| GET | `/messages` | Inbox |
| GET/POST | `/messages/<user_id>` | DM chat (POST returns JSON for AJAX) |
| GET | `/messages/<user_id>/poll` | Poll for new DMs |
| GET/POST | `/chat` | Group chat (POST returns JSON for AJAX) |
| GET | `/chat/poll` | Poll for new group messages |

### Admin (admin only)
| Method | Route | Description |
|---|---|---|
| GET | `/admin` | Dashboard |
| POST | `/admin/set-ip` | Update server IP |
| POST | `/admin/delete/image/<id>` | Delete image |
| POST | `/admin/delete/comment/<id>` | Delete comment |
| POST | `/admin/toggle-admin/<user_id>` | Grant/revoke admin |
| GET | `/admin/shop` | Shop management |
| POST | `/admin/shop/category/add` | Add category |
| POST | `/admin/shop/category/delete/<id>` | Delete category (+ its products) |
| POST | `/admin/shop/product/add` | Add product |
| POST | `/admin/shop/product/delete/<id>` | Delete product |
| POST | `/admin/shop/product/toggle/<id>` | Toggle in/out of stock |

---

## Running Locally

### 1. Prerequisites

- Python 3.11+
- PostgreSQL running locally

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set environment variables

```env
DATABASE_URL=postgresql://user:password@localhost:5432/your_db
SESSION_SECRET=any-long-random-string
```

### 4. Start the server

```bash
gunicorn --bind 0.0.0.0:5000 --reload main:app
```

Open `http://localhost:5000`. **First registered account is automatically admin.**

---

## Admin Panel Guide

Access at `/admin` — requires `is_admin = True`.

| Tab | What you can do |
|---|---|
| Server IP | Change the IP shown site-wide (stored in DB) |
| Images | View all uploads; delete any image (also removes file from disk) |
| Comments | View all comments; delete inappropriate ones |
| Users | View all accounts; grant or revoke admin |
| Shop | Create categories, add products with images/prices, toggle stock |

### Shop setup
1. Go to **Admin → Shop**
2. Create a **category** (e.g. "VIP Ranks")
3. Add **products** with name, price, description, image, stock status
4. Players see the shop at `/shop` and click **Get → Discord** to contact you

---

## Messaging

Both DMs (`/messages/<id>`) and group chat (`/chat`) use **AJAX fetch polling**:

- Sending a message does a `fetch()` POST — the page never reloads and your input is never cleared
- New messages from other users appear automatically every 3 seconds via a poll endpoint
- A `Set` of known message IDs prevents any duplicate bubbles

---

## Content Moderation

`profanity.py` blocks banned words in image uploads, comments, DMs, and group chat before saving.

---

## Notes

- The Babel standalone warning in console is expected — React components compile in-browser for convenience
- Server IP is stored in `server_config` DB table and injected into every template via a context processor
- `db.create_all()` auto-creates all tables on first startup; new columns require `ALTER TABLE` manually
