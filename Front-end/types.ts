
export type UnitType = 'apartment' | 'villa' | 'sco' | 'motor';
export type Floor = 'GF' | 'FF' | 'SF' | null;
export type BHKType = '2BHK' | '4BHK' | '5BHK' | null;
export type BillStatus = 'Paid' | 'Pending' | 'Overdue';

export interface Unit {
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
  // Essential additions for billing context
  last_reading?: number;
  last_reading_date?: string;
  last_bill_amount?: number;
  last_bill_status?: BillStatus;
}

export interface BillPreview {
  unit_id: string;
  unit_type: UnitType;
  flat_no: string;
  floor: Floor;
  bhk_type: BHKType;
  period: string;
  flat_consumption: number;
  motor_consumption?: number;
  total_block_consumption?: number;
  water_motor_share: number;
  total_units: number;
  usage_charge: number;
  fixed_charge: number;
  total_bill: number;
  current_reading: number;
  previous_reading: number;
  rate_per_unit: number;
  breakdown: string[];
}

export interface BillingCalculationInput {
  currentFlatReading: number;
  previousFlatReading: number;
  currentMotorReading?: number;
  previousMotorReading?: number;
  totalBlockConsumption?: number;
}

// Analytics Types
export interface MonthlyReportItem {
  unit: Unit;
  consumption: number;
  billAmount: number;
  status: BillStatus;
  generatedDate: string;
}

export interface MonthlyReport {
  year: number;
  monthIndex: number;
  monthName: string;
  totalRevenue: number;
  totalConsumption: number;
  totalCollected: number;
  totalPending: number;
  collectionRate: number;
  topConsumer: MonthlyReportItem | null;
  items: MonthlyReportItem[];
}

// Ledger Types
export interface BillingHistoryItem {
  month: string;
  year: number;
  amount: number;
  status: BillStatus;
  consumption: number;
  generatedDate: string;
}
