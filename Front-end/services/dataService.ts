
import { Unit, UnitType, Floor, BHKType, BillStatus, BillingHistoryItem } from '../types';
import { MASTER_DATA_JSONL } from './mockData';

const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June', 
  'July', 'August', 'September', 'October', 'November', 'December'
];

// Helper to generate consistent pseudo-random numbers based on string seed
const seededRandom = (seed: string) => {
  let h = 0xdeadbeef;
  for (let i = 0; i < seed.length; i++)
    h = Math.imul(h ^ seed.charCodeAt(i), 2654435761);
  return ((h ^ h >>> 17) >>> 0) / 4294967296;
};

export const loadMasterData = (): Unit[] => {
  const lines = MASTER_DATA_JSONL.trim().split('\n');
  const units: Unit[] = [];

  lines.forEach(line => {
    if (!line.trim()) return;
    try {
      const entry = JSON.parse(line);
      const outputText = entry.output;
      const unit = parseUnitOutput(outputText);
      if (unit && unit.unit_type !== 'motor') {
        units.push(unit);
      }
    } catch (e) {
      console.warn("Failed to parse line", line, e);
    }
  });

  return units;
};

const cleanPhoneNumber = (raw: string | undefined): string | undefined => {
  if (!raw || !raw.trim() || raw.trim().toLowerCase() === 'nan') return undefined;
  
  // Remove .0 suffix (floating point artifact)
  let cleaned = raw.trim().replace(/\.0+$/, '');
  
  // Remove any non-digit characters except +
  cleaned = cleaned.replace(/[^\d+]/g, '');

  if (!cleaned) return undefined;

  // Format Indian numbers starting with 91 (12 digits)
  // Example: 918288860588 -> +91 82888 60588
  if (cleaned.length === 12 && cleaned.startsWith('91')) {
    return `+91 ${cleaned.substring(2, 7)} ${cleaned.substring(7)}`;
  }
  
  // Format standard 10 digit Indian numbers (add +91 if missing)
  if (cleaned.length === 10 && /^[6-9]\d{9}$/.test(cleaned)) {
    return `+91 ${cleaned.substring(0, 5)} ${cleaned.substring(5)}`;
  }

  return cleaned;
};

const cleanMeterNumber = (raw: string | undefined): string => {
  if (!raw || raw.trim().toLowerCase() === 'nan') return '';
  return raw.replace(/\.0+$/, '').trim();
};

const cleanFlatNumber = (raw: string | undefined): string => {
  if (!raw) return '';
  // Fix artifacts like "B5, B6-nan" or just "nan"
  let cleaned = raw.replace(/-nan/g, '').replace(/nan/g, '');
  return cleaned.trim();
};

const parseUnitOutput = (text: string): Unit | null => {
  const lines = text.split('\n');
  const data: Record<string, string> = {};

  lines.forEach(l => {
    const parts = l.split(': ');
    if (parts.length >= 2) {
      const key = parts[0].trim();
      const value = parts.slice(1).join(': ').trim();
      data[key] = value;
    }
  });

  const unitId = data['Unit_ID'];
  if (!unitId) return null;

  let unitType: UnitType = 'apartment';
  let bhkType: BHKType = null;
  
  if (unitId.startsWith('VILLA')) {
    unitType = 'villa';
  } else if (unitId.startsWith('SCO')) {
    unitType = 'sco';
  } else if (unitId.startsWith('MOTOR')) {
    unitType = 'motor';
  } else {
    // Apartments usually start with 2BHK, 4BHK etc
    if (unitId.includes('2BHK')) bhkType = '2BHK';
    else if (unitId.includes('4BHK')) bhkType = '4BHK';
    else if (unitId.includes('5BHK')) bhkType = '5BHK';
  }

  // Parse floor
  let floor: Floor = null;
  const rawFloor = data['Floor'];
  if (rawFloor === 'GF') floor = 'GF';
  else if (rawFloor === 'FF') floor = 'FF';
  else if (rawFloor === 'SF') floor = 'SF';

  // Parse currency
  const fixedChargeStr = data['Fixed Charge']?.replace('₹', '') || '0';
  const rateStr = data['Rate Per Unit']?.replace('₹', '') || '12';

  // --- MOCK DATA GENERATION FOR ESSENTIAL FIELDS ---
  // We use the unitId as a seed to ensure data persists across reloads for the same unit
  const seed = seededRandom(unitId);
  const lastReading = Math.floor(1000 + (seed * 20000));
  const lastBillAmount = Math.floor(fixedChargeStr ? parseFloat(fixedChargeStr) + (seed * 1500) : 2000);
  
  const statuses: BillStatus[] = ['Paid', 'Paid', 'Paid', 'Pending', 'Overdue'];
  const statusIndex = Math.floor(seed * statuses.length);
  const lastStatus = statuses[statusIndex];

  return {
    unit_id: unitId,
    unit_type: unitType,
    bhk_type: bhkType,
    flat_no: cleanFlatNumber(data['Flat no']),
    floor: floor,
    client_name: data['Client Name'] || '',
    meter_no: cleanMeterNumber(data['Meter No.']),
    fixed_charge: parseFloat(fixedChargeStr),
    rate_per_unit: parseFloat(rateStr),
    water_motor_meter_no: cleanMeterNumber(data['Water Motor Meter No']),
    phone: cleanPhoneNumber(data['Phone Number']),
    email: data['Email'],
    // Essential Mock Data
    last_reading: lastReading,
    last_reading_date: 'Oct 01, 2024',
    last_bill_amount: lastBillAmount,
    last_bill_status: lastStatus
  };
};

