# ⚡ Blessings City Billing (Streamlit‑First)

This repository contains an electricity billing system designed to be run **primarily via Streamlit**.

It supports:
- **Field Engineer** flow: capture meter readings + upload meter photos.
- **Admin** flow: validate readings, calculate bills, store bills in Supabase, and confirm payments.

---

## What you run

- **Main app (recommended): Streamlit UI**
  - Entry point: [streamlit_app.py](streamlit_app.py)
  - Run: `python -m streamlit run streamlit_app.py`

- **Optional: Flask API**
  - Entry point: [app.py](app.py)
  - Useful if you want API/webhook integrations (Stripe/WhatsApp). Not required for Streamlit-first usage.

---

## Current business rules (important)

### 1) November 2025 is locked

To protect historical data, the backend prevents any **new bill insert** whose:
- `billing_period_end` is in **Nov 2025** (`2025-11-xx`)

This is enforced for:
- Single-bill creation (`DatabaseService.create_bill`)
- Bulk generation (`DatabaseService.generate_bills_for_month`)

Re-verify lock (read-only): `python -m scripts.verify_supabase_november`

### 2) Bills are never overwritten

Supabase enforces a unique constraint on:
- `(flat_id, billing_period_start)`

If a new bill would collide, the system **does not overwrite** the existing record. It retries the insert with an **alternate `billing_period_start`** (moved forward) so the new bill is stored as a separate row.

### 3) Workflow readings are monthly units (no subtraction)

In the Admin billing workflow (Step 6/7), the reading you enter is treated as **absolute monthly consumption** (units for that period). It is **not** computed as `current - previous`.

Note: the readings ingestion path can still compute a `consumption` field from historical readings for the same meter. Some legacy/imported rows may have `consumption <= 0`, and UI estimates may fall back to the raw reading value.

---

## Pricing rules (rate + fixed charge)

The system uses an explicit formula-based bill:

$$\text{total\_amount} = (\text{flat\_units} + \text{water\_motor\_share})\times \text{rate\_per\_unit} + \text{fixed\_charge} + \text{previous\_outstanding}$$

Pricing lookup is in [services/pricing_service.py](services/pricing_service.py).

### Rate per unit

- Loaded from `data/Blessings_City_Master_Data.xlsx` (by flat code like `B17-FF`).
- Default fallback is `12.0` when not found.

### Special 9₹ flats (no fixed charge)

- `C14-SF`, `D3-SF`, `D4-SF`
- When rate is 9, fixed charge is forced to 0.

### Fixed charge by BHK (when BHK is available)

If the identifier includes a prefix like `5BHK-B17-FF`, fixed charge is overridden by BHK count:
- 5BHK → `2311`
- 4BHK → `1890`
- 2BHK → `1474`

The 9₹ rule always wins (fixed forced to 0).

---

## Setup (Windows)

### Prerequisites

- Python 3.10+
- Supabase project (recommended)

Optional integrations:
- Cloudinary (meter photos)
- Discord (bill/payment notifications)
- Stripe (payment links)
- OpenAI (AI validation and message generation)

### 1) Create and activate a virtual environment

```powershell
cd "D:\Machine Learning Projects\Billing"
# ⚡ Blessings City Billing (Streamlit‑First)

This repository contains an electricity billing system designed to be run **primarily via Streamlit**.

What it gives you:
- A **Field Engineer** UI to capture readings + photos.
- An **Admin** UI to review readings, calculate bills, store them in Supabase, and mark payments.
- Optional backend/API pieces (Flask webhooks, Stripe/WhatsApp integrations, scheduler).

If you’re totally new: start with **Quick Start**, then follow the **End‑to‑End Workflow** section to understand how data moves through the system.

---

## Quick start (Windows)

### 1) Python environment

```powershell
cd "D:\Machine Learning Projects\Billing"
python -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 2) Create `.env`

Copy one of these and fill values:
- `.env.supabase.example` (recommended)
- `.env.example`

Minimum required to run with Supabase:

```dotenv
SUPABASE_URL=https://<your-project-ref>.supabase.co
SUPABASE_KEY=<your-service-role-key-or-anon-key>
```

Optional integrations (only if you want them):

