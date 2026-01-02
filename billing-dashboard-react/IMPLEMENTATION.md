# Implementation Plan — Blessings Electric Billing AI MVP

> Status note: this is a frontend implementation plan/prototype document.
> The current working backend + schema are defined in the repo root `README.md`, `SUPABASE_SETUP.md`, and `database/supabase_schema.sql`.
> This plan mentions **Clerk**, but the current Python app uses **Auth0** (optional) and does not depend on Clerk.

## Current State

The app currently has:
- Working React + Vite + Tailwind frontend
- UI components for Directory, Billing, and Reports
- Billing calculation logic (correct formula)
- Data parsing from JSONL (hardcoded in mockData.ts)
- localStorage for temporary reading persistence

**What's Missing:**
- Backend/database (will use Supabase)
- Authentication (will use Clerk)
- Real data persistence
- Data migration from JSONL to database

---

## Reference: Data Schema

### Unit Types & Fixed Charges

| Type | Fixed Charge | Notes |
|------|--------------|-------|
| 2BHK Flat | ₹1,474 | Has shared water motor |
| 4BHK Flat | ₹1,890 | Has shared water motor |
| 5BHK Flat | ₹2,311 | Has shared water motor |
| Villa | ₹1,857 | No shared water motor |
| SCO | ₹2,157 | Commercial, no shared motor |

### Water Motors (6 total)

| Motor ID | Meter No. | Serves Blocks |
|----------|-----------|---------------|
| MOTOR-B | 87923504 | B5, B6, B17, B18 (12 flats) |
| MOTOR-C | 86729933 | C8-C17 (24 flats) |
| MOTOR-D1 | 90199696 | D1-D4 (12 flats) |
| MOTOR-D2 | 19152168 | D6-D11 (18 flats) |
| MOTOR-F1 | 86729926 | F2-F6, F19-F23 (30 flats) |
| MOTOR-F2 | 97701102 | F7-F10, F15-F18 (24 flats) |

### Billing Formula

```
Final Bill = (Flat Units + Water Motor Share) × ₹12 + Fixed Charge

Where:
- Water Motor Share = (Motor Units ÷ Total Block Units) × Flat Units
- Round to 2 decimal places
```

### Summary Statistics

- **Total units:** 147 entries
  - 120 flats (2BHK, 4BHK, 5BHK across GF/FF/SF)
  - 6 water motors
  - 11 villas
  - 9 SCO units
- **Rate per unit:** ₹12 (universal)

---

## Phase 1: Supabase Setup

### 1.1 Create Supabase Project
- [ ] Create new project at supabase.com
- [ ] Note down project URL and anon key
- [ ] Create `.env.local` with credentials

```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

### 1.2 Database Schema

Run in Supabase SQL Editor:

```sql
-- Units table (will be populated from JSONL)
CREATE TABLE units (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  unit_id TEXT UNIQUE NOT NULL,
  unit_type TEXT NOT NULL CHECK (unit_type IN ('apartment', 'villa', 'sco', 'motor')),
  bhk_type TEXT CHECK (bhk_type IN ('2BHK', '4BHK', '5BHK') OR bhk_type IS NULL),
  flat_no TEXT NOT NULL,
  floor TEXT CHECK (floor IN ('GF', 'FF', 'SF') OR floor IS NULL),
  client_name TEXT,
  meter_no TEXT,
  fixed_charge NUMERIC NOT NULL,
  rate_per_unit NUMERIC DEFAULT 12,
  water_motor_meter_no TEXT,
  phone TEXT,
  email TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Meter readings table
CREATE TABLE readings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  unit_id TEXT NOT NULL REFERENCES units(unit_id) ON DELETE CASCADE,
  period TEXT NOT NULL,
  previous_reading NUMERIC NOT NULL,
  current_reading NUMERIC NOT NULL,
  consumption NUMERIC GENERATED ALWAYS AS (current_reading - previous_reading) STORED,
  reading_date DATE DEFAULT CURRENT_DATE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(unit_id, period)
);

