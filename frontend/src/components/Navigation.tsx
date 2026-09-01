import React from 'react';
import { LayoutDashboard, Route, Video, MapPin, AlertOctagon, Camera, Activity, Film } from 'lucide-react';

export type TabType = 'overview' | 'journey' | 'grid' | 'video_intel' | 'map' | 'alerts' | 'registry' | 'health';

interface NavigationProps {
  activeTab: TabType;
  setActiveTab: (tab: TabType) => void;
  unreadAlertCount: number;
}

export const Navigation: React.FC<NavigationProps> = ({ activeTab, setActiveTab, unreadAlertCount }) => {
  const tabs = [
    { id: 'overview', label: 'Command Overview', icon: LayoutDashboard },
    { id: 'journey', label: 'Vehicle Journey Tracking', icon: Route, highlight: true },
    { id: 'grid', label: 'Live Camera Grid', icon: Video },
    { id: 'video_intel', label: 'Video Intelligence', icon: Film, highlight: true },
    { id: 'map', label: 'State GIS Map', icon: MapPin },
    { id: 'alerts', label: 'Watchlist & Alerts', icon: AlertOctagon, badge: unreadAlertCount },
    { id: 'registry', label: 'Camera Registry', icon: Camera },
    { id: 'health', label: 'Pipeline Telemetry', icon: Activity },
  ];

  return (
    <nav className="bg-[#0c121e] border-b border-cyan-950 px-6 py-2 flex items-center gap-2 overflow-x-auto shadow-inner">
      {tabs.map((tab) => {
        const Icon = tab.icon;
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as TabType)}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold tracking-wide transition-all whitespace-nowrap ${
              isActive
                ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-black shadow-lg shadow-cyan-500/20 font-bold'
                : 'text-slate-400 hover:text-cyan-300 hover:bg-[#131b2e]'
            } ${tab.highlight && !isActive ? 'border border-cyan-500/40 text-cyan-400' : ''}`}
          >
            <Icon className={`w-4 h-4 ${isActive ? 'text-black' : 'text-cyan-400'}`} />
            <span>{tab.label}</span>
            {tab.badge !== undefined && tab.badge > 0 && (
              <span className={`ml-1 px-1.5 py-0.5 rounded-full text-[10px] font-bold ${
                isActive ? 'bg-black text-cyan-400' : 'bg-rose-600 text-white'
              }`}>
                {tab.badge}
              </span>
            )}
          </button>
        );
      })}
    </nav>
  );
};
