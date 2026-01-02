
import React from 'react';
import { Sparkles, LayoutGrid, FileText, BarChart3 } from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
  activeTab: string;
  onTabChange: (tab: string) => void;
}

export const Layout: React.FC<LayoutProps> = ({ children, activeTab, onTabChange }) => {
  return (
    <div className="min-h-screen flex flex-col bg-[#fafafa] text-zinc-900 pb-20">
      {/* Floating Glass Header */}
      <header className="fixed top-4 left-4 right-4 md:left-8 md:right-8 h-16 rounded-2xl glass-panel z-50 flex items-center justify-between px-6 transition-all duration-300">
        <div 
          className="flex items-center gap-3 cursor-pointer group" 
          onClick={() => onTabChange('list')}
        >
           <div className="w-8 h-8 rounded-full bg-black flex items-center justify-center text-white shadow-lg group-hover:scale-105 transition-transform duration-300">
             <Sparkles className="w-4 h-4" />
           </div>
           <div className="flex flex-col">
             <span className="font-bold text-sm tracking-tight leading-none text-black">Blessings City</span>
             <span className="text-[10px] text-zinc-500 font-medium tracking-wide">AI BILLING AGENT</span>
           </div>
        </div>
        
        <nav className="flex gap-2">
          <button 
            onClick={() => onTabChange('list')}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-300 flex items-center gap-2 ${
              activeTab === 'list' 
                ? 'bg-black text-white shadow-lg' 
                : 'text-zinc-500 hover:bg-zinc-100 hover:text-black'
            }`}
          >
            <LayoutGrid className="w-4 h-4" />
            <span className="hidden sm:inline">Directory</span>
          </button>
          <button 
            onClick={() => onTabChange('billing')}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-300 flex items-center gap-2 ${
              activeTab === 'billing' 
                ? 'bg-black text-white shadow-lg' 
                : 'text-zinc-500 hover:bg-zinc-100 hover:text-black'
            }`}
          >
            <FileText className="w-4 h-4" />
            <span className="hidden sm:inline">Billing</span>
          </button>
          <button 
            onClick={() => onTabChange('reports')}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-300 flex items-center gap-2 ${
              activeTab === 'reports' 
                ? 'bg-black text-white shadow-lg' 
                : 'text-zinc-500 hover:bg-zinc-100 hover:text-black'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            <span className="hidden sm:inline">Reports</span>
          </button>
        </nav>
      </header>

      {/* Main Content Spacer for Fixed Header */}
      <div className="h-24"></div>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 md:px-8">
        {children}
      </main>
    </div>
  );
};
