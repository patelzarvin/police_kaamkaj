import React, { useState, useEffect, useMemo } from 'react';
import { CameraAsset } from '../types';
import { apiUrl } from '../services/api';
import { Radio, Eye, Video, Cpu, Play, Square, X } from 'lucide-react';

interface LiveCameraGridProps {
  cameras: CameraAsset[];
  onSelectCamera?: (camera: CameraAsset) => void;
}

const VISIBLE_LIMIT = 4;
const SNAPSHOT_INTERVAL_MS = 3000;

export const LiveCameraGrid: React.FC<LiveCameraGridProps> = ({ cameras, onSelectCamera }) => {
  const [activeAIProcessingCams, setActiveAIProcessingCams] = useState<Record<string, boolean>>({});
  const [viewingHlsCam, setViewingHlsCam] = useState<CameraAsset | null>(null);
  const [selectedCam, setSelectedCam] = useState<CameraAsset | null>(null);
  const [snapshotTick, setSnapshotTick] = useState(0);

  const activeCamerasList = useMemo(() => {
    const sorted = [...cameras].sort((a, b) => {
      const parseCam = (id: string) => {
        const m = id.toLowerCase().match(/^cam(\d+)$/);
        return m ? parseInt(m[1], 10) : 9999;
      };
      const pa = parseCam(a.camera_id);
      const pb = parseCam(b.camera_id);
      if (pa !== pb) return pa - pb;
      return a.camera_id.localeCompare(b.camera_id);
    });
    return sorted.slice(0, VISIBLE_LIMIT);
  }, [cameras]);

  useEffect(() => {
    const interval = setInterval(() => setSnapshotTick((t) => t + 1), SNAPSHOT_INTERVAL_MS);
    return () => clearInterval(interval);
  }, []);

  const toggleAIProcessing = (cam: CameraAsset) => {
    const cid = cam.camera_id;
    setActiveAIProcessingCams((prev) => ({ ...prev, [cid]: !prev[cid] }));
  };

  return (
    <div className="p-6 space-y-6 font-sans">
      <div className="glass-panel rounded-2xl p-6 border border-cyan-900/60">
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs uppercase tracking-wider font-semibold">
              <Radio className="w-4 h-4 text-cyan-400" />
              <span>Live CCTV Stream Controller</span>
            </div>
            <h2 className="text-xl font-bold text-white mt-1">Fast Preview Grid ({activeCamerasList.length} cameras)</h2>
          </div>
          <span className="bg-emerald-950 text-emerald-400 border border-emerald-800 px-3.5 py-1.5 rounded-xl font-mono text-xs font-bold">
            {cameras.length} CAMERAS REGISTERED
          </span>
        </div>
      </div>

      {activeCamerasList.length === 0 ? (
        <div className="glass-panel rounded-2xl p-12 text-center text-slate-400 font-mono">
          No cameras loaded yet. Open Registry tab or wait for API sync.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {activeCamerasList.map((cam) => {
            const cid = cam.camera_id;
            const isSelected = selectedCam?.camera_id === cid;
            const isAIProcessing = !!activeAIProcessingCams[cid];
            const frameUrl = `${apiUrl(`/api/cameras/${cid}/frame`)}?v=${snapshotTick}`;

            return (
              <div
                key={cid}
                className={`glass-panel rounded-2xl overflow-hidden transition-all duration-300 border flex flex-col ${
                  isSelected ? 'border-cyan-400 ring-2 ring-cyan-500/50' : 'border-cyan-900/60 hover:border-cyan-500/80'
                }`}
              >
                <div className="bg-[#0c1322] px-4 py-3 border-b border-cyan-950 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="bg-cyan-950 text-cyan-400 border border-cyan-800 text-xs font-mono px-2 py-0.5 rounded font-bold">
                      {cid}
                    </span>
                    <span className="text-xs font-bold text-white truncate max-w-[180px]">{cam.name}</span>
                  </div>
                  <span className="bg-emerald-950/80 text-emerald-400 border border-emerald-800/60 px-2 py-0.5 rounded text-[10px] font-mono font-bold">
                    ONLINE
                  </span>
                </div>

                <div className="relative bg-black aspect-video overflow-hidden">
                  <img
                    src={frameUrl}
                    alt={cam.name}
                    loading="lazy"
                    decoding="async"
                    className="w-full h-full object-cover"
                  />
                  {isAIProcessing && (
                    <div className="absolute top-2 right-2 bg-emerald-950/90 text-emerald-300 border border-emerald-700 px-2 py-0.5 rounded text-[10px] font-mono font-bold flex items-center gap-1">
                      <Cpu className="w-3 h-3" /> AI ACTIVE
                    </div>
                  )}
                </div>

                <div className="p-3 bg-[#0a0f1d] border-t border-cyan-950 grid grid-cols-2 gap-2 font-mono text-xs">
                  <button
                    onClick={() => setViewingHlsCam(cam)}
                    className="bg-slate-900 border border-slate-700 hover:border-cyan-400 text-slate-300 px-3 py-1.5 rounded-xl font-semibold flex items-center justify-center gap-1.5"
                  >
                    <Eye className="w-3.5 h-3.5 text-cyan-400" /> VIEW LIVE
                  </button>
                  {isAIProcessing ? (
                    <button
                      onClick={() => toggleAIProcessing(cam)}
                      className="bg-rose-950 border border-rose-800 text-rose-300 px-3 py-1.5 rounded-xl font-bold flex items-center justify-center gap-1.5"
                    >
                      <Square className="w-3.5 h-3.5" /> STOP AI
                    </button>
                  ) : (
                    <button
                      onClick={() => { setSelectedCam(cam); toggleAIProcessing(cam); onSelectCamera?.(cam); }}
                      className="bg-emerald-950 border border-emerald-800 text-emerald-300 px-3 py-1.5 rounded-xl font-bold flex items-center justify-center gap-1.5"
                    >
                      <Play className="w-3.5 h-3.5" /> START AI
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {viewingHlsCam && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-panel border border-cyan-800 rounded-2xl max-w-3xl w-full p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs font-bold uppercase">
                <Video className="w-4 h-4" /> {viewingHlsCam.name}
              </div>
              <button onClick={() => setViewingHlsCam(null)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="relative bg-black aspect-video rounded-xl overflow-hidden border border-cyan-900">
              <img
                src={apiUrl(`/api/cameras/${viewingHlsCam.camera_id}/stream`)}
                alt={viewingHlsCam.name}
                className="w-full h-full object-contain"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
