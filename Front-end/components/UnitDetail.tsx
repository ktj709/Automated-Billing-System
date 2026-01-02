import React, { useMemo } from 'react';
import { ArrowLeft, User, Zap, Droplets, Mail, Phone, ChevronRight, Clock, CheckCircle2, AlertCircle, CalendarClock, Ban, Receipt } from 'lucide-react';
import { Unit } from '../types';
import { getUnitBillingHistory, calculateOutstandingDues } from '../services/dataService';

interface UnitDetailProps {
  unit: Unit;
  onBack: () => void;
  onGenerateBill: (unit: Unit) => void;
  backLabel?: string;
}

export const UnitDetail: React.FC<UnitDetailProps> = ({ unit, onBack, onGenerateBill, backLabel }) => {
  
  const history = useMemo(() => getUnitBillingHistory(unit), [unit]);
  const totalDues = useMemo(() => calculateOutstandingDues(history), [history]);

  const getStatusColor = (status: string | undefined) => {
    if (status === 'Paid') return 'bg-emerald-100 text-emerald-700 border-emerald-200';
    if (status === 'Overdue') return 'bg-red-100 text-red-700 border-red-200';
    return 'bg-amber-100 text-amber-700 border-amber-200';
  };

  const getStatusIcon = (status: string) => {
      if (status === 'Paid') return <CheckCircle2 className="w-3 h-3" />;
      if (status === 'Overdue') return <AlertCircle className="w-3 h-3" />;
      return <Clock className="w-3 h-3" />;
  };

  return (
    <div className="max-w-5xl mx-auto animate-in slide-in-from-bottom-8 duration-500 ease-out pb-20">
      
      {/* Navigation */}
      <button 
        onClick={onBack}
        className="mb-8 flex items-center gap-2 text-sm font-medium text-zinc-400 hover:text-black transition-colors group"
      >
        <div className="w-8 h-8 rounded-full bg-white border border-zinc-200 flex items-center justify-center group-hover:border-black transition-colors">
           <ArrowLeft className="w-4 h-4" />
        </div>
        <span>{backLabel || 'Back to Directory'}</span>
      </button>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* LEFT COLUMN: Main Info */}
        <div className="lg:col-span-2 space-y-8">
            {/* Header Card - Elevated (Active) */}
            <div className="bg-white rounded-[2rem] shadow-xl shadow-zinc-200/50 border border-zinc-100 overflow-hidden relative p-8 hover:-translate-y-1 transition-transform duration-500">
                {/* Subtle decorative gradient */}
                <div className="absolute top-0 right-0 w-64 h-64 bg-zinc-50 rounded-full blur-3xl -mr-20 -mt-20"></div>
                
                <div className="relative">
                    <div className="flex justify-between items-start mb-6">
                        <div>
                            <h1 className="text-4xl font-bold text-black tracking-tight mb-2">
                                {unit.flat_no}
                            </h1>
                            <div className="flex items-center gap-2 text-zinc-500">
                                <span className="font-mono text-sm bg-zinc-100 px-2 py-1 rounded-md border border-zinc-200">{unit.unit_id}</span>
                                <span className="text-zinc-300">•</span>
                                <span className="text-sm font-medium">{unit.floor ? `${unit.floor} Floor` : unit.unit_type}</span>
                            </div>
                        </div>
                        <div className="bg-black text-white px-4 py-2 rounded-full text-sm font-bold shadow-lg shadow-zinc-200">
                            {unit.bhk_type || unit.unit_type.toUpperCase()}
                        </div>
                    </div>

                    <div className="flex items-start gap-4 p-4 rounded-2xl bg-zinc-50/80 border border-zinc-100">
                        <div className="w-12 h-12 rounded-xl bg-white border border-zinc-100 flex items-center justify-center text-zinc-400 shadow-sm">
                            <User className="w-6 h-6" />
                        </div>
                        <div className="flex-1">
                            <p className="text-xs font-bold text-zinc-400 uppercase tracking-wider mb-1">Registered Owner</p>
                            <p className="font-semibold text-lg text-black leading-none mb-3">{unit.client_name}</p>
                            
                            <div className="flex flex-wrap gap-2">
                                {unit.phone ? (
                                    <a href={`tel:${unit.phone}`} className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-zinc-200 rounded-lg text-xs font-medium text-zinc-700 hover:border-black hover:text-black transition-colors">
                                        <Phone className="w-3 h-3" />
                                        Call
                                    </a>
                                ) : (
                                    <span className="flex items-center gap-1.5 px-3 py-1.5 bg-zinc-100 border border-transparent rounded-lg text-xs font-medium text-zinc-400 cursor-not-allowed">
                                        <Phone className="w-3 h-3" />
                                        No Phone
                                    </span>
                                )}

                                {unit.email ? (
                                    <a href={`mailto:${unit.email}`} className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-zinc-200 rounded-lg text-xs font-medium text-zinc-700 hover:border-black hover:text-black transition-colors">
                                        <Mail className="w-3 h-3" />
                                        Email
                                    </a>
                                ) : (
                                    <span className="flex items-center gap-1.5 px-3 py-1.5 bg-zinc-100 border border-transparent rounded-lg text-xs font-medium text-zinc-400 cursor-not-allowed">
                                        <Mail className="w-3 h-3" />
                                        No Email
                                    </span>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Billing Ledger / History - Recessed (Passive/Read-only) */}
            <div className="bg-zinc-50 rounded-[2rem] shadow-inner border border-zinc-200 p-8">
                <div className="flex items-center justify-between mb-6">
                    <h3 className="text-sm font-bold text-zinc-500 uppercase tracking-widest flex items-center gap-2">
                        <Receipt className="w-4 h-4" />
                        Billing Ledger
                    </h3>
                    <span className="text-xs font-medium text-zinc-400">History (Read-Only)</span>
                </div>

                <div className="space-y-3">
                    {history.map((item, index) => (
                        <div key={index} className="flex items-center justify-between p-4 rounded-xl border border-zinc-200/60 bg-white/50 hover:bg-white transition-colors">
                            <div className="flex items-center gap-4">
                                <div className={`w-10 h-10 rounded-full flex items-center justify-center border ${
                                    item.status === 'Paid' ? 'bg-emerald-50 border-emerald-100 text-emerald-600' :
                                    item.status === 'Overdue' ? 'bg-red-50 border-red-100 text-red-600' :
                                    'bg-amber-50 border-amber-100 text-amber-600'
                                }`}>
                                    {getStatusIcon(item.status)}
                                </div>
                                <div>
                                    <p className="font-bold text-zinc-800">{item.month} {item.year}</p>
                                    <p className="text-xs text-zinc-500 font-mono">{item.consumption} units</p>
                                </div>
                            </div>
                            <div className="text-right">
                                <p className="font-bold text-zinc-700">₹{item.amount.toLocaleString()}</p>
                                <p className={`text-[10px] font-bold uppercase tracking-wider ${
                                    item.status === 'Paid' ? 'text-emerald-600' : 
                                    item.status === 'Overdue' ? 'text-red-600' : 'text-amber-600'
                                }`}>{item.status}</p>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Meter Info - Semi-Active */}
            <div className="bg-white rounded-[2rem] shadow-sm border border-zinc-100 p-8">
                <h3 className="text-sm font-bold text-black uppercase tracking-widest mb-6 flex items-center gap-2">
                    <Zap className="w-4 h-4" />
                    Meter Configuration
                </h3>
                <div className="space-y-4">
                    {/* Electricity Meter Card */}
                    <div className="border border-zinc-200 rounded-2xl p-5 hover:border-zinc-400 transition-colors bg-white">
                        <div className="flex justify-between items-center mb-4">
                            <div className="flex items-center gap-2">
                                <div className="p-2 bg-zinc-100 rounded-lg">
                                    <Zap className="w-4 h-4 text-zinc-700" />
                                </div>
                                <span className="font-medium text-zinc-900">Electricity Meter</span>
                            </div>
                            <span className="font-mono text-lg font-bold text-black tracking-tight">{unit.meter_no}</span>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4 pt-4 border-t border-zinc-100">
                             <div>
                                <p className="text-[10px] font-bold text-zinc-400 uppercase">Last Reading</p>
                                <p className="text-xl font-medium text-zinc-700 font-mono mt-0.5">
                                    {unit.last_reading?.toLocaleString() || '---'}
                                </p>
                             </div>
                             <div>
                                <p className="text-[10px] font-bold text-zinc-400 uppercase">Date Recorded</p>
                                <p className="text-sm font-medium text-zinc-500 mt-1 flex items-center gap-1">
                                    <Clock className="w-3 h-3" />
                                    {unit.last_reading_date || 'N/A'}
                                </p>
                             </div>
                        </div>
                    </div>

                    {/* Water Motor Card */}
                    {unit.water_motor_meter_no && unit.water_motor_meter_no !== 'nan' ? (
                       <div className="border border-blue-100 bg-blue-50/30 rounded-2xl p-5">
                          <div className="flex justify-between items-center mb-2">
                             <div className="flex items-center gap-2">
                                <div className="p-2 bg-blue-100 text-blue-600 rounded-lg">
                                    <Droplets className="w-4 h-4" />
                                </div>
                                <span className="font-medium text-zinc-900">Water Motor</span>
                             </div>
                             <span className="font-mono text-sm font-bold text-zinc-700">{unit.water_motor_meter_no}</span>
                          </div>
                       </div>
                    ) : null}
                </div>
            </div>
        </div>

        {/* RIGHT COLUMN: Billing Status & Actions */}
        <div className="space-y-6">
            
            {/* Total Outstanding Card - Active Alert */}
            <div className={`rounded-[2rem] shadow-lg border p-6 relative overflow-hidden transition-all duration-300 hover:scale-[1.02] ${totalDues > 0 ? 'bg-red-50 border-red-100 shadow-red-100/50' : 'bg-emerald-50 border-emerald-100 shadow-emerald-100/50'}`}>
                <div className="relative z-10">
                    <div className="flex justify-between items-start mb-4">
                        <div className="flex items-center gap-2">
                             {totalDues > 0 ? (
                                <div className="p-2 bg-red-100 rounded-lg text-red-600"><AlertCircle className="w-4 h-4" /></div>
                             ) : (
                                <div className="p-2 bg-emerald-100 rounded-lg text-emerald-600"><CheckCircle2 className="w-4 h-4" /></div>
                             )}
                             <span className={`text-sm font-bold uppercase tracking-wider ${totalDues > 0 ? 'text-red-700' : 'text-emerald-700'}`}>
                                 Total Dues
                             </span>
                        </div>
                    </div>
                    
                    <div>
                        <span className={`text-4xl font-bold tracking-tight ${totalDues > 0 ? 'text-red-900' : 'text-emerald-900'}`}>
                            ₹{totalDues.toLocaleString('en-IN')}
                        </span>
                        {totalDues > 0 && (
                            <p className="text-red-600/80 text-sm mt-2 font-medium">
                                Cumulative outstanding from previous cycles.
                            </p>
                        )}
                         {totalDues === 0 && (
                            <p className="text-emerald-600/80 text-sm mt-2 font-medium">
                                No pending payments. Great job!
                            </p>
                        )}
                    </div>
                </div>
                
                {/* Decorative Blob */}
                <div className={`absolute -right-6 -bottom-6 w-32 h-32 rounded-full blur-2xl ${totalDues > 0 ? 'bg-red-200' : 'bg-emerald-200'}`}></div>
            </div>

            {/* Snapshot Card - Recessed */}
            <div className="bg-zinc-50 rounded-[2rem] shadow-inner border border-zinc-200 p-6">
                <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-widest mb-6">Rates & Charges</h3>
                <div className="space-y-3">
                    <div className="flex justify-between text-sm">
                            <span className="text-zinc-500">Fixed Charge</span>
                            <span className="font-medium text-zinc-900">₹{unit.fixed_charge}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                            <span className="text-zinc-500">Unit Rate</span>
                            <span className="font-medium text-zinc-900">₹{unit.rate_per_unit}/unit</span>
                    </div>
                </div>
            </div>

            {/* Primary Action - High Elevation */}
            <button 
                onClick={() => onGenerateBill(unit)}
                className="w-full group bg-black text-white hover:bg-zinc-800 transition-all rounded-[1.5rem] p-6 shadow-xl shadow-zinc-300 text-left relative overflow-hidden transform active:scale-95"
            >
                <div className="relative z-10 flex justify-between items-center">
                    <div>
                        <p className="font-bold text-lg">Initialize Billing</p>
                        <p className="text-zinc-400 text-sm mt-1">Start new cycle</p>
                    </div>
                    <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center group-hover:bg-white group-hover:text-black transition-all">
                        <ChevronRight className="w-5 h-5" />
                    </div>
                </div>
            </button>
        </div>

      </div>
    </div>
  );
};