-- Bills table
CREATE TABLE bills (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  unit_id TEXT NOT NULL REFERENCES units(unit_id) ON DELETE CASCADE,
  period TEXT NOT NULL,
  flat_consumption NUMERIC NOT NULL,
  motor_consumption NUMERIC,
  total_block_consumption NUMERIC,
  water_motor_share NUMERIC DEFAULT 0,
  total_units NUMERIC NOT NULL,
  usage_charge NUMERIC NOT NULL,
  fixed_charge NUMERIC NOT NULL,
  total_amount NUMERIC NOT NULL,
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'overdue')),
  breakdown JSONB,
  generated_at TIMESTAMPTZ DEFAULT NOW(),
  paid_at TIMESTAMPTZ,
  UNIQUE(unit_id, period)
);

-- Indexes for common queries
CREATE INDEX idx_units_unit_type ON units(unit_type);
CREATE INDEX idx_units_water_motor ON units(water_motor_meter_no);
CREATE INDEX idx_readings_period ON readings(period);
CREATE INDEX idx_bills_period ON bills(period);
CREATE INDEX idx_bills_status ON bills(status);
```

### 1.3 Install Supabase Client

```bash
npm install @supabase/supabase-js
```

### 1.4 Create Supabase Client

Create `src/lib/supabase.ts`:

```typescript
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
```

---

## Phase 2: Data Migration

### 2.1 Create Migration Script

Create `scripts/migrate-data.ts`:

```typescript
// One-time script to migrate JSONL data to Supabase
// Uses existing parsing logic from dataService.ts
// Run with: npx ts-node scripts/migrate-data.ts
```

Key steps:
- Read JSONL from `data/blessings_city_master_data_with_villas.jsonl`
- Parse each line using existing logic
- Insert into Supabase `units` table
- Include motors (needed for water share calculation)

### 2.2 Run Migration

```bash
npx ts-node scripts/migrate-data.ts
```

### 2.3 Verify Data

- [ ] Check Supabase Table Editor
- [ ] Confirm ~147 units imported (including motors)
- [ ] Verify all fields populated correctly
- [ ] Test a few queries in SQL Editor

---

## Phase 3: Clerk Authentication

### 3.1 Create Clerk Application
- [ ] Sign up at clerk.com
- [ ] Create new application
- [ ] Get publishable key
- [ ] Add to `.env.local`:

```env
VITE_CLERK_PUBLISHABLE_KEY=pk_test_...
```

### 3.2 Install Clerk

```bash
npm install @clerk/clerk-react
```

### 3.3 Setup Clerk Provider

Update `src/main.tsx`:

```typescript
import { ClerkProvider } from '@clerk/clerk-react';

const PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

ReactDOM.createRoot(document.getElementById('root')!).render(
  <ClerkProvider publishableKey={PUBLISHABLE_KEY}>
    <App />
  </ClerkProvider>
);
```

### 3.4 Protect Routes

Update `src/App.tsx`:

```typescript
import { SignedIn, SignedOut, SignInButton, UserButton } from '@clerk/clerk-react';

function App() {
  return (
    <>
      <SignedOut>
        <div className="login-page">
          <SignInButton />
        </div>
      </SignedOut>
      <SignedIn>
        {/* Existing app content */}
        <Layout>...</Layout>
      </SignedIn>
    </>
  );
}
```

---

## Phase 4: Connect Services to Supabase

### 4.1 Update Unit Service

Rewrite `src/services/unitService.ts`:

```typescript
import { supabase } from '../lib/supabase';
import { Unit } from '../types';

export async function loadUnits(): Promise<Unit[]> {
  const { data, error } = await supabase
    .from('units')
    .select('*')
    .neq('unit_type', 'motor')
    .order('unit_id');

  if (error) throw error;
  return data;
}

export async function searchUnits(query: string): Promise<Unit[]> {
  const { data, error } = await supabase
    .from('units')
    .select('*')
    .neq('unit_type', 'motor')
    .or(`unit_id.ilike.%${query}%,client_name.ilike.%${query}%,flat_no.ilike.%${query}%,meter_no.ilike.%${query}%`);

  if (error) throw error;
  return data;
}

