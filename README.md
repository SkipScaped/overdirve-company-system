# ⚡ OVERDRIVE — Company Management Portal

> Built by **Aaliyan** · Premium internal team management platform

---

## 🚀 Overview

**Overdrive** is a full-featured, premium dark-themed internal company management portal built entirely from scratch by Aaliyan. It centralises everything a modern team needs: company announcements, expense tracking, idea management, job postings, real-time team chat, direct messaging, an AI assistant, and an energy drink inventory system — all in one sleek interface.

The project runs on Python/Flask with a PostgreSQL database, featuring a Groq-powered AI assistant, Spline 3D animations, and a fully installable PWA experience.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11 · Flask 3 · SQLAlchemy · Flask-WTF · Flask-Login |
| **Database** | PostgreSQL (Replit managed) |
| **AI** | Groq API · `llama-3.3-70b-versatile` model |
| **Frontend** | Bootstrap 5.3 · Custom dark CSS design system |
| **3D / Animation** | Spline (WebGL) · GSAP |
| **Fonts** | Inter (Google Fonts) |
| **Icons** | Font Awesome 6 |
| **Audio** | Web Audio API (no audio files — synthesised sounds) |
| **PWA** | Web App Manifest · Service Worker (offline capable) |
| **Voice/Video** | Jitsi Meet (WebRTC, no API key needed) |
| **Server** | Gunicorn (WSGI) · Replit deployment |

---

## ✨ Features

### 🏠 Dashboard
- Company stats at a glance
- Pinned announcements
- Open suggestions feed
- Active job listings

### 📢 Company Updates
- Rich announcement system with categories (General, Dev, Finance, HR, Design…)
- Pin/unpin important updates
- Full CRUD for admins

### 💸 Expense Proposals
- Submit expenses with receipt attachments
- Admin approve/reject workflow with review notes
- Full expense history per user

### 💡 Ideas & Suggestions
- Anyone can post ideas (anonymous option)
- Team voting system
- Status tracking (Open → Reviewed → Implemented)

### 💼 Job Openings
- Admin posts open positions
- External applications with cover letter + resume
- Application review pipeline

### 💬 Team Chat & DMs
- Real-time group chat with image sharing
- Private 1-on-1 direct messages
- Message polling every 2.5s
- Clickable URL detection (linkify)
- Web Audio sound effects

### 🤖 Overdrive AI
- Powered by Groq (llama-3.3-70b-versatile)
- Full live company context injected as system prompt
- Knows team members, roles, recent messages, expenses, suggestions, jobs
- Floating chat widget accessible from any page

### 👥 Team & Roles
- Team directory with member cards
- Custom role/position system (create roles with colours and icons)
- Assign multiple roles to members
- Role badges on profiles and team cards

### 🧃 Energy Drink Inventory (White-Label)
- White-label brand settings (name, logo, colours, tagline)
- Full product catalogue (SKU, flavour, size, pricing)
- Real-time stock tracking with movement history
- Low-stock alerts
- CSV bulk import
- Public-facing store page

### 📱 PWA (Progressive Web App)
- Installable on iOS, Android, and desktop
- Service worker for offline support
- Smooth transitions and mobile-optimised layout

### 🔐 Admin Panel
- Tabbed admin dashboard (Overview, Updates, Jobs, Expenses, Team, Roles)
- Toggle admin status for users
- Remove members
- Full store inventory management

### 📞 Voice & Video Calling
- Jitsi Meet integration (WebRTC, free, no API key required)
- Start calls from DM conversations
- Auto-notifies the other person with a join link
- Voice-only or full video

### 🌍 Notifications
- Real-time notification bell with polling
- Typed notifications (message, update, expense, job, vote)
- Mark individual or all as read

---

## 🏗️ Project Structure

```
overdrive/
├── app.py                    # All Flask routes and application setup
├── models.py                 # SQLAlchemy database models
├── forms.py                  # Flask-WTF form definitions
├── main.py                   # Gunicorn entry point
├── static/
│   ├── css/
│   │   └── overdrive.css     # Full custom dark design system
│   ├── images/               # Logos and static assets
│   ├── uploads/              # User-uploaded files (images, receipts)
│   ├── manifest.json         # PWA manifest
│   └── sw.js                 # Service Worker (offline cache)
├── templates/
│   ├── base.html             # Master layout (topbar, sidebar, AI widget, notifications)
│   ├── dashboard.html        # Main dashboard
│   ├── team.html             # Team directory
│   ├── auth/
│   │   ├── login.html        # Standalone login (GSAP + Spline)
│   │   ├── register.html     # Standalone register
│   │   ├── profile.html      # User profile with roles and actions
│   │   └── edit_profile.html
│   ├── messages/
│   │   ├── inbox.html        # DM inbox
│   │   ├── conversation.html # 1-on-1 chat with call button
│   │   └── group_chat.html   # Team group chat with Spline BG
│   ├── admin/
│   │   ├── dashboard.html    # Admin tabbed hub
│   │   ├── roles.html        # Role management
│   │   ├── store.html        # Energy drink inventory admin
│   │   └── applications.html
│   ├── store/
│   │   └── index.html        # Public energy drink store
│   ├── calls/
│   │   └── room.html         # Jitsi voice/video call room
│   └── ...
└── README.md
```

