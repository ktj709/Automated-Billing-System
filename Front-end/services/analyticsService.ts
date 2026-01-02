
import { Unit, MonthlyReport, MonthlyReportItem, BillStatus } from '../types';

// Deterministic random generator based on string seed
const seededRandom = (seed: string) => {
  let h = 0xdeadbeef;
  for (let i = 0; i < seed.length; i++)
    h = Math.imul(h ^ seed.charCodeAt(i), 2654435761);
  return ((h ^ h >>> 17) >>> 0) / 4294967296;
};

const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

export const generateMonthlyReport = (
  units: Unit[], 
  year: number, 
  monthIndex: number
): MonthlyReport => {
  const items: MonthlyReportItem[] = [];
  
  // Filter out motors for the report overview, only keep billable units
  const billableUnits = units.filter(u => u.unit_type !== 'motor');
  
  let totalRevenue = 0;
  let totalConsumption = 0;
  let totalCollected = 0;
  let totalPending = 0;

  billableUnits.forEach(unit => {
    // Create a unique seed for this unit + date combo
    const seedStr = `${unit.unit_id}-${year}-${monthIndex}`;
    const rand = seededRandom(seedStr);
    
    // Simulate Data
    // Consumption varies between 100 and 800 units based on random seed
    const consumption = Math.floor(100 + (rand * 700));
    
    const usageCost = consumption * unit.rate_per_unit;
    const totalBill = usageCost + unit.fixed_charge;
    
    // Simulate Status: 75% chance of being Paid
    // We modify the seed slightly for status so it's not directly correlated to consumption
    const statusRand = seededRandom(seedStr + "_status");
    let status: BillStatus = 'Pending';
    
    // Make past months more likely to be paid
    const isPast = new Date().getTime() > new Date(year, monthIndex + 1, 1).getTime();
    
    if (isPast) {
       status = statusRand > 0.15 ? 'Paid' : 'Overdue';
    } else {
       status = statusRand > 0.6 ? 'Paid' : 'Pending';
    }

    // Accumulate Stats
    totalRevenue += totalBill;
    totalConsumption += consumption;
    
    if (status === 'Paid') {
        totalCollected += totalBill;
    } else {
        totalPending += totalBill;
    }

    items.push({
      unit,
      consumption,
      billAmount: totalBill,
      status,
      generatedDate: `${year}-${String(monthIndex + 1).padStart(2, '0')}-01`
    });
  });

  // Find Top Consumer
  const topConsumer = items.length > 0 
    ? items.reduce((prev, current) => (prev.consumption > current.consumption) ? prev : current)
    : null;

  return {
    year,
    monthIndex,
    monthName: MONTH_NAMES[monthIndex],
    totalRevenue,
    totalConsumption,
    totalCollected,
    totalPending,
    collectionRate: totalRevenue > 0 ? (totalCollected / totalRevenue) * 100 : 0,
    topConsumer,
    items
  };
};
