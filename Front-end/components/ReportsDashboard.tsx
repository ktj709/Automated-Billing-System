import React, { useState, useMemo } from 'react';
import { Unit, MonthlyReport } from '../types';
import { generateMonthlyReport } from '../services/analyticsService';
import { getUnitBillingHistory, calculateOutstandingDues } from '../services/dataService';
import { UnitDetail } from './UnitDetail';
import { 
  Calendar, ArrowRight, CheckCircle2, TrendingUp, Zap, 
  AlertCircle, ChevronLeft, ChevronRight, Wallet, PieChart, Ban, History, Users, Send, Bell
} from 'lucide-react';

interface ReportsDashboardProps {
  units: Unit[];
  onGenerateBill: (unit: Unit) => void;
}

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

type ViewState = 'selector' | 'dashboard' | 'detail';
type TabState = 'overview' | 'paid' | 'unpaid';
type MainTab = 'financials' | 'collections';

export const ReportsDashboard: React.FC<ReportsDashboardProps> = ({ units, onGenerateBill }) => {
  const [mainTab, setMainTab] = useState<MainTab>('financials');
  
  // Financials State
  const [view, setView] = useState<ViewState>('selector');
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [selectedMonth, setSelectedMonth] = useState<number>(new Date().getMonth());
  const [report, setReport] = useState<MonthlyReport | null>(null);
  const [activeTab, setActiveTab] = useState<TabState>('overview');
  
  // Shared State
  const [selectedUnit, setSelectedUnit] = useState<Unit | null>(null);

  // Collections Logic
  const defaulters = useMemo(() => {
    if (mainTab !== 'collections') return [];
    
    return units
      .map(unit => {
        const history = getUnitBillingHistory(unit);
        const totalDue = calculateOutstandingDues(history);
        const unpaidMonthsCount = history.filter(h => h.status !== 'Paid').length;
        return { unit, totalDue, unpaidMonthsCount };
      })
      .filter(item => item.totalDue > 0)
      .sort((a, b) => b.totalDue - a.totalDue); // Highest debt first
  }, [units, mainTab]);

  const totalArrears = useMemo(() => {
      return defaulters.reduce((acc, curr) => acc + curr.totalDue, 0);
  }, [defaulters]);

  // Handlers
  const handleGenerateReport = (year: number, monthIndex: number) => {
    setSelectedYear(year);
    setSelectedMonth(monthIndex);
    const data = generateMonthlyReport(units, year, monthIndex);
    setReport(data);
    setView('dashboard');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleUnitClick = (unit: Unit) => {
    setSelectedUnit(unit);
    setView('detail');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleBack = () => {
    if (view === 'detail') {
        // If we came from collections, go back to collections main view
        if (mainTab === 'collections') {
             setView('selector'); // In collections mode, 'selector' acts as the main view technically in this refactor, or we just reset unit
             setSelectedUnit(null);
             return;
        }
        // If we came from dashboard
        setView('dashboard');
        setSelectedUnit(null);
    } else if (view === 'dashboard') {
        setView('selector');
    }
  };

  // --- SUB-COMPONENTS ---

  const CollectionsView = () => (
      <div className="max-w-6xl mx-auto space-y-8 animate-in fade-in duration-700 py-6">
          <div className="flex flex-col md:flex-row gap-6">
              {/* Summary Card 1: Total Arrears */}
              <div className="flex-1 bg-gradient-to-br from-red-50 to-white border border-red-100 rounded-[2rem] p-8 relative overflow-hidden shadow-lg shadow-red-50/50">
                  <div className="relative z-10">
                      <div className="flex items-center gap-3 mb-4 text-red-700 font-bold uppercase tracking-wider text-sm">
                          <Ban className="w-5 h-5" />
                          <span>Total Outstanding Arrears</span>
                      </div>
                      <div className="text-5xl font-bold text-red-950 tracking-tight">
                          ₹{totalArrears.toLocaleString('en-IN')}
                      </div>
                      <p className="text-red-600/70 mt-2 font-medium">
                          Cumulative debt across all units
                      </p>
                  </div>
                  {/* Decor */}
                  <div className="absolute top-0 right-0 w-64 h-64 bg-red-100/50 rounded-full blur-3xl -mr-16 -mt-16 pointer-events-none"></div>
              </div>

               {/* Summary Card 2: Defaulters Count */}
               <div className="flex-1 bg-white border border-zinc-100 rounded-[2rem] p-8 shadow-sm">
                  <div className="flex items-center gap-3 mb-4 text-zinc-500 font-bold uppercase tracking-wider text-sm">
                      <Users className="w-5 h-5" />
                      <span>Units with Dues</span>
                  </div>
                  <div className="text-5xl font-bold text-zinc-900 tracking-tight">
                      {defaulters.length} <span className="text-lg text-zinc-400 font-medium">units</span>
                  </div>
                  <p className="text-zinc-400 mt-2">
                      Requiring follow-up
                  </p>
              </div>
          </div>

          <div className="bg-white rounded-[2rem] shadow-sm border border-zinc-100 overflow-hidden">
             <div className="p-6 border-b border-zinc-50 bg-zinc-50/50 flex justify-between items-center">
                 <h3 className="font-bold text-lg text-black">Defaulters List</h3>
                 <span className="text-xs font-bold bg-red-100 text-red-700 px-3 py-1 rounded-full border border-red-200 uppercase tracking-wide">
                     Priority Action
                 </span>
             </div>
             
             {/* RESPONSIVE LAYOUT: Cards on Mobile, Table on Desktop */}
             <div>
                 {/* Desktop Table View */}
                 <div className="hidden md:block overflow-x-auto">
                     <table className="w-full text-sm text-left">
                        <thead className="bg-white text-zinc-400 uppercase text-[10px] font-bold tracking-wider border-b border-zinc-100">
                            <tr>
                                <th className="px-6 py-4">Unit</th>
                                <th className="px-6 py-4">Owner</th>
                                <th className="px-6 py-4 text-center">Unpaid Months</th>
                                <th className="px-6 py-4 text-right">Total Due</th>
                                <th className="px-6 py-4"></th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-zinc-50">
                            {defaulters.map(({ unit, totalDue, unpaidMonthsCount }) => (
                                <tr 
                                    key={unit.unit_id}
                                    onClick={() => handleUnitClick(unit)}
                                    className="group hover:bg-zinc-50 cursor-pointer transition-colors"
                                >
                                    <td className="px-6 py-4">
                                        <div className="font-bold text-black group-hover:underline">{unit.flat_no}</div>
                                        <div className="text-[10px] text-zinc-400 font-mono">{unit.unit_id}</div>
                                    </td>
                                    <td className="px-6 py-4 font-medium text-zinc-600">
                                        {unit.client_name}
                                    </td>
                                    <td className="px-6 py-4 text-center">
                                        <span className={`inline-flex items-center justify-center px-2.5 py-1 rounded-full text-xs font-bold ${
                                            unpaidMonthsCount >= 3 ? 'bg-red-100 text-red-700' : 'bg-amber-50 text-amber-700'
                                        }`}>
                                            {unpaidMonthsCount} Months
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-right font-bold text-red-600 text-lg">
                                        ₹{totalDue.toLocaleString()}
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <div className="w-8 h-8 rounded-full border border-zinc-200 flex items-center justify-center bg-white text-zinc-400 group-hover:border-black group-hover:text-black transition-all">
                                            <ArrowRight className="w-4 h-4" />
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                     </table>
                 </div>

                 {/* Mobile Card View */}
                 <div className="md:hidden p-4 space-y-4 bg-zinc-50/50">
                    {defaulters.map(({ unit, totalDue, unpaidMonthsCount }) => (
                        <div 
                           key={unit.unit_id}
                           onClick={() => handleUnitClick(unit)}
                           className="bg-white rounded-2xl p-5 shadow-sm border border-zinc-100 active:scale-[0.98] transition-transform"
                        >
                           <div className="flex justify-between items-start mb-4">
                               <div>
                                   <div className="flex items-center gap-2">
                                       <span className="font-bold text-xl text-black">{unit.flat_no}</span>
                                       <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide border ${
                                            unpaidMonthsCount >= 3 
                                            ? 'bg-red-50 text-red-700 border-red-100' 
                                            : 'bg-amber-50 text-amber-700 border-amber-100'
                                       }`}>
                                           {unpaidMonthsCount} Mo. Due
                                       </span>
                                   </div>
                                   <p className="text-xs text-zinc-500 mt-1">{unit.client_name}</p>
                               </div>
                               <div className="w-8 h-8 rounded-full bg-zinc-50 flex items-center justify-center text-zinc-400">
                                   <ArrowRight className="w-4 h-4" />
                               </div>
                           </div>
                           
                           <div className="flex items-end justify-between border-t border-zinc-50 pt-4">
                               <div>
                                   <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider">Outstanding</p>
                                   <p className="text-2xl font-bold text-red-600 tracking-tight">₹{totalDue.toLocaleString()}</p>
                               </div>
                               <button 
                                  onClick={(e) => {
                                      e.stopPropagation();
                                      // Mock reminder action
                                      alert(`Reminder sent to ${unit.client_name}`);
                                  }}
                                  className="flex items-center gap-2 px-4 py-2 bg-black text-white rounded-lg text-xs font-bold shadow-lg shadow-zinc-200 active:bg-zinc-800"
                               >
                                  <Bell className="w-3 h-3" />
                                  Remind
                               </button>
                           </div>
                        </div>
                    ))}
                 </div>

                 {defaulters.length === 0 && (
                     <div className="p-12 text-center text-zinc-400">
                         <CheckCircle2 className="w-12 h-12 mx-auto text-emerald-200 mb-4" />
                         <p className="text-lg font-medium text-zinc-600">All Clear!</p>
                         <p>No units have outstanding dues at this moment.</p>
                     </div>
                 )}
             </div>
          </div>
      </div>
  );

  const FinancialsSelectorView = () => (
    <div className="max-w-6xl mx-auto space-y-12 animate-in fade-in duration-700 py-6">
      <div className="flex flex-col items-center justify-center space-y-6">
        <p className="text-zinc-500 text-center max-w-md">
            Analyze revenue, consumption trends, and payment statuses by billing cycle.
        </p>
        
        {/* Year Stepper */}
        <div className="flex items-center gap-1 bg-white p-1.5 rounded-full border border-zinc-200 shadow-sm hover:shadow-md transition-all duration-300">
            <button 
                onClick={() => setSelectedYear(y => y - 1)}
                className="w-12 h-12 rounded-full flex items-center justify-center text-zinc-400 hover:text-black hover:bg-zinc-100 transition-colors"
            >
                <ChevronLeft className="w-5 h-5" />
            </button>
            <div className="px-8 flex items-center gap-3 border-x border-zinc-100">
                <Calendar className="w-5 h-5 text-zinc-400" />
                <span className="text-2xl font-bold text-zinc-900 font-mono tracking-tight">{selectedYear}</span>
            </div>
            <button 
                onClick={() => setSelectedYear(y => y + 1)}
                className="w-12 h-12 rounded-full flex items-center justify-center text-zinc-400 hover:text-black hover:bg-zinc-100 transition-colors"
            >
                <ChevronRight className="w-5 h-5" />
            </button>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6 px-4">
        {MONTHS.map((month, index) => {
            const isFuture = selectedYear > new Date().getFullYear() || (selectedYear === new Date().getFullYear() && index > new Date().getMonth());
            
            return (
                <div 
                    key={month}
                    onClick={() => !isFuture && handleGenerateReport(selectedYear, index)}
                    className={`group relative p-6 rounded-3xl border transition-all duration-300 overflow-hidden
                        ${isFuture 
                            ? 'bg-zinc-50 border-transparent opacity-50 cursor-not-allowed' 
                            : 'bg-white border-zinc-100 hover:border-black cursor-pointer hover:shadow-xl hover:-translate-y-1'
                        }
                    `}
                >
                    <div className="flex justify-between items-start mb-8">
                        <span className="text-2xl font-bold tracking-tight text-black">
                            {month}
                        </span>
                        <span className="text-sm font-mono text-zinc-400">
                            {index + 1 < 10 ? `0${index+1}` : index+1}
                        </span>
                    </div>

                    {!isFuture ? (
                        <div className="flex items-center justify-between mt-4">
                            <span className="text-xs font-medium text-zinc-500 group-hover:text-black transition-colors">
                                View Report
                            </span>
                            <div className="w-8 h-8 rounded-full border border-zinc-100 flex items-center justify-center bg-white group-hover:bg-black group-hover:text-white transition-all">
                                <ArrowRight className="w-4 h-4" />
                            </div>
                        </div>
                    ) : (
                        <div className="mt-4 flex items-center gap-2 text-zinc-400">
                             <AlertCircle className="w-4 h-4" />
                             <span className="text-xs">No Data</span>
                        </div>
                    )}
                </div>
            )
        })}
      </div>
    </div>
  );

  const FinancialsDashboardView = () => {
    if (!report) return null;

    const filteredItems = useMemo(() => {
        if (activeTab === 'paid') return report.items.filter(i => i.status === 'Paid');
        if (activeTab === 'unpaid') return report.items.filter(i => i.status !== 'Paid');
        return report.items;
    }, [report, activeTab]);

    return (
      <div className="animate-in slide-in-from-bottom-8 duration-500 pb-20">
         {/* Navigation */}
         <div className="flex items-center justify-between mb-8">
            <button 
                onClick={handleBack}
                className="flex items-center gap-2 text-sm font-medium text-zinc-400 hover:text-black transition-colors group"
            >
                <div className="w-8 h-8 rounded-full bg-white border border-zinc-200 flex items-center justify-center group-hover:border-black transition-colors">
                   <ChevronLeft className="w-4 h-4" />
                </div>
                <span>Back to Months</span>
            </button>
            <div className="text-xl font-bold text-black flex items-center gap-2">
                {report.monthName} {report.year}
            </div>
         </div>

         {/* Bento Grid Stats */}
         <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            
            {/* Revenue Card (Dark) - Lifted Elevation */}
            <div className="md:col-span-2 bg-black text-white rounded-[2rem] p-8 relative overflow-hidden shadow-2xl hover:scale-[1.01] transition-transform duration-500">
                <div className="relative z-10 flex flex-col justify-between h-full min-h-[160px]">
                    <div className="flex justify-between items-start">
                        <div className="flex items-center gap-2 text-zinc-400 text-sm font-medium uppercase tracking-widest">
                            <Wallet className="w-4 h-4" />
                            <span>Total Revenue</span>
                        </div>
                        <div className="bg-zinc-800/50 px-3 py-1 rounded-full text-xs font-bold border border-zinc-700">
                             {report.items.length} Units Billed
                        </div>
                    </div>
                    <div>
                        <div className="text-5xl md:text-6xl font-bold tracking-tight mb-2">
                           ₹{(report.totalRevenue).toLocaleString('en-IN')}
                        </div>
                        <div className="flex gap-4 text-sm text-zinc-400">
                            <span>Collected: <span className="text-emerald-400">₹{report.totalCollected.toLocaleString()}</span></span>
                            <span>Pending: <span className="text-amber-400">₹{report.totalPending.toLocaleString()}</span></span>
                        </div>
                    </div>
                </div>
                {/* Decorative blob */}
                <div className="absolute top-0 right-0 w-64 h-64 bg-zinc-800 rounded-full blur-3xl -mr-20 -mt-20 opacity-50"></div>
            </div>

            {/* Collection Rate & Consumption (Stacked) */}
            <div className="space-y-6">
                 {/* Rate - Lifted */}
                 <div className="bg-white border border-zinc-100 rounded-[2rem] p-6 shadow-lg flex-1 hover:-translate-y-1 transition-transform">
                     <div className="flex justify-between items-start mb-4">
                         <span className="text-xs font-bold text-zinc-400 uppercase">Collection Rate</span>
                         <PieChart className="w-4 h-4 text-black" />
                     </div>
                     <div className="flex items-end gap-2">
                        <span className="text-4xl font-bold text-black">{report.collectionRate.toFixed(1)}%</span>
                        <span className="text-sm text-zinc-500 mb-1">paid</span>
                     </div>
                     <div className="w-full bg-zinc-100 h-2 rounded-full mt-4 overflow-hidden">
                        <div className="bg-black h-full rounded-full transition-all duration-1000" style={{ width: `${report.collectionRate}%` }}></div>
                     </div>
                 </div>

                 {/* Watts - Lifted */}
                 <div className="bg-white border border-zinc-100 rounded-[2rem] p-6 shadow-lg flex-1 hover:-translate-y-1 transition-transform">
                     <div className="flex justify-between items-start mb-4">
                         <span className="text-xs font-bold text-zinc-400 uppercase">Consumption</span>
                         <Zap className="w-4 h-4 text-black" />
                     </div>
                     <div className="flex items-end gap-2">
                        <span className="text-3xl font-bold text-black">{report.totalConsumption.toLocaleString()}</span>
                        <span className="text-sm text-zinc-500 mb-1">units</span>
                     </div>
                 </div>
            </div>
         </div>

         {/* Detailed Lists */}
         <div className="space-y-6">
             {/* Tabs */}
             <div className="flex items-center gap-2 p-1 bg-white border border-zinc-100 rounded-xl w-fit shadow-sm">
                 <button 
                    onClick={() => setActiveTab('overview')}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === 'overview' ? 'bg-zinc-900 text-white shadow-md' : 'text-zinc-500 hover:bg-zinc-50'}`}
                 >
                    All Transactions
                 </button>
                 <button 
                    onClick={() => setActiveTab('paid')}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${activeTab === 'paid' ? 'bg-emerald-500 text-white shadow-md' : 'text-zinc-500 hover:bg-zinc-50'}`}
                 >
                    <CheckCircle2 className="w-3 h-3" />
                    Paid ({report.items.filter(i => i.status === 'Paid').length})
                 </button>
                 <button 
                    onClick={() => setActiveTab('unpaid')}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${activeTab === 'unpaid' ? 'bg-amber-500 text-white shadow-md' : 'text-zinc-500 hover:bg-zinc-50'}`}
                 >
                    <AlertCircle className="w-3 h-3" />
                    Unpaid ({report.items.filter(i => i.status !== 'Paid').length})
                 </button>
             </div>

             {/* Recessed Table/Card List Container */}
             <div className="bg-zinc-50/50 border border-zinc-200 rounded-[2rem] overflow-hidden shadow-inner">
                 
                 {/* Desktop Table View */}
                 <div className="hidden md:block overflow-x-auto">
                    <table className="w-full text-sm text-left">
                        <thead className="bg-zinc-100 text-zinc-400 uppercase text-[10px] font-bold tracking-wider">
                            <tr>
                                <th className="px-6 py-4">Unit</th>
                                <th className="px-6 py-4">Owner</th>
                                <th className="px-6 py-4 text-right">Consumption</th>
                                <th className="px-6 py-4 text-right">Amount</th>
                                <th className="px-6 py-4 text-right">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-zinc-200">
                            {filteredItems.map((item) => (
                                <tr 
                                    key={item.unit.unit_id} 
                                    onClick={() => handleUnitClick(item.unit)}
                                    className="hover:bg-white cursor-pointer transition-colors group"
                                >
                                    <td className="px-6 py-4">
                                        <div className="font-bold text-black group-hover:underline">{item.unit.flat_no}</div>
                                        <div className="text-[10px] text-zinc-400">
                                            {item.unit.floor ? `${item.unit.floor} Floor` : item.unit.unit_type}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 font-medium text-zinc-600">
                                        {item.unit.client_name}
                                    </td>
                                    <td className="px-6 py-4 text-right text-zinc-600 font-mono">
                                        {item.consumption}
                                    </td>
                                    <td className="px-6 py-4 text-right font-bold text-black">
                                        ₹{item.billAmount.toLocaleString('en-IN')}
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border
                                            ${item.status === 'Paid' 
                                                ? 'bg-emerald-50 text-emerald-700 border-emerald-100' 
                                                : 'bg-amber-50 text-amber-700 border-amber-100'
                                            }
                                        `}>
                                            {item.status}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                            {filteredItems.length === 0 && (
                                <tr>
                                    <td colSpan={5} className="px-6 py-12 text-center text-zinc-400">
                                        No records found for this category.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                 </div>

                 {/* Mobile Card View for Transactions */}
                 <div className="md:hidden p-4 space-y-3">
                     {filteredItems.map((item) => (
                         <div 
                             key={item.unit.unit_id} 
                             onClick={() => handleUnitClick(item.unit)}
                             className="bg-white p-4 rounded-2xl shadow-sm border border-zinc-100 active:scale-[0.98] transition-transform"
                         >
                             <div className="flex justify-between items-start mb-2">
                                 <div>
                                     <h4 className="font-bold text-black text-lg">{item.unit.flat_no}</h4>
                                     <p className="text-xs text-zinc-500">{item.unit.client_name}</p>
                                 </div>
                                 <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide border ${
                                     item.status === 'Paid' 
                                     ? 'bg-emerald-50 text-emerald-700 border-emerald-100' 
                                     : 'bg-amber-50 text-amber-700 border-amber-100'
                                 }`}>
                                     {item.status}
                                 </span>
                             </div>
                             
                             <div className="flex justify-between items-end mt-4 pt-4 border-t border-zinc-50">
                                 <div className="text-xs text-zinc-400">
                                     <span className="block font-bold uppercase tracking-wider mb-0.5">Consumption</span>
                                     <span className="font-mono text-zinc-600 text-sm">{item.consumption} units</span>
                                 </div>
                                 <div className="text-right">
                                     <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-0.5">Amount</p>
                                     <p className="text-xl font-bold text-black">₹{item.billAmount.toLocaleString('en-IN')}</p>
                                 </div>
                             </div>
                         </div>
                     ))}
                     {filteredItems.length === 0 && (
                        <div className="text-center py-10 text-zinc-400">
                            <p>No records found.</p>
                        </div>
                     )}
                 </div>

             </div>
         </div>
      </div>
    );
  };

  // Main Render Switch
  
  // Detail view overrides everything
  if (selectedUnit) {
      return (
          <UnitDetail 
              unit={selectedUnit}
              onBack={handleBack}
              onGenerateBill={onGenerateBill}
              backLabel={mainTab === 'collections' ? 'Back to Defaulters' : 'Back to Report'}
          />
      );
  }

  // Dashboard structure
  return (
      <div className="pb-20">
          {/* Main Tab Toggle - Elevated */}
          <div className="max-w-md mx-auto mb-8 flex p-1 bg-white rounded-2xl border border-zinc-200 shadow-lg sticky top-24 z-30">
               <button 
                  onClick={() => { setMainTab('financials'); setView('selector'); }}
                  className={`flex-1 py-3 text-sm font-bold rounded-xl transition-all ${mainTab === 'financials' ? 'bg-zinc-900 text-white shadow-md' : 'text-zinc-500 hover:text-black hover:bg-zinc-50'}`}
               >
                   Financial Reports
               </button>
               <button 
                  onClick={() => { setMainTab('collections'); setView('selector'); }}
                  className={`flex-1 py-3 text-sm font-bold rounded-xl transition-all ${mainTab === 'collections' ? 'bg-red-600 text-white shadow-md' : 'text-zinc-500 hover:text-red-600 hover:bg-red-50'}`}
               >
                   Collections
               </button>
          </div>

          {mainTab === 'financials' && (
              view === 'selector' ? <FinancialsSelectorView /> : <FinancialsDashboardView />
          )}

          {mainTab === 'collections' && <CollectionsView />}
      </div>
  );
};