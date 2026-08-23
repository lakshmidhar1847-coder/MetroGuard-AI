import React, { useState, useEffect } from 'react';
import { 
  BrainCircuit, 
  ShieldAlert, 
  Activity, 
  Layers, 
  TrendingUp, 
  CheckCircle2, 
  AlertTriangle,
  Info,
  Zap,
  BarChart3,
  Search,
  Loader2,
  Gauge,
  Clock,
  Calendar,
  Wrench,
  HelpCircle,
  Cpu,
  RefreshCw,
  AlertOctagon,
  ArrowRight
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer, 
  Cell,
  CartesianGrid
} from 'recharts';
import { getFeatureImportance, getModelInfo, getDocumentedEvents, predictHybridRisk } from '../services/api';
import RiskGauge from '../components/RiskGauge';
import StatusBadge from '../components/StatusBadge';

export default function RiskAssessmentPage({ latestData }) {
  const [featureImportance, setFeatureImportance] = useState([]);
  const [modelInfo, setModelInfo] = useState(null);
  const [events, setEvents] = useState([]);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [isLoadingRisk, setIsLoadingRisk] = useState(false);
  const [evalError, setEvalError] = useState(null);
  const [customTimestamp, setCustomTimestamp] = useState('');
  
  // Real dynamic dual-engine hybrid risk state initialized cleanly
  const [activeHybrid, setActiveHybrid] = useState({
    timestamp_requested: '',
    timestamp_matched: '',
    time_difference_seconds: 0.0,
    target: null,
    failure_status: 'unknown',
    xgboost: {
      risk_probability: 0.0,
      risk_percentage: 0.0,
      status: 'NORMAL',
      threshold: 0.10
    },
    anomaly: {
      score: 0.0,
      threshold: 0.5040,
      high_threshold: 0.5350,
      status: 'NORMAL'
    },
    hybrid: {
      status: 'NORMAL',
      reason: 'Awaiting telemetry evaluation.'
    },
    alert: {
      level: 'NORMAL',
      title: 'Compressor System Operating Within Normal Envelope',
      reason: 'Nominal baseline telemetry.',
      recommendations: []
    },
    evidence: [],
    features_analyzed: 65
  });

  useEffect(() => {
    loadMetadataAndInit();
  }, []);

  const loadMetadataAndInit = async () => {
    try {
      const [featRes, modelRes, evRes] = await Promise.all([
        getFeatureImportance(),
        getModelInfo(),
        getDocumentedEvents()
      ]);
      setFeatureImportance(featRes || []);
      setModelInfo(modelRes || {});
      setEvents(evRes || []);
      
      // Auto-evaluate Event #1 on initial mount using real hybrid backend
      if (evRes && evRes.length > 0) {
        const initialEvent = evRes[0];
        setSelectedEvent(initialEvent);
        await evaluateTimestamp(initialEvent.warning_start);
      }
    } catch (err) {
      console.error('Error loading AI risk metadata:', err);
    }
  };

  const evaluateTimestamp = async (ts) => {
    if (!ts || !ts.trim()) {
      setEvalError('Please enter a valid timestamp.');
      return;
    }
    setIsLoadingRisk(true);
    setEvalError(null);
    try {
      const res = await predictHybridRisk({ timestamp: ts.trim() });
      if (res && res.xgboost && res.anomaly && res.hybrid) {
        setActiveHybrid(res);
      } else {
        setEvalError('Incomplete response received from inference engine.');
      }
    } catch (err) {
      console.error('Hybrid prediction request error:', err);
      const detail = err.response?.data?.detail || err.message;
      if (err.response?.status === 404) {
        setEvalError(`Telemetry observation not found: ${detail}`);
      } else if (err.response?.status === 400) {
        setEvalError(`Invalid request: ${detail}`);
      } else {
        setEvalError(`Unable to connect to MetroGuard backend (${detail})`);
      }
    } finally {
      setIsLoadingRisk(false);
    }
  };

  const handleSelectEvent = async (ev) => {
    setSelectedEvent(ev);
    setCustomTimestamp(ev.warning_start);
    await evaluateTimestamp(ev.warning_start);
  };

  const handleCustomEval = async (e) => {
    e.preventDefault();
    if (customTimestamp.trim()) {
      setSelectedEvent(null);
      await evaluateTimestamp(customTimestamp.trim());
    }
  };

  const threshold = activeHybrid.xgboost?.threshold || modelInfo?.selected_threshold || 0.10;

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* 1. TOP-LEVEL MACHINE HEALTH SUMMARY */}
      <div className="bg-gradient-to-r from-industrial-850 via-industrial-800 to-industrial-850 p-6 rounded-2xl border border-industrial-700/60 shadow-xl space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-industrial-700/50 pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded bg-blue-500/20 border border-blue-500/30 text-blue-400 text-xs font-mono font-bold flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5" />
                MACHINE HEALTH MONITOR
              </span>
              <span className="text-xs font-mono text-slate-400">Unit: MetroPT-3 Main Air Compressor</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Predictive Maintenance Intelligence & Decision Center
            </h2>
            <p className="text-xs sm:text-sm text-slate-300 max-w-3xl leading-relaxed">
              Continuous multi-tier assessment: Supervised pneumatic leak classification combined with unsupervised anomaly isolation over a 30-minute forward horizon.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
            <div className="bg-industrial-900/90 px-4 py-2.5 rounded-xl border border-industrial-700/60 flex items-center gap-3">
              <span className="text-xs font-mono text-slate-400 uppercase font-semibold">Overall Status:</span>
              <StatusBadge status={activeHybrid.alert?.level || activeHybrid.hybrid?.status || 'NORMAL'} size="lg" />
            </div>
          </div>
        </div>

        {/* Live Top-Level KPI Ribbon */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs">
          <div className="bg-industrial-900/80 p-3 rounded-xl border border-industrial-700/40 space-y-1">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Known Failure Risk</span>
            <span className="text-xl font-bold text-white">
              {activeHybrid.xgboost?.risk_percentage !== undefined ? `${activeHybrid.xgboost.risk_percentage}%` : '0.00%'}
            </span>
            <span className="text-[10px] text-slate-400 block">
              Tier 1 Supervised XGBoost
            </span>
          </div>

          <div className="bg-industrial-900/80 p-3 rounded-xl border border-industrial-700/40 space-y-1">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block">System Anomaly Index</span>
            <span className="text-xl font-bold text-cyan-300">
              {activeHybrid.anomaly?.score !== undefined ? activeHybrid.anomaly.score.toFixed(4) : '0.0000'}
            </span>
            <span className="text-[10px] text-slate-400 block">
              Tier 2 Isolation Forest
            </span>
          </div>

          <div className="bg-industrial-900/80 p-3 rounded-xl border border-industrial-700/40 space-y-1">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Active Alert Level</span>
            <span className="text-base font-bold text-amber-300 truncate block">
              {activeHybrid.alert?.level || 'NORMAL'}
            </span>
            <span className="text-[10px] text-slate-400 block truncate">
              {activeHybrid.alert?.title || 'Nominal Operation'}
            </span>
          </div>

          <div className="bg-industrial-900/80 p-3 rounded-xl border border-industrial-700/40 space-y-1">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Matched Observation</span>
            <span className="text-xs font-bold text-slate-200 truncate block">
              {activeHybrid.timestamp_matched || '—'}
            </span>
            <span className="text-[10px] text-slate-400 block">
              {activeHybrid.time_difference_seconds !== undefined ? `Tolerance Δ ${activeHybrid.time_difference_seconds}s` : '—'}
            </span>
          </div>
        </div>
      </div>

      {/* 2. PRIMARY RISK / ANOMALY VISUALIZATION & DUAL-TIER COMPARISON */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Authentic Risk Gauge Card */}
        <div className="relative">
          <RiskGauge
            riskProbability={activeHybrid.xgboost?.risk_probability || 0.0}
            riskPercentage={activeHybrid.xgboost?.risk_percentage || 0.0}
            status={activeHybrid.xgboost?.status || 'NORMAL'}
            threshold={threshold}
          />
          {isLoadingRisk && (
            <div className="absolute inset-0 bg-industrial-950/80 backdrop-blur-sm rounded-2xl flex flex-col items-center justify-center p-6 text-center space-y-3 z-20">
              <Loader2 className="w-10 h-10 animate-spin text-blue-400" />
              <div className="space-y-1">
                <strong className="text-sm text-white font-mono block">Analyzing Compressor Telemetry...</strong>
                <span className="text-xs text-slate-400 font-sans">Executing Dual XGBoost + Isolation Forest Pipeline</span>
              </div>
            </div>
          )}
        </div>

        {/* Center & Right: Dual-Tier Architecture & Diagnostic Center */}
        <div className="lg:col-span-2 bg-industrial-850 rounded-2xl p-6 border border-industrial-700/60 shadow-xl space-y-5 flex flex-col justify-between">
          <div className="space-y-4">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-industrial-700/60 pb-3">
              <div>
                <span className="text-xs font-mono uppercase tracking-wider text-slate-400">
                  DUAL-TIER INFERENCE ENGINES
                </span>
                <h3 className="text-lg font-bold text-white mt-0.5">
                  Supervised Classification & Unsupervised Outlier Isolation
                </h3>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono text-slate-400">Hybrid Decision:</span>
                <StatusBadge status={activeHybrid.hybrid?.status || 'NORMAL'} size="md" />
              </div>
            </div>

            {/* Dual-Tier Comparative Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 font-mono text-xs">
              {/* Tier 1: Known Failure Risk */}
              <div className="bg-industrial-900/80 p-4 rounded-xl border border-industrial-700/50 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-blue-300 font-bold uppercase">Tier 1: Known Failure Risk</span>
                  <StatusBadge status={activeHybrid.xgboost?.status || 'NORMAL'} size="sm" />
                </div>
                <div className="flex items-baseline justify-between pt-1">
                  <span className="text-2xl font-bold text-white">
                    {activeHybrid.xgboost?.risk_percentage !== undefined ? `${activeHybrid.xgboost.risk_percentage}%` : '0.00%'}
                  </span>
                  <span className="text-[10px] text-slate-400">
                    Threshold: {threshold}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 font-sans leading-relaxed pt-1">
                  Supervised XGBoost model trained on verified pneumatic valve leakage signatures.
                </p>
              </div>

              {/* Tier 2: System Anomaly Index */}
              <div className="bg-industrial-900/80 p-4 rounded-xl border border-industrial-700/50 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-cyan-300 font-bold uppercase">Tier 2: System Anomaly Index</span>
                  <StatusBadge status={activeHybrid.anomaly?.status || 'NORMAL'} size="sm" />
                </div>
                <div className="flex items-baseline justify-between pt-1">
                  <span className="text-2xl font-bold text-cyan-300">
                    {activeHybrid.anomaly?.score !== undefined ? activeHybrid.anomaly.score.toFixed(4) : '0.0000'}
                  </span>
                  <span className="text-[10px] text-slate-400">
                    Threshold: {activeHybrid.anomaly?.threshold?.toFixed(4) || '0.5040'}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 font-sans leading-relaxed pt-1">
                  Unsupervised Isolation Forest measuring multi-channel operating deviations without labels.
                </p>
              </div>
            </div>

            {/* 4. "WHY THIS ALERT?" DIAGNOSTIC EXPLANATION PANEL */}
            <div className="bg-industrial-900/95 p-4 rounded-xl border border-industrial-700/60 space-y-3">
              <div className="flex items-center justify-between border-b border-industrial-700/40 pb-2">
                <div className="flex items-center gap-2">
                  <Zap className="w-4 h-4 text-amber-400 shrink-0" />
                  <strong className="text-white font-bold text-xs uppercase font-mono tracking-wider">
                    Why This Alert?
                  </strong>
                </div>
                <span className="text-[11px] font-mono text-slate-400">
                  {activeHybrid.evidence?.length || 0} Deviating Signal(s)
                </span>
              </div>

              <div className="space-y-1">
                <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block font-semibold">
                  Primary Decision Rationale:
                </span>
                <p className="text-slate-200 text-xs font-sans leading-relaxed">
                  {activeHybrid.alert?.reason || activeHybrid.hybrid?.reason || 'Nominal operating conditions detected.'}
                </p>
              </div>

              {/* Core Innovation Highlight for Unseen Failure Regimes (e.g. Event #4) */}
              {activeHybrid.xgboost?.status === 'NORMAL' && activeHybrid.alert?.level === 'WARNING' && (
                <div className="bg-amber-500/10 border border-amber-500/30 p-3 rounded-lg flex items-start gap-2.5 text-xs text-amber-200">
                  <Info className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                  <div className="space-y-0.5 leading-snug">
                    <strong className="text-amber-300 font-mono font-bold block text-[11px]">Core Innovation Story (Dual-Tier Discovery):</strong>
                    <span className="font-sans text-[11px] text-slate-200">
                      XGBoost does not identify this as a known failure, but the unsupervised Anomaly & Physical Evidence layer detects abnormal operating behavior.
                    </span>
                  </div>
                </div>
              )}

              {/* Physical Evidence Attribution List */}
              {activeHybrid.evidence && activeHybrid.evidence.length > 0 ? (
                <div className="space-y-1.5 pt-1">
                  <span className="text-[10px] font-mono text-amber-300 uppercase tracking-wider block font-semibold">
                    Physical Telemetry Evidence (&gt; 2.0σ Deviation from Baseline):
                  </span>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 font-mono text-[11px]">
                    {activeHybrid.evidence.slice(0, 3).map((ev, idx) => (
                      <div key={idx} className="bg-industrial-800/80 p-2.5 rounded-lg border border-amber-500/20 space-y-1">
                        <div className="flex items-center justify-between">
                          <strong className="text-white font-bold truncate">{ev.feature}</strong>
                          <span className="text-[10px] px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 font-bold">
                            {ev.z_score > 0 ? `+${ev.z_score}σ` : `${ev.z_score}σ`}
                          </span>
                        </div>
                        <div className="text-[10px] text-slate-400 flex justify-between">
                          <span>Actual: <strong className="text-slate-200">{ev.actual_value} {ev.unit}</strong></span>
                          <span>Med: {ev.baseline_median}</span>
                        </div>
                        <p className="text-[10px] text-slate-300 font-sans leading-tight line-clamp-2">
                          {ev.reason}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-xs text-slate-400 font-sans italic bg-industrial-850/50 p-2.5 rounded-lg border border-industrial-700/30">
                  All 15 physical telemetry channels conform strictly to nominal operating distributions.
                </div>
              )}
            </div>

            {/* 5. PRESCRIPTIVE MAINTENANCE SECTION */}
            {activeHybrid.alert?.recommendations && activeHybrid.alert.recommendations.length > 0 && (
              <div className="bg-industrial-900/90 p-4 rounded-xl border border-blue-500/20 space-y-2.5">
                <div className="flex items-center gap-2 border-b border-industrial-700/40 pb-2">
                  <Wrench className="w-4 h-4 text-blue-400 shrink-0" />
                  <strong className="text-white font-bold text-xs uppercase font-mono tracking-wider">
                    Recommended Maintenance Actions
                  </strong>
                </div>

                <div className="space-y-1.5">
                  {activeHybrid.alert.recommendations.map((rec, rIdx) => (
                    <div key={rIdx} className="flex items-start gap-2.5 text-xs font-sans text-slate-200 bg-industrial-800/60 p-2.5 rounded-lg border border-industrial-700/40">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                      <span className="leading-snug">{rec}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 3. EVENT TIMELINE & QUICK-JUMP */}
            <div className="space-y-2 pt-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-slate-300 uppercase font-semibold flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5 text-blue-400" />
                  Historical Incident Timeline Quick-Jump:
                </span>
                <span className="text-[10px] font-mono text-slate-400">4 Documented UCI #791 Episodes</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 font-mono text-xs">
                {events.map((ev) => {
                  const isSelected = selectedEvent?.id === ev.id;
                  return (
                    <button
                      key={ev.id}
                      onClick={() => handleSelectEvent(ev)}
                      disabled={isLoadingRisk}
                      className={`p-3 rounded-xl text-left border transition-all ${
                        isSelected
                          ? 'bg-blue-600/20 border-blue-500 text-white shadow-lg shadow-blue-500/10'
                          : 'bg-industrial-900/60 border-industrial-700/60 text-slate-300 hover:bg-industrial-700/40'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <strong className="font-bold text-blue-300">{ev.name.split(':')[0]}</strong>
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-industrial-700 text-slate-300">
                          {ev.partition}
                        </span>
                      </div>
                      <span className="text-[11px] text-slate-400 block truncate">{ev.type}</span>
                      <span className="text-[10px] text-slate-400 block mt-1">Warning Interval: {ev.warning_start.slice(5, 16)}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* 10. CUSTOM TIMESTAMP EVALUATION */}
            <div className="pt-1">
              <form onSubmit={handleCustomEval} className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
                <div className="relative flex-1">
                  <input
                    type="text"
                    placeholder="Evaluate custom timestamp (e.g. 2020-04-17 23:30:00)..."
                    value={customTimestamp}
                    onChange={(e) => setCustomTimestamp(e.target.value)}
                    className="w-full bg-industrial-900/90 border border-industrial-700/60 rounded-xl px-3.5 py-2 text-xs font-mono text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
                  />
                </div>
                <button
                  type="submit"
                  disabled={isLoadingRisk}
                  className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-xl text-xs font-mono font-semibold flex items-center justify-center gap-1.5 transition-all shadow-md shadow-blue-600/20"
                >
                  <Search className="w-3.5 h-3.5" />
                  <span>Evaluate Timestamp</span>
                </button>
              </form>
            </div>

            {/* 9. OPERATOR-FACING ERROR BANNER */}
            {evalError && (
              <div className="bg-rose-500/10 border border-rose-500/30 text-rose-300 p-3.5 rounded-xl text-xs font-mono flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <AlertOctagon className="w-4 h-4 shrink-0 text-rose-400" />
                  <span>{evalError}</span>
                </div>
                <button 
                  onClick={() => setEvalError(null)} 
                  className="text-slate-400 hover:text-white text-[10px] underline shrink-0"
                >
                  Dismiss
                </button>
              </div>
            )}
          </div>

          {/* Footer Metadata */}
          <div className="pt-3 border-t border-industrial-700/40 flex flex-wrap items-center justify-between gap-2 text-xs font-mono text-slate-400">
            <span>Requested: <strong className="text-slate-300">{activeHybrid.timestamp_requested || '—'}</strong></span>
            <span>Matched: <strong className="text-slate-200">{activeHybrid.timestamp_matched || '—'}</strong> ({activeHybrid.time_difference_seconds !== undefined ? `Δ ${activeHybrid.time_difference_seconds}s` : '—'})</span>
            <span>Analyzed: <strong className="text-blue-400">{activeHybrid.features_analyzed || 65} Features</strong></span>
          </div>
        </div>
      </div>

      {/* FEATURE IMPORTANCE & MODEL TRANSPARENCY PANEL */}
      <div className="bg-industrial-850 rounded-2xl p-6 border border-industrial-700/60 shadow-xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-industrial-700/60 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-blue-400" />
              <h3 className="text-lg font-bold text-white">
                Key Signals Analyzed & Model Feature Attribution
              </h3>
            </div>
            <p className="text-xs text-slate-400">
              Feature Gini Gain Weights across 65 engineered time-series features
            </p>
          </div>
          <span className="text-xs font-mono px-3 py-1 rounded-lg bg-industrial-700/60 border border-industrial-600/50 text-slate-300">
            Top 10 Driving Features
          </span>
        </div>

        {/* Feature Importance Bar Chart */}
        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={featureImportance.slice(0, 10)}
              layout="vertical"
              margin={{ top: 5, right: 30, left: 140, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2b48" horizontal={false} />
              <XAxis 
                type="number" 
                stroke="#64748b" 
                tick={{ fill: '#64748b', fontSize: 10, fontFamily: 'monospace' }}
                unit="%"
              />
              <YAxis 
                dataKey="feature" 
                type="category" 
                stroke="#64748b" 
                tick={{ fill: '#94a3b8', fontSize: 11, fontFamily: 'monospace' }}
                tickLine={false}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#111726',
                  borderColor: '#2d3b5e',
                  borderRadius: '0.75rem',
                  fontSize: '0.75rem',
                  fontFamily: 'monospace',
                  color: '#f1f5f9'
                }}
                formatter={(val) => [`${val}%`, 'Importance Weight']}
              />
              <Bar dataKey="importance_percentage" radius={[0, 4, 4, 0]}>
                {featureImportance.slice(0, 10).map((entry, idx) => (
                  <Cell 
                    key={`cell-${idx}`} 
                    fill={idx < 3 ? '#3b82f6' : idx < 6 ? '#06b6d4' : '#8b5cf6'} 
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Detailed Feature Explanations Table */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
          {featureImportance.slice(0, 8).map((feat, idx) => (
            <div 
              key={feat.feature}
              className="bg-industrial-900/70 p-3.5 rounded-xl border border-industrial-700/40 flex items-start justify-between gap-3 text-xs font-mono"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="w-5 h-5 rounded-full bg-blue-500/20 text-blue-400 font-bold flex items-center justify-center text-[10px]">
                    #{idx + 1}
                  </span>
                  <strong className="text-white font-bold">{feat.feature}</strong>
                </div>
                <p className="text-[11px] text-slate-400 font-sans leading-snug">
                  {feat.explanation}
                </p>
              </div>
              <span className="text-xs font-bold text-blue-400 shrink-0 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
                {feat.importance_percentage}%
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
