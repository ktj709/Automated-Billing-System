import React, { useState, useEffect } from 'react';
import { Layout } from './components/Layout';
import { UnitList } from './components/UnitList';
import { UnitDetail } from './components/UnitDetail';
import { BillPreview } from './components/BillPreview';
import { PeriodSelector } from './components/PeriodSelector';
import { ReportsDashboard } from './components/ReportsDashboard'; // Import new component
import { loadMasterData } from './services/dataService';
import { Unit } from './types';

const MONTH_NAMES = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
];

type BillingFlowStep = 'period-select' | 'block-select' | 'worksheet';
type DirectoryFlowStep = 'overview' | 'group-view' | 'detail-view';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState('list');
  const [units, setUnits] = useState<Unit[]>([]);
  
  // === Directory Tab State ===
  const [directoryStep, setDirectoryStep] = useState<DirectoryFlowStep>('overview');
  const [directorySelectedGroup, setDirectorySelectedGroup] = useState<{name: string, units: Unit[]} | null>(null);
  const [selectedDirectoryUnit, setSelectedDirectoryUnit] = useState<Unit | null>(null);

  // === Billing Tab State ===
  const [billingStep, setBillingStep] = useState<BillingFlowStep>('period-select');
  const [billingYear, setBillingYear] = useState<number>(new Date().getFullYear());
  const [billingMonth, setBillingMonth] = useState<number>(new Date().getMonth());
  
  const [selectedBillingUnit, setSelectedBillingUnit] = useState<Unit | null>(null);
  const [selectedBillingGroupUnits, setSelectedBillingGroupUnits] = useState<Unit[]>([]);
  const [selectedBillingGroupName, setSelectedBillingGroupName] = useState<string | undefined>(undefined);

  useEffect(() => {
    const data = loadMasterData();
    setUnits(data);
  }, []);

  // --- Directory Handlers ---
  
  const handleDirectoryGroupSelect = (name: string, groupUnits: Unit[]) => {
      setDirectorySelectedGroup({ name, units: groupUnits });
      setDirectoryStep('group-view');
      window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleDirectoryUnitSelect = (unit: Unit) => {
    setSelectedDirectoryUnit(unit);
    setDirectoryStep('detail-view');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleDirectoryBackToOverview = () => {
    setDirectoryStep('overview');
    setDirectorySelectedGroup(null);
  };

  const handleDirectoryBackToGroup = () => {
    setDirectoryStep('group-view');
    setSelectedDirectoryUnit(null);
  };

  // --- Billing Flow Handlers ---

  const handlePeriodSelect = (year: number, month: number) => {
    setBillingYear(year);
    setBillingMonth(month);
    setBillingStep('block-select');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleBillingBlockSelect = (groupName: string, groupUnits: Unit[]) => {
      if (groupUnits.length > 0) {
          setSelectedBillingUnit(groupUnits[0]);
          setSelectedBillingGroupUnits(groupUnits);
          setSelectedBillingGroupName(groupName);
          setBillingStep('worksheet');
          window.scrollTo({ top: 0, behavior: 'smooth' });
      }
  };

  const handleBillingUnitSelect = (unit: Unit) => {
      setSelectedBillingUnit(unit);
      setSelectedBillingGroupUnits([]); // Single unit mode
      setSelectedBillingGroupName(undefined);
      setBillingStep('worksheet');
      window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleBillingBackToBlocks = () => {
      setBillingStep('block-select');
      setSelectedBillingUnit(null);
      setSelectedBillingGroupUnits([]);
      setSelectedBillingGroupName(undefined);
  };

  const handleBillingBackToPeriod = () => {
      setBillingStep('period-select');
  };

  // --- Tab Switching ---
  const handleTabChange = (tab: string) => {
    setActiveTab(tab);
    if (tab === 'list') {
        if (directoryStep === 'detail-view') setDirectoryStep('overview');
    } else if (tab === 'billing') {
        if (billingStep === 'worksheet') setBillingStep('period-select');
    }
    // Reports tab maintains its internal state via its own component
  };

  const handleGenerateBillFromDetail = (unit: Unit) => {
      setActiveTab('billing');
      setBillingYear(new Date().getFullYear());
      setBillingMonth(new Date().getMonth());
      setSelectedBillingUnit(unit);
      setSelectedBillingGroupUnits([]);
      setBillingStep('worksheet');
  };

  return (
    <Layout activeTab={activeTab} onTabChange={handleTabChange}>
      
      {/* Tab: Directory */}
      {activeTab === 'list' && (
        <>
            {/* View 1: Overview (All Blocks) */}
            {directoryStep === 'overview' && (
                <UnitList 
                    units={units} 
                    viewMode="groups"
                    onSelectUnit={handleDirectoryUnitSelect} 
                    onSelectGroup={handleDirectoryGroupSelect}
                />
            )}

            {/* View 2: Group View (Units in a Block) */}
            {directoryStep === 'group-view' && directorySelectedGroup && (
                <UnitList 
                    units={directorySelectedGroup.units}
                    viewMode="list"
                    headerTitle={directorySelectedGroup.name}
                    headerSubtitle={`${directorySelectedGroup.units.length} units in this block`}
                    onSelectUnit={handleDirectoryUnitSelect}
                    onSelectGroup={() => {}} // No-op in list mode
                    onBack={handleDirectoryBackToOverview}
                />
            )}
            
            {/* View 3: Detail View */}
            {directoryStep === 'detail-view' && selectedDirectoryUnit && (
                <UnitDetail 
                    unit={selectedDirectoryUnit} 
                    onBack={directorySelectedGroup ? handleDirectoryBackToGroup : handleDirectoryBackToOverview}
                    onGenerateBill={handleGenerateBillFromDetail}
                />
            )}
        </>
      )}

      {/* Tab: Billing (Time Travel Flow) */}
      {activeTab === 'billing' && (
          <>
            {billingStep === 'period-select' && (
                <PeriodSelector onSelect={handlePeriodSelect} />
            )}

            {billingStep === 'block-select' && (
                <UnitList 
                    units={units}
                    viewMode="groups"
                    onSelectUnit={handleBillingUnitSelect}
                    onSelectGroup={handleBillingBlockSelect}
                    headerTitle={`Billing • ${MONTH_NAMES[billingMonth]} ${billingYear}`}
                    headerSubtitle="Select a block to begin entry"
                    onBack={handleBillingBackToPeriod}
                />
            )}

            {billingStep === 'worksheet' && selectedBillingUnit && (
                <BillPreview 
                    unit={selectedBillingUnit}
                    units={units}
                    customUnits={selectedBillingGroupUnits.length > 0 ? selectedBillingGroupUnits : undefined}
                    groupName={selectedBillingGroupName}
                    onBack={handleBillingBackToBlocks}
                    billingYear={billingYear}
                    billingMonth={billingMonth}
                />
            )}
          </>
      )}

      {/* Tab: Reports */}
      {activeTab === 'reports' && (
          <ReportsDashboard units={units} onGenerateBill={handleGenerateBillFromDetail} />
      )}

    </Layout>
  );
};

export default App;