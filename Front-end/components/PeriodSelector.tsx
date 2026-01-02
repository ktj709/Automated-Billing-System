import React, { useState } from 'react';
import { Calendar, CheckCircle2, ArrowRight, ChevronLeft, ChevronRight } from 'lucide-react';

interface PeriodSelectorProps {
  onSelect: (year: number, month: number) => void;
}

export const PeriodSelector: React.FC<PeriodSelectorProps> = ({ onSelect }) => {
  const currentYear = new Date().getFullYear();
  const [year, setYear] = useState(currentYear);

  const months = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  const currentMonthIndex = new Date().getMonth();

  return (
    <div className="max-w-6xl mx-auto space-y-12 animate-in fade-in duration-700 py-10">
      <div className="flex flex-col items-center justify-center space-y-6">
        <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-black text-center">
           Select Billing Cycle
        </h1>
        <p className="text-zinc-500 text-center max-w-md">
            Choose a period to manage readings and generate statements for that specific month.
        </p>
        
        {/* Year Selector Stepper */}
        <div className="flex items-center gap-1 bg-white p-1.5 rounded-full border border-zinc-200 shadow-sm hover:shadow-md transition-all duration-300">
            <button 
                onClick={() => setYear(y => y - 1)}
                className="w-12 h-12 rounded-full flex items-center justify-center text-zinc-400 hover:text-black hover:bg-zinc-100 transition-colors"
                aria-label="Previous Year"
            >
                <ChevronLeft className="w-5 h-5" />
            </button>
            
            <div className="px-8 flex items-center gap-3 border-x border-zinc-100">
                <Calendar className="w-5 h-5 text-zinc-400" />
                <span className="text-2xl font-bold text-zinc-900 font-mono tracking-tight">{year}</span>
            </div>

            <button 
                onClick={() => setYear(y => y + 1)}
                className="w-12 h-12 rounded-full flex items-center justify-center text-zinc-400 hover:text-black hover:bg-zinc-100 transition-colors"
                aria-label="Next Year"
            >
                <ChevronRight className="w-5 h-5" />
            </button>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6 px-4">
        {months.map((month, index) => {
            const isPast = year < currentYear || (year === currentYear && index < currentMonthIndex);
            const isCurrent = year === currentYear && index === currentMonthIndex;
            
            return (
                <div 
                    key={month}
                    onClick={() => onSelect(year, index)}
                    className={`group relative p-6 rounded-3xl border transition-all duration-300 cursor-pointer overflow-hidden
                        ${isCurrent 
                            ? 'bg-black text-white border-black shadow-xl scale-105 z-10' 
                            : 'bg-white text-black border-zinc-100 hover:border-zinc-300 hover:shadow-lg hover:-translate-y-1'
                        }
                    `}
                >
                    <div className="flex justify-between items-start mb-8">
                        <span className={`text-2xl font-bold tracking-tight ${isCurrent ? 'text-white' : 'text-black'}`}>
                            {month}
                        </span>
                        <span className={`text-sm font-mono opacity-50 ${isCurrent ? 'text-zinc-400' : 'text-zinc-400'}`}>
                            {index + 1 < 10 ? `0${index+1}` : index+1}
                        </span>
                    </div>

                    <div className="flex items-center justify-between mt-4">
                        <div className="flex items-center gap-2">
                             {isPast ? (
                                 <span className="flex items-center gap-1.5 text-xs font-medium text-emerald-500">
                                     <CheckCircle2 className="w-3 h-3" />
                                     <span>Archived</span>
                                 </span>
                             ) : isCurrent ? (
                                <span className="flex items-center gap-1.5 text-xs font-medium text-zinc-300">
                                     <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></div>
                                     <span>Active</span>
                                 </span>
                             ) : (
                                <span className="text-xs text-zinc-400">Upcoming</span>
                             )}
                        </div>
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center transition-all ${isCurrent ? 'bg-zinc-800 group-hover:bg-zinc-700' : 'bg-zinc-50 group-hover:bg-black group-hover:text-white'}`}>
                            <ArrowRight className="w-4 h-4" />
                        </div>
                    </div>
                </div>
            )
        })}
      </div>
    </div>
  );
};