import React, { useState } from 'react';
import { Camera, Radio, Eye, AlertTriangle, Search, Activity, Cpu, ShieldCheck, Zap } from 'lucide-react';
import { SystemMetrics, AlertNotification } from '../types';

interface DashboardOverviewProps {
  metrics: SystemMetrics | null;
  alerts: AlertNotification[];
  onSearchPlate: (plate: string) => void;
  onNavigateTab: (tab: any) => void;
}

export const DashboardOverview: React.FC<DashboardOverviewProps> = ({ metrics, alerts, onSearchPlate, onNavigateTab }) => {
  const [quickSearch, setQuickSearch] = useState('');

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (quickSearch.trim()) {
      onSearchPlate(quickSearch.trim());
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Quick Search Banner */}
      <div className="bg-gradient-to-r from-cyan-950/80 via-[#131b2e] to-blue-950/80 border border-cyan-500/30 rounded-2xl p-6 shadow-2xl relative overflow-hidden">
        <div className="absolute right-0 top-0 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />
        <div className="max-w-3xl space-y-3 relative z-10">
          <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs uppercase tracking-widest font-semibold">
            <Zap className="w-4 h-4 text-cyan-400" />
            <span>Statewide Vehicle Intelligence Search</span>
          </div>
          <h2 className="text-2xl font-black text-white tracking-tight">
            Reconstruct Vehicle Movement Across 80,000 CCTV Streams
          </h2>
          <p className="text-sm text-slate-300">
            Enter any Indian license plate number (e.g. <span className="font-mono text-cyan-300 font-bold bg-cyan-950 px-2 py-0.5 rounded border border-cyan-800">GJ01AB1234</span>) to query PostGIS detection logs, retrieve image evidence, and map multi-camera route history.
          </p>

          <form onSubmit={handleSearchSubmit} className="pt-2 flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <input
                type="text"
                placeholder="Enter Vehicle Plate Number (e.g. GJ01AB1234)..."
                value={quickSearch}
                onChange={(e) => setQuickSearch(e.target.value)}
                className="w-full bg-[#0a0e17] border-2 border-cyan-500/60 rounded-xl py-3 pl-12 pr-4 text-base font-mono text-cyan-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400 shadow-inner"
              />
              <Search className="w-5 h-5 text-cyan-400 absolute left-4 top-3.5" />
            </div>
            <button
              type="submit"
              className="bg-gradient-to-r from-cyan-400 to-blue-500 hover:from-cyan-300 hover:to-blue-400 text-black font-extrabold px-8 py-3 rounded-xl transition-all shadow-lg cyan-glow flex items-center justify-center gap-2"
            >
              <span>RECONSTRUCT JOURNEY</span>
            </button>
          </form>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-panel rounded-2xl p-5 border border-cyan-900/60 flex items-center justify-between">
          <div>
            <div className="text-xs font-mono text-slate-400 uppercase tracking-wider">Total Onboarded Cameras</div>
            <div className="text-3xl font-extrabold font-mono text-white mt-1">
              {metrics ? metrics.total_cameras : 26}
            </div>
            <div className="text-[11px] text-cyan-400 font-mono mt-1">26 Departments Integrated</div>
          </div>
          <div className="bg-cyan-950 p-3.5 rounded-xl border border-cyan-800 text-cyan-400">
            <Camera className="w-6 h-6" />
          </div>
        </div>

        <div className="glass-panel rounded-2xl p-5 border border-emerald-900/60 flex items-center justify-between">
          <div>
            <div className="text-xs font-mono text-slate-400 uppercase tracking-wider">Active Live Streams</div>
            <div className="text-3xl font-extrabold font-mono text-emerald-400 mt-1">
              {metrics ? metrics.online_cameras : 24}
            </div>
            <div className="text-[11px] text-emerald-400 font-mono mt-1">RTSP / TCP Healthy</div>
          </div>
          <div className="bg-emerald-950 p-3.5 rounded-xl border border-emerald-800 text-emerald-400">
            <Radio className="w-6 h-6" />
          </div>
        </div>

        <div className="glass-panel rounded-2xl p-5 border border-blue-900/60 flex items-center justify-between">
          <div>
            <div className="text-xs font-mono text-slate-400 uppercase tracking-wider">24h AI ANPR Detections</div>
            <div className="text-3xl font-extrabold font-mono text-blue-400 mt-1">
              {metrics ? metrics.total_detections_24h : 1420}
            </div>
            <div className="text-[11px] text-blue-400 font-mono mt-1">Indexed in PostGIS</div>
          </div>
          <div className="bg-blue-950 p-3.5 rounded-xl border border-blue-800 text-blue-400">
            <Eye className="w-6 h-6" />
          </div>
        </div>

        <div className="glass-panel rounded-2xl p-5 border border-rose-900/60 flex items-center justify-between">
          <div>
            <div className="text-xs font-mono text-slate-400 uppercase tracking-wider">Active Watchlist Alerts</div>
            <div className="text-3xl font-extrabold font-mono text-rose-400 mt-1">
              {metrics ? metrics.active_alerts : 3}
            </div>
            <div className="text-[11px] text-rose-400 font-mono mt-1">Requires Officer Action</div>
          </div>
          <div className="bg-rose-950 p-3.5 rounded-xl border border-rose-800 text-rose-400">
            <AlertTriangle className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Main Command Center Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Live Sentinel Stream Preview */}
        <div className="lg:col-span-2 space-y-4">
          <div className="glass-panel rounded-2xl p-5 border border-cyan-900/60 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Radio className="w-5 h-5 text-cyan-400" />
                <h3 className="text-base font-bold text-white font-mono uppercase">
                  Sentinel Feed Ingestion & AI Stream Processor
                </h3>
              </div>
              <button
                onClick={() => onNavigateTab('grid')}
                className="text-xs font-mono text-cyan-400 hover:text-cyan-300 underline"
              >
                View Full 4-Cam Grid $\rightarrow$
              </button>
            </div>

            {/* Video Stream Preview Frame */}
            <div className="relative rounded-xl overflow-hidden bg-black border border-cyan-900 aspect-video shadow-2xl">
              <img
                src="https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&w=1200&q=80"
                alt="Sentinel CCTV Feed Preview"
                className="w-full h-full object-cover opacity-80"
              />
              
              {/* Overlay Bounding Box Simulation */}
              <div className="absolute top-[35%] left-[30%] w-[35%] h-[40%] border-2 border-cyan-400 rounded bg-cyan-500/10 p-2 flex flex-col justify-between">
                <div className="bg-cyan-950/90 text-cyan-300 font-mono text-[11px] px-2 py-0.5 rounded border border-cyan-700 self-start font-bold">
                  GJ01AB1234 [Car | 96% ANPR]
                </div>
                <div className="bg-rose-950/90 text-rose-300 font-mono text-[10px] px-2 py-0.5 rounded border border-rose-700 self-end font-bold animate-pulse">
                  🚨 MATCH: STOLEN
                </div>
              </div>

              {/* Stream Parameters HUD */}
              <div className="absolute top-3 left-3 bg-black/80 backdrop-blur border border-slate-700 px-3 py-1.5 rounded-lg text-xs font-mono text-slate-300 flex items-center gap-3">
                <span className="flex items-center gap-1 text-emerald-400 font-bold">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                  RTSP TCP LIVE
                </span>
                <span>CAM-31 (GIFT City Toll Gate)</span>
                <span>H.264 | 1080p | 25 FPS</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Active Watchlist Alerts Feed */}
        <div className="space-y-4">
          <div className="glass-panel rounded-2xl p-5 border border-rose-900/60 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-rose-400 font-mono text-sm font-bold uppercase">
                <AlertTriangle className="w-5 h-5 text-rose-500" />
                <span>Live Alert Desk</span>
              </div>
              <button
                onClick={() => onNavigateTab('alerts')}
                className="text-xs font-mono text-cyan-400 hover:underline"
              >
                Manage All
              </button>
            </div>

            <div className="space-y-3">
              {alerts.slice(0, 3).map((alert) => (
                <div key={alert.id} className="bg-rose-950/40 border border-rose-800/80 rounded-xl p-4 space-y-2 hover:border-rose-500 transition-all">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-sm font-extrabold text-white bg-rose-950 px-2 py-0.5 rounded border border-rose-700">
                      {alert.vehicle_number}
                    </span>
                    <span className="text-[10px] font-mono font-bold bg-rose-900 text-rose-200 px-2 py-0.5 rounded-full uppercase">
                      {alert.priority} PRIORITY
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 leading-snug">{alert.notes}</p>
                  <div className="text-[11px] font-mono text-slate-400 flex items-center justify-between pt-1 border-t border-rose-900/50">
                    <span>{alert.location_name}</span>
                    <span>{new Date(alert.timestamp).toLocaleTimeString()}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
