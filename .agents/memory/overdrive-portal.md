---
name: Overdrive Portal Architecture
description: Flask company management portal — key decisions, models, and patterns for future work.
---

## Stack
Flask + SQLAlchemy + Flask-WTF + Flask-Login. Gunicorn on port 5000. PostgreSQL via DATABASE_URL.

## Auth
- First registered user auto-becomes admin (`is_admin=True`).
- `auth/login.html` and `auth/register.html` are **standalone HTML** (no `{% extends 'base.html' %}`), so they have their own `<head>` with Spline, GSAP, etc.
- Both auth pages receive `open_jobs` context for the jobs teaser section.

## Models (models.py)
All company models: `CompanyUpdate`, `ExpenseProposal`, `Suggestion`, `SuggestionVote`, `JobListing`, `JobApplication`, `Notification` (integer PK), `Role`, `UserRole`.
Legacy: `User`, `DirectMessage` (has `image_path`), `GroupMessage` (has `image_path`), `Image`, `Comment`, `ServerConfig`.

## CSRF Pattern
- `window.OD_CSRF = '{{ csrf_token() }}'` is set globally in base.html `<head>` — use this in ALL JS fetch calls that POST to Flask routes.
- Notification `POST /notifications/read` requires `'X-CSRFToken': window.OD_CSRF` header.
- AI `POST /ai/chat` also requires this header.
- Forms in templates use `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">` as usual.

## Notification System
- Model: `Notification` with `ntype` (info|message|update|vote|expense|job), `is_read`, `link`.
- Helper: `create_notification(user_id, ntype, title, body, link)` — caller must commit.
- Routes: `GET /notifications` (JSON), `POST /notifications/read` (mark one or all).
- CSS fix: `.od-notif-panel` has `display:none` base; `.od-notif-panel.show { display:flex !important; }` controls Bootstrap dropdown visibility.

## Notification CSS Bug (FIXED)
Bootstrap dropdown adds/removes `.show` class. The panel must use `display:none` as base and `display:flex` only in `.show` state — NOT `display:flex` in base rule.

## PWA
- `static/manifest.json` — theme #e63946, standalone display.
- `static/sw.js` — cache-first for static assets, network-first for HTML, skip API/poll endpoints.
- Registered in base.html on page load.

## Sound Engine
- `window.OD_SOUND` defined globally in base.html (Web Audio API, no files).
- Types: `send` (upward tick), `receive` (two-note chime), `notif` (bell), `open` (rising tone).
- Unlocked on first user gesture.

## Group Chat & DM Conversations
- Group chat: Spline 3D background (`AATNdo0u4uGpBox4`), own messages RIGHT (red bubble), others LEFT (dark glass), consecutive grouping, sound effects.
- DM conversation.html fully rewritten to match group chat style — same bubble/avatar pattern, image upload support, auto-grow textarea, poll every 2.5s.
- Both support image uploads: group `/chat/upload`, DM `/messages/<user_id>/upload`.
- Poll endpoints return `image_path` in each message object.
- Links are auto-linkified via `linkify()` in both chat JS blocks (converts https:// to `<a>` tags).
- Image button in group chat input uses `/chat/upload`; in DM uses `/messages/<user_id>/upload`.
- **Critical bug that was fixed**: `|escapejs` Jinja2 filter does NOT exist — use `|tojson` instead for JS string literals.
- **Critical bug fixed**: save `pendingImage` reference to a local var BEFORE calling `clearImage()` in send handlers.

## Roles System
- Models: `Role` (name, color, icon, position, created_by) and `UserRole` (user_id, role_id, assigned_by).
- Routes: `GET /admin/roles`, `POST /admin/roles/create`, `POST /admin/roles/<id>/delete`, `POST /admin/roles/<id>/assign/<uid>`, `POST /admin/roles/<id>/unassign/<uid>`.
- Assign/unassign return JSON `{ok: true}` — used by roles.html JS without page reload.
- Role pills shown in team.html and (future) profile.html via `member.user_roles` → `ur.role_obj`.

## Team Page
- Route: `GET /team` → renders `team.html` with all `User` rows.
- Shows member grid with role pills, DM button, profile link, search filter.
- Linked in desktop nav and sidebar.

## AI Chat (Groq)
- Route: `POST /ai/chat`, login_required.
- Model: `llama-3.3-70b-versatile`.
- System prompt includes live company stats + current user profile.
- Widget: floating button bottom-right, quick chips, typing indicator.
- Returns actual error string on failure (shown as ⚠️ prefix in bubble).

## Startup Block Pattern
- `db.create_all()` runs first, then safe `ALTER TABLE` for `image_path` columns via try/except rollback.
- `ServerConfig` default seed runs last.

## Global Spline Background
- `templates/base.html` has a `position:fixed; z-index:-1` div containing the blackhole Spline (`AATNdo0u4uGpBox4`) at opacity 0.09 — visible on all authenticated pages.
- Must use `z-index: -1` (not 0) — `z-index: 0` positioned elements appear ON TOP of static-flow content.
- Group chat has its own higher-opacity Spline (0.22) layered inside the page as `z-index: 2` content.

## Energy Drink White-Label Store
- Models: `EnergyDrinkBrand` (brand settings), `EnergyDrinkProduct` (inventory), `StockMovement` (history)
- Routes: `/store` (public), `/admin/store` (admin hub with tabs), `/admin/store/brand`, `/admin/store/product/add|edit|delete|stock`, `/admin/store/import`, `/admin/store/csv-template`
- CSV bulk import: columns name,sku,flavor,size_ml,price_cost,price_retail,stock_quantity,description; duplicate SKUs skipped
- Admin store template uses Bootstrap modals for Add/Edit/Stock-adjust; `openEditModal(p|tojson)` sets form fields

## Voice/Video Calling (Jitsi)
- Routes: `/call/<room_id>` (room page), `/call/start/<user_id>` (POST — creates room, sends DM + notification to other user)
- No API key needed — uses `meet.jit.si` iframe embed
- Call button in conversation.html header calls `startCall('voice'|'video')` which POSTs to `/call/start/<user_id>` then opens room in new tab
- Room ID format: `od-{20 hex chars}` (random per call)

## Email Verification
- Model: `EmailVerification` (user_id, token, is_used, created_at)
- Routes: `/verify-email/<token>` (GET), `/resend-verification` (POST)
- `send_email()` helper uses stdlib smtplib; reads MAIL_SERVER, MAIL_USERNAME, MAIL_PASSWORD, MAIL_PORT, MAIL_FROM from env — gracefully skips if not configured
- If MAIL_SERVER not set: logs a warning but never errors

## 3D Toggle
- `#od-3d-toggle` floating button (bottom-right, z-index 9000) in base.html — toggles `#od-global-spline-bg` visibility
- Preference saved to `localStorage('od_3d')` as 'on'|'off' (default on)
- On mobile (≤768px) the button moves up to `bottom:72px` to avoid mobile nav overlap

## Key Patterns
- `create_notification()` must be called BEFORE `db.session.commit()`.
- `inject_globals()` context processor provides `unread_count` and `notif_unread` to all templates.
- Watermark coverage: CSS hides `.spline-watermark`; overlay div covers bottom-right corner.
- `window.OD_CSRF` is the single source of CSRF token for all JS fetch calls — do NOT use `document.querySelector('input[name="csrf_token"]')` as a fallback (forms may not exist on page).

**Why separate auth templates:** Full layout control for 3-column GSAP/Spline experience without base.html sidebar/topbar.