---

## ⚙️ Environment Variables / Secrets

Set these in **Replit Secrets** (never commit them):

| Secret | Required | Description |
|---|---|---|
| `DATABASE_URL` | ✅ | PostgreSQL connection string (auto-set by Replit DB) |
| `SESSION_SECRET` | ✅ | Flask session signing key (random long string) |
| `GROQ_API_KEY` | ✅ | Groq API key for the AI assistant |
| `MAIL_SERVER` | Optional | SMTP host (e.g. `smtp.gmail.com`) for email verification |
| `MAIL_PORT` | Optional | SMTP port (default `587`) |
| `MAIL_USERNAME` | Optional | SMTP username / email address |
| `MAIL_PASSWORD` | Optional | SMTP app password |
| `MAIL_FROM` | Optional | From address for sent emails |

---

## 📧 Email Verification Setup

Email verification is **optional** — if `MAIL_SERVER` is not set, accounts are auto-verified.

To enable email verification:
1. **Gmail**: Enable 2-Step Verification → Google Account → Security → App Passwords → Generate for "Mail"
2. Add Replit Secrets:
   ```
   MAIL_SERVER = smtp.gmail.com
   MAIL_PORT = 587
   MAIL_USERNAME = youraddress@gmail.com
   MAIL_PASSWORD = xxxx xxxx xxxx xxxx  (16-char App Password)
   MAIL_FROM = Overdrive <youraddress@gmail.com>
   ```
3. Email verification tokens are stored in the database and expire after 24 hours

---

## 📞 Voice & Video Calling

Overdrive uses **Jitsi Meet** (free, open-source WebRTC) — **no API key required**.

**How it works:**
1. Open a DM conversation with a team member
2. Click the 📞 (voice) or 🎥 (video) button in the top-right corner
3. A unique private room is created and a call link is sent to the other person as a DM
4. Both users join via the Jitsi iframe in Overdrive

**Why Jitsi?**
- Free, unlimited minutes
- Works on HTTPS (Replit deployed apps are HTTPS ✅)
- No account or API key needed
- Full WebRTC: end-to-end encrypted

**Upgrade options:**
- [Daily.co](https://daily.co) — 10,000 free minutes/month, custom UI, recording
- [Agora.io](https://agora.io) — 10,000 free minutes/month, lower latency
- [LiveKit](https://livekit.io) — open source, self-hostable

---

## 🚀 Getting Started (Local Development)

```bash
# Clone the repo
git clone <repo-url>
cd overdrive

# Install dependencies
pip install flask flask-sqlalchemy flask-login flask-wtf groq gunicorn psycopg2-binary

# Set environment variables
export DATABASE_URL="postgresql://..."
export SESSION_SECRET="your-secret-key"
export GROQ_API_KEY="your-groq-key"

# Run
gunicorn --bind 0.0.0.0:5000 --reload main:app
```

---

## 🗄️ Database Models

| Model | Purpose |
|---|---|
| `User` | Team members with auth, profile, admin flag |
| `CompanyUpdate` | Announcements with categories and pinning |
| `ExpenseProposal` | Expense submissions and approval workflow |
| `Suggestion` | Ideas with voting |
| `SuggestionVote` | Per-user votes on suggestions |
| `JobListing` | Open positions |
| `JobApplication` | Applications for jobs |
| `DirectMessage` | 1-on-1 messages (with image support) |
| `GroupMessage` | Team chat messages (with image support) |
| `Notification` | In-app notifications |
| `Role` | Custom team roles/positions |
| `UserRole` | Role assignments |
| `ServerConfig` | Key-value config store |
| `EnergyDrinkBrand` | White-label brand settings |
| `EnergyDrinkProduct` | Drink products with stock tracking |
| `StockMovement` | Inventory movement history |
| `EmailVerification` | Email verification tokens |

---

## 🎨 Design System

The portal uses a custom dark design system defined in `overdrive.css`:

- **Background**: `#0a0a0a` (near-black)
- **Surface levels**: `#111`, `#181818`, `#1f1f1f`, `#252525` (layered depth)
- **Accent**: `#e63946` (Overdrive red)
- **Typography**: Inter (variable weight: 400–900)
- **Border radius**: 10px (cards), 14px (modals), 20px (pills)
- **Shadows**: layered with high opacity for depth
- **3D**: Spline blackhole background (`AATNdo0u4uGpBox4`) at 9% opacity

---

## 👤 Creator

**Aaliyan** — built Overdrive end-to-end as an internal company management portal.

The project was developed iteratively with full-stack ownership: database schema design, Flask routing, Jinja2 templating, custom CSS design system, AI integration, WebRTC calling, and PWA implementation.

---

## 📜 License

Private — internal use only.