```dotenv
# AI (optional)
OPENAI_API_KEY=sk-...

# Discord (optional)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Cloudinary (optional)
CLOUDINARY_URL=cloudinary://<api_key>:<api_secret>@<cloud_name>
CLOUDINARY_UPLOAD_PRESET=<unsigned_preset_if_using_unsigned_upload>

# Stripe (optional)
STRIPE_API_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# WhatsApp (optional)
WHATSAPP_PHONE_NUMBER_ID=...
WHATSAPP_ACCESS_TOKEN=...

# Auth0 (optional)
AUTH0_DOMAIN=your-tenant.us.auth0.com
AUTH0_API_IDENTIFIER=https://billing-api.example.com

# Simple header token (optional, used by Flask API)
HEADER_AUTH_TOKEN=your-dev-token
```

Security rules:
- Do not commit `.env`.
- Do not commit any JWT tokens (including any local token files).

### 3) Create Supabase tables

In Supabase Dashboard → **SQL Editor**, run:
- [database/supabase_schema.sql](database/supabase_schema.sql)

Then seed a minimal dataset so the Field Engineer dropdown has something to show (example below).

### 4) Run Streamlit

```powershell
.\venv\Scripts\Activate.ps1
python -m streamlit run streamlit_app.py
```

Open: http://localhost:8501

---

## What runs where (components)

### Streamlit (primary UI)

- Entry point: [streamlit_app.py](streamlit_app.py)
- Roles:
  - **Field Engineer**: add readings + upload meter photos
  - **Administrator**: review readings, compute bills, save bills, mark payments

### Supabase (primary database)

- Used in “Supabase REST mode” when `SUPABASE_URL` + `SUPABASE_KEY` are set.
- Expected tables are the normalized schema in [database/supabase_schema.sql](database/supabase_schema.sql)

### Optional: Flask API

- Entry point: [app.py](app.py)
- Provides webhook-style endpoints (meter-reading ingestion, Stripe webhook).
- Not required for Streamlit workflows.

Important: some Flask/API flows are more “reference implementation” than the Streamlit-first path; prefer Streamlit for day-to-day ops.

---

## Supabase setup in detail (beginner-friendly)

### A) Create the schema

Run this once in Supabase SQL Editor:
- [database/supabase_schema.sql](database/supabase_schema.sql)

### B) Minimal seed data (so the UI has 1 active meter)

If you don’t already have real data migrated into Supabase, run a minimal seed like this in Supabase SQL Editor.

This creates:
- 1 floor
- 1 flat type
- 1 flat
- 1 owner
- 1 flat_owner link (required because the UI expects an owner)
- 1 meter in `active` status

```sql
insert into public.floors (code, name)
values ('FF', 'First Floor')
on conflict (code) do nothing;

insert into public.flat_types (name)
values ('2BHK')
on conflict (name) do nothing;

insert into public.flats (code, floor_id, type_id)
select
  'B17-FF',
  (select id from public.floors where code = 'FF'),
  (select id from public.flat_types where name = '2BHK')
on conflict (code) do nothing;

insert into public.owners (name, phone)
values ('Test Owner', '+910000000000')
returning id;

insert into public.flat_owners (flat_id, owner_id, is_primary)
select
  (select id from public.flats where code = 'B17-FF'),
  (select id from public.owners where name = 'Test Owner' order by id desc limit 1),
  true;

insert into public.meters (meter_number, flat_id, status)
select
  '19152159',
  (select id from public.flats where code = 'B17-FF'),
  'active'
on conflict (meter_number) do nothing;
```

### C) Verify connectivity

Run locally:

```powershell
python scripts\verify_migration.py
```

---

## End‑to‑end workflow (how the system actually works)

This section explains the **real operational flow**: Field Engineer → Admin → database.

### 1) Field Engineer flow (Streamlit)

Where: **Field Engineer Dashboard** in [streamlit_app.py](streamlit_app.py)

What the engineer does:
1. Select a flat + floor (the dropdown is built from Supabase `meters → flats → owners`)
2. Enter **Reading Value (kWh)**
3. Optionally enter **Motor Reading / Share (kWh)** (if a shared motor applies)
4. Select the **Reading Date**
5. Optionally upload a **meter photo**
6. Submit

