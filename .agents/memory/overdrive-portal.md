---
name: Overdrive Portal Architecture
description: Flask company management portal — key decisions, models, and patterns for future work.
---

## Stack
Flask + SQLAlchemy + Flask-WTF + Flask-Login. Gunicorn on port 5000. PostgreSQL via DATABASE_URL.

## Auth
- First registered user auto-becomes admin (`is_admin=True`).
- `auth/login.html` and `auth/register.html` are **standalone HTML** (no `{% extends 'base.html' %}`), so they have their own `<head>` with Spline, GSAP, etc.
- Both auth pages now receive `open_jobs` context for the jobs teaser section.

## Models (models.py)
All 7 company models: `CompanyUpdate`, `ExpenseProposal`, `Suggestion`, `SuggestionVote`, `JobListing`, `JobApplication`, `Notification` (integer PK, auto-increment).
Legacy: `User`, `DirectMessage`, `GroupMessage`, `Image`, `Comment`, `ServerConfig`.

## Notification System
- Model: `Notification` with `ntype` field (info|message|update|vote|expense|job), `is_read`, `link`.
- Helper: `create_notification(user_id, ntype, title, body, link)` — caller must commit.
- Routes: `GET /notifications` (JSON), `POST /notifications/read` (mark one or all).
- Triggers wired: DM sent → recipient, company update posted → all users, expense reviewed → submitter, suggestion voted → author.
- Bell icon in topbar polls every 20s, plays `notif` sound on new items.

## PWA
- `static/manifest.json` — theme #e63946, standalone display.
- `static/sw.js` — cache-first for static assets, network-first for HTML, skip API/poll endpoints.
- Registered in base.html on page load.

## Sound Engine
- `window.OD_SOUND` defined globally in base.html (Web Audio API, no files).
- Types: `send` (upward tick), `receive` (two-note chime), `notif` (bell), `open` (rising tone).
- Unlocked on first user gesture.

## Group Chat
- Template completely rewritten: Spline 3D background (`AATNdo0u4uGpBox4`), glassmorphism card.
- **Own messages** now show avatar + username on the RIGHT (red gradient bubble).
- Others' messages: avatar + username on LEFT (dark glassmorphism bubble).
- Consecutive messages from same sender are "grouped" (avatar hidden, meta hidden).
- Sound effects: send/receive via `window.OD_SOUND`.
- Auto-grow textarea, char counter, Enter=send / Shift+Enter=newline.

## AI Chat (Groq)
- Route: `POST /ai/chat`, login_required.
- Model: `llama-3.3-70b-versatile`.
- System prompt includes: live company stats (members, jobs, updates, expenses, suggestions), pinned announcements, recent updates, top suggestions, open jobs, current user profile.
- Widget: floating button bottom-right, quick chips, typing indicator, clear button.

## Key Patterns
- `create_notification()` must be called BEFORE `db.session.commit()` since it adds to the session.
- Auth pages pass `open_jobs` via template context for the jobs teaser section.
- Watermark coverage: `.spline-wm-kill` div overlays bottom-right corner; CSS hides `.spline-watermark`.
- `inject_globals()` context processor provides `unread_count` and `notif_unread` to all templates.

**Why separate auth templates:** Gives full layout control for the 3-column GSAP/Spline experience without inheriting base.html's sidebar/topbar.
