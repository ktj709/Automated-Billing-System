import React, { useState, useMemo } from 'react';
import { Search, Filter, Send, Eye, CheckCircle, AlertCircle, Home, Zap, IndianRupee, Users, X, FileText, Calendar, Building } from 'lucide-react';

// Synthetic data based on the Excel sheet
const generateSyntheticData = () => {
  const units = [
    { unitId: '4BHK-C8-SF', flatNo: 'C8', floor: 'SF', type: '4BHK', clientName: 'S.Jora Singh and S. Bahadur Singh', meterNo: '21129958', fixedCharges: 1890, occupancy: 'Occupied', email: 'jora.singh@email.com' },
    { unitId: '4BHK-C8-FF', flatNo: 'C8', floor: 'FF', type: '4BHK', clientName: 'Jaswant Singh Randhawa', meterNo: '21129916', fixedCharges: 1890, occupancy: 'Occupied', email: 'jaswant.randhawa@email.com' },
    { unitId: '4BHK-C8-GF', flatNo: 'C8', floor: 'GF', type: '4BHK', clientName: 'S.Jora Singh and S. Bahadur Singh', meterNo: '24114213', fixedCharges: 1890, occupancy: 'Occupied', email: 'jora.singh@email.com' },
    { unitId: '4BHK-C9-SF', flatNo: 'C9', floor: 'SF', type: '4BHK', clientName: 'Rajbir Kaur', meterNo: '528011', fixedCharges: 1890, occupancy: 'Occupied', email: 'rajbir.kaur@email.com' },
    { unitId: '4BHK-C9-FF', flatNo: 'C9', floor: 'FF', type: '4BHK', clientName: 'Jarnail Singh Powar', meterNo: '22102869', fixedCharges: 1890, occupancy: 'Occupied', email: 'jarnail.powar@email.com' },
    { unitId: '4BHK-C10-SF', flatNo: 'C10', floor: 'SF', type: '4BHK', clientName: 'Balbir Singh', meterNo: '20054610', fixedCharges: 1890, occupancy: 'Occupied', email: 'balbir.singh@email.com' },
    { unitId: '4BHK-C10-FF', flatNo: 'C10', floor: 'FF', type: '4BHK', clientName: 'Daljit Kaur', meterNo: '20054604', fixedCharges: 1890, occupancy: 'Occupied', email: 'daljit.kaur@email.com' },
    { unitId: '4BHK-C10-GF', flatNo: 'C10', floor: 'GF', type: '4BHK', clientName: 'Regent Land Holdings Pvt Ltd', meterNo: '20054606', fixedCharges: 1890, occupancy: 'Vacant', email: 'billing@regentland.com' },
    { unitId: '2BHK-D3-SF', flatNo: 'D3', floor: 'SF', type: '2BHK', clientName: 'Regent Land Holdings Pvt Ltd', meterNo: '19152248', fixedCharges: 1474, occupancy: 'Vacant', email: 'billing@regentland.com' },
    { unitId: '2BHK-D3-FF', flatNo: 'D3', floor: 'FF', type: '2BHK', clientName: 'Dr. Prem Rana', meterNo: '19152248', fixedCharges: 1474, occupancy: 'Occupied', email: 'dr.prem.rana@email.com' },
    { unitId: '2BHK-D3-GF', flatNo: 'D3', floor: 'GF', type: '2BHK', clientName: 'Iqbal Singh', meterNo: '19152248', fixedCharges: 1474, occupancy: 'Occupied', email: 'iqbal.singh@email.com' },
    { unitId: '2BHK-D4-SF', flatNo: 'D4', floor: 'SF', type: '2BHK', clientName: 'Regent Land Holdings Pvt Ltd', meterNo: '19152170', fixedCharges: 1474, occupancy: 'Vacant', email: 'billing@regentland.com' },
    { unitId: '2BHK-D4-FF', flatNo: 'D4', floor: 'FF', type: '2BHK', clientName: 'Aarti Garg', meterNo: '19152170', fixedCharges: 1474, occupancy: 'Occupied', email: 'aarti.garg@email.com' },
    { unitId: '2BHK-D8-SF', flatNo: 'D8', floor: 'SF', type: '2BHK', clientName: 'Anshu Gupta', meterNo: '19152165', fixedCharges: 1474, occupancy: 'Occupied', email: 'anshu.gupta@email.com' },
    { unitId: '2BHK-D8-FF', flatNo: 'D8', floor: 'FF', type: '2BHK', clientName: 'Ashok Kumar Mehra', meterNo: '19152165', fixedCharges: 1474, occupancy: 'Occupied', email: 'ashok.mehra@email.com' },
    { unitId: '2BHK-F4-SF', flatNo: 'F4', floor: 'SF', type: '2BHK', clientName: 'Varun Vasudeva', meterNo: '19152229', fixedCharges: 1474, occupancy: 'Occupied', email: 'varun.vasudeva@email.com' },
    { unitId: '2BHK-F4-FF', flatNo: 'F4', floor: 'FF', type: '2BHK', clientName: 'Ravinder Singh', meterNo: '19152229', fixedCharges: 1474, occupancy: 'Occupied', email: 'ravinder.singh@email.com' },
    { unitId: '2BHK-F15-SF', flatNo: 'F15', floor: 'SF', type: '2BHK', clientName: 'Kashmir Singh', meterNo: '20098564', fixedCharges: 1474, occupancy: 'Occupied', email: 'kashmir.singh@email.com' },
    { unitId: '2BHK-F15-FF', flatNo: 'F15', floor: 'FF', type: '2BHK', clientName: 'Geeta Khurana', meterNo: '20098564', fixedCharges: 1474, occupancy: 'Occupied', email: 'geeta.khurana@email.com' },
    { unitId: '5BHK-E1-SF', flatNo: 'E1', floor: 'SF', type: '5BHK', clientName: 'Harpreet Sandhu', meterNo: '22103001', fixedCharges: 2311, occupancy: 'Occupied', email: 'harpreet.sandhu@email.com' },
    { unitId: '5BHK-E1-FF', flatNo: 'E1', floor: 'FF', type: '5BHK', clientName: 'Manpreet Kaur', meterNo: '22103002', fixedCharges: 2311, occupancy: 'Occupied', email: 'manpreet.kaur@email.com' },
    { unitId: '5BHK-E2-GF', flatNo: 'E2', floor: 'GF', type: '5BHK', clientName: 'Regent Land Holdings Pvt Ltd', meterNo: '22103003', fixedCharges: 2311, occupancy: 'Vacant', email: 'billing@regentland.com' },
  ];

  return units.map(unit => ({
    ...unit,
    previousReading: Math.floor(Math.random() * 5000) + 1000,
    currentReading: unit.occupancy === 'Occupied' 
      ? Math.floor(Math.random() * 5000) + 1500 
      : null,
    consumption: null,
    usageCharges: null,
    totalBill: null,
    calculated: false,
    billSent: false,
    billSentDate: null
  }));
};

