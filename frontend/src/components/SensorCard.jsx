import React from 'react';
import { Gauge, ArrowUpRight, ArrowDownRight, Minus, AlertTriangle, ShieldCheck } from 'lucide-react';

export default function SensorCard({ sensor, onClick = null, isSelected = false }) {
  if (!sensor) return null;

  const {
    id,
    name,
    value,
    unit = '',
    category = 'Pneumatic',
    delta = 0,
    normal_min,
    normal_max,
    roll_mean_1m,
    roll_mean_5m
  } = sensor;

  // Determine warning status based on normal bounds
  const isOutOfRange = (normal_min !== undefined && value < normal_min) || (normal_max !== undefined && value > normal_max);

  const deltaIcon = delta > 0.005 ? (
    <ArrowUpRight className="w-3.5 h-3.5 text-blue-400" />
  ) : delta < -0.005 ? (
    <ArrowDownRight className="w-3.5 h-3.5 text-amber-400" />
  ) : (
    <Minus className="w-3.5 h-3.5 text-slate-500" />
  );

  return (
    <div
      onClick={onClick}
      className={`bg-industrial-850 rounded-2xl p-5 border transition-all relative overflow-hidden group ${
        onClick ? 'cursor-pointer hover:border-blue-500/50 hover:shadow-lg hover:shadow-blue-500/5' : ''
      } ${
        isSelected
          ? 'border-blue-500 shadow-md shadow-blue-500/10 bg-industrial-800'
          : isOutOfRange
          ? 'border-amber-500/40 bg-amber-500/5'
          : 'border-industrial-700/60'
      }`}
    >
      {/* Top row: Name, Category, ID Badge */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <span className="text-[11px] font-mono uppercase tracking-wider text-slate-400 font-semibold block">
            {category}
          </span>
          <h3 className="text-sm font-bold text-slate-100 group-hover:text-blue-300 transition-colors">
            {name}
          </h3>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="px-2 py-0.5 rounded-md bg-industrial-700/60 border border-industrial-600/40 text-xs font-mono font-bold text-blue-400">
            {id}
          </span>
        </div>
      </div>

      {/* Primary Value & Unit */}
      <div className="flex items-baseline justify-between mt-2">
        <div className="flex items-baseline space-x-1.5">
          <span className="text-3xl font-extrabold font-mono text-white tracking-tight">
            {typeof value === 'number' ? value.toFixed(2) : value}
          </span>
          <span className="text-sm font-semibold text-slate-400 font-mono">
            {unit}
          </span>
        </div>

        {/* Delta change */}
        <div className="flex items-center gap-1 bg-industrial-900/80 px-2 py-1 rounded-md border border-industrial-700/50 text-xs font-mono text-slate-300">
          {deltaIcon}
          <span>{delta >= 0 ? `+${delta.toFixed(2)}` : delta.toFixed(2)}</span>
        </div>
      </div>

      {/* Secondary Metrics: 1m and 5m rolling averages */}
      <div className="mt-4 pt-3 border-t border-industrial-700/40 grid grid-cols-2 gap-2 text-xs font-mono text-slate-400">
        <div>
          <span className="text-[10px] text-slate-400 block">1m Avg:</span>
          <span className="font-semibold text-slate-200">{roll_mean_1m !== undefined ? `${roll_mean_1m} ${unit}` : '—'}</span>
        </div>
        <div>
          <span className="text-[10px] text-slate-400 block">5m Avg:</span>
          <span className="font-semibold text-slate-200">{roll_mean_5m !== undefined ? `${roll_mean_5m} ${unit}` : '—'}</span>
        </div>
      </div>

      {/* Normal Range indicator */}
      {normal_min !== undefined && normal_max !== undefined && (
        <div className="mt-2.5 flex items-center justify-between text-[10px] font-mono text-slate-400">
          <span>Target: {normal_min} - {normal_max} {unit}</span>
          {isOutOfRange ? (
            <span className="text-amber-400 flex items-center gap-0.5">
              <AlertTriangle className="w-3 h-3" /> Warning
            </span>
          ) : (
            <span className="text-emerald-400 flex items-center gap-0.5">
              <ShieldCheck className="w-3 h-3" /> Nominal
            </span>
          )}
        </div>
      )}
    </div>
  );
}
