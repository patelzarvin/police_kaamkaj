export interface CameraAsset {
  camera_id: string;
  name: string;
  department: string;
  district: string;
  city: string;
  latitude: number;
  longitude: number;
  address?: string;
  stream_type: string;
  rtsp_url?: string;
  hls_url?: string;
  webrtc_url?: string;
  codec: string;
  resolution: string;
  fps: number;
  status: 'ONLINE' | 'OFFLINE' | 'DEGRADED';
  last_seen: string;
}

export interface DetectionEvent {
  detection_id: string;
  camera_id: string;
  camera_name?: string;
  source_type?: string;
  timestamp: string;
  vehicle_class: string;
  track_id: number;
  plate_number: string;
  plate_confidence: number;
  detection_confidence: number;
  bbox_x1: number;
  bbox_y1: number;
  bbox_x2: number;
  bbox_y2: number;
  plate_bbox_x1?: number;
  plate_bbox_y1?: number;
  plate_bbox_x2?: number;
  plate_bbox_y2?: number;
  image_path?: string;
  plate_crop_path?: string;
  latitude: number;
  longitude: number;
  watchlist_flag?: string;
}

export interface JourneyStep {
  step_number: number;
  camera_id: string;
  camera_name: string;
  timestamp: string;
  formatted_time: string;
  latitude: number;
  longitude: number;
  plate_number: string;
  vehicle_class: string;
  plate_confidence: number;
  detection_confidence: number;
  image_path?: string;
  plate_crop_path?: string;
  watchlist_status: string;
}

export interface VehicleJourney {
  plate_number: string;
  vehicle_class: string;
  total_detections: number;
  first_seen: string;
  last_seen: string;
  watchlist_status: string;
  watchlist_category?: string;
  journey_steps: JourneyStep[];
  route_coordinates: [number, number][]; // [[lat, lng], [lat, lng]]
}

export interface WatchlistEntry {
  id: number;
  vehicle_number: string;
  category: 'STOLEN' | 'WANTED' | 'SUSPICIOUS' | 'UNREGISTERED';
  priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  reason?: string;
  added_by: string;
  is_active: boolean;
  created_at: string;
}

export interface AlertNotification {
  id: number;
  detection_id?: string;
  watchlist_id?: number;
  timestamp: string;
  camera_id: string;
  camera_name?: string;
  vehicle_number: string;
  alert_category: string;
  priority: 'CRITICAL' | 'HIGH' | 'MEDIUM';
  status: 'UNREAD' | 'READ' | 'ACKNOWLEDGED' | 'DISPATCHED';
  notes?: string;
  location_name: string;
  latitude: number;
  longitude: number;
}

export interface SystemMetrics {
  total_cameras: number;
  online_cameras: number;
  offline_cameras: number;
  degraded_cameras: number;
  total_detections_24h: number;
  active_alerts: number;
  ai_workers_active: number;
  avg_inference_ms: number;
  stream_gateway_status: string;
  uptime_seconds: number;
}
