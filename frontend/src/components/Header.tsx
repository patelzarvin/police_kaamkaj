import React, { useState, useEffect } from 'react';
import { Shield, Radio, AlertTriangle, Search, Clock, UserCheck, Activity } from 'lucide-react';

interface HeaderProps {
  onSearchPlate: (plate: string) => void;
  unreadAlertCount: number;
  processingMode?: string;
}

export const Header: React.FC<HeaderProps> = ({ onSearchPlate, unreadAlertCount, processingMode = 'REAL PROCESSING (LOCAL VIDEO)' }) => {
  const [currentTime, setCurrentTime] = useState('');
  const [searchInput, setSearchInput] = useState('');

  useEffect(() => {
    const updateClock = () => {
      const now = new Date();
      setCurrentTime(now.toLocaleTimeString('en-US', { hour12: false }) + ' | ' + now.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }));
    };
    updateClock();
    const interval = setInterval(updateClock, 1000);
    return () => clearInterval(interval);
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchInput.trim()) {
      onSearchPlate(searchInput.trim());
    }
  };

  return (
    <header className="bg-[#0f172a]/95 backdrop-blur-md border-b border-cyan-950 px-6 py-3.5 flex flex-col md:flex-row items-center justify-between gap-4 sticky top-0 z-50 shadow-2xl">
      {/* Brand Title */}
      <div className="flex items-center gap-3">
        <div className="bg-gradient-to-br from-cyan-500 to-blue-700 p-2.5 rounded-xl shadow-lg cyan-glow">
          <Shield className="w-7 h-7 text-black font-extrabold" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-extrabold tracking-wider bg-gradient-to-r from-cyan-400 via-sky-200 to-white bg-clip-text text-transparent">
              GUJARAT POLICE SENTINEL
            </h1>
            <span className="bg-cyan-950 text-cyan-400 border border-cyan-800 text-[10px] font-mono px-2 py-0.5 rounded-full uppercase tracking-wider font-semibold">
              AI CCTV INTELLIGENCE
            </span>
          </div>
          <p className="text-xs text-slate-400 font-mono">
            Statewide CCTV Intelligence & Real-Time ANPR Vehicle Tracking
          </p>
        </div>
      </div>

      {/* Quick Search Bar */}
      <form onSubmit={handleSearchSubmit} className="relative w-full max-w-md">
        <div className="relative">
          <input
            type="text"
            placeholder="Search Registration Plate (e.g. GJ01AB1234)..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="w-full bg-[#131b2e] border border-cyan-900/80 rounded-xl py-2 pl-10 pr-24 text-sm font-mono text-cyan-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition-all"
          />
          <Search className="w-4 h-4 text-cyan-400 absolute left-3.5 top-3" />
          <button
            type="submit"
            className="absolute right-1.5 top-1.5 bg-cyan-500 hover:bg-cyan-400 text-black font-semibold text-xs px-3 py-1.5 rounded-lg transition-all shadow-md"
          >
            TRACK
          </button>
        </div>
      </form>

      {/* Clock & Real Processing Status */}
      <div className="flex items-center gap-4">
        <div className="hidden lg:flex items-center gap-2 text-xs font-mono text-cyan-400/90 bg-[#131b2e] px-3 py-1.5 rounded-lg border border-slate-800">
          <Clock className="w-4 h-4 text-cyan-400" />
          <span>{currentTime}</span>
        </div>

        {/* Real Processing Badge */}
        <div className="flex items-center gap-2 bg-emerald-950/80 border border-emerald-700 text-emerald-300 px-3 py-1.5 rounded-lg text-xs font-mono font-bold shadow-md">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
          <Activity className="w-3.5 h-3.5 text-emerald-400" />
          <span>{processingMode}</span>
        </div>

        {/* Alert Pulse Counter */}
        {unreadAlertCount > 0 && (
          <div className="flex items-center gap-1.5 bg-rose-950/80 border border-rose-800 text-rose-300 px-3 py-1.5 rounded-lg text-xs font-bold animate-pulse-red">
            <AlertTriangle className="w-4 h-4 text-rose-400" />
            <span>{unreadAlertCount} ALERTS</span>
          </div>
        )}

        {/* User Badge */}
        <div className="flex items-center gap-2 text-xs text-slate-300 bg-[#131b2e] px-3 py-1.5 rounded-lg border border-slate-800">
          <UserCheck className="w-4 h-4 text-cyan-400" />
          <div>
            <div className="font-bold text-white leading-none">Cmdt. S. K. Sharma</div>
            <div className="text-[10px] text-slate-400">SCRB Gandhinagar</div>
          </div>
        </div>
      </div>
    </header>
  );
};
