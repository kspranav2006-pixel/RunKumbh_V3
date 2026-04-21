# RunKumbh - Monsoon Run 2.0 — PRD

## Original Problem Statement
Remake the entire RunKumbh website with a completely new design look matching monsoon and summer vibes. Build a full-stack event registration platform for "RunKumbh - Monsoon Run 2.0" organized by RV Institute.

### Key Requirements
- Landing page with monsoon/summer vibes
- Stripe-integrated registration flow for multiple race categories
- Admin dashboard with full CRUD
- Post-payment: Category/gender-specific BIB numbers (OSM001 / OSW001 etc.)
- Auto-generated printable BIB card image (Pillow + QR + barcode)
- Email BIB card to participant via Gmail
- Admin-side: CSV export, QR code check-in, analytics, search/filter
- Download BIB card + Preview from admin

## Tech Stack
- **Frontend**: React, Tailwind CSS, Shadcn UI, Recharts
- **Backend**: FastAPI, MongoDB (motor), Pillow, qrcode, python-barcode, smtplib
- **Payments**: Stripe (to be switched to Razorpay later — user deferred)
- **Email**: Gmail SMTP via App Password

## Key Data Models
- `events`: {id, title, category, date, distance, price, image_url, ...}
- `registrations`: {id, event_id, user_name, user_email, user_phone, gender, dob, tshirt_size, emergency_contact_*, medical_condition, consents[], bib_number, qr_code, bib_card (base64 PNG data URL), checked_in, checked_in_at, status}
- `payment_transactions`: {session_id, event_id, user_email, user_name, amount, payment_status, bib_number, metadata}

## Key API Endpoints
- `GET /api/events`, `POST/PUT/DELETE /api/admin/events/*`
- `POST /api/payments/checkout/session` — starts Stripe checkout
- `GET /api/payments/checkout/status/{session_id}` — post-payment BIB + email trigger
- `GET /api/admin/registrations` — returns registrations, transactions, events, totals
- `POST /api/admin/registrations` — manual create + auto email
- `POST /api/admin/registrations/{id}/send-email` — **resend BIB email**
- `PUT /api/admin/registrations/{id}` — update status
- `DELETE /api/admin/registrations/{id}`
- `POST /api/admin/registrations/{id}/checkin` — mark checked-in
- `GET /api/admin/registrations/bib/{bib_number}` — lookup for check-in
- `GET /api/admin/registrations/export` — CSV export
- `GET /api/admin/analytics` — dashboard metrics

## Implemented (Feb 2026)
- Full registration flow + 17-field schema
- Admin auth + CRUD for events, registrations, transactions
- Search, filters (gender / check-in status), CSV export, analytics panel
- QR-code check-in tab with manual BIB lookup
- Category/gender-specific BIB number generation after payment
- BIB card image generator (Pillow + barcode + QR, base64 PNG)
- **[Feb 21]** Download BIB Card button in admin registrations row
- **[Feb 21]** Registration Details modal with BIB preview + info panel
- **[Feb 21]** Gmail SMTP email service (`/app/backend/email_service.py`) sending HTML email with BIB card embedded (CID) + attached (PNG)
- **[Feb 21]** Auto-email on: Stripe payment success, manual admin registration, on-demand resend

## Backlog / Roadmap
### P1
- Switch payment platform from Stripe → Razorpay (user said "I'll provide the API keys later")
- Bulk Email Tool for Admins (UI + real send via Gmail — currently only a stub that returns recipients)
- Polish BIB card PNG rendering — text font/positioning looks cramped on some categories (flagged as cosmetic in iteration_2 test report)

### P2
- Refactor `/app/frontend/src/App.js` (2300+ lines) into route-based components: `Landing/`, `Registration/`, `Admin/` (reduce JSX fragility)
- Refactor `/app/backend/server.py` (1217 lines) into routers: `admin_router.py`, `payments_router.py`, `email_router.py`
- User accounts + "My Registrations" page so participants can re-download their BIB
- Refund workflow (admin side)
- SMS confirmation (Twilio) alongside email

## Credentials
- Admin password: `RunKumbh2026Admin` (see `/app/memory/test_credentials.md`)
- Gmail: `runkumbh@gmail.com` (backend/.env)
