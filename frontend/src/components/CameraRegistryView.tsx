import React from 'react';
import { CameraAsset } from '../types';
import { Camera, Radio, Server, CheckCircle2, ShieldCheck } from 'lucide-react';

interface CameraRegistryViewProps {
  cameras: CameraAsset[];
}

export const CameraRegistryView: React.FC<CameraRegistryViewProps> = ({ cameras }) => {
  return (
    <div className="p-6 space-y-6">
      <div className="glass-panel rounded-2xl p-6 border border-cyan-900/60 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs uppercase tracking-wider font-semibold">
            <Camera className="w-4 h-4 text-cyan-400" />
            <span>Statewide Asset Inventory & Metadata Contract</span>
          </div>
          <h2 className="text-xl font-bold text-white mt-1">CCTV Camera Registry & Catalog</h2>
        </div>

        <div className="flex items-center gap-3">
          <div className="bg-cyan-950 border border-cyan-800 text-cyan-400 text-xs font-mono px-3 py-1.5 rounded-lg flex items-center gap-2">
            <Server className="w-4 h-4" />
            <span>CONTRACT: /api/ingest</span>
          </div>
        </div>
      </div>

      <div className="glass-panel rounded-2xl overflow-hidden border border-cyan-900/80 shadow-2xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-[#0f172a] text-[11px] font-mono text-cyan-400 uppercase tracking-wider border-b border-cyan-950">
                <th className="py-3.5 px-4">Camera ID</th>
                <th className="py-3.5 px-4">Camera Name & Location</th>
                <th className="py-3.5 px-4">Department</th>
                <th className="py-3.5 px-4">District</th>
                <th className="py-3.5 px-4">Codec</th>
                <th className="py-3.5 px-4">Resolution</th>
                <th className="py-3.5 px-4">Protocol</th>
                <th className="py-3.5 px-4">Live Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-cyan-950 text-xs font-mono text-slate-200">
              {cameras.map((cam) => (
                <tr key={cam.camera_id} className="hover:bg-cyan-950/40 transition-colors">
                  <td className="py-3.5 px-4 font-bold text-cyan-400">{cam.camera_id}</td>
                  <td className="py-3.5 px-4">
                    <div className="font-bold text-white">{cam.name}</div>
                    <div className="text-[10px] text-slate-400">{cam.address}</div>
                  </td>
                  <td className="py-3.5 px-4 text-slate-300">{cam.department}</td>
                  <td className="py-3.5 px-4 text-slate-300">{cam.district}</td>
                  <td className="py-3.5 px-4">
                    <span className="bg-slate-800 text-cyan-300 px-2 py-0.5 rounded font-bold">{cam.codec}</span>
                  </td>
                  <td className="py-3.5 px-4 text-slate-300">{cam.resolution}</td>
                  <td className="py-3.5 px-4 text-emerald-400 font-bold">{cam.stream_type} (TCP)</td>
                  <td className="py-3.5 px-4">
                    <span className="bg-emerald-950 text-emerald-400 border border-emerald-800 px-2.5 py-0.5 rounded-full text-[10px] font-bold flex items-center gap-1.5 w-fit">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                      {cam.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
