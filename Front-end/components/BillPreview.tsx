import React, { useState, useEffect, useMemo } from 'react';
import { Unit, BillPreview as BillPreviewType } from '../types';
import { generateBillPreview } from '../services/billingService';
import { getUnitsByMotor, getUnitBillingHistory } from '../services/dataService';
import { Calculator, FileText, ArrowLeft, Download, RefreshCw, Zap, Droplets, ChevronDown, ChevronUp, Sparkles, CheckCircle2, Calendar, AlertCircle, AlertTriangle } from 'lucide-react';

interface BillPreviewProps {
  unit: Unit;
  units: Unit[];
  customUnits?: Unit[];
  groupName?: string;
  onBack: () => void;
  // New props for date context
  billingYear: number;
  billingMonth: number;
}

interface ReadingInput {
  current: number | '';
  previous: number | '';
}

const STORAGE_KEY_FLATS = 'blessings_flat_readings';
const STORAGE_KEY_MOTORS = 'blessings_motor_readings';

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June', 
  'July', 'August', 'September', 'October', 'November', 'December'
];

// Micro Sparkline Component for Data Visualization
const ConsumptionSparkline = ({ unit }: { unit: Unit | undefined }) => {
  const history = useMemo(() => {
    if (!unit) return [];
    // Get history, reverse to show chronological order (oldest -> newest) for the chart
    return getUnitBillingHistory(unit).slice(0, 6).reverse(); 
  }, [unit]);

  if (!history || history.length < 2) return null;

  const values = history.map(h => h.consumption);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const height = 40;
  const width = 200;

  const points = values.map((val, i) => {
    const x = (i / (values.length - 1)) * width;
    const normalizedVal = (val - min) / range;
    const y = height - (normalizedVal * height) + 5; // +5 padding top
    return `${x},${y}`;
  }).join(' ');

  return (
    <div className="mt-6 mb-2 p-4 bg-zinc-50/50 rounded-xl border border-zinc-100">
      <div className="flex justify-between items-end mb-4">
        <div>
           <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider block">6-Month Trend</span>
           <span className="text-xs font-medium text-zinc-600">Consumption Pattern</span>
        </div>
        <div className="flex gap-3">
             <div className="text-right">
                <span className="text-[10px] text-zinc-400 block">Low</span>
                <span className="text-xs font-mono font-medium">{min}</span>
             </div>
             <div className="text-right">
                <span className="text-[10px] text-zinc-400 block">High</span>
                <span className="text-xs font-mono font-medium">{max}</span>
             </div>
        </div>
      </div>
      <div className="relative h-14 w-full">
        <svg viewBox={`0 0 ${width} ${height + 10}`} className="w-full h-full overflow-visible preserve-3d">
          <defs>
            <linearGradient id="gradient" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor="currentColor" stopOpacity="0.1"/>
              <stop offset="100%" stopColor="currentColor" stopOpacity="0"/>
            </linearGradient>
          </defs>
          <polyline 
             points={points} 
             fill="none" 
             stroke="#000" 
             strokeWidth="2" 
             strokeLinecap="round" 
             strokeLinejoin="round"
             className="drop-shadow-sm"
          />
          {values.map((val, i) => {
               const x = (i / (values.length - 1)) * width;
               const normalizedVal = (val - min) / range;
               const y = height - (normalizedVal * height) + 5;
               return (
                   <g key={i} className="group/point">
                     <circle cx={x} cy={y} r="3" className="fill-white stroke-black stroke-2 hover:r-4 transition-all" />
                     {/* Tooltip hint purely via SVG/CSS positioning is tricky without JS hover state, sticking to visual cue */}
                   </g>
               );
          })}
        </svg>
      </div>
    </div>
  );
};

