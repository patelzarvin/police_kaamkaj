import React, { useState } from 'react';
import { WatchlistEntry, AlertNotification } from '../types';
import { AlertOctagon, Plus, ShieldAlert, CheckCircle, Clock, Trash2, Filter } from 'lucide-react';
import { addWatchlistEntry } from '../services/api';

interface WatchlistAlertDeskProps {
  watchlist: WatchlistEntry[];
  alerts: AlertNotification[];
  onRefresh: () => void;
}

export const WatchlistAlertDesk: React.FC<WatchlistAlertDeskProps> = ({ watchlist, alerts, onRefresh }) => {
  const [showAddModal, setShowAddModal] = useState(false);
  const [newVehicle, setNewVehicle] = useState('');
  const [newCategory, setNewCategory] = useState('STOLEN');
  const [newPriority, setNewPriority] = useState('HIGH');
  const [newReason, setNewReason] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newVehicle.trim()) return;
    setSubmitting(true);
    try {
      await addWatchlistEntry({
        vehicle_number: newVehicle.trim(),
        category: newCategory,
        priority: newPriority,
        reason: newReason
      });
      setShowAddModal(false);
      setNewVehicle('');
      setNewReason('');
      onRefresh();
    } catch (e) {
      alert('Error adding vehicle to watchlist');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="glass-panel rounded-2xl p-6 border border-cyan-900/60 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-rose-400 font-mono text-xs uppercase tracking-wider font-semibold">
            <AlertOctagon className="w-4 h-4 text-rose-500" />
            <span>State Police Intelligence Operations</span>
          </div>
          <h2 className="text-xl font-bold text-white mt-1">Watchlist & Real-Time Alert Desk</h2>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs px-5 py-2.5 rounded-xl transition-all shadow-lg flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          <span>ADD WATCHLIST VEHICLE</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Watchlist Management Panel */}
        <div className="glass-panel rounded-2xl p-5 border border-cyan-900/80 space-y-4">
          <h3 className="text-base font-bold text-white font-mono uppercase flex items-center gap-2 border-b border-cyan-950 pb-3">
            <ShieldAlert className="w-5 h-5 text-cyan-400" />
            <span>Active Police Watchlist Database ({watchlist.length})</span>
          </h3>

          <div className="space-y-3">
            {watchlist.map((item) => (
              <div key={item.id} className="bg-[#0f172a] border border-cyan-900/60 rounded-xl p-4 flex items-center justify-between gap-4 hover:border-cyan-400 transition-all">
                <div className="space-y-1">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-base font-extrabold text-white bg-cyan-950 px-3 py-1 rounded border border-cyan-700">
                      {item.vehicle_number}
                    </span>
                    <span className="text-xs font-mono font-bold bg-rose-950 text-rose-300 border border-rose-800 px-2 py-0.5 rounded uppercase">
                      {item.category}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300">{item.reason}</p>
                </div>
                <div className="text-[11px] font-mono text-slate-400 text-right">
                  <div>Added by: {item.added_by}</div>
                  <div className="text-rose-400 font-bold">{item.priority} PRIORITY</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Real-Time Alerts Dispatch Feed */}
        <div className="glass-panel rounded-2xl p-5 border border-rose-900/80 space-y-4">
          <h3 className="text-base font-bold text-rose-400 font-mono uppercase flex items-center gap-2 border-b border-rose-950 pb-3">
            <AlertOctagon className="w-5 h-5 text-rose-500" />
            <span>Automated Real-Time Alerts Feed</span>
          </h3>

          <div className="space-y-3">
            {alerts.map((alert) => (
              <div key={alert.id} className="bg-rose-950/40 border border-rose-800 rounded-xl p-4 space-y-2 hover:border-rose-400 transition-all">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-base font-extrabold text-white bg-rose-950 px-3 py-1 rounded border border-rose-700">
                    {alert.vehicle_number}
                  </span>
                  <span className="text-xs font-mono font-bold bg-rose-900 text-rose-100 px-2.5 py-0.5 rounded-full uppercase">
                    {alert.priority} PRIORITY
                  </span>
                </div>
                <p className="text-xs text-slate-200 font-semibold">{alert.notes}</p>
                <div className="text-[11px] font-mono text-slate-400 flex items-center justify-between pt-2 border-t border-rose-900/50">
                  <span>Camera: {alert.camera_name || alert.camera_id}</span>
                  <span>{new Date(alert.timestamp).toLocaleTimeString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Add Watchlist Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="glass-panel rounded-2xl p-6 border border-cyan-500 max-w-md w-full space-y-4">
            <h3 className="text-lg font-bold text-white font-mono uppercase">Add Vehicle to Police Watchlist</h3>
            <form onSubmit={handleAddSubmit} className="space-y-4">
              <div>
                <label className="text-xs font-mono text-slate-300 block mb-1">Registration Number</label>
                <input
                  type="text"
                  placeholder="e.g. GJ01AB1234"
                  value={newVehicle}
                  onChange={(e) => setNewVehicle(e.target.value)}
                  className="w-full bg-[#0a0e17] border border-cyan-800 rounded-xl py-2 px-3 text-sm font-mono text-white focus:outline-none focus:border-cyan-400"
                  required
                />
              </div>

              <div>
                <label className="text-xs font-mono text-slate-300 block mb-1">Category</label>
                <select
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                  className="w-full bg-[#0a0e17] border border-cyan-800 rounded-xl py-2 px-3 text-sm font-mono text-white"
                >
                  <option value="STOLEN">STOLEN VEHICLE</option>
                  <option value="WANTED">WANTED CRIMINAL</option>
                  <option value="SUSPICIOUS">SUSPICIOUS ACTIVITY</option>
                  <option value="UNREGISTERED">UNREGISTERED PLATE</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-mono text-slate-300 block mb-1">Reason / FIR Details</label>
                <textarea
                  placeholder="Enter FIR number or reason..."
                  value={newReason}
                  onChange={(e) => setNewReason(e.target.value)}
                  className="w-full bg-[#0a0e17] border border-cyan-800 rounded-xl py-2 px-3 text-sm font-mono text-white focus:outline-none focus:border-cyan-400"
                  rows={3}
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-mono text-slate-400 hover:text-white"
                >
                  CANCEL
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs px-5 py-2 rounded-xl"
                >
                  {submitting ? 'SAVING...' : 'ADD TO WATCHLIST'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
