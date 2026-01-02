import React, { useState, useMemo } from 'react';
import { Search, User, Zap, Home, Building2, Store, ArrowRight, Droplets, ArrowLeft, Layers } from 'lucide-react';
import { Unit } from '../types';
import { searchUnits } from '../services/dataService';

interface UnitListProps {
  units: Unit[];
  viewMode: 'groups' | 'list'; // Explicit mode control
  onSelectUnit: (unit: Unit) => void;
  onSelectGroup: (groupName: string, groupUnits: Unit[]) => void;
  
  // Custom Header Props
  headerTitle?: string;
  headerSubtitle?: string;
  onBack?: () => void;
}

const MOTOR_NAMES: Record<string, string> = {
  '87923504': 'Block B',
  '86729933': 'Block C',
  '90199696': 'Block D1',
  '19152168': 'Block D2',
  '86729926': 'Block F1',
  '97701102': 'Block F2',
};

const SORT_ORDER = [
  'Block B',
  'Block C',
  'Block D1',
  'Block D2',
  'Block F1',
  'Block F2',
  'Villas',
  'SCOs'
];

export const UnitList: React.FC<UnitListProps> = ({ 
  units, 
  viewMode,
  onSelectUnit, 
  onSelectGroup,
  headerTitle,
  headerSubtitle,
  onBack
}) => {
  const [query, setQuery] = useState('');
  
  // Compute groups
  const groups = useMemo(() => {
    const g: Record<string, Unit[]> = {};
    const add = (key: string, u: Unit) => {
      if (!g[key]) g[key] = [];
      g[key].push(u);
    };

    units.forEach(u => {
      if (u.unit_type === 'motor') return;
      if (u.unit_type === 'villa') add('Villas', u);
      else if (u.unit_type === 'sco') add('SCOs', u);
      else if (u.unit_type === 'apartment') {
        const motor = u.water_motor_meter_no;
        if (motor && MOTOR_NAMES[motor]) add(MOTOR_NAMES[motor], u);
        else {
          if (u.unit_id.includes('-B')) add('Block B', u);
          else if (u.unit_id.includes('-C')) add('Block C', u);
          else if (u.unit_id.includes('-D')) add('Block D', u);
          else if (u.unit_id.includes('-F')) add('Block F', u);
          else add('Apartments', u);
        }
      }
    });
    return g;
  }, [units]);

  // Sort groups
  const sortedGroupKeys = useMemo(() => {
    return Object.keys(groups).sort((a, b) => {
      const idxA = SORT_ORDER.indexOf(a);
      const idxB = SORT_ORDER.indexOf(b);
      if (idxA !== -1 && idxB !== -1) return idxA - idxB;
      if (idxA !== -1) return -1;
      if (idxB !== -1) return 1;
      return a.localeCompare(b);
    });
  }, [groups]);

  // Search filter
  const filteredUnits = useMemo(() => {
    if (!query) return units;
    return searchUnits(units, query);
  }, [units, query]);

  // Determine which view to render
  // If searching, always show list. Otherwise respect viewMode.
  const isSearching = query.length > 0;
  const activeView = isSearching ? 'list' : viewMode;

  return (
    <div className="space-y-12 animate-in fade-in duration-500">
      
      {/* Header Section */}
      <div className="flex flex-col items-center justify-center space-y-8 py-10 relative">
        {onBack && (
            <button 
                onClick={onBack}
                className="absolute left-0 top-10 flex items-center gap-2 text-zinc-400 hover:text-black transition-colors"
            >
                <div className="w-8 h-8 rounded-full border border-zinc-200 flex items-center justify-center bg-white hover:border-black transition-colors">
                    <ArrowLeft className="w-4 h-4" />
                </div>
                <span className="text-sm font-medium hidden sm:inline">Back</span>
            </button>
        )}

        <div className="text-center space-y-2">
           <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-black">
             {headerTitle || 'Directory'}
           </h1>
           <p className="text-zinc-500 max-w-lg mx-auto">
             {headerSubtitle || 'Manage units, meters, and billing details.'}
           </p>
        </div>

        <div className="w-full max-w-xl relative group z-20">
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-zinc-400 group-focus-within:text-black transition-colors" />
          </div>
          <input
            type="text"
            className="block w-full pl-12 pr-4 py-4 rounded-2xl glass-panel text-lg placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-black/5 transition-all shadow-sm group-hover:shadow-md"
            placeholder="Search unit (e.g. C8), owner, or meter..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          {query && (
             <div className="absolute inset-y-0 right-4 flex items-center">
                <span className="text-xs font-medium text-zinc-400 bg-zinc-100 px-2 py-1 rounded-full">
                  {filteredUnits.length} results
                </span>
             </div>
          )}
        </div>
      </div>

      {activeView === 'groups' ? (
        // === GRID VIEW OF BLOCKS ===
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {sortedGroupKeys.map((name) => {
            const groupUnits = groups[name];
            if (!groupUnits || groupUnits.length === 0) return null;
            const hasSharedMotor = name.includes('Block');
            
            return (
              <div 
                key={name}
                onClick={() => onSelectGroup(name, groupUnits)}
                className="group relative bg-white rounded-3xl p-6 border border-zinc-100 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 cursor-pointer overflow-hidden"
              >
                {/* Visual Accent */}
                <div className="absolute top-0 right-0 w-32 h-32 bg-zinc-50 rounded-full blur-3xl -mr-16 -mt-16 group-hover:bg-zinc-100 transition-colors"></div>

                <div className="relative z-10">
                  <div className="flex justify-between items-start mb-8">
                    <div className="flex flex-col">
                      <h3 className="text-2xl font-bold text-black tracking-tight">{name}</h3>
                      <span className="text-xs font-medium text-zinc-400 mt-1 uppercase tracking-wide">
                        {groupUnits.length} Units
                      </span>
                    </div>
                    {hasSharedMotor ? (
                      <div className="w-10 h-10 rounded-full bg-black flex items-center justify-center text-white shadow-lg">
                        <Droplets className="w-4 h-4" />
                      </div>
                    ) : (
                      <div className="w-10 h-10 rounded-full bg-zinc-100 flex items-center justify-center text-zinc-900">
                         <Layers className="w-4 h-4" />
                      </div>
                    )}
                  </div>

                  <div className="flex items-center justify-between mt-8 pt-6 border-t border-zinc-50">
                     <span className="text-sm font-medium text-zinc-500 group-hover:text-black transition-colors">
                       Open Block
                     </span>
                     <div className="w-8 h-8 rounded-full border border-zinc-100 flex items-center justify-center bg-white group-hover:bg-black group-hover:text-white transition-all">
                        <ArrowRight className="w-4 h-4" />
                     </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        // === LIST VIEW OF UNITS ===
        <div className="space-y-3 max-w-4xl mx-auto pb-20">
          {filteredUnits.length > 0 && (
             <div className="flex justify-between items-center px-2 mb-4">
                <span className="text-xs font-bold text-zinc-400 uppercase tracking-widest">Unit List</span>
                <span className="text-xs text-zinc-400">{filteredUnits.length} items</span>
             </div>
          )}
          
          {filteredUnits.map((unit) => (
            <div 
              key={unit.unit_id}
              onClick={() => onSelectUnit(unit)}
              className="group flex items-center justify-between bg-white p-4 rounded-2xl border border-zinc-100 hover:border-black/20 hover:shadow-lg transition-all cursor-pointer"
            >
              <div className="flex items-center gap-5">
                <div className="w-12 h-12 rounded-2xl bg-zinc-50 flex items-center justify-center text-zinc-400 group-hover:bg-black group-hover:text-white transition-colors shadow-sm">
                   {unit.unit_type === 'villa' ? <Home className="w-5 h-5" /> : 
                    unit.unit_type === 'sco' ? <Store className="w-5 h-5" /> : 
                    <Building2 className="w-5 h-5" />}
                </div>
                <div>
                  <h3 className="font-bold text-lg text-black leading-tight">{unit.flat_no}</h3>
                  <div className="flex items-center gap-2 text-xs text-zinc-500 mt-1">
                    <User className="w-3 h-3" />
                    <span className="truncate max-w-[150px] sm:max-w-xs">{unit.client_name || 'No Name'}</span>
                  </div>
                </div>
              </div>
              
              <div className="flex items-center gap-6">
                <div className="hidden sm:block text-right">
                   <p className="text-[10px] text-zinc-400 uppercase tracking-wide font-bold">Meter No</p>
                   <p className="font-mono text-sm font-medium text-zinc-700">{unit.meter_no || 'N/A'}</p>
                </div>
                <div className="w-8 h-8 rounded-full border border-zinc-100 flex items-center justify-center group-hover:bg-zinc-100 transition-colors">
                   <ArrowRight className="w-4 h-4 text-zinc-300 group-hover:text-black" />
                </div>
              </div>
            </div>
          ))}

          {filteredUnits.length === 0 && (
            <div className="text-center py-20 bg-white rounded-3xl border border-dashed border-zinc-200">
              <div className="w-16 h-16 bg-zinc-50 rounded-full flex items-center justify-center mx-auto mb-4">
                <Search className="w-6 h-6 text-zinc-300" />
              </div>
              <p className="text-zinc-900 font-medium">No units found</p>
              <p className="text-zinc-500 text-sm mt-1">Try adjusting your search query.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};