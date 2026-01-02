import { Unit, BillPreview, BillingCalculationInput } from '../types';

export const generateBillPreview = (
  unit: Unit,
  input: BillingCalculationInput,
  billingDate: Date = new Date()
): BillPreview => {
  const breakdown: string[] = [];
  const flatConsumption = input.currentFlatReading - input.previousFlatReading;
  
  let waterMotorShare = 0;
  let calculationNote = "";

  // 1. Calculate Water Motor Share
  if (unit.unit_type === 'apartment' && unit.water_motor_meter_no) {
    if (input.currentMotorReading !== undefined && 
        input.previousMotorReading !== undefined && 
        input.totalBlockConsumption !== undefined && 
        input.totalBlockConsumption > 0) {
      
      const motorConsumption = input.currentMotorReading - input.previousMotorReading;
      
      // Formula: (Motor Units / Total Block Units) * Flat Units
      const rawShare = (motorConsumption / input.totalBlockConsumption) * flatConsumption;
      waterMotorShare = parseFloat(rawShare.toFixed(2));
      
      calculationNote = `Water Motor Share = (${motorConsumption} ÷ ${input.totalBlockConsumption}) × ${flatConsumption} = ${waterMotorShare} units`;
      breakdown.push(`Step 1: Calculate Water Motor Share`);
      breakdown.push(calculationNote);
    } else {
        breakdown.push(`Step 1: Water Motor Share skipped (Missing motor readings or zero block consumption)`);
    }
  } else {
    breakdown.push(`Step 1: No Water Motor Share (Not an apartment or no motor assigned)`);
  }

  // 2. Total Units
  const totalUnits = parseFloat((flatConsumption + waterMotorShare).toFixed(2));
  breakdown.push(`Step 2: Calculate Total Units`);
  breakdown.push(`Total Units = Flat Units (${flatConsumption}) + Water Motor Share (${waterMotorShare}) = ${totalUnits} units`);

  // 3. Usage Charge
  const usageCharge = parseFloat((totalUnits * unit.rate_per_unit).toFixed(2));
  breakdown.push(`Step 3: Calculate Usage Charge`);
  breakdown.push(`Usage Charge = ${totalUnits} × ₹${unit.rate_per_unit} = ₹${usageCharge.toLocaleString('en-IN')}`);

  // 4. Fixed Charge
  const fixedCharge = unit.fixed_charge;
  breakdown.push(`Step 4: Add Fixed Charge`);
  breakdown.push(`Fixed Charge (${unit.bhk_type || unit.unit_type}) = ₹${fixedCharge.toLocaleString('en-IN')}`);

  // 5. Final Bill
  const finalBill = parseFloat((usageCharge + fixedCharge).toFixed(2));
  breakdown.push(`Step 5: Final Bill Calculation`);
  breakdown.push(`Final Bill = ₹${usageCharge.toLocaleString('en-IN')} + ₹${fixedCharge.toLocaleString('en-IN')} = ₹${finalBill.toLocaleString('en-IN')}`);

  const period = `${billingDate.toLocaleString('default', { month: 'long' })} ${billingDate.getFullYear()}`;

  return {
    unit_id: unit.unit_id,
    unit_type: unit.unit_type,
    flat_no: unit.flat_no,
    floor: unit.floor,
    bhk_type: unit.bhk_type,
    current_reading: input.currentFlatReading,
    previous_reading: input.previousFlatReading,
    rate_per_unit: unit.rate_per_unit,
    period: period,
    flat_consumption: flatConsumption,
    motor_consumption: (input.currentMotorReading && input.previousMotorReading) ? (input.currentMotorReading - input.previousMotorReading) : undefined,
    total_block_consumption: input.totalBlockConsumption,
    water_motor_share: waterMotorShare,
    total_units: totalUnits,
    usage_charge: usageCharge,
    fixed_charge: fixedCharge,
    total_bill: finalBill,
    breakdown: breakdown
  };
};