const RATE_PER_UNIT = 7.50;

export default function BillingDashboard() {
  const [data, setData] = useState(generateSyntheticData());
  const [searchTerm, setSearchTerm] = useState('');
  const [occupancyFilter, setOccupancyFilter] = useState('All');
  const [typeFilter, setTypeFilter] = useState('All');
  const [selectedUnit, setSelectedUnit] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  const [sentBillsLog, setSentBillsLog] = useState([]);
  const [showSentLog, setShowSentLog] = useState(false);
  const [billingMonth, setBillingMonth] = useState('December 2025');

  const calculateConsumption = (unitId) => {
    setData(prev => prev.map(unit => {
      if (unit.unitId === unitId) {
        const consumption = unit.occupancy === 'Occupied' && unit.currentReading
          ? Math.max(0, unit.currentReading - unit.previousReading)
          : 0;
        const usageCharges = consumption * RATE_PER_UNIT;
        const totalBill = usageCharges + unit.fixedCharges;
        return { ...unit, consumption, usageCharges, totalBill, calculated: true };
      }
      return unit;
    }));
  };

  const calculateAll = () => {
    setData(prev => prev.map(unit => {
      const consumption = unit.occupancy === 'Occupied' && unit.currentReading
        ? Math.max(0, unit.currentReading - unit.previousReading)
        : 0;
      const usageCharges = consumption * RATE_PER_UNIT;
      const totalBill = usageCharges + unit.fixedCharges;
      return { ...unit, consumption, usageCharges, totalBill, calculated: true };
    }));
  };

  const sendBill = (unit) => {
    const billRecord = {
      billId: `BC-${Date.now()}`,
      unitId: unit.unitId,
      clientName: unit.clientName,
      email: unit.email,
      amount: unit.totalBill || unit.fixedCharges,
      dateSent: new Date().toLocaleString(),
      billingMonth,
      status: 'Sent'
    };
    setSentBillsLog(prev => [billRecord, ...prev]);
    setData(prev => prev.map(u => 
      u.unitId === unit.unitId 
        ? { ...u, billSent: true, billSentDate: new Date().toLocaleString() }
        : u
    ));
    setShowPreview(false);
    setSelectedUnit(null);
  };

  const filteredData = useMemo(() => {
    return data.filter(unit => {
      const matchesSearch = 
        unit.clientName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        unit.flatNo.toLowerCase().includes(searchTerm.toLowerCase()) ||
        unit.unitId.toLowerCase().includes(searchTerm.toLowerCase()) ||
        unit.meterNo.includes(searchTerm);
      const matchesOccupancy = occupancyFilter === 'All' || unit.occupancy === occupancyFilter;
      const matchesType = typeFilter === 'All' || unit.type === typeFilter;
      return matchesSearch && matchesOccupancy && matchesType;
    });
  }, [data, searchTerm, occupancyFilter, typeFilter]);

  const stats = useMemo(() => {
    const occupied = data.filter(u => u.occupancy === 'Occupied').length;
    const vacant = data.filter(u => u.occupancy === 'Vacant').length;
    const totalFixedCharges = data.reduce((sum, u) => sum + u.fixedCharges, 0);
    const totalBilled = data.filter(u => u.calculated).reduce((sum, u) => sum + (u.totalBill || 0), 0);
    const billsSent = data.filter(u => u.billSent).length;
    return { occupied, vacant, totalFixedCharges, totalBilled, billsSent };
  }, [data]);

  const getDueDate = () => {
    const date = new Date();
    date.setDate(date.getDate() + 15);
    return date.toLocaleDateString('en-IN', { day: '2-digit', month: '2-digit', year: '2-digit' });
  };

  return (
    <div className="min-h-screen bg-gray-50 p-3">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-800 to-blue-600 rounded-xl p-4 mb-4 text-white">
        <div className="flex justify-between items-start flex-wrap gap-2">
          <div>
            <h1 className="text-xl font-bold flex items-center gap-2">
              <Building className="w-6 h-6" />
              Blessings City - Admin Dashboard
            </h1>
            <p className="text-blue-200 text-sm">Electricity Billing System</p>
          </div>
          <div className="text-right">
            <div className="text-xs text-blue-200">Billing Period</div>
            <select 
              value={billingMonth} 
              onChange={(e) => setBillingMonth(e.target.value)}
              className="bg-white/20 border border-white/30 rounded px-2 py-1 text-white text-sm"
            >
              <option value="December 2025">December 2025</option>
              <option value="November 2025">November 2025</option>
              <option value="October 2025">October 2025</option>
            </select>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-5 gap-2 mb-4">
        <div className="bg-white rounded-lg p-3 shadow-sm border">
          <div className="flex items-center gap-2">
            <div className="bg-green-100 p-1.5 rounded"><Home className="w-4 h-4 text-green-600" /></div>
            <div>
              <div className="text-xl font-bold">{stats.occupied}</div>
              <div className="text-xs text-gray-500">Occupied</div>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg p-3 shadow-sm border">
          <div className="flex items-center gap-2">
            <div className="bg-orange-100 p-1.5 rounded"><AlertCircle className="w-4 h-4 text-orange-600" /></div>
            <div>
              <div className="text-xl font-bold">{stats.vacant}</div>
              <div className="text-xs text-gray-500">Vacant</div>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg p-3 shadow-sm border">
          <div className="flex items-center gap-2">
            <div className="bg-blue-100 p-1.5 rounded"><IndianRupee className="w-4 h-4 text-blue-600" /></div>
            <div>
              <div className="text-lg font-bold">₹{stats.totalFixedCharges.toLocaleString()}</div>
              <div className="text-xs text-gray-500">Fixed</div>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg p-3 shadow-sm border">
          <div className="flex items-center gap-2">
            <div className="bg-purple-100 p-1.5 rounded"><Zap className="w-4 h-4 text-purple-600" /></div>
            <div>
              <div className="text-lg font-bold">₹{stats.totalBilled.toLocaleString()}</div>
              <div className="text-xs text-gray-500">Billed</div>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg p-3 shadow-sm border">
          <div className="flex items-center gap-2">
            <div className="bg-teal-100 p-1.5 rounded"><Send className="w-4 h-4 text-teal-600" /></div>
            <div>
              <div className="text-xl font-bold">{stats.billsSent}</div>
              <div className="text-xs text-gray-500">Sent</div>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg p-3 mb-3 shadow-sm border">
        <div className="flex flex-wrap gap-2 items-center justify-between">
          <div className="flex flex-wrap gap-2 items-center">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-2 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search..."
                className="pl-8 pr-3 py-1.5 border rounded-lg w-48 text-sm"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <select className="px-2 py-1.5 border rounded-lg text-sm" value={occupancyFilter} onChange={(e) => setOccupancyFilter(e.target.value)}>
              <option value="All">All Status</option>
              <option value="Occupied">Occupied</option>
              <option value="Vacant">Vacant</option>
            </select>
            <select className="px-2 py-1.5 border rounded-lg text-sm" value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
              <option value="All">All Types</option>
              <option value="2BHK">2BHK</option>
              <option value="4BHK">4BHK</option>
              <option value="5BHK">5BHK</option>
            </select>
          </div>
          <div className="flex gap-2">
            <button onClick={calculateAll} className="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 flex items-center gap-1">
              <Zap className="w-4 h-4" /> Calculate All
            </button>
            <button onClick={() => setShowSentLog(true)} className="px-3 py-1.5 bg-gray-100 rounded-lg text-sm font-medium hover:bg-gray-200 flex items-center gap-1">
              <FileText className="w-4 h-4" /> Log ({sentBillsLog.length})
            </button>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-3 py-2 text-left font-semibold text-gray-600">Unit ID</th>
                <th className="px-3 py-2 text-left font-semibold text-gray-600">Flat</th>
                <th className="px-3 py-2 text-left font-semibold text-gray-600">Client</th>
                <th className="px-3 py-2 text-left font-semibold text-gray-600">Status</th>
                <th className="px-3 py-2 text-right font-semibold text-gray-600">Prev</th>
                <th className="px-3 py-2 text-right font-semibold text-gray-600">Curr</th>
                <th className="px-3 py-2 text-right font-semibold text-gray-600">Units</th>
                <th className="px-3 py-2 text-right font-semibold text-gray-600">Fixed</th>
                <th className="px-3 py-2 text-right font-semibold text-gray-600">Total</th>
                <th className="px-3 py-2 text-center font-semibold text-gray-600">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {filteredData.map((unit) => (
                <tr key={unit.unitId} className={`hover:bg-gray-50 ${unit.occupancy === 'Vacant' ? 'bg-amber-50' : ''} ${unit.billSent ? 'bg-green-50' : ''}`}>
                  <td className="px-3 py-2 font-mono text-xs">{unit.unitId}</td>
                  <td className="px-3 py-2">
                    <div className="font-medium">{unit.flatNo}-{unit.floor}</div>
                    <div className="text-xs text-gray-500">{unit.type}</div>
                  </td>
                  <td className="px-3 py-2">
                    <div className="font-medium truncate max-w-[120px]">{unit.clientName}</div>
                    <div className="text-xs text-gray-400">{unit.meterNo}</div>
                  </td>
                  <td className="px-3 py-2">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${unit.occupancy === 'Occupied' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'}`}>
                      {unit.occupancy}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-xs">{unit.previousReading}</td>
                  <td className="px-3 py-2 text-right font-mono text-xs">{unit.currentReading || '—'}</td>
                  <td className="px-3 py-2 text-right font-mono font-medium">{unit.calculated ? unit.consumption : '—'}</td>
                  <td className="px-3 py-2 text-right text-xs">₹{unit.fixedCharges.toLocaleString()}</td>
                  <td className="px-3 py-2 text-right font-semibold">
                    {unit.calculated ? <span className="text-blue-600">₹{unit.totalBill?.toLocaleString()}</span> : '—'}
                  </td>
                  <td className="px-3 py-2">
                    <div className="flex items-center justify-center gap-1">
                      {!unit.calculated && (
                        <button onClick={() => calculateConsumption(unit.unitId)} className="p-1 text-blue-600 hover:bg-blue-50 rounded" title="Calculate">
                          <Zap className="w-4 h-4" />
                        </button>
                      )}
                      <button onClick={() => { setSelectedUnit(unit); setShowPreview(true); }} className="p-1 text-gray-600 hover:bg-gray-100 rounded" title="Preview">
                        <Eye className="w-4 h-4" />
                      </button>
                      {unit.billSent ? (
                        <CheckCircle className="w-4 h-4 text-green-500" />
                      ) : (
                        <button onClick={() => { setSelectedUnit(unit); setShowPreview(true); }} className="p-1 text-teal-600 hover:bg-teal-50 rounded" title="Send">
                          <Send className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="px-3 py-2 bg-gray-50 border-t text-xs text-gray-500">
          Showing {filteredData.length} of {data.length} units • <span className="text-amber-600">Yellow = Vacant</span> • <span className="text-green-600">Green = Bill Sent</span>
        </div>
      </div>

      {/* Bill Preview Modal */}
      {showPreview && selectedUnit && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
            <div className="bg-blue-800 text-white p-4 rounded-t-xl">
              <div className="flex justify-between items-start">
                <div>
                  <h2 className="text-lg font-bold">BLESSINGS CITY</h2>
                  <p className="text-blue-200 text-xs">Residential Society, Ludhiana</p>
                </div>
                <button onClick={() => { setShowPreview(false); setSelectedUnit(null); }} className="text-white/70 hover:text-white">
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>
            
            <div className="p-4">
              <div className="text-center mb-3">
                <h3 className="font-bold text-gray-800">ELECTRICITY BILL</h3>
                <p className="text-xs text-gray-500">{billingMonth}</p>
              </div>

              <div className="bg-gray-50 rounded-lg p-3 mb-3 text-sm">
                <div className="grid grid-cols-2 gap-2">
                  <div><span className="text-gray-500">Unit:</span> <span className="font-medium">{selectedUnit.unitId}</span></div>
                  <div><span className="text-gray-500">Meter:</span> <span className="font-medium">{selectedUnit.meterNo}</span></div>
                  <div className="col-span-2"><span className="text-gray-500">Name:</span> <span className="font-medium">{selectedUnit.clientName}</span></div>
                  <div className="col-span-2"><span className="text-gray-500">Email:</span> <span className="font-medium text-xs">{selectedUnit.email}</span></div>
                </div>
              </div>

              {selectedUnit.occupancy === 'Occupied' && (
                <div className="mb-3">
                  <div className="text-xs font-semibold text-gray-600 mb-1">Meter Reading</div>
                  <div className="grid grid-cols-3 gap-2 text-sm">
                    <div className="bg-gray-100 p-2 rounded text-center">
                      <div className="text-gray-500 text-xs">Previous</div>
                      <div className="font-bold">{selectedUnit.previousReading}</div>
                    </div>
                    <div className="bg-gray-100 p-2 rounded text-center">
                      <div className="text-gray-500 text-xs">Current</div>
                      <div className="font-bold">{selectedUnit.currentReading || '—'}</div>
                    </div>
                    <div className="bg-blue-100 p-2 rounded text-center">
                      <div className="text-blue-600 text-xs">Units</div>
                      <div className="font-bold text-blue-700">{selectedUnit.consumption ?? '—'}</div>
                    </div>
                  </div>
                </div>
              )}

              <div className="border rounded-lg overflow-hidden mb-3 text-sm">
                <table className="w-full">
                  <tbody className="divide-y">
                    {selectedUnit.occupancy === 'Occupied' && selectedUnit.calculated && (
                      <tr>
                        <td className="px-3 py-2">Energy ({selectedUnit.consumption} × ₹{RATE_PER_UNIT})</td>
                        <td className="px-3 py-2 text-right">₹{selectedUnit.usageCharges?.toLocaleString()}</td>
                      </tr>
                    )}
                    <tr>
                      <td className="px-3 py-2">Fixed Charges</td>
                      <td className="px-3 py-2 text-right">₹{selectedUnit.fixedCharges.toLocaleString()}</td>
                    </tr>
                    <tr className="bg-blue-50 font-bold">
                      <td className="px-3 py-2">Total Due</td>
                      <td className="px-3 py-2 text-right text-blue-700">₹{(selectedUnit.totalBill || selectedUnit.fixedCharges).toLocaleString()}</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div className="bg-amber-50 border border-amber-200 rounded-lg p-2 mb-3 flex items-center gap-2 text-sm">
                <Calendar className="w-4 h-4 text-amber-600" />
                <span className="text-gray-600">Due Date:</span>
                <span className="font-bold text-amber-700">{getDueDate()}</span>
              </div>

              <div className="text-xs text-gray-500 border-t pt-2">
                <p className="font-semibold mb-1">Terms:</p>
                <ul className="list-disc ml-4 space-y-0.5">
                  <li>18% interest if payment not made within 15 days after due date</li>
                  <li>₹500 fine for dishonoured cheques + 18% interest</li>
                  <li>All T&C as per Electricity Supply Agreement</li>
                </ul>
              </div>
            </div>

            <div className="p-3 bg-gray-50 rounded-b-xl flex gap-2 justify-end border-t">
              <button onClick={() => { setShowPreview(false); setSelectedUnit(null); }} className="px-3 py-1.5 text-gray-600 hover:bg-gray-200 rounded-lg text-sm">
                Cancel
              </button>
              <button
                onClick={() => sendBill(selectedUnit)}
                disabled={selectedUnit.billSent}
                className="px-3 py-1.5 bg-teal-600 text-white rounded-lg text-sm font-medium hover:bg-teal-700 flex items-center gap-1 disabled:opacity-50"
              >
                <Send className="w-4 h-4" />
                {selectedUnit.billSent ? 'Sent' : 'Send Bill'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Sent Log Modal */}
      {showSentLog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-xl w-full max-h-[70vh] overflow-hidden">
            <div className="p-3 border-b flex justify-between items-center">
              <h3 className="font-bold">Sent Bills Log</h3>
              <button onClick={() => setShowSentLog(false)} className="text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
            </div>
            <div className="overflow-y-auto max-h-[50vh]">
              {sentBillsLog.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  <FileText className="w-10 h-10 mx-auto mb-2 opacity-30" />
                  <p>No bills sent yet</p>
                </div>
              ) : (
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 sticky top-0">
                    <tr>
                      <th className="px-3 py-2 text-left">Bill ID</th>
                      <th className="px-3 py-2 text-left">Client</th>
                      <th className="px-3 py-2 text-right">Amount</th>
                      <th className="px-3 py-2 text-left">Sent</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {sentBillsLog.map((log) => (
                      <tr key={log.billId} className="hover:bg-gray-50">
                        <td className="px-3 py-2 font-mono text-xs">{log.billId}</td>
                        <td className="px-3 py-2">
                          <div className="truncate max-w-[150px]">{log.clientName}</div>
                          <div className="text-xs text-gray-400">{log.email}</div>
                        </td>
                        <td className="px-3 py-2 text-right font-medium">₹{log.amount.toLocaleString()}</td>
                        <td className="px-3 py-2 text-xs text-gray-500">{log.dateSent}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
            <div className="p-3 bg-gray-50 border-t">
              <button onClick={() => setShowSentLog(false)} className="w-full px-3 py-1.5 bg-gray-200 rounded-lg text-sm hover:bg-gray-300">Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
