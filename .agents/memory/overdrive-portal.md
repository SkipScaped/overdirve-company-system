---
name: Overdrive Portal Architecture
description: Company management portal decisions — models, routes, design system
---

# Overdrive Company Management Portal

## Stack
- Flask + SQLAlchemy + Flask-Login + Flask-WTF
- Bootstrap 5.1 (layout backbone) + custom `static/css/overdrive.css` (dark theme)
- Gunicorn via `main:app` workflow

## Key Design Decisions
- Existing User model kept intact (is_admin flag, profile pics, etc.)
- First registered user automatically becomes admin
- New models: CompanyUpdate, ExpenseProposal, Suggestion, SuggestionVote, JobListing, JobApplication
- All routes require @login_required; admin routes also require @admin_required
- Logo: `static/images/overdrive_logo.png`
- CSS file: `static/css/overdrive.css` — do NOT add styles to style.css (old Minecraft CSS, not loaded)
- `inject_globals` context processor provides `unread_count` and `now` to all templates

**Why:** App was originally a Minecraft SMP site; transformed to corporate management portal while keeping auth/DM/group-chat infrastructure intact.

## Routes Overview
- `/` → dashboard (login required)
- `/updates`, `/updates/new`, `/updates/<id>` — company updates (new/edit admin only)
- `/expenses`, `/expenses/new`, `/expenses/<id>`, `/expenses/<id>/review` — expense proposals
- `/suggestions`, `/suggestions/new`, `/suggestions/<id>`, `/suggestions/<id>/vote` (POST, returns JSON)
- `/jobs`, `/jobs/<id>`, `/jobs/<id>/apply`
- `/admin/jobs`, `/admin/jobs/new`, `/admin/jobs/<id>/edit`, `/admin/jobs/<id>/applications`, `/admin/applications/<id>/review`
- `/messages`, `/messages/<user_id>`, `/chat` — messaging (existing)
- `/admin` — admin dashboard

## Template Structure
- `templates/base.html` — Overdrive base with sidebar/topbar
- `templates/dashboard.html`
- `templates/updates/` — list, new, detail
- `templates/expenses/` — list, new, detail
- `templates/suggestions/` — list, new, detail
- `templates/jobs/` — list, detail
- `templates/admin/` — dashboard, jobs, new_job, applications
- `templates/auth/` — login, register, profile, edit_profile, change_password
- `templates/messages/` — inbox, conversation, group_chat
