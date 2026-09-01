import React, { useState, useEffect, Suspense, lazy } from 'react';
import { Header } from './components/Header';
import { Navigation, TabType } from './components/Navigation';
import { DashboardOverview } from './components/DashboardOverview';

import { CameraAsset, WatchlistEntry, AlertNotification, SystemMetrics } from './types';
import { fetchSystemHealth, fetchCameras, fetchWatchlist, fetchAlerts } from './services/api';

const VehicleJourneyView = lazy(() => import('./components/VehicleJourneyView').then(m => ({ default: m.VehicleJourneyView })));
const LiveCameraGrid = lazy(() => import('./components/LiveCameraGrid').then(m => ({ default: m.LiveCameraGrid })));
const VideoIntelligenceView = lazy(() => import('./components/VideoIntelligenceView').then(m => ({ default: m.VideoIntelligenceView })));
const GISMapView = lazy(() => import('./components/GISMapView').then(m => ({ default: m.GISMapView })));
const WatchlistAlertDesk = lazy(() => import('./components/WatchlistAlertDesk').then(m => ({ default: m.WatchlistAlertDesk })));
const CameraRegistryView = lazy(() => import('./components/CameraRegistryView').then(m => ({ default: m.CameraRegistryView })));
const PipelineHealthView = lazy(() => import('./components/PipelineHealthView').then(m => ({ default: m.PipelineHealthView })));

const TabLoader = () => (
  <div className="p-12 text-center text-cyan-400 font-mono text-sm animate-pulse">Loading module...</div>
);

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [targetPlate, setTargetPlate] = useState('');

  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [cameras, setCameras] = useState<CameraAsset[]>([]);
  const [watchlist, setWatchlist] = useState<WatchlistEntry[]>([]);
  const [alerts, setAlerts] = useState<AlertNotification[]>([]);

  const loadData = async () => {
    try {
      const m = await fetchSystemHealth();
      setMetrics(m);
    } catch (e) {
      console.error('Error loading health:', e);
    }
  };

  const loadTabData = async (tab: TabType) => {
    try {
      if (tab === 'grid' || tab === 'map' || tab === 'registry') {
        if (cameras.length === 0) setCameras(await fetchCameras());
      }
      if (tab === 'alerts') {
        const [w, a] = await Promise.all([fetchWatchlist(), fetchAlerts()]);
        setWatchlist(w);
        setAlerts(a);
      }
    } catch (e) {
      console.error('Error loading tab data:', e);
    }
  };

  useEffect(() => {
    loadData();
    fetchAlerts().then(setAlerts).catch(() => {});

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/alerts`;
    let ws: WebSocket | null = null;

    try {
      ws = new WebSocket(wsUrl);
      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.type === 'REALTIME_ALERT') {
            setAlerts((prev) => [
              {
                id: payload.alert_id || Date.now(),
                camera_id: payload.camera_id,
                camera_name: payload.camera_name,
                vehicle_number: payload.vehicle_number,
                alert_category: payload.category,
                priority: payload.priority,
                status: 'UNREAD',
                notes: `🚨 REALTIME WATCHLIST ALERT: ${payload.category} vehicle ${payload.vehicle_number} detected!`,
                location_name: payload.camera_name,
                latitude: payload.latitude,
                longitude: payload.longitude,
                timestamp: new Date().toISOString()
              },
              ...prev
            ]);
          }
        } catch (e) {
          console.error('Error parsing WS message:', e);
        }
      };
    } catch (e) {
      console.warn('WebSocket connection not available');
    }

    const healthPoll = setInterval(loadData, 10000);

    return () => {
      if (ws) ws.close();
      clearInterval(healthPoll);
    };
  }, []);

  useEffect(() => {
    if (activeTab !== 'overview') {
      loadTabData(activeTab);
    }
  }, [activeTab]);

  const handleSearchPlate = (plate: string) => {
    setTargetPlate(plate);
    setActiveTab('journey');
  };

  const unreadAlerts = alerts.filter((a) => a.status === 'UNREAD').length;

  return (
    <div className="min-h-screen bg-[#0a0e17] text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-black">
      <Header
        onSearchPlate={handleSearchPlate}
        unreadAlertCount={unreadAlerts}
        processingMode={metrics?.stream_gateway_status || 'REAL VIDEO PROCESSING (LOCAL)'}
      />
      <Navigation activeTab={activeTab} setActiveTab={setActiveTab} unreadAlertCount={unreadAlerts} />

      <main className="flex-1 max-w-7xl w-full mx-auto">
        {activeTab === 'overview' && (
          <DashboardOverview
            metrics={metrics}
            alerts={alerts}
            onSearchPlate={handleSearchPlate}
            onNavigateTab={setActiveTab}
          />
        )}

        <Suspense fallback={<TabLoader />}>
          {activeTab === 'journey' && (
            <VehicleJourneyView initialPlate={targetPlate} />
          )}

          {activeTab === 'grid' && (
            <LiveCameraGrid cameras={cameras} />
          )}

          {activeTab === 'video_intel' && (
            <VideoIntelligenceView />
          )}

          {activeTab === 'map' && (
            <GISMapView cameras={cameras} />
          )}

          {activeTab === 'alerts' && (
            <WatchlistAlertDesk watchlist={watchlist} alerts={alerts} onRefresh={loadTabData.bind(null, 'alerts')} />
          )}

          {activeTab === 'registry' && (
            <CameraRegistryView cameras={cameras} />
          )}

          {activeTab === 'health' && (
            <PipelineHealthView />
          )}
        </Suspense>
      </main>

      <footer className="bg-[#0c121e] border-t border-cyan-950 px-6 py-3 text-center text-xs font-mono text-slate-400">
        Gujarat Police Sentinel CCTV Intelligence Platform &copy; 2026 — State Crime Record Bureau (SCRB), Gandhinagar
      </footer>
    </div>
  );
};