export const searchUnits = (units: Unit[], query: string): Unit[] => {
  const lowerQuery = query.toLowerCase();
  return units.filter(u => 
    u.unit_id.toLowerCase().includes(lowerQuery) ||
    u.client_name.toLowerCase().includes(lowerQuery) ||
    u.flat_no.toLowerCase().includes(lowerQuery) ||
    u.meter_no.includes(lowerQuery)
  );
};

export const getUnitById = (units: Unit[], id: string): Unit | undefined => {
  return units.find(u => u.unit_id === id);
};

export const getUnitsByMotor = (units: Unit[], motorNumber: string): Unit[] => {
  if (!motorNumber || motorNumber === 'nan') return [];
  // Return all units sharing this motor
  return units.filter(u => u.water_motor_meter_no === motorNumber);
};

// --- LEDGER / HISTORY SERVICE ---

export const getUnitBillingHistory = (unit: Unit): BillingHistoryItem[] => {
    const history: BillingHistoryItem[] = [];
    const today = new Date();
    
    // Generate last 6 months
    for (let i = 0; i < 6; i++) {
        const d = new Date(today.getFullYear(), today.getMonth() - i, 1);
        const monthIndex = d.getMonth();
        const year = d.getFullYear();
        
        // Use a unique seed per month per unit
        const seedStr = `${unit.unit_id}-${year}-${monthIndex}`;
        const rand = seededRandom(seedStr);
        
        // Consumption Simulation
        const consumption = Math.floor(100 + (rand * 700));
        const amount = Math.floor((consumption * unit.rate_per_unit) + unit.fixed_charge);
        
        // Status Simulation
        // We create "Defaulter Profiles" based on the unit ID hash
        const unitReliability = seededRandom(unit.unit_id + "reliability"); // 0.0 to 1.0
        
        let status: BillStatus = 'Paid';
        
        // Profile A: Reliable (80% of units) -> almost always pays
        // Profile B: Forgetful (10% of units) -> pays late
        // Profile C: Defaulter (10% of units) -> misses last 3 months
        
        if (unitReliability < 0.1) {
            // Defaulter: Misses recent months
            if (i < 3) status = 'Overdue'; // Last 3 months overdue
            else if (i < 4) status = 'Pending';
            else status = 'Paid';
        } else if (unitReliability < 0.3) {
             // Forgetful: Random pending
             status = rand > 0.5 ? 'Paid' : (i === 0 ? 'Pending' : 'Overdue');
        } else {
             // Reliable: Mostly paid, maybe current month pending
             if (i === 0) status = 'Pending';
             else status = 'Paid';
        }
        
        history.push({
            month: MONTH_NAMES[monthIndex],
            year: year,
            amount: amount,
            status: status,
            consumption: consumption,
            generatedDate: `${year}-${String(monthIndex + 1).padStart(2, '0')}-01`
        });
    }
    
    return history;
};

export const calculateOutstandingDues = (history: BillingHistoryItem[]): number => {
    return history
        .filter(item => item.status !== 'Paid')
        .reduce((sum, item) => sum + item.amount, 0);
};
