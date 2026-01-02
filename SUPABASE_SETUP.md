# Supabase Setup Guide (Current / Streamlit-First)

This repo primarily runs in **Supabase REST mode** via `supabase-py` (PostgREST). The Streamlit app talks to Supabase directly through `DatabaseService`.

> There is a legacy direct-Postgres (`psycopg2`) mode, but the recommended/default path is Supabase REST.

## 1) Create a Supabase project

1. Go to https://supabase.com and create/select a project.
2. In the Supabase dashboard, open **Project Settings → API**.
3. Copy:
	- **Project URL** (for `SUPABASE_URL`)
	- **Service role key** (for `SUPABASE_KEY`)

Security note: the service role key bypasses RLS; keep it server-side only (local dev is fine). Never put it in a browser/frontend.

## 2) Create tables (normalized schema)

1. Open **SQL Editor** in Supabase.
2. Create a new query.
3. Paste the contents of `database/supabase_schema.sql`.
4. Click **Run**.

This schema matches what `services/database_service.py` expects in Supabase mode (`flats`, `meters`, `readings`, `bills`, `notifications`, `payment_events`, etc.).

## 3) Configure local environment

Copy the env template:

```powershell
copy .env.supabase.example .env
```

Set (at minimum):

```env
SUPABASE_URL=https://<your-project-ref>.supabase.co
SUPABASE_KEY=<your-service-role-key>
```

Optional integrations (only if you use them): Stripe, WhatsApp, Discord, Cloudinary, Auth0.

## 4) Quick connectivity test

This verifies the app can talk to Supabase using the REST client:

```powershell
./venv/Scripts/python.exe -c "from services.database_service import DatabaseService; db=DatabaseService(); print('use_supabase=', db.use_supabase); print('active_meters=', len(db.get_active_meters() or []))"
```

If `use_supabase=False`, your env vars are not being picked up (or are missing).

## 5) Run Streamlit

If the `streamlit.exe` launcher is broken (common when a venv was moved), use module mode:

```powershell
./venv/Scripts/python.exe -m streamlit run streamlit_app.py
```

## Notes / RLS

- If you turn on RLS, you must add policies that allow the operations the app performs.
- Easiest local dev setup: keep RLS disabled for these tables or use the service role key.
