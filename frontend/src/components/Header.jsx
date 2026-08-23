import React, { useState, useEffect } from 'react';
import { Train, Activity, Clock, ShieldCheck, Database, Radio } from 'lucide-react';

export default function Header({ systemHealth = 'ONLINE', lastTimestamp = null, isSimulating = false }) {
  const [currentTime, setCurrentTime] = useState(new Date().toLocaleTimeString());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="bg-industrial-850 border-b border-industrial-700/60 px-6 py-4 sticky top-0 z-30 shadow-lg">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Brand & Subtitle */}
        <div className="flex items-center space-x-3.5">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-700 flex items-center justify-center shadow-md shadow-blue-500/20">
            <Train className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                METROGUARD <span className="text-blue-400 font-mono text-xs bg-blue-500/20 px-2 py-0.5 rounded border border-blue-500/30">AI</span>
              </h1>
              <span className="text-xs font-mono text-slate-400 hidden sm:inline">v1.0.0</span>
            </div>
            <p className="text-xs text-slate-400 font-medium">
              Predictive Maintenance Intelligence for Metro Train Air Compressors
            </p>
          </div>
        </div>

        {/* Live System Status Badges */}
        <div className="flex flex-wrap items-center gap-3 text-xs font-mono">
          {/* Simulation Indicator */}
          {isSimulating && (
            <div className="flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 px-3 py-1.5 rounded-lg animate-pulse">
              <Radio className="w-3.5 h-3.5" />
              <span>SIMULATION STREAMING</span>
            </div>
          )}

          {/* Dataset Status */}
          <div className="flex items-center gap-2 bg-industrial-700/50 border border-industrial-600/50 px-3 py-1.5 rounded-lg text-slate-300">
            <Database className="w-3.5 h-3.5 text-cyan-400" />
            <span>Dataset: <strong className="text-white">MetroPT-3</strong> (1.5M Records)</span>
          </div>

          {/* Telemetry Clock */}
          <div className="flex items-center gap-2 bg-industrial-700/50 border border-industrial-600/50 px-3 py-1.5 rounded-lg text-slate-300">
            <Clock className="w-3.5 h-3.5 text-blue-400" />
            <span>Telemetry: <strong className="text-blue-300">{lastTimestamp || '2020-09-01 03:59:20'}</strong></span>
          </div>

          {/* System Online Status */}
          <div className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 px-3 py-1.5 rounded-lg font-semibold glow-green">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            <Activity className="w-3.5 h-3.5" />
            <span>SYSTEM: {systemHealth}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