export async function getUnitsByMotor(motorMeterNo: string): Promise<Unit[]> {
  const { data, error } = await supabase
    .from('units')
    .select('*')
    .eq('water_motor_meter_no', motorMeterNo)
    .neq('unit_type', 'motor');

  if (error) throw error;
  return data;
}
```

### 4.2 Create Reading Service

Create `src/services/readingService.ts`:

```typescript
import { supabase } from '../lib/supabase';
import { MeterReading } from '../types';

export async function saveReadings(readings: Omit<MeterReading, 'id' | 'consumption'>[]): Promise<void> {
  const { error } = await supabase
    .from('readings')
    .upsert(readings, { onConflict: 'unit_id,period' });

  if (error) throw error;
}

export async function getReadingsForPeriod(period: string): Promise<MeterReading[]> {
  const { data, error } = await supabase
    .from('readings')
    .select('*')
    .eq('period', period);

  if (error) throw error;
  return data || [];
}

export async function getLastReading(unitId: string): Promise<MeterReading | null> {
  const { data, error } = await supabase
    .from('readings')
    .select('*')
    .eq('unit_id', unitId)
    .order('period', { ascending: false })
    .limit(1)
    .single();

  if (error && error.code !== 'PGRST116') throw error;
  return data;
}

export async function getPreviousReading(unitId: string, currentPeriod: string): Promise<number | null> {
  const [year, month] = currentPeriod.split('-').map(Number);
  const prevMonth = month === 1 ? 12 : month - 1;
  const prevYear = month === 1 ? year - 1 : year;
  const prevPeriod = `${prevYear}-${String(prevMonth).padStart(2, '0')}`;

  const { data } = await supabase
    .from('readings')
    .select('current_reading')
    .eq('unit_id', unitId)
    .eq('period', prevPeriod)
    .single();

  return data?.current_reading ?? null;
}
```

### 4.3 Update Billing Service

Update `src/services/billingService.ts` to add persistence:

```typescript
import { supabase } from '../lib/supabase';
import { Bill } from '../types';

// Keep existing generateBillPreview function (calculation logic)

export async function saveBills(bills: Omit<Bill, 'id'>[]): Promise<void> {
  const { error } = await supabase
    .from('bills')
    .upsert(bills, { onConflict: 'unit_id,period' });

  if (error) throw error;
}

export async function getBillsForPeriod(period: string): Promise<Bill[]> {
  const { data, error } = await supabase
    .from('bills')
    .select('*, units(*)')
    .eq('period', period);

  if (error) throw error;
  return data || [];
}

export async function getBillsForUnit(unitId: string): Promise<Bill[]> {
  const { data, error } = await supabase
    .from('bills')
    .select('*')
    .eq('unit_id', unitId)
    .order('period', { ascending: false });

  if (error) throw error;
  return data || [];
}

export async function updateBillStatus(billId: string, status: 'pending' | 'paid' | 'overdue'): Promise<void> {
  const { error } = await supabase
    .from('bills')
    .update({
      status,
      paid_at: status === 'paid' ? new Date().toISOString() : null
    })
    .eq('id', billId);

  if (error) throw error;
}

