# Overdrive Company Management Portal

## Overview
Internal company management platform for Overdrive. Dark-themed, professional web portal built with Flask.

**Company website:** https://overdrive-568529096082.us-west1.run.app  
**Lead Developer / Admin:** Aaliyan

## Features
- **Company Updates** — Admins post updates (pinned, categorised) visible to all team members
- **Expense Proposals** — Staff submit expense requests; admins approve or reject with notes
- **Suggestions** — Any member can submit ideas (optionally anonymous); team votes on them
- **Job Listings** — Admins post open positions; logged-in users apply with cover letter + resume
- **Direct Messages** — 1-on-1 messaging between team members
- **Team Chat** — Company-wide group chat
- **Admin Panel** — User management, pending expense review, job management

## Tech Stack
- **Backend:** Python / Flask + SQLAlchemy + Flask-Login + Flask-WTF
- **Database:** PostgreSQL (via `DATABASE_URL` env var)
- **Frontend:** Bootstrap 5 + custom dark CSS (`static/css/overdrive.css`)
- **Server:** Gunicorn (`main:app`)

## User Preferences
- Dark professional theme — all UI uses `static/css/overdrive.css`, NOT the old `style.css`
- First registered user becomes admin automatically
- Admin username: Aaliyan
- Overdrive logo at `static/images/overdrive_logo.png`

## Running Locally
```bash
gunicorn --bind 0.0.0.0:5000 --reload main:app
```
