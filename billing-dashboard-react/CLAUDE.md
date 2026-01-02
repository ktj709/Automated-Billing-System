# CLAUDE.md — Blessings Electric Billing AI MVP

> Status note: this document is a historical planning prompt for a frontend MVP.
> The current working system in this repo is Streamlit-first and uses the normalized Supabase schema in `database/supabase_schema.sql`.
> This doc mentions **Clerk**; the current Python app uses **Auth0** (optional) and does not depend on Clerk.

## 1. Project Overview

You are an AI coding assistant embedded in the Blessings Electric Billing AI project.

This project is for a small office team that manages electricity billing for apartments and villas in a gated community ("Blessings City"). The goal is to build an MVP that:

- Helps office admins look up residents, meters, and units
- Supports billing workflows (entering readings, generating bills per block/unit for a given month)
- Tracks billing history and payment status
- Manages defaulters and collections

### Data Sources

**Initial Master Data (for migration):**
- `data/blessings_city_master_data_with_villas.jsonl` — Master data for all units (146 entries)
- `data/blessings_city_billing_training.jsonl` — Billing Q&A training examples (58 entries)

**Production Data Storage:** Supabase (PostgreSQL)

## 2. Target Users & Context

**Primary users:**

**Office Admin (main persona)**
- Low technical literacy, needs very simple UI
- Tasks:
  - Search a flat/villa by number, block, or resident name
  - See meter ID, tariff, and any relevant billing info
  - Enter meter readings for a billing period (block-by-block)
  - Generate bills for all units in a block
  - Track payment status (paid/pending/overdue)
  - View defaulters and outstanding dues
  - Export/share data for invoicing

**(Later) Field Engineer**
- Takes meter readings in the field
- For MVP, assume office admin enters readings manually

For this MVP, we focus on Office Admin tooling only.

## 3. MVP Scope

### 3.1 Core MVP Features

#### Authentication (Clerk)

- Office admin login via Clerk
- Protected routes for all app functionality
- Single role for MVP (admin)

#### Data Layer (Supabase)

**Database Schema:**

```sql
-- Units table (migrated from JSONL)
CREATE TABLE units (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  unit_id TEXT UNIQUE NOT NULL,        -- e.g., "4BHK-C8-SF", "VILLA-A2"
  unit_type TEXT NOT NULL,             -- 'apartment' | 'villa' | 'sco' | 'motor'
  bhk_type TEXT,                       -- '2BHK' | '4BHK' | '5BHK' | null
  flat_no TEXT NOT NULL,               -- Block identifier, e.g., "C8", "B5"
  floor TEXT,                          -- 'GF' | 'FF' | 'SF' | null
  client_name TEXT,
  meter_no TEXT,
  fixed_charge NUMERIC NOT NULL,       -- 1474 / 1857 / 1890 / 2157 / 2311
  rate_per_unit NUMERIC DEFAULT 12,
  water_motor_meter_no TEXT,           -- For flats: linked motor meter
  phone TEXT,
  email TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Meter readings (entered by admin each billing cycle)
CREATE TABLE readings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  unit_id TEXT REFERENCES units(unit_id),
  period TEXT NOT NULL,                -- 'YYYY-MM' format, e.g., '2024-12'
  previous_reading NUMERIC NOT NULL,
  current_reading NUMERIC NOT NULL,
  consumption NUMERIC GENERATED ALWAYS AS (current_reading - previous_reading) STORED,
  reading_date DATE DEFAULT CURRENT_DATE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(unit_id, period)
);

-- Generated bills
CREATE TABLE bills (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  unit_id TEXT REFERENCES units(unit_id),
  period TEXT NOT NULL,                -- 'YYYY-MM'
  flat_consumption NUMERIC NOT NULL,
  motor_consumption NUMERIC,
  total_block_consumption NUMERIC,
  water_motor_share NUMERIC DEFAULT 0,
  total_units NUMERIC NOT NULL,
  usage_charge NUMERIC NOT NULL,
  fixed_charge NUMERIC NOT NULL,
  total_amount NUMERIC NOT NULL,
  status TEXT DEFAULT 'pending',       -- 'pending' | 'paid' | 'overdue'
  breakdown JSONB,                     -- Step-by-step calculation
  generated_at TIMESTAMPTZ DEFAULT NOW(),
  paid_at TIMESTAMPTZ,
  UNIQUE(unit_id, period)
);
```

**TypeScript Types:**

