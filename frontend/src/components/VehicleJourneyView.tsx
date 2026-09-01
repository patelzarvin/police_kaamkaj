import React, { useState, useEffect } from 'react';
import { Search, Route, ShieldAlert, Camera, MapPin, Clock, ArrowRight, CheckCircle2, AlertTriangle, Image as ImageIcon, Video, Database } from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import L from 'leaflet';
import { fetchVehicleJourney } from '../services/api';
import { VehicleJourney } from '../types';

const cameraMarkerIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-cyan.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

interface VehicleJourneyViewProps {
  initialPlate?: string;
}

export const VehicleJourneyView: React.FC<VehicleJourneyViewProps> = ({ initialPlate = '' }) => {
  const [plateQuery, setPlateQuery] = useState(initialPlate);
  const [journeyData, setJourneyData] = useState<VehicleJourney | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [samplePlates, setSamplePlates] = useState<string[]>([]);

  useEffect(() => {
    fetch('/api/vehicles/sample-plates')
      .then(r => r.json())
      .then(data => {
        if (data.sample_plates && Array.isArray(data.sample_plates)) {
          setSamplePlates(data.sample_plates);
        }
      })
      .catch(e => console.error("Error fetching sample plates:", e));
  }, []);

  const handleSearch = async (plateToSearch: string) => {
    if (!plateToSearch.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchVehicleJourney(plateToSearch.trim());
      setJourneyData(data);
    } catch (e: any) {
      if (plateToSearch.trim().toUpperCase() === 'DL2CA27993') {
        setError("DL2CA27993 was not genuinely verified from the real-world Getty footage.");
      } else {
        setError(e.message || `No CCTV detection history found for registration plate '${plateToSearch}'`);
      }
      setJourneyData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (initialPlate) {
      handleSearch(initialPlate);
    }
  }, [initialPlate]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSearch(plateQuery);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Search Header */}
      <div className="glass-panel rounded-2xl p-6 border border-cyan-900/60 shadow-xl space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs uppercase tracking-wider font-semibold">
              <Route className="w-4 h-4 text-cyan-400" />
              <span>Real-Time Multi-Camera Trajectory Engine</span>
            </div>
            <h2 className="text-xl font-bold text-white mt-1">Vehicle Movement History & Route Analysis</h2>
          </div>

          <div className="flex flex-col md:flex-row gap-3 items-end md:items-center">
            {samplePlates.length > 0 && (
              <div className="flex items-center gap-2 bg-[#0a0e17] px-3 py-1.5 rounded-xl border border-cyan-800">
                <Database className="w-3.5 h-3.5 text-cyan-400" />
                <span className="text-[11px] font-mono text-cyan-300 font-bold">Use Sample DB Plate:</span>
                <select
                  onChange={(e) => {
                    if (e.target.value) {
                      setPlateQuery(e.target.value);
                      handleSearch(e.target.value);
                    }
                  }}
                  className="bg-[#0f172a] text-cyan-200 font-mono text-xs border border-cyan-700 rounded-lg px-2 py-1 focus:outline-none focus:border-cyan-400 cursor-pointer"
                >
                  <option value="">-- Select DB Plate --</option>
                  {samplePlates.map((p) => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                </select>
              </div>
            )}

            <form onSubmit={handleSubmit} className="flex gap-3 w-full md:w-auto">
              <div className="relative flex-1 md:w-80">
                <input
                  type="text"
                  placeholder="Enter Plate Number (e.g. GJ01AB1234)..."
                  value={plateQuery}
                  onChange={(e) => setPlateQuery(e.target.value)}
                  className="w-full bg-[#0a0e17] border border-cyan-500/60 rounded-xl py-2.5 pl-10 pr-4 text-sm font-mono text-cyan-100 placeholder-slate-500 focus:outline-none focus:border-cyan-400"
                />
                <Search className="w-4 h-4 text-cyan-400 absolute left-3.5 top-3" />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="bg-cyan-500 hover:bg-cyan-400 text-black font-extrabold text-xs px-6 py-2.5 rounded-xl transition-all shadow-md cyan-glow flex items-center gap-2"
              >
                {loading ? 'SEARCHING...' : 'RECONSTRUCT'}
              </button>
            </form>
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-rose-950/80 border border-rose-800 text-rose-200 p-6 rounded-2xl text-center space-y-2">
          <AlertTriangle className="w-8 h-8 text-rose-400 mx-auto" />
          <div className="font-mono text-base font-bold text-white">{error}</div>
          <p className="text-xs text-slate-300 font-mono">
            No matching vehicle found in database logs. Please verify the registration plate number.
          </p>
        </div>
      )}

      {!journeyData && !error && !loading && (
        <div className="glass-panel rounded-2xl p-12 text-center text-slate-400 font-mono space-y-3">
          <Search className="w-12 h-12 text-cyan-500/40 mx-auto" />
          <div className="text-base text-slate-200 font-bold">Search Vehicle Registration Plate</div>
          <p className="text-xs max-w-md mx-auto">
            Enter a registration plate above or select from DB Stored Sample Plates to search real PostGIS detection logs and map chronological camera movements.
          </p>
        </div>
      )}

      {journeyData && (
        <>
          {/* Vehicle Metadata Summary Bar */}
          <div className="glass-panel rounded-2xl p-5 border border-cyan-500/40 bg-gradient-to-r from-[#131b2e] via-[#0f172a] to-cyan-950/40 shadow-2xl flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="bg-cyan-950 border-2 border-cyan-400 text-cyan-300 font-mono text-xl font-extrabold px-4 py-2 rounded-xl tracking-wider shadow-inner">
                {journeyData.plate_number}
              </div>
              <div>
                <div className="text-xs text-slate-400 font-mono">VEHICLE TYPE: <span className="text-white font-bold">{journeyData.vehicle_class}</span></div>
                <div className="text-xs text-slate-400 font-mono mt-0.5">TOTAL DETECTIONS: <span className="text-cyan-400 font-bold">{journeyData.total_detections} Camera Nodes</span></div>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div>
                <div className="text-[11px] text-slate-400 font-mono">FIRST SEEN</div>
                <div className="text-xs font-mono text-slate-200 font-semibold">{new Date(journeyData.first_seen).toLocaleTimeString()}</div>
              </div>
              <ArrowRight className="w-4 h-4 text-cyan-500" />
              <div>
                <div className="text-[11px] text-slate-400 font-mono">LAST SEEN</div>
                <div className="text-xs font-mono text-slate-200 font-semibold">{new Date(journeyData.last_seen).toLocaleTimeString()}</div>
              </div>

              <div className={`px-4 py-2 rounded-xl border text-xs font-mono font-extrabold uppercase flex items-center gap-1.5 ${
                journeyData.watchlist_status !== 'CLEAR'
                  ? 'bg-rose-950/80 border-rose-700 text-rose-300 animate-pulse-red'
                  : 'bg-emerald-950/80 border-emerald-700 text-emerald-300'
              }`}>
                {journeyData.watchlist_status !== 'CLEAR' ? (
                  <>
                    <ShieldAlert className="w-4 h-4 text-rose-400" />
                    <span>WATCHLIST: {journeyData.watchlist_status}</span>
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <span>STATUS: CLEAR</span>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Chronological Journey Flow Cards */}
          <div className="glass-panel rounded-2xl p-5 border border-cyan-900/60 space-y-4">
            <h3 className="text-sm font-mono font-bold text-cyan-400 uppercase tracking-wider flex items-center gap-2">
              <Clock className="w-4 h-4 text-cyan-400" />
              <span>Chronological Detection Timeline</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {journeyData.journey_steps.map((step) => {
                const isStockVideo = step.camera_id.includes('STOCK') || step.camera_id.includes('LOCAL') || step.camera_id.includes('FILE');
                
                return (
                  <div key={step.step_number} className="bg-[#0f172a] border border-cyan-900/80 rounded-xl p-4 space-y-3 relative hover:border-cyan-400 transition-all shadow-lg">
                    <div className="flex items-center justify-between border-b border-cyan-950 pb-2">
                      <span className="bg-cyan-950 text-cyan-400 border border-cyan-800 text-xs font-mono px-2 py-0.5 rounded-full font-bold">
                        NODE #{step.step_number}
                      </span>
                      <span className="text-xs font-mono text-slate-300 font-bold">{step.formatted_time}</span>
                    </div>

                    <div>
                      <div className="text-xs font-bold text-white flex items-center gap-1">
                        <Camera className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                        <span className="truncate">{step.camera_name}</span>
                      </div>
                      <div className="text-[11px] font-mono text-slate-400 flex items-center gap-1 mt-1">
                        <MapPin className="w-3 h-3 text-rose-400" />
                        <span>{step.latitude.toFixed(4)}, {step.longitude.toFixed(4)}</span>
                      </div>
                    </div>

                    {/* REAL Video Bounding Box Crop & Plate Crop Images Rendered from Backend */}
                    <div className="grid grid-cols-2 gap-2">
                      <div className="rounded-lg overflow-hidden border border-cyan-950 bg-black aspect-video relative group flex items-center justify-center">
                        <img
                          src={step.image_path ? (step.image_path.startsWith('http') ? step.image_path : `${step.image_path.startsWith('/') ? '' : '/'}${step.image_path}`) : '/static/crops/vehicle_crop_sample.jpg'}
                          alt={`Vehicle Crop at ${step.camera_name}`}
                          className="w-full h-full object-cover group-hover:scale-105 transition-all"
                          onError={(e) => {
                            (e.target as HTMLImageElement).src = '/static/crops/vehicle_crop_sample.jpg';
                          }}
                        />
                        <div className="absolute bottom-1 left-1 bg-black/90 px-1.5 py-0.5 rounded text-[9px] font-mono text-cyan-300 font-bold border border-cyan-800">
                          Vehicle Photo
                        </div>
                      </div>

                      <div className="rounded-lg overflow-hidden border border-emerald-950 bg-black aspect-video relative group flex items-center justify-center">
                        <img
                          src={step.plate_crop_path ? (step.plate_crop_path.startsWith('http') ? step.plate_crop_path : `${step.plate_crop_path.startsWith('/') ? '' : '/'}${step.plate_crop_path}`) : '/static/crops/plate_crop_sample.jpg'}
                          alt={`Plate Crop at ${step.camera_name}`}
                          className="w-full h-full object-contain p-1 group-hover:scale-105 transition-all"
                          onError={(e) => {
                            (e.target as HTMLImageElement).src = '/static/crops/plate_crop_sample.jpg';
                          }}
                        />
                        <div className="absolute bottom-1 left-1 bg-black/90 px-1.5 py-0.5 rounded text-[9px] font-mono text-emerald-300 font-bold border border-emerald-800">
                          Plate Crop
                        </div>
                      </div>
                    </div>

                    {/* Clear Source Label UI distinguishing Synthetic, Real-world local video, and Sentinel Live */}
                    <div className="text-[11px] font-mono flex items-center justify-between pt-1">
                      <span className="text-slate-400">Data Source:</span>
                      <span className={
                        step.camera_id === 'STOCK_VIDEO_CAM'
                          ? "text-amber-400 font-bold bg-amber-950/80 border border-amber-800 px-2 py-0.5 rounded"
                          : step.camera_id.startsWith('SYNTHETIC')
                          ? "text-purple-400 font-bold bg-purple-950/80 border border-purple-800 px-2 py-0.5 rounded"
                          : "text-emerald-400 font-bold bg-emerald-950/80 border border-emerald-800 px-2 py-0.5 rounded"
                      }>
                        {step.camera_id === 'STOCK_VIDEO_CAM'
                          ? 'REAL_WORLD_LOCAL_VIDEO (gettyimages-1164849900-640_adpp.mp4)'
                          : step.camera_id.startsWith('SYNTHETIC')
                          ? 'SYNTHETIC_TEST_VIDEO'
                          : 'SENTINEL_LIVE_CAMERA'}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* GIS Route Polyline Map */}
          <div className="glass-panel rounded-2xl p-5 border border-cyan-900/60 space-y-4">
            <h3 className="text-sm font-mono font-bold text-cyan-400 uppercase tracking-wider flex items-center gap-2">
              <MapPin className="w-4 h-4 text-cyan-400" />
              <span>GIS Route Map & Spatial Trajectory</span>
            </h3>

            <div className="h-96 rounded-xl overflow-hidden border border-cyan-900 shadow-2xl">
              <MapContainer
                center={journeyData.route_coordinates[0] || [23.0276, 72.5074]}
                zoom={11}
                scrollWheelZoom={false}
                className="w-full h-full"
              >
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                  url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                />

                {journeyData.journey_steps.map((step) => (
                  <Marker
                    key={step.step_number}
                    position={[step.latitude, step.longitude]}
                    icon={cameraMarkerIcon}
                  >
                    <Popup>
                      <div className="space-y-1">
                        <div className="font-bold text-xs text-cyan-400 font-mono">Node #{step.step_number}: {step.camera_name}</div>
                        <div className="text-[11px] text-slate-300">Time: {step.formatted_time}</div>
                        <div className="text-[11px] font-mono text-cyan-300">Plate: {step.plate_number}</div>
                      </div>
                    </Popup>
                  </Marker>
                ))}

                <Polyline
                  positions={journeyData.route_coordinates}
                  color="#00f0ff"
                  weight={4}
                  dashArray="8, 8"
                />
              </MapContainer>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
