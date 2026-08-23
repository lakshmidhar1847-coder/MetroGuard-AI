import React from 'react';
import { CheckCircle2, AlertTriangle, AlertOctagon, Eye, ShieldAlert, Activity } from 'lucide-react';

export default function StatusBadge({ status = 'NORMAL', size = 'md' }) {
  const normStatus = (status || 'NORMAL').toUpperCase();

  const configs = {
    NORMAL: {
      bg: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400',
      dot: 'bg-emerald-400',
      icon: CheckCircle2,
      glow: 'glow-green',
      label: 'NORMAL'
    },
    MONITOR: {
      bg: 'bg-cyan-500/10 border-cyan-500/30 text-cyan-300',
      dot: 'bg-cyan-400',
      icon: Eye,
      glow: 'glow-blue',
      label: 'MONITOR'
    },
    'ANOMALY WARNING': {
      bg: 'bg-purple-500/10 border-purple-500/30 text-purple-300',
      dot: 'bg-purple-400',
      icon: Activity,
      glow: 'glow-purple',
      label: 'ANOMALY WARNING'
    },
    'FAILURE WARNING': {
      bg: 'bg-amber-500/10 border-amber-500/30 text-amber-400',
      dot: 'bg-amber-400',
      icon: AlertTriangle,
      glow: 'glow-amber',
      label: 'FAILURE WARNING'
    },
    WARNING: {
      bg: 'bg-amber-500/10 border-amber-500/30 text-amber-400',
      dot: 'bg-amber-400',
      icon: AlertTriangle,
      glow: 'glow-amber',
      label: 'WARNING'
    },
    ELEVATED: {
      bg: 'bg-purple-500/10 border-purple-500/30 text-purple-300',
      dot: 'bg-purple-400',
      icon: Activity,
      glow: 'glow-purple',
      label: 'ELEVATED'
    },
    HIGH: {
      bg: 'bg-rose-500/10 border-rose-500/30 text-rose-400',
      dot: 'bg-rose-400',
      icon: AlertOctagon,
      glow: 'glow-red',
      label: 'HIGH'
    },
    'HIGH RISK': {
      bg: 'bg-rose-500/10 border-rose-500/30 text-rose-400',
      dot: 'bg-rose-400',
      icon: ShieldAlert,
      glow: 'glow-red',
      label: 'HIGH RISK'
    }
  };

  const config = configs[normStatus] || configs.NORMAL;
  const Icon = config.icon;

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs gap-1.5',
    md: 'px-3 py-1 text-xs sm:text-sm gap-2',
    lg: 'px-4 py-2 text-sm sm:text-base gap-2.5 font-semibold'
  };

  return (
    <div className={`inline-flex items-center rounded-full border ${config.bg} ${sizeClasses[size] || sizeClasses.md} font-mono font-bold transition-all shadow-sm`}>
      <span className={`w-2 h-2 rounded-full ${config.dot} animate-pulse shrink-0`} />
      <Icon className="w-4 h-4 shrink-0" />
      <span>{normStatus}</span>
    </div>
  );
}