```typescript
type UnitType = 'apartment' | 'villa' | 'sco' | 'motor';
type Floor = 'GF' | 'FF' | 'SF' | null;
type BHKType = '2BHK' | '4BHK' | '5BHK' | null;
type BillStatus = 'pending' | 'paid' | 'overdue';

interface Unit {
  id: string;
  unit_id: string;
  unit_type: UnitType;
  bhk_type: BHKType;
  flat_no: string;
  floor: Floor;
  client_name: string;
  meter_no: string;
  fixed_charge: number;
  rate_per_unit: number;
  water_motor_meter_no?: string;
  phone?: string;
  email?: string;
}

interface MeterReading {
  id: string;
  unit_id: string;
  period: string;
  previous_reading: number;
  current_reading: number;
  consumption: number;
  reading_date: string;
}

interface Bill {
  id: string;
  unit_id: string;
  period: string;
  flat_consumption: number;
  motor_consumption?: number;
  total_block_consumption?: number;
  water_motor_share: number;
  total_units: number;
  usage_charge: number;
  fixed_charge: number;
  total_amount: number;
  status: BillStatus;
  breakdown: string[];
  generated_at: string;
  paid_at?: string;
}
```

**Fixed Charges by Unit Type:**

| Type | Fixed Charge |
|------|--------------|
| 2BHK Flat | ₹1,474 |
| 4BHK Flat | ₹1,890 |
| 5BHK Flat | ₹2,311 |
| Villa | ₹1,857 |
| SCO | ₹2,157 |

**Water Motors (6 total):**

| Motor ID | Meter No. | Serves Blocks |
|----------|-----------|---------------|
| MOTOR-B | 87923504 | B5, B6, B17, B18 (12 flats) |
| MOTOR-C | 86729933 | C8-C17 (24 flats) |
| MOTOR-D1 | 90199696 | D1-D4 (12 flats) |
| MOTOR-D2 | 19152168 | D6-D11 (18 flats) |
| MOTOR-F1 | 86729926 | F2-F6, F19-F23 (30 flats) |
| MOTOR-F2 | 97701102 | F7-F10, F15-F18 (24 flats) |

#### Unit Search / Directory

- Search units by: Unit ID, Flat/Block number, Meter ID, Resident name, Unit type
- View unit details: owner info, meter config, billing history
- Group units by block (based on shared water motor)

#### Billing Workflow

**Block-Based Batch Entry Flow:**

1. **Select Period** — Admin picks month/year (e.g., December 2024)
2. **Select Block** — Admin picks a block (e.g., Block C) which groups all flats sharing a water motor
3. **Enter Readings** — Admin enters:
   - Motor reading (previous + current) for the shared water motor
   - Flat readings (previous + current) for EACH flat in the block
4. **Generate Bills** — System calculates water motor share and generates bills for all flats simultaneously
5. **Review & Save** — Bills are saved to Supabase

**Master Billing Formula:**

```
Final Bill = (Flat Units + Water Motor Share) × ₹12 + Fixed Charge

Where:
- Water Motor Share = (Motor Units ÷ Total Block Units) × Flat Units
- Total Block Units = Sum of all flat consumption in the block
- Round to 2 decimal places
```

**First-Time Data Entry:**
When starting fresh (e.g., December 2024), admin enters BOTH previous (November) and current (December) readings. For subsequent months, previous reading is auto-populated from the last saved current reading.

#### Reports Dashboard

- **Financial Reports**: Monthly revenue, consumption, collection rates
- **Collections View**: List of defaulters sorted by outstanding amount
- **Payment Status**: Track paid/pending/overdue bills

## 4. Non-Goals (for Now)

For the first MVP, do not:
- Build complex role-based permissions (single admin role is fine)
- Integrate with payment gateways
- Send WhatsApp/SMS notifications
- Guarantee production-scale performance (small dataset, single-office usage is fine)
- Add AI/ML features beyond basic billing logic

See `ROADMAP.md` for future features.

## 5. Implementation Guidelines

### 5.1 Tech Stack (REQUIRED)

**Package Manager:** npm

**Frontend:**
- React 19 (with TypeScript)
- Vite (build tooling and dev server)
- Tailwind CSS (styling)
- Lucide React (icons)

**Backend-as-a-Service:**
- Supabase (PostgreSQL database, real-time subscriptions, Edge Functions if needed)

**Authentication:**
- Clerk (user authentication)

**Language:** TypeScript (strict mode preferred)

