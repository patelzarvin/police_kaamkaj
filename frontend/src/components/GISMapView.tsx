import React from 'react';
import { CameraAsset } from '../types';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import { MapPin, Camera, Layers, CheckCircle2, AlertOctagon } from 'lucide-react';

const greenCamIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

interface GISMapViewProps {
  cameras: CameraAsset[];
}

export const GISMapView: React.FC<GISMapViewProps> = ({ cameras }) => {
  return (
    <div className="p-6 space-y-6">
      <div className="glass-panel rounded-2xl p-6 border border-cyan-900/60 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs uppercase tracking-wider font-semibold">
            <MapPin className="w-4 h-4 text-cyan-400" />
            <span>Statewide GIS Spatial Command Layer</span>
          </div>
          <h2 className="text-xl font-bold text-white mt-1">Gujarat CCTV Grid Spatial Map</h2>
        </div>

        <div className="flex items-center gap-4 text-xs font-mono text-slate-300">
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-emerald-500" /> Online Camera ({cameras.length})</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-rose-500" /> Offline</span>
        </div>
      </div>

      <div className="glass-panel rounded-2xl p-2 border border-cyan-900/80 shadow-2xl h-[600px] overflow-hidden">
        <MapContainer
          center={[23.0276, 72.5074]}
          zoom={8}
          scrollWheelZoom={true}
          className="w-full h-full rounded-xl"
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          />

          {cameras.map((cam) => (
            <Marker
              key={cam.camera_id}
              position={[cam.latitude, cam.longitude]}
              icon={greenCamIcon}
            >
              <Popup>
                <div className="space-y-1.5 p-1">
                  <div className="font-mono text-xs font-bold text-cyan-400">{cam.camera_id}: {cam.name}</div>
                  <div className="text-[11px] text-slate-300">Dept: {cam.department}</div>
                  <div className="text-[11px] text-slate-300">District: {cam.district}</div>
                  <div className="text-[11px] font-mono text-emerald-400 font-bold">Codec: {cam.codec} | {cam.resolution}</div>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
    </div>
  );
};