What happens in the backend when you submit:
- The app resolves the selected meter’s internal IDs from Supabase.
- The reading is inserted into Supabase **`readings`** via `DatabaseService.insert_meter_reading`.
- Consumption is computed (for storage) as:
  - `consumption = current_reading_value - previous_reading_value` (based on the previous reading in `readings` for that meter).
  - This is storage-level convenience for some analytics/estimates.

Photo handling:
- If you upload an image, Streamlit always saves a local copy under `data/meter_photos/`.
- If Cloudinary is configured (`CLOUDINARY_URL` and optionally `CLOUDINARY_UPLOAD_PRESET`), the photo is also uploaded.
- Uploaded URLs are indexed into `data/meter_photo_links.json` so the Admin screen can show photos next to readings.

Motor meter lookup (optional):
- If your database has `flat_motors` + `motors` + a motor-linked `meters.motor_id`, the Field Engineer screen attempts to show the motor meter number.
- If you don’t use shared motors, you can ignore this.

### 2) Admin login (Streamlit)

Where: **Administrator Login** in [streamlit_app.py](streamlit_app.py)

How auth behaves:
- If Auth0 is configured (`AUTH0_DOMAIN` + `AUTH0_API_IDENTIFIER` and `python-jose` is installed), the JWT is verified against Auth0.
- If Auth0 is NOT configured, the app falls back to a simple check:
  - your User ID must start with `auth0|...`
  - you still must fill the “JWT Token” field (any non-empty value) due to current UI validation

#### Generate a new Auth0 token (for the “JWT Token” field)

There are two supported ways to get a token for testing.

Option A (recommended, interactive):

```powershell
python get_auth0_token.py
```

Option B (simple, env-based):

1) Add these to your `.env` (do not commit this file):

```dotenv
AUTH0_DOMAIN=your-tenant.us.auth0.com
AUTH0_API_IDENTIFIER=https://billing-api.example.com
AUTH0_M2M_CLIENT_ID=...
AUTH0_M2M_CLIENT_SECRET=...
```

2) Run:

```powershell
python get_token_simple.py
```

By default it also writes the token to `auth0_token.txt` for convenience (this repo ignores that file so it won’t be pushed).

### 3) Admin review + bill creation (Streamlit)

Where: **Administrator** dashboard in [streamlit_app.py](streamlit_app.py)

What the admin does:
1. Review new readings
2. View the associated photo (if present)
3. Optionally run AI validation (if OpenAI key is present)
4. Confirm/approve a reading
5. Calculate the bill
6. Save the bill to Supabase

Key internal steps:

#### A) “Pending readings”
- Admin screen loads recent rows from **`readings`**.
- It filters out readings that are already referenced by existing bills (`bills.flat_reading_id` / `bills.motor_reading_id`).

#### B) Pricing lookup
Pricing is resolved by [services/pricing_service.py](services/pricing_service.py):
- It reads `data/Blessings_City_Master_Data.xlsx` (if present) to get:
  - `rate_per_unit`
  - base `fixed_charge`
- It applies overrides:
  - **Default rate** fallback: 12.0
  - **Special 9₹ flats**: `C14-SF`, `D3-SF`, `D4-SF` → rate 9 and fixed forced to 0
  - **BHK fixed override** (when unit id contains a prefix like `5BHK-B17-FF`):
    - 5BHK → 2311
    - 4BHK → 1890
    - 2BHK → 1474
  - 9₹ rule always wins (fixed forced to 0)

#### C) Bill calculation
Bill arithmetic is in [services/tariff_rules.py](services/tariff_rules.py).

Current formula used by the “simple” calculator:

$$\text{total\_amount} = (\text{flat\_units} + \text{water\_motor\_share})\times \text{rate\_per\_unit} + \text{fixed\_charge} + \text{previous\_outstanding}$$

Important semantics:
- In the Admin workflow, the value you approve is treated as **monthly units for that period**.
- The system does not subtract previous readings at bill-calculation time in that workflow.

#### D) Saving bills + safety rules
Bills are inserted via `DatabaseService.create_bill`.

Business-critical protections:
1) **November 2025 is locked**
   - Any attempt to create a bill whose `billing_period_end` falls in **Nov 2025** is blocked.
   - Bulk generation for a period touching Nov 2025 is blocked.

   Verification script (read-only):
   - `python -m scripts.verify_supabase_november`