### 5.2 Project Structure

```
/
├── CLAUDE.md                          # This file
├── IMPLEMENTATION.md                  # Implementation phases
├── ROADMAP.md                         # Future features
├── README.md                          # Setup instructions
├── package.json
├── tsconfig.json
├── vite.config.ts
├── index.html
├── .env.local                         # Supabase + Clerk keys (git-ignored)
│
├── data/                              # Original JSONL (for reference/migration)
│   ├── blessings_city_billing_training.jsonl
│   └── blessings_city_master_data_with_villas.jsonl
│
├── src/
│   ├── main.tsx                       # App entry point
│   ├── App.tsx                        # Main app with routing
│   │
│   ├── types/
│   │   └── index.ts                   # TypeScript interfaces
│   │
│   ├── lib/
│   │   ├── supabase.ts                # Supabase client
│   │   └── clerk.ts                   # Clerk config
│   │
│   ├── services/
│   │   ├── unitService.ts             # Unit CRUD operations
│   │   ├── readingService.ts          # Meter reading operations
│   │   ├── billingService.ts          # Bill calculation + storage
│   │   └── analyticsService.ts        # Reports + aggregations
│   │
│   ├── components/
│   │   ├── Layout.tsx                 # App shell with navigation
│   │   ├── UnitList.tsx               # Directory view (groups + list)
│   │   ├── UnitDetail.tsx             # Single unit view
│   │   ├── PeriodSelector.tsx         # Month/year picker
│   │   ├── BillPreview.tsx            # Reading entry + bill generation
│   │   └── ReportsDashboard.tsx       # Financial reports + collections
│   │
│   └── hooks/
│       └── useUnits.ts                # Data fetching hooks
│
└── supabase/
    └── migrations/                    # Database migrations
        └── 001_initial_schema.sql
```

### 5.3 Environment Variables

```env
# .env.local
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_CLERK_PUBLISHABLE_KEY=pk_test_...
```

### 5.4 Supabase Setup

1. Create a new Supabase project
2. Run the schema migrations
3. Migrate data from JSONL files using a one-time script
4. Enable Row Level Security (RLS) if needed later

### 5.5 Coding Style & Quality

- Prefer small, pure functions with clear inputs/outputs
- Add JSDoc/TSDoc comments on public functions
- Use React hooks for data fetching (consider react-query later)
- Handle loading and error states in UI

## 6. How You (Claude) Should Work in This Repo

When the user asks you to do something in this project, follow this process:

### Understand the Request
Map the user's ask to one or more of:
- Database schema changes
- Supabase queries/operations
- Service layer functions
- Frontend component development
- Authentication setup

### Use Correct Tools
- **Package management:** `npm install`, `npm run dev`
- **Database:** Supabase dashboard or migrations
- **Dev server:** `npm run dev`

### Design Small, Composable Modules
- Start with types (`src/types/index.ts`) before building services
- Use TypeScript interfaces to make the code self-documenting
- Keep services focused (one responsibility per file)

### Explain Your Changes
When you output code, also include:
- A short explanation of what each file does
- How to run it (e.g., `npm install && npm run dev`)

## 7. Example User Stories (to Guide Design)

### Search by Flat Number
> "As an office admin, I want to type 'C8' and immediately see:
> - Block/building
> - Meter ID
> - Resident name (if available)
> - Unit type (apartment/villa)
> - Fixed charge and rate"

### Enter Readings for a Block
> "As an office admin, I select December 2024 and Block C, then:
> - Enter the motor reading (previous + current)
> - Enter each flat's reading (previous + current)
> - Click 'Generate Bills' to calculate all bills at once
> - See the generated bills with breakdowns"

### First-Time Data Entry
> "As an office admin starting in December:
> - I enter November readings as 'previous'
> - I enter December readings as 'current'
> - System calculates consumption and generates December bills
> - For January, previous readings auto-populate from December"

### View Defaulters
> "As an office admin, I go to Collections view and see:
> - All units with unpaid bills
> - Sorted by total outstanding amount
> - How many months each unit is overdue
> - Quick action to view unit details"

## 8. Priorities

If you are unsure what to implement next, prioritize in this order:

1. Supabase setup + schema migration
2. Migrate units data from JSONL to Supabase
3. Clerk authentication integration
4. Connect existing UI components to Supabase
5. Replace localStorage with Supabase for readings/bills
6. Reports dashboard with real data
7. README with setup instructions
