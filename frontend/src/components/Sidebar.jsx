import React from 'react';
import { 
  LayoutDashboard, 
  Activity, 
  BrainCircuit, 
  LineChart, 
  Award,
  ChevronRight,
  Zap,
  Info,
  FileText
} from 'lucide-react';

const NAV_ITEMS = [
  {
    id: 'overview',
    label: 'Overview',
    icon: LayoutDashboard,
    badge: null,
    description: 'Compressor health & KPI summary'
  },
  {
    id: 'monitoring',
    label: 'Live Monitoring',
    icon: Activity,
    badge: 'LIVE',
    badgeColor: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    description: 'Real-time telemetry stream & charts'
  },
  {
    id: 'risk',
    label: 'AI Risk Assessment',
    icon: BrainCircuit,
    badge: 'AI',
    badgeColor: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    description: 'Predictive early warning horizon'
  },
  {
    id: 'sensor-analysis',
    label: 'Sensor Analysis',
    icon: LineChart,
    badge: null,
    description: 'Multi-scale rolling analytics'
  },
  {
    id: 'model-performance',
    label: 'Model Performance',
    icon: Award,
    badge: 'METRICS',
    badgeColor: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    description: 'Validation & test transparency'
  },
  {
    id: 'case-study',
    label: 'Case Studies',
    icon: FileText,
    badge: 'CASES',
    badgeColor: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
    description: 'Real-world incidents & impact'
  }
];

export default function Sidebar({ activeTab, setActiveTab }) {
  return (
    <aside className="w-full md:w-64 bg-industrial-850 border-r border-industrial-700/60 p-4 flex flex-col justify-between shrink-0 shadow-lg">
      <div className="space-y-6">
        <div className="px-3 pt-2">
          <p className="text-[11px] font-mono uppercase tracking-wider text-slate-400 font-semibold">
            CONTROL CENTER
          </p>
        </div>

        <nav className="space-y-1.5">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center justify-between px-3.5 py-3 rounded-xl text-sm font-medium transition-all text-left group ${
                  isActive
                    ? 'bg-blue-600/15 text-blue-400 border border-blue-500/30 shadow-sm shadow-blue-500/10'
                    : 'text-slate-300 hover:bg-industrial-700/50 hover:text-white border border-transparent'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Icon className={`w-5 h-5 transition-colors ${isActive ? 'text-blue-400' : 'text-slate-400 group-hover:text-slate-200'}`} />
                  <div>
                    <span className="block font-semibold">{item.label}</span>
                    <span className="text-[11px] text-slate-400 block -mt-0.5">{item.description}</span>
                  </div>
                </div>
                {item.badge && (
                  <span className={`text-[10px] font-mono px-2 py-0.5 rounded border font-semibold ${item.badgeColor}`}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Industrial Spec Footer */}
      <div className="mt-8 pt-4 border-t border-industrial-700/60 text-xs text-slate-400 space-y-2 font-mono">
        <div className="bg-industrial-900/60 p-3 rounded-lg border border-industrial-700/40">
          <div className="flex items-center justify-between text-[11px] mb-1">
            <span className="text-slate-400 flex items-center gap-1"><Zap className="w-3 h-3 text-amber-400" /> APU System</span>
            <span className="text-emerald-400 font-semibold">Active</span>
          </div>
          <p className="text-[10px] text-slate-400 leading-tight">
            Twin-tower desiccant air dryer & 3-phase compressor unit
          </p>
        </div>
        <p className="text-[10px] text-slate-400 text-center">
          MetroGuard AI © 2026 • Predictive Rail Maintenance
        </p>
      </div>
    </aside>
  );
}
