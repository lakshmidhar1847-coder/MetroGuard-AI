import React from 'react';
import { ShieldAlert, Activity, CheckCircle, AlertTriangle, AlertOctagon } from 'lucide-react';

export default function RiskGauge({ riskProbability = 0.0004, riskPercentage = 0.04, status = 'NORMAL', threshold = 0.10 }) {
  // Clamp between 0 and 100
  const pct = Math.min(100, Math.max(0, riskPercentage));
  
  // Calculate stroke dash for semi-circle or full ring
  const radius = 64;
  const circumference = 2 * Math.PI * radius;
  // Let's use a 240-degree arc
  const arcFraction = 240 / 360;
  const totalArc = circumference * arcFraction;
  const strokeDashoffset = totalArc - (pct / 100) * totalArc;

  const colorMap = {
    NORMAL: {
      stroke: '#10b981', // emerald-500
      text: 'text-emerald-400',
      bg: 'bg-emerald-500/10',
      border: 'border-emerald-500/30',
      label: 'NORMAL',
      desc: 'Nominal pneumatic delivery. Air leak risk within baseline tolerances.'
    },
    WARNING: {
      stroke: '#f59e0b', // amber-500
      text: 'text-amber-400',
      bg: 'bg-amber-500/10',
      border: 'border-amber-500/30',
      label: 'ELEVATED RISK',
      desc: 'Significant pneumatic volatility detected. Impending failure possible within 30 min.'
    },
    'HIGH RISK': {
      stroke: '#ef4444', // rose-500
      text: 'text-rose-400',
      bg: 'bg-rose-500/10',
      border: 'border-rose-500/30',
      label: 'HIGH FAILURE RISK',
      desc: 'Critical air leak signatures recognized. Recommend immediate maintenance protocol.'
    }
  };

  const normStatus = (status || 'NORMAL').toUpperCase();
  const theme = colorMap[normStatus] || colorMap.NORMAL;

  return (
    <div className="bg-industrial-850 rounded-2xl p-6 border border-industrial-700/60 flex flex-col items-center justify-between text-center relative overflow-hidden shadow-xl">
      <div className="w-full flex items-center justify-between mb-4">
        <span className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-400">
          AI Risk Assessment Engine
        </span>
        <span className="text-[11px] font-mono text-blue-400 bg-blue-500/10 border border-blue-500/20 px-2 py-0.5 rounded">
          Horizon: 30 Min
        </span>
      </div>

      {/* Radial Gauge SVG */}
      <div className="relative w-44 h-44 flex items-center justify-center my-2">
        <svg className="w-full h-full -rotate-90 transform" viewBox="0 0 160 160">
          {/* Background Track */}
          <circle
            cx="80"
            cy="80"
            r={radius}
            stroke="#1f2b48"
            strokeWidth="12"
            fill="transparent"
            strokeDasharray={totalArc}
            strokeDashoffset="0"
            strokeLinecap="round"
            style={{
              transformOrigin: '50% 50%',
              transform: 'rotate(-30deg)'
            }}
          />
          {/* Progress Fill */}
          <circle
            cx="80"
            cy="80"
            r={radius}
            stroke={theme.stroke}
            strokeWidth="12"
            fill="transparent"
            strokeDasharray={totalArc}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-700 ease-out"
            style={{
              transformOrigin: '50% 50%',
              transform: 'rotate(-30deg)'
            }}
          />
        </svg>

        {/* Center Text */}
        <div className="absolute flex flex-col items-center justify-center">
          <span className={`text-4xl font-extrabold font-mono tracking-tight ${theme.text}`}>
            {pct < 0.1 && pct > 0 ? pct.toFixed(2) : pct.toFixed(1)}%
          </span>
          <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider mt-0.5">
            Failure Risk
          </span>
        </div>
      </div>

      {/* Calibrated Threshold Information */}
      <div className="w-full mt-3 space-y-2">
        <div className={`p-3 rounded-xl border ${theme.bg} ${theme.border} text-left`}>
          <div className="flex items-center justify-between text-xs font-mono font-bold mb-1">
            <span className={theme.text}>{theme.label}</span>
            <span className="text-slate-400">Trigger: &ge; {(threshold * 100).toFixed(1)}%</span>
          </div>
          <p className="text-xs text-slate-300 leading-snug">
            {theme.desc}
          </p>
        </div>

        <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 px-1">
          <span>0% Normal</span>
          <span className="text-amber-400">10% Alert</span>
          <span className="text-rose-400">70% Critical</span>
        </div>
      </div>
    </div>
  );
}