export async function getUnpaidBills(): Promise<Bill[]> {
  const { data, error } = await supabase
    .from('bills')
    .select('*, units(*)')
    .neq('status', 'paid')
    .order('total_amount', { ascending: false });

  if (error) throw error;
  return data || [];
}
```

---

## Phase 5: Update UI Components

### 5.1 Update App.tsx

- [ ] Add loading state while fetching units
- [ ] Fetch units from Supabase on mount
- [ ] Handle errors gracefully
- [ ] Add Clerk UserButton to header

### 5.2 Update BillPreview.tsx

Replace localStorage with Supabase:

- [ ] On mount: Fetch existing readings for the period from Supabase
- [ ] Auto-populate previous readings from last period's current readings
- [ ] On generate: Save readings to `readings` table
- [ ] On generate: Save bills to `bills` table
- [ ] Remove all localStorage calls

### 5.3 Update UnitDetail.tsx

- [ ] Fetch real billing history from `bills` table
- [ ] Calculate outstanding dues from actual unpaid bills
- [ ] Remove mock data generation (`getUnitBillingHistory`)

### 5.4 Update ReportsDashboard.tsx

- [ ] Fetch real bills for selected period from Supabase
- [ ] Calculate actual revenue from `bills` table
- [ ] Calculate real collection rates (paid vs total)
- [ ] Defaulters list from actual unpaid bills

---

## Phase 6: Auto-Populate Previous Readings

### 6.1 Logic

When entering readings for a period:

1. Check if previous period has readings in database
2. If yes: Auto-fill previous reading field (read-only)
3. If no: Allow manual entry (first-time scenario)

### 6.2 Implementation in BillPreview.tsx

```typescript
useEffect(() => {
  async function loadPreviousReadings() {
    for (const unit of blockUnits) {
      const prevReading = await getPreviousReading(unit.unit_id, currentPeriod);
      if (prevReading !== null) {
        setFlatReadings(prev => ({
          ...prev,
          [unit.unit_id]: { ...prev[unit.unit_id], previous: prevReading, previousLocked: true }
        }));
      }
    }
  }
  loadPreviousReadings();
}, [blockUnits, currentPeriod]);
```

---

## Phase 7: Cleanup & Polish

### 7.1 Remove Unused Files

- [ ] Delete `src/services/mockData.ts`
- [ ] Delete `src/services/dataService.ts` (replaced by unitService)
- [ ] Remove localStorage keys and related code

### 7.2 Error Handling

- [ ] Add toast notifications (success/error feedback)
- [ ] Handle network errors gracefully
- [ ] Show loading spinners during async operations
- [ ] Validate readings before submission

### 7.3 Testing Scenarios

- [ ] Login/logout flow with Clerk
- [ ] Search units by name, flat number, meter
- [ ] View unit details with real billing history
- [ ] First-time reading entry (manual prev + current)
- [ ] Subsequent reading entry (prev auto-filled)
- [ ] Generate bills for entire block
- [ ] View generated bills with breakdown
- [ ] Mark bill as paid
- [ ] View monthly financial reports
- [ ] View defaulters list

### 7.4 Update README.md

- [ ] Setup instructions for Supabase
- [ ] Setup instructions for Clerk
- [ ] Environment variables list
- [ ] How to run locally
- [ ] How to run migration script

---

## Files to Change

| File | Action | Description |
|------|--------|-------------|
| `.env.local` | Create | Supabase + Clerk keys |
| `src/lib/supabase.ts` | Create | Supabase client |
| `src/main.tsx` | Modify | Add ClerkProvider |
| `src/App.tsx` | Modify | Add auth guards, async loading |
| `src/types/index.ts` | Create | Move types here |
| `src/services/unitService.ts` | Rewrite | Supabase queries |
| `src/services/readingService.ts` | Create | Reading CRUD |
| `src/services/billingService.ts` | Modify | Add Supabase persistence |
| `src/services/dataService.ts` | Delete | Replaced by unitService |
| `src/services/mockData.ts` | Delete | No longer needed |
| `src/components/BillPreview.tsx` | Modify | Supabase instead of localStorage |
| `src/components/UnitDetail.tsx` | Modify | Real billing history |
| `src/components/ReportsDashboard.tsx` | Modify | Real analytics |
| `scripts/migrate-data.ts` | Create | One-time migration |
| `README.md` | Update | Setup instructions |

---

## Dependencies to Add

```bash
npm install @supabase/supabase-js @clerk/clerk-react
```

---

## Notes

- Keep existing UI components — they're well-designed
- Keep existing billing calculation logic — it's correct
- Motors stay in database but are filtered from UI display
- Motors are used for water share calculation
- localStorage removal happens after Supabase is fully connected
