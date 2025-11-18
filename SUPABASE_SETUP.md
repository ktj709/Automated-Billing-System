# Supabase Setup Guide

## Step 1: Get Supabase Connection Details

1. Go to https://supabase.com
2. Create a new project or select existing one
3. Go to **Settings** → **Database**
4. Find your connection string under "Connection String" → "URI"

## Step 2: Create Tables in Supabase

### Option A: Using Supabase SQL Editor (Easiest)

1. Go to **SQL Editor** in Supabase dashboard
2. Create a new query
3. Copy and paste content from `database/schema.sql`
4. Click **Run**

### Option B: Using psql locally

```powershell
# Copy the connection string from Supabase
$env:PGPASSWORD="your-password"
psql "postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres" -f "database\schema.sql"
```

## Step 3: Configure Environment

Create `.env` file:

```bash
copy .env.supabase.example .env
```

Edit `.env` and add your Supabase details:

```env
# Get this from Supabase → Settings → Database → Connection String
POSTGRES_CONNECTION_STRING=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres

# Or use individual parameters:
POSTGRES_HOST=db.[YOUR-PROJECT-REF].supabase.co
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=[YOUR-PASSWORD]

# Other configs (optional for now)
API_SECRET_KEY=dev-secret-key-change-this
HEADER_AUTH_TOKEN=test-token-123
```

## Step 4: Test Connection

```powershell
python -c "from services import DatabaseService; db = DatabaseService(); conn = db.get_connection(); print('✓ Connected to Supabase!'); conn.close()"
```

## Step 5: Insert Sample Data

```powershell
python -c "from utils.sample_data import SampleDataGenerator; print(SampleDataGenerator.generate_sql_inserts(SampleDataGenerator.generate_meter_readings()))" > sample_data.sql
```

Then run in Supabase SQL Editor or:

```powershell
psql "your-connection-string" -f sample_data.sql
```

## Step 6: Test the API

```powershell
python app.py
```

In another terminal:

```powershell
curl http://localhost:5000/health
```

## Notes

- Supabase uses PostgreSQL 15 (fully compatible)
- Connection pooling is handled automatically
- SSL is enabled by default
- Row Level Security (RLS) is available if needed
- Free tier: 500MB database, 2GB bandwidth/month