export const BillPreview: React.FC<BillPreviewProps> = ({ 
  unit, 
  units, 
  customUnits, 
  groupName, 
  onBack,
  billingYear,
  billingMonth
}) => {
  const blockUnits = useMemo(() => {
    if (customUnits && customUnits.length > 0) return customUnits;
    if (unit.unit_type === 'apartment' && unit.water_motor_meter_no && unit.water_motor_meter_no !== 'nan') {
      return getUnitsByMotor(units, unit.water_motor_meter_no);
    }
    return [unit];
  }, [unit, units, customUnits]);

  const hasSharedMotor = useMemo(() => {
    if (blockUnits.length === 0) return false;
    const firstMotor = blockUnits[0].water_motor_meter_no;
    if (!firstMotor || firstMotor === 'nan') return false;
    return blockUnits.every(u => u.water_motor_meter_no === firstMotor);
  }, [blockUnits]);

  const isBatchMode = blockUnits.length > 1;

  const [flatReadings, setFlatReadings] = useState<Record<string, ReadingInput>>({});
  const [motorReading, setMotorReading] = useState<ReadingInput>({ current: '', previous: '' });
  const [generatedBills, setGeneratedBills] = useState<BillPreviewType[]>([]);
  const [expandedBillId, setExpandedBillId] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  
  // Anomaly Detection State
  const [averages, setAverages] = useState<Record<string, number>>({});
  const [anomalies, setAnomalies] = useState<Record<string, string>>({});

  // Persistence logic
  const saveFlatReading = (unitId: string, reading: ReadingInput) => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY_FLATS);
      const parsed = saved ? JSON.parse(saved) : {};
      parsed[unitId] = reading;
      localStorage.setItem(STORAGE_KEY_FLATS, JSON.stringify(parsed));
    } catch (e) {}
  };

  const saveMotorReading = (motorId: string, reading: ReadingInput) => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY_MOTORS);
      const parsed = saved ? JSON.parse(saved) : {};
      parsed[motorId] = reading;
      localStorage.setItem(STORAGE_KEY_MOTORS, JSON.stringify(parsed));
    } catch (e) {}
  };

  useEffect(() => {
    let savedFlats: Record<string, ReadingInput> = {};
    let savedMotors: Record<string, ReadingInput> = {};
    try {
        const sf = localStorage.getItem(STORAGE_KEY_FLATS);
        if (sf) savedFlats = JSON.parse(sf);
        const sm = localStorage.getItem(STORAGE_KEY_MOTORS);
        if (sm) savedMotors = JSON.parse(sm);
    } catch(e) {}

    const initialReadings: Record<string, ReadingInput> = {};
    const newAverages: Record<string, number> = {};

    blockUnits.forEach(u => {
      initialReadings[u.unit_id] = savedFlats[u.unit_id] || { current: '', previous: '' };
      
      // Calculate historical average for anomaly detection
      const history = getUnitBillingHistory(u);
      const activeMonths = history.filter(h => h.consumption > 0);
      if (activeMonths.length > 0) {
          const total = activeMonths.reduce((sum, item) => sum + item.consumption, 0);
          newAverages[u.unit_id] = total / activeMonths.length;
      } else {
          newAverages[u.unit_id] = 300; // Fallback average
      }
    });

    setFlatReadings(initialReadings);
    setAverages(newAverages);

    if (hasSharedMotor && blockUnits.length > 0) {
        const motorId = blockUnits[0].water_motor_meter_no;
        if (motorId) setMotorReading(savedMotors[motorId] || { current: '', previous: '' });
    } else {
        setMotorReading({ current: '', previous: '' });
    }
    setGeneratedBills([]);
    setExpandedBillId(null);
    setErrorMessage(null);
    setAnomalies({});
  }, [blockUnits, hasSharedMotor]);

  const handleFlatReadingChange = (id: string, field: 'current' | 'previous', value: string) => {
    setErrorMessage(null);
    const numValue = value === '' ? '' : parseFloat(value);
    
    setFlatReadings(prev => {
      const updatedUnitReadings = { ...prev[id], [field]: numValue };
      
      // Anomaly Check logic
      const current = field === 'current' ? numValue : updatedUnitReadings.current;
      const previous = field === 'previous' ? numValue : updatedUnitReadings.previous;
      
      let anomalyMsg = '';
      if (current !== '' && previous !== '' && typeof current === 'number' && typeof previous === 'number') {
          const consumption = current - previous;
          const avg = averages[id];
          
          if (consumption > 0 && avg > 0) {
              // Threshold: 50% higher (1.5x)
              if (consumption > avg * 1.5) {
                  const multiplier = (consumption / avg).toFixed(1);
                  anomalyMsg = `Consumption is ${multiplier}x higher than usual (~${avg.toFixed(0)}). Verify reading?`;
              }
          }
      }

      setAnomalies(curr => {
          if (anomalyMsg) {
              return { ...curr, [id]: anomalyMsg };
          } else {
              const copy = { ...curr };
              delete copy[id];
              return copy;
          }
      });

      saveFlatReading(id, updatedUnitReadings);
      return { ...prev, [id]: updatedUnitReadings };
    });
  };

  const handleMotorReadingChange = (field: 'current' | 'previous', value: string) => {
    setErrorMessage(null);
    const numValue = value === '' ? '' : parseFloat(value);
    setMotorReading(prev => {
      const updated = { ...prev, [field]: numValue };
      if (hasSharedMotor && blockUnits.length > 0) {
          const motorId = blockUnits[0].water_motor_meter_no;
          if (motorId) saveMotorReading(motorId, updated);
      }
      return updated;
    });
  };

  const calculateTotalBlockConsumption = () => {
    let total = 0;
    // Explicitly cast to ReadingInput[] to avoid 'unknown' type errors
    (Object.values(flatReadings) as ReadingInput[]).forEach(reading => {
      if (reading.current !== '' && reading.previous !== '') {
        const diff = Number(reading.current) - Number(reading.previous);
        if (diff > 0) total += diff;
      }
    });
    return total;
  };

  const handleGenerate = () => {
    setErrorMessage(null);
    const errors: string[] = [];
    
    // Validate Motor Readings
    if (hasSharedMotor && motorReading.current !== '' && motorReading.previous !== '') {
        if (Number(motorReading.current) < Number(motorReading.previous)) {
            errors.push("Shared Motor");
        }
    }

    // Validate Flat Readings
    blockUnits.forEach(u => {
        const r = flatReadings[u.unit_id];
        if (r.current !== '' && r.previous !== '') {
            if (Number(r.current) < Number(r.previous)) {
                errors.push(u.flat_no);
            }
        }
    });

    if (errors.length > 0) {
        setErrorMessage("Action Blocked: Current readings cannot be lower than previous readings. Please check inputs highlighted in red.");
        return;
    }

    setIsProcessing(true);
    // Simulate AI processing delay for UX
    setTimeout(() => {
      const totalBlockConsumption = hasSharedMotor ? calculateTotalBlockConsumption() : undefined;
      const billingDate = new Date(billingYear, billingMonth, 1);
      const bills: BillPreviewType[] = [];

      blockUnits.forEach(u => {
        const readings = flatReadings[u.unit_id];
        if (readings.current === '' || readings.previous === '') return;

        const input = {
          currentFlatReading: Number(readings.current),
          previousFlatReading: Number(readings.previous),
          currentMotorReading: hasSharedMotor && motorReading.current !== '' ? Number(motorReading.current) : undefined,
          previousMotorReading: hasSharedMotor && motorReading.previous !== '' ? Number(motorReading.previous) : undefined,
          totalBlockConsumption: totalBlockConsumption
        };
        bills.push(generateBillPreview(u, input, billingDate));
      });

      setGeneratedBills(bills);
      if (bills.length > 0) setExpandedBillId(bills[0].unit_id);
      setIsProcessing(false);
    }, 600);
  };

  return (
    <div className="flex flex-col lg:flex-row gap-8 animate-in fade-in duration-500">
      
      {/* LEFT: Worksheet */}
      <div className={`flex-1 transition-all duration-500 ${generatedBills.length > 0 ? 'lg:max-w-md' : 'max-w-4xl mx-auto w-full'}`}>
        
        {/* Header Navigation */}
        <div className="flex items-center justify-between mb-6">
           <button 
             onClick={onBack}
             className="flex items-center gap-2 text-sm font-medium text-zinc-400 hover:text-black transition-colors"
           >
             <ArrowLeft className="w-4 h-4" />
             Back to Block
           </button>
           
           <div className="flex items-center gap-2">
             <div className="flex items-center gap-1 bg-zinc-100 px-3 py-1 rounded-full text-xs font-semibold text-zinc-600">
                <Calendar className="w-3 h-3" />
                {MONTHS[billingMonth]} {billingYear}
             </div>
             {isBatchMode && (
                <span className="text-[10px] font-bold tracking-widest uppercase bg-black text-white px-3 py-1 rounded-full">
                {groupName || 'Batch'}
                </span>
             )}
           </div>
        </div>

        <div className="bg-white rounded-[2rem] shadow-sm border border-zinc-100 overflow-hidden">
           
           <div className="p-8 border-b border-zinc-100 bg-zinc-50/30">
              <h2 className="text-2xl font-bold text-black flex items-center gap-2">
                 Data Entry
                 <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
              </h2>
              <p className="text-zinc-500 text-sm mt-1">
                 Please input current meter readings. The AI will automatically calculate specific consumption and shared motor ratios.
              </p>
           </div>

           <div className="p-6 space-y-8 max-h-[60vh] overflow-y-auto">
              
              {/* Motor Section */}
              {hasSharedMotor && (
                 <div className="space-y-4">
                    <div className="flex items-center gap-2 text-sm font-bold text-zinc-900 uppercase tracking-wider">
                       <Droplets className="w-4 h-4" />
                       Shared Motor ({blockUnits[0].water_motor_meter_no})
                    </div>
                    <div className="p-4 rounded-2xl bg-zinc-50 border border-zinc-100">
                       <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-1">
                             <label className="text-[10px] uppercase font-bold text-zinc-400">Previous</label>
                             <input 
                                type="number" 
                                className="w-full bg-white border-none rounded-lg p-2 text-sm shadow-sm ring-1 ring-zinc-200 focus:ring-2 focus:ring-black outline-none transition-all"
                                placeholder="0000"
                                value={motorReading.previous}
                                onChange={e => handleMotorReadingChange('previous', e.target.value)}
                             />
                          </div>
                          <div className="space-y-1">
                             <label className="text-[10px] uppercase font-bold text-zinc-400">Current</label>
                             <input 
                                type="number" 
                                className="w-full bg-white border-none rounded-lg p-2 text-sm shadow-sm ring-1 ring-zinc-200 focus:ring-2 focus:ring-black outline-none transition-all"
                                placeholder="0000"
                                value={motorReading.current}
                                onChange={e => handleMotorReadingChange('current', e.target.value)}
                             />
                          </div>
                       </div>
                    </div>
                 </div>
              )}

              {/* Units Section */}
              <div className="space-y-4">
                 <div className="flex items-center gap-2 text-sm font-bold text-zinc-900 uppercase tracking-wider">
                    <Zap className="w-4 h-4" />
                    Unit Readings
                 </div>
                 
                 <div className="space-y-3">
                    {blockUnits.map(u => {
                       const r = flatReadings[u.unit_id] || { current: '', previous: '' };
                       const diff = (r.current !== '' && r.previous !== '') ? Number(r.current) - Number(r.previous) : null;
                       const isNegative = diff !== null && diff < 0;
                       const anomalyWarning = anomalies[u.unit_id];

                       return (
                          <div key={u.unit_id} className={`group p-4 rounded-2xl border transition-all bg-white ${isNegative ? 'border-red-200 shadow-sm ring-1 ring-red-100' : (anomalyWarning ? 'border-amber-200 ring-1 ring-amber-100' : 'border-zinc-100 hover:border-zinc-300 hover:shadow-md')}`}>
                             <div className="flex justify-between items-center mb-3">
                                <div className="flex items-center gap-2">
                                   <span className="font-bold text-black">{u.flat_no}</span>
                                   {u.floor && (
                                     <span className="text-[10px] font-bold text-zinc-500 bg-zinc-100 px-2 py-0.5 rounded-full uppercase tracking-wider">
                                       {u.floor}
                                     </span>
                                   )}
                                </div>
                                <span className="text-[10px] font-mono text-zinc-400">{u.meter_no}</span>
                             </div>
                             <div className="flex items-end gap-3">
                                <div className="flex-1 space-y-1">
                                   <label className="text-[10px] uppercase font-bold text-zinc-400">Previous</label>
                                   <input 
                                      type="number" 
                                      className="w-full bg-zinc-50 border-none rounded-lg p-2 text-sm focus:ring-2 focus:ring-black outline-none transition-all"
                                      value={r.previous}
                                      onChange={e => handleFlatReadingChange(u.unit_id, 'previous', e.target.value)}
                                   />
                                </div>
                                <div className="flex-1 space-y-1">
                                   <label className="text-[10px] uppercase font-bold text-zinc-400">Current</label>
                                   <input 
                                      type="number" 
                                      className="w-full bg-zinc-50 border-none rounded-lg p-2 text-sm focus:ring-2 focus:ring-black outline-none transition-all"
                                      value={r.current}
                                      onChange={e => handleFlatReadingChange(u.unit_id, 'current', e.target.value)}
                                   />
                                </div>
                                {diff !== null && (
                                   <div className={`h-[38px] px-3 rounded-lg flex items-center justify-center font-mono text-sm font-bold min-w-[3rem] transition-colors ${isNegative ? 'bg-red-100 text-red-600' : 'bg-black text-white'}`}>
                                      {diff}
                                   </div>
                                )}
                             </div>
                             {anomalyWarning && (
                                <div className="mt-3 flex items-start gap-2 p-2 bg-amber-50 border border-amber-100 rounded-lg text-xs font-medium text-amber-700 animate-in slide-in-from-top-2">
                                    <AlertTriangle className="w-4 h-4 shrink-0 text-amber-500 mt-0.5" />
                                    <span className="leading-tight">{anomalyWarning}</span>
                                </div>
                             )}
                          </div>
                       );
                    })}
                 </div>
              </div>
           </div>

           <div className="p-6 bg-zinc-50 border-t border-zinc-100 space-y-4">
             {errorMessage && (
                <div className="flex items-start gap-3 p-4 bg-red-50 text-red-700 rounded-xl text-sm border border-red-100">
                    <AlertCircle className="w-5 h-5 shrink-0" />
                    <p className="font-medium">{errorMessage}</p>
                </div>
             )}

             <button 
                onClick={handleGenerate}
                disabled={isProcessing}
                className="w-full bg-black hover:bg-zinc-800 text-white font-medium py-4 rounded-xl shadow-lg shadow-zinc-300 transition-all flex justify-center items-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed"
             >
                {isProcessing ? (
                   <>
                      <RefreshCw className="w-5 h-5 animate-spin" />
                      <span>Processing...</span>
                   </>
                ) : (
                   <>
                      <Sparkles className="w-5 h-5" />
                      <span>Calculate & Generate Bills</span>
                   </>
                )}
             </button>
           </div>
        </div>
      </div>

      {/* RIGHT: Results */}
      {generatedBills.length > 0 && (
         <div className="flex-1 animate-in slide-in-from-right-8 duration-500">
            <div className="h-full flex flex-col">
               <div className="flex justify-between items-center mb-6">
                  <h3 className="font-bold text-xl text-black">Generated Statements</h3>
                  <button onClick={() => setGeneratedBills([])} className="text-sm text-zinc-400 hover:text-black">Clear All</button>
               </div>

               <div className="flex-1 overflow-y-auto pr-2 pb-20 space-y-4">
                  {generatedBills.map((bill) => {
                     const isExpanded = expandedBillId === bill.unit_id;
                     const currentUnit = units.find(u => u.unit_id === bill.unit_id);

                     return (
                        <div 
                           key={bill.unit_id} 
                           className={`bg-white rounded-2xl border transition-all duration-300 overflow-hidden ${
                              isExpanded 
                              ? 'border-black shadow-xl ring-1 ring-black/5' 
                              : 'border-zinc-200 shadow-sm hover:border-zinc-300'
                           }`}
                        >
                           {/* Card Header */}
                           <div 
                              onClick={() => setExpandedBillId(isExpanded ? null : bill.unit_id)}
                              className="p-5 cursor-pointer flex justify-between items-center bg-white"
                           >
                              <div className="flex items-center gap-4">
                                 <div className={`w-10 h-10 rounded-full flex items-center justify-center transition-colors ${isExpanded ? 'bg-black text-white' : 'bg-zinc-100 text-zinc-500'}`}>
                                    <FileText className="w-5 h-5" />
                                 </div>
                                 <div>
                                    <h4 className="font-bold text-lg text-black flex items-center gap-2">
                                        {bill.flat_no}
                                        {bill.floor && (
                                            <span className="text-[10px] font-bold text-zinc-500 bg-zinc-100 px-2 py-0.5 rounded border border-zinc-200 uppercase tracking-wider">
                                                {bill.floor}
                                            </span>
                                        )}
                                    </h4>
                                    <p className="text-xs text-zinc-400 font-medium uppercase tracking-wide">
                                       {bill.period}
                                    </p>
                                 </div>
                              </div>
                              <div className="flex items-center gap-4">
                                 <span className="font-bold text-lg text-black">₹{bill.total_bill.toLocaleString('en-IN')}</span>
                                 {isExpanded ? <ChevronUp className="w-4 h-4 text-zinc-400" /> : <ChevronDown className="w-4 h-4 text-zinc-400" />}
                              </div>
                           </div>

                           {/* Detailed Receipt View */}
                           {isExpanded && (
                              <div className="bg-zinc-50/50 border-t border-zinc-100 p-6 animate-in fade-in duration-300">
                                 
                                 {/* Data Viz: Consumption Trend */}
                                 <ConsumptionSparkline unit={currentUnit} />

                                 {/* Summary Table */}
                                 <div className="bg-white border border-zinc-200 rounded-xl overflow-hidden mb-6">
                                    <table className="w-full text-sm">
                                       <thead className="bg-zinc-50 border-b border-zinc-200 text-xs text-zinc-500 uppercase font-medium">
                                          <tr>
                                             <th className="px-4 py-3 text-left">Item</th>
                                             <th className="px-4 py-3 text-right">Units</th>
                                             <th className="px-4 py-3 text-right">Rate</th>
                                             <th className="px-4 py-3 text-right">Total</th>
                                          </tr>
                                       </thead>
                                       <tbody className="divide-y divide-zinc-100">
                                          <tr>
                                             <td className="px-4 py-3 text-zinc-900 font-medium">Electricity</td>
                                             <td className="px-4 py-3 text-right text-zinc-600">{bill.flat_consumption}</td>
                                             <td className="px-4 py-3 text-right text-zinc-600">₹{bill.rate_per_unit}</td>
                                             <td className="px-4 py-3 text-right text-zinc-900 font-medium">₹{(bill.flat_consumption * bill.rate_per_unit).toLocaleString('en-IN')}</td>
                                          </tr>
                                          {bill.water_motor_share > 0 && (
                                             <tr>
                                                <td className="px-4 py-3 text-zinc-900 font-medium">Water Share</td>
                                                <td className="px-4 py-3 text-right text-zinc-600">{bill.water_motor_share}</td>
                                                <td className="px-4 py-3 text-right text-zinc-600">₹{bill.rate_per_unit}</td>
                                                <td className="px-4 py-3 text-right text-zinc-900 font-medium">₹{(bill.water_motor_share * bill.rate_per_unit).toLocaleString('en-IN')}</td>
                                             </tr>
                                          )}
                                          <tr>
                                             <td className="px-4 py-3 text-zinc-900 font-medium">Fixed Charges</td>
                                             <td className="px-4 py-3 text-right text-zinc-400">-</td>
                                             <td className="px-4 py-3 text-right text-zinc-400">-</td>
                                             <td className="px-4 py-3 text-right text-zinc-900 font-medium">₹{bill.fixed_charge.toLocaleString('en-IN')}</td>
                                          </tr>
                                          <tr className="bg-zinc-50">
                                             <td className="px-4 py-4 font-bold text-black">Total Payable</td>
                                             <td className="px-4 py-4" colSpan={2}></td>
                                             <td className="px-4 py-4 text-right font-bold text-xl text-black">₹{bill.total_bill.toLocaleString('en-IN')}</td>
                                          </tr>
                                       </tbody>
                                    </table>
                                 </div>

                                 <div className="flex justify-end">
                                    <button className="flex items-center gap-2 px-4 py-2 bg-white border border-zinc-200 rounded-lg text-sm font-medium hover:bg-zinc-50 transition-colors">
                                       <Download className="w-4 h-4" />
                                       Export PDF
                                    </button>
                                 </div>
                              </div>
                           )}
                        </div>
                     );
                  })}
               </div>
            </div>
         </div>
      )}
    </div>
  );
};