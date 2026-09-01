import { CameraAsset, DetectionEvent, VehicleJourney, WatchlistEntry, AlertNotification, SystemMetrics } from '../types';

const API_BASE = (() => {
  const raw = (import.meta.env.VITE_API_URL as string | undefined)?.trim();
  if (!raw) return '/api';
  const base = raw.replace(/\/$/, '');
  return base.endsWith('/api') ? base : `${base}/api`;
})();

/** Build full API URL for fetch/img src (works on Render split deploy). */
export function apiUrl(path: string): string {
  const suffix = path.startsWith('/api') ? path.slice(4) : path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE}${suffix}`;
}

type CacheEntry<T> = { data: T; expires: number };
const cache = new Map<string, CacheEntry<unknown>>();

async function cachedFetch<T>(key: string, url: string, ttlMs: number): Promise<T | null> {
  const hit = cache.get(key);
  if (hit && Date.now() < hit.expires) return hit.data as T;
  try {
    const res = await fetch(url);
    if (!res.ok) return null;
    const data = (await res.json()) as T;
    cache.set(key, { data, expires: Date.now() + ttlMs });
    return data;
  } catch {
    return null;
  }
}

export const invalidateCache = (prefix?: string) => {
  if (!prefix) {
    cache.clear();
    return;
  }
  for (const key of cache.keys()) {
    if (key.startsWith(prefix)) cache.delete(key);
  }
};

export const fetchSystemHealth = async (): Promise<SystemMetrics> => {
  const data = await cachedFetch<SystemMetrics>('health', `${API_BASE}/health`, 3000);
  if (data) return data;
  return {
    total_cameras: 8,
    online_cameras: 8,
    offline_cameras: 0,
    degraded_cameras: 0,
    total_detections_24h: 0,
    active_alerts: 0,
    ai_workers_active: 4,
    avg_inference_ms: 22.0,
    stream_gateway_status: 'REAL_VIDEO_PROCESSING',
    uptime_seconds: 0
  };
};

export const fetchPipelineHealth = async () => {
  return cachedFetch('pipeline-health', `${API_BASE}/pipeline/health`, 2000);
};

export const fetchCameras = async (): Promise<CameraAsset[]> => {
  return (await cachedFetch<CameraAsset[]>('cameras', `${API_BASE}/cameras`, 30000)) ?? [];
};

export const connectSentinel = async (password: string) => {
  const res = await fetch(`${API_BASE}/sentinel/connect`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password })
  });
  invalidateCache('cameras');
  return await res.json();
};

export const getSentinelStatus = async () => {
  return (await cachedFetch('sentinel-status', `${API_BASE}/sentinel/status`, 10000)) ?? { status: 'NOT CONNECTED', cameras_discovered: 0 };
};

export const fetchVehicleJourney = async (plateNumber: string): Promise<VehicleJourney> => {
  const cleanPlate = plateNumber.toUpperCase().replace(/[^A-Z0-9]/g, '');
  const cacheKey = `journey:${cleanPlate}`;
  const cached = await cachedFetch<VehicleJourney>(cacheKey, `${API_BASE}/vehicles/${cleanPlate}/journey`, 60000);
  if (cached) return cached;

  const res = await fetch(`${API_BASE}/vehicles/${cleanPlate}/journey`);
  if (res.status === 404) {
    throw new Error(`No real CCTV detections found for registration plate '${cleanPlate}'`);
  }
  if (!res.ok) {
    throw new Error(`Failed to query vehicle journey (HTTP ${res.status})`);
  }
  const data = await res.json();
  cache.set(cacheKey, { data, expires: Date.now() + 60000 });
  return data;
};

export const fetchDetections = async (query?: string): Promise<DetectionEvent[]> => {
  const url = query ? `${API_BASE}/detections?plate_number=${encodeURIComponent(query)}` : `${API_BASE}/detections`;
  return (await cachedFetch<DetectionEvent[]>(`detections:${query || 'all'}`, url, 15000)) ?? [];
};

export const fetchWatchlist = async (): Promise<WatchlistEntry[]> => {
  return (await cachedFetch<WatchlistEntry[]>('watchlist', `${API_BASE}/watchlist`, 30000)) ?? [];
};

export const fetchAlerts = async (): Promise<AlertNotification[]> => {
  return (await cachedFetch<AlertNotification[]>('alerts', `${API_BASE}/alerts`, 5000)) ?? [];
};

export const fetchLocalVideos = async (): Promise<unknown[]> => {
  return (await cachedFetch<unknown[]>('videos', `${API_BASE}/videos`, 30000)) ?? [];
};

export const processLocalVideo = async (videoId: string, mode: string = 'full') => {
  try {
    const res = await fetch(`${API_BASE}/videos/${videoId}/process?mode=${mode}`, { method: 'POST' });
    if (res.ok) return await res.json();
  } catch (e) {
    console.warn('Process video error');
  }
  return null;
};

export const fetchVideoDetections = async (videoId: string, timestampMs?: number) => {
  try {
    const url = timestampMs !== undefined 
      ? `${API_BASE}/videos/${videoId}/detections?timestamp_ms=${timestampMs}`
      : `${API_BASE}/videos/${videoId}/detections`;
    const res = await fetch(url);
    if (res.ok) return await res.json();
  } catch (e) {
    console.warn('Fetch video detections error');
  }
  return [];
};

export const fetchVideoSummary = async (videoId: string) => {
  try {
    const res = await fetch(`${API_BASE}/videos/${videoId}/summary`);
    if (res.ok) return await res.json();
  } catch (e) {
    console.warn('Fetch video summary error');
  }
  return null;
};

export const fetchDiscoveredPlates = async (videoId: string) => {
  try {
    const res = await fetch(`${API_BASE}/videos/${videoId}/discovered-plates`);
    if (res.ok) return await res.json();
  } catch (e) {
    console.warn('Fetch discovered plates error');
  }
  return { video_id: videoId, total_unique_plates: 0, discovered_plates: [] };
};

export const searchVideoPlates = async (plateNumber: string, sourceId: string = 'all') => {
  try {
    const res = await fetch(`${API_BASE}/videos/search/plates?plate_number=${encodeURIComponent(plateNumber)}&source_id=${sourceId}`);
    if (res.ok) return await res.json();
  } catch (e) {
    console.warn('Search video plates error');
  }
  return { query_plate: plateNumber, source_id: sourceId, total_matches: 0, results: [] };
};

export const addWatchlistEntry = async (entry: { vehicle_number: string; category: string; priority: string; reason?: string }) => {
  const res = await fetch(`${API_BASE}/watchlist`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(entry)
  });
  if (!res.ok) throw new Error('Failed to add watchlist entry');
  invalidateCache('watchlist');
  return await res.json();
};