2) **Bills are never overwritten**
   - There is a uniqueness constraint on `(flat_id, billing_period_start)`.
   - If an insert collides, the code retries with an alternate `billing_period_start` so the new bill becomes a separate row.

### 4) Marking payments (Admin)

Admin can:
- Mark bills as `paid` (updates `bills.status`).
- Optionally send Discord notifications if `DISCORD_WEBHOOK_URL` is configured.
- Log notifications to the `notifications` table.

---

## Optional: bulk monthly generation

The Admin “Generate Monthly Bills” button calls a Supabase RPC:
- `rpc('generate_bills_for_month', {p_billing_period_start, p_billing_period_end, p_due_date})`

This requires you to create a **database function** named `generate_bills_for_month` in your Supabase project.

Note: this repo does not currently ship an authoritative SQL implementation of that function because bill computation uses Python pricing + business rules. Many teams implement this RPC server-side in SQL, or replace it with a Python-side batch job.

If you don’t have the RPC yet, you can still run the system fully by generating bills from the Admin workflow (per reading).

---

## Optional: Flask API + webhooks (advanced)

Run:

```powershell
.\venv\Scripts\Activate.ps1
python app.py
```

Endpoints:
- `POST /webhook/meter-reading` – accepts a reading payload, validates, bills, sends notifications
- `POST /webhook/stripe` – Stripe webhook → marks bill paid + logs `payment_events`
- `GET /health`

Authentication:
- Supports a simple `HEADER_AUTH_TOKEN` bearer token, OR Auth0 JWT verification.

Important:
- Some API paths assume legacy columns (e.g., `customer_id` on bills) that do not exist in the normalized Supabase bills table.
- Treat the Flask API as optional; Streamlit is the primary operational interface.

---

## Optional: Scheduler (advanced)

The scheduler in [services/scheduler_service.py](services/scheduler_service.py) uses APScheduler to run recurring jobs (monthly bill generation, reminders, overdue marking).

Status:
- Consider this component “experimental/legacy” until it is fully aligned to the normalized Supabase schema (some fields referenced there are from an older schema).

---

## Data files (what’s in /data)

- `data/Blessings_City_Master_Data.xlsx`
  - Pricing source used by PricingService
  - If missing, the system falls back to a default rate

- `data/meter_photos/`
  - Local saved photos uploaded by Field Engineer

- `data/meter_photo_links.json`
  - Local index mapping readings → Cloudinary URLs (only when Cloudinary upload succeeds)

- `data/meter_registry.json`
  - Optional legacy export/cached registry (Streamlit loads registry live from Supabase)

---

## Useful scripts (smoke tests)

- Verify Supabase connection + whether `meters`/`flats` exist: `python scripts\verify_migration.py`
- Verify November 2025 lock (read-only): `python -m scripts.verify_supabase_november`
- Tariff sanity test: `python test_tariff.py`
- Stripe test: `python test_stripe.py`
- Discord test: `python test_discord.py`
- WhatsApp test: `python test_whatsapp.py`
- Auth0 verification test: `python verify_token.py`

---

## Troubleshooting (common beginner issues)

### Streamlit doesn’t start

- Make sure the venv is activated and Streamlit is installed:

```powershell
.\venv\Scripts\Activate.ps1
python -m streamlit run streamlit_app.py
```

### “No active meters found”

- Your Supabase database likely has no `meters` (or they are not `status = 'active'`).
- Also ensure each meter’s flat has at least one owner mapping (`flat_owners`), because the active-meter query uses joins.

### Supabase errors about missing tables/columns

- You must run the normalized schema:
  - [database/supabase_schema.sql](database/supabase_schema.sql)
- The legacy schema in [database/schema.sql](database/schema.sql) is not what Streamlit uses.

### Bills fail to insert

Common reasons:
- Attempting to create a November 2025 bill (blocked by design)
- Missing/incorrect unit → flat → meter mapping (cannot resolve `flat_id`)
- Duplicate `(flat_id, billing_period_start)` (auto-retried with alternate start)

### Cloudinary upload fails

- Install dependency: `python -m pip install cloudinary`
- Ensure `CLOUDINARY_URL` is set
- If using unsigned upload, ensure `CLOUDINARY_UPLOAD_PRESET` is set


