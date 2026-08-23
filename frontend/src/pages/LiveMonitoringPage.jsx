import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, 
  Pause, 
  RotateCcw, 
  Activity, 
  Clock, 
  Layers, 
  Calendar, 
  TrendingUp, 
  TrendingDown,
  Minus,
  Zap, 
  Radio, 
  Sliders,
  AlertOctagon,
  CheckCircle2,
  AlertTriangle,
  SkipForward,
  Cpu,
  Flame,
  Gauge,
  Wrench,
  ShieldCheck,
  Info,
  History,
  HelpCircle,
  Compass,
  FileSearch,
  Bell,
  Check,
  CheckSquare,
  Square,
  ClipboardList,
  ShieldAlert,
  AlertCircle
} from 'lucide-react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer, 
  CartesianGrid, 
  Legend, 
  ReferenceLine, 
  AreaChart, 
  Area 
} from 'recharts';
import { 
  getStreamStatus, 
  getStreamCurrent, 
  startStream, 
  stopStream, 
  resetStream, 
  setStreamScenario, 
  setStreamSpeed,
  stepStream,
  getAnomalyExplanation,
  acknowledgeAlert,
  resolveAlert 
} from '../services/api';
import StatusBadge from '../components/StatusBadge';

const SCENARIOS = [
  { id: 'normal', name: '1. Normal Baseline', shortDesc: 'Cyclical Pumping (30m)' },
  { id: 'gradual_anomaly', name: '2. Gradual Anomaly', shortDesc: 'Thermal Buildup & Drift' },
  { id: 'pre_failure', name: '3. Pre-Failure (Event #1)', shortDesc: 'XGBoost 98.78% High Risk' },
  { id: 'unseen_anomaly', name: '4. Summer Regime (Event #4)', shortDesc: 'Dual-Tier Anomaly (WARNING)' }
];

const SPEED_OPTIONS = [
  { label: '1x Realtime', value: 1.0 },
  { label: '2x Fast', value: 2.0 },
  { label: '5x Demo', value: 5.0 },
  { label: '10x Turbo', value: 10.0 }
];

export default function LiveMonitoringPage() {
  const [streamState, setStreamState] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isChangingScenario, setIsChangingScenario] = useState(false);
  const [chartChannel, setChartChannel] = useState('pressures'); // 'pressures' | 'thermal' | 'risk'
  const [checkedItems, setCheckedItems] = useState({});
  const [actionMessage, setActionMessage] = useState(null);

  const pollIntervalRef = useRef(null);

  // Poll current stream state every 800ms
  useEffect(() => {
    fetchCurrentSnapshot();
    pollIntervalRef.current = setInterval(fetchCurrentSnapshot, 800);
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, []);

  const fetchCurrentSnapshot = async () => {
    try {
      const data = await getStreamCurrent();
      if (data) {
        setStreamState(data);
      }
    } catch (err) {
      console.error('Error polling stream snapshot:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStart = async () => {
    try {
      await startStream();
      fetchCurrentSnapshot();
    } catch (err) {
      console.error('Error starting stream:', err);
    }
  };

  const handleStop = async () => {
    try {
      await stopStream();
      fetchCurrentSnapshot();
    } catch (err) {
      console.error('Error pausing stream:', err);
    }
  };

  const handleReset = async () => {
    try {
      await resetStream();
      setCheckedItems({});
      setActionMessage(null);
      fetchCurrentSnapshot();
    } catch (err) {
      console.error('Error resetting stream:', err);
    }
  };

  const handleScenarioChange = async (scenarioId) => {
    setIsChangingScenario(true);
    try {
      await setStreamScenario(scenarioId);
      setCheckedItems({});
      setActionMessage(null);
      await fetchCurrentSnapshot();
    } catch (err) {
      console.error('Error changing scenario:', err);
    } finally {
      setIsChangingScenario(false);
    }
  };

  const handleSpeedChange = async (speed) => {
    try {
      await setStreamSpeed(speed);
      fetchCurrentSnapshot();
    } catch (err) {
      console.error('Error setting speed:', err);
    }
  };

  const handleStep = async () => {
    try {
      const stepRes = await stepStream();
      setStreamState(stepRes);
    } catch (err) {
      console.error('Error stepping stream:', err);
    }
  };

  const handleAcknowledge = async (alertId) => {
    try {
      await acknowledgeAlert(alertId);
      setActionMessage(`Alert ${alertId} acknowledged.`);
      setTimeout(() => setActionMessage(null), 3000);
      fetchCurrentSnapshot();
    } catch (err) {
      console.error('Error acknowledging alert:', err);
    }
  };

  const handleResolve = async (alertId) => {
    try {
      await resolveAlert(alertId);
      setActionMessage(`Alert ${alertId} marked as resolved.`);
      setTimeout(() => setActionMessage(null), 3000);
      fetchCurrentSnapshot();
    } catch (err) {
      console.error('Error resolving alert:', err);
    }
  };

  const toggleCheckItem = (idx) => {
    setCheckedItems(prev => ({
      ...prev,
      [idx]: !prev[idx]
    }));
  };

  const isRunning = streamState?.is_running ?? true;
  const currentScenario = streamState?.scenario || 'normal';
  const sensors = streamState?.sensors || {};
  const alert = streamState?.alert || { level: 'NORMAL', title: 'Nominal Operation', reason: 'Nominal baseline.' };
  const evidence = streamState?.evidence || [];
  const chartHistory = streamState?.chart_history || [];
  const currentSpeed = streamState?.playback_speed || 1.0;
  
  // Explainable Anomaly Intelligence payload
  const anomalyIntel = streamState?.anomaly_intelligence || {
    anomaly_severity: 0,
    severity_label: 'NOMINAL',
    severity_color: 'emerald',
    trajectory: 'STABLE',
    persistence: { abnormal_count: 0, window_size: 30, is_persistent: false, status: 'TRANSIENT' },
    top_sensor_deviations: [],
    operational_hypothesis: {
      title: 'Nominal Operation',
      evidence: 'All sensors conform to baseline distributions.',
      confidence: 'HIGH',
      recommended_inspection: 'No action required.'
    }
  };

  const severityScore = anomalyIntel.anomaly_severity || 0;
  const severityLabel = anomalyIntel.severity_label || 'NOMINAL';
  const trajectory = anomalyIntel.trajectory || 'STABLE';
  const persistence = anomalyIntel.persistence || { abnormal_count: 0, window_size: 30, status: 'TRANSIENT' };
  const topDeviations = anomalyIntel.top_sensor_deviations || [];
  const hypothesis = anomalyIntel.operational_hypothesis || {};

  // Task 20: Intelligent Operator Alert & Prescriptive Workflow
  const activeOperatorAlert = streamState?.active_operator_alert;
  const prescriptiveRec = streamState?.prescriptive_recommendation || {
    action: 'Maintain routine preventive maintenance inspection cycle.',
    priority: 'Routine',
    reason: 'All monitored physical sensor channels conform to nominal baseline operating distributions.',
    inspection_checklist: [
      'Verify standard compressor visual indicators and oil sight glass',
      'Log operating duty cycle and charging frequency',
      'Ensure electrical motor current is balanced'
    ],
    evidence_strength: 'LOW EVIDENCE'
  };
  const operatorAlertHistory = streamState?.operator_alert_history || [];

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* 1. TOP LIVE CONTROLS & STATUS BAR */}
      <div className="bg-industrial-850 p-6 rounded-2xl border border-industrial-700/60 shadow-xl space-y-5">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-industrial-700/50 pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className={`px-2.5 py-0.5 rounded text-xs font-mono font-bold flex items-center gap-1.5 border ${
                isRunning 
                  ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' 
                  : 'bg-amber-500/20 text-amber-300 border-amber-500/30'
              }`}>
                <span className={`w-2 h-2 rounded-full ${isRunning ? 'bg-emerald-400 animate-ping' : 'bg-amber-400'}`} />
                {isRunning ? 'STREAMING (LIVE)' : 'STREAM PAUSED'}
              </span>
              <span className="text-xs font-mono text-slate-400">
                MetroPT-3 APU-TR-03 Replay Pipeline
              </span>
            </div>
            <h2 className="text-2xl font-extrabold text-white tracking-tight">
              Real-Time Sensor Telemetry & Replay Command Center
            </h2>
            <p className="text-xs text-slate-300 max-w-3xl">
              Chronological replay of authentic MetroPT-3 operating sequences through live feature extraction, dual ML engines, explainable anomaly intelligence, and prescriptive operator workflows.
            </p>
          </div>

          {/* Action Control Buttons */}
          <div className="flex items-center gap-2.5 flex-wrap">
            {isRunning ? (
              <button
                onClick={handleStop}
                className="px-3.5 py-2 rounded-xl bg-amber-500/20 border border-amber-500/40 text-amber-300 font-mono text-xs font-bold flex items-center gap-1.5 hover:bg-amber-500/30 transition-all"
              >
                <Pause className="w-3.5 h-3.5" />
                Pause Stream
              </button>
            ) : (
              <button
                onClick={handleStart}
                className="px-3.5 py-2 rounded-xl bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 font-mono text-xs font-bold flex items-center gap-1.5 hover:bg-emerald-500/30 transition-all shadow-lg shadow-emerald-500/10"
              >
                <Play className="w-3.5 h-3.5" />
                Start / Resume
              </button>
            )}

            <button
              onClick={handleStep}
              className="px-3 py-2 rounded-xl bg-industrial-800 border border-industrial-700 text-slate-300 font-mono text-xs hover:bg-industrial-700 transition-all flex items-center gap-1"
              title="Step forward 1 observation"
            >
              <SkipForward className="w-3.5 h-3.5 text-blue-400" />
              Step
            </button>

            <button
              onClick={handleReset}
              className="px-3 py-2 rounded-xl bg-industrial-800 border border-industrial-700 text-slate-300 font-mono text-xs hover:bg-industrial-700 transition-all flex items-center gap-1"
              title="Reset scenario to beginning"
            >
              <RotateCcw className="w-3.5 h-3.5 text-slate-400" />
              Reset
            </button>

            {/* Speed Multiplier */}
            <div className="flex items-center rounded-xl bg-industrial-900 border border-industrial-700 p-0.5 text-xs font-mono">
              {SPEED_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => handleSpeedChange(opt.value)}
                  className={`px-2 py-1 rounded-lg text-[11px] transition-all ${
                    currentSpeed === opt.value
                      ? 'bg-blue-600 text-white font-bold'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {opt.label.split(' ')[0]}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Scenario Switcher Tabs */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs font-mono">
            <span className="text-slate-400 uppercase font-semibold flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-blue-400" />
              Select Operating Scenario:
            </span>
            <span className="text-slate-400 text-[11px]">
              Timestamp: <strong className="text-slate-200">{streamState?.timestamp || '—'}</strong> ({streamState?.current_index || 0} / {streamState?.total_records || 0} rows, {streamState?.progress_percent || 0}%)
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
            {SCENARIOS.map((sc) => {
              const isSelected = currentScenario === sc.id;
              return (
                <button
                  key={sc.id}
                  onClick={() => handleScenarioChange(sc.id)}
                  disabled={isChangingScenario}
                  className={`p-3 rounded-xl text-left border transition-all ${
                    isSelected
                      ? 'bg-blue-600/20 border-blue-500 text-white shadow-lg shadow-blue-500/10'
                      : 'bg-industrial-900/60 border-industrial-700/60 text-slate-300 hover:bg-industrial-800'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1 font-mono text-xs">
                    <strong className={isSelected ? 'text-blue-300' : 'text-slate-200'}>
                      {sc.name}
                    </strong>
                    {isSelected && <span className="w-2 h-2 rounded-full bg-blue-400" />}
                  </div>
                  <span className="text-[11px] text-slate-400 block truncate font-sans">
                    {sc.shortDesc}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Progress Line */}
        <div className="w-full bg-industrial-900 rounded-full h-1.5 overflow-hidden border border-industrial-700/40">
          <div 
            className="bg-gradient-to-r from-blue-500 to-cyan-400 h-full transition-all duration-300"
            style={{ width: `${streamState?.progress_percent || 0}%` }}
          />
        </div>
      </div>

      {/* Action Notification Toast */}
      {actionMessage && (
        <div className="p-3 bg-blue-500/20 border border-blue-500/40 rounded-xl text-blue-300 font-mono text-xs flex items-center gap-2 animate-bounce">
          <Check className="w-4 h-4 text-emerald-400" />
          <span>{actionMessage}</span>
        </div>
      )}

      {/* 2. TASK 20: INTELLIGENT ALERT CENTER & OPERATOR WORKFLOW */}
      <div className="bg-industrial-850 rounded-2xl p-6 border border-amber-500/30 shadow-2xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-industrial-700/60 pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-amber-400" />
              <h3 className="text-xl font-extrabold text-white tracking-tight">
                Intelligent Alert Center & Operator Workflow
              </h3>
            </div>
            <p className="text-xs text-slate-300">
              Real-time incident management, deduplicated operator alerts, evidence-backed inspection actions, and lifecycle state tracking.
            </p>
          </div>

          <div className="flex items-center gap-2 font-mono text-xs">
            <span className="text-slate-400">Operator State:</span>
            {activeOperatorAlert ? (
              <span className={`px-2.5 py-0.5 rounded font-bold border ${
                activeOperatorAlert.status === 'ACTIVE' 
                  ? 'bg-rose-500/20 text-rose-300 border-rose-500/40 animate-pulse' 
                  : 'bg-blue-500/20 text-blue-300 border-blue-500/40'
              }`}>
                {activeOperatorAlert.status} ({activeOperatorAlert.alert_id})
              </span>
            ) : (
              <span className="px-2.5 py-0.5 rounded font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                ALL CLEAR (NO ACTIVE INCIDENTS)
              </span>
            )}
          </div>
        </div>

        {/* Current Active Incident Card (if present) */}
        {activeOperatorAlert ? (
          <div className="bg-gradient-to-r from-industrial-900 via-industrial-850 to-industrial-900 p-5 rounded-2xl border border-amber-500/40 shadow-xl space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-industrial-700/60 pb-3">
              <div className="flex items-center gap-3">
                <span className="font-mono text-xs font-bold text-slate-300 bg-industrial-800 px-2.5 py-1 rounded-lg border border-industrial-700">
                  {activeOperatorAlert.alert_id}
                </span>
                <span className={`px-2.5 py-1 rounded-lg font-mono text-xs font-black tracking-wide ${
                  activeOperatorAlert.priority === 'CRITICAL' 
                    ? 'bg-rose-500 text-white' 
                    : activeOperatorAlert.priority === 'HIGH' 
                    ? 'bg-amber-500 text-industrial-950 font-extrabold' 
                    : 'bg-cyan-500 text-industrial-950 font-bold'
                }`}>
                  PRIORITY: {activeOperatorAlert.priority}
                </span>
                <StatusBadge status={activeOperatorAlert.alert_level} size="md" />
              </div>

              {/* Operator Action Buttons */}
              <div className="flex items-center gap-2">
                {activeOperatorAlert.status === 'ACTIVE' && (
                  <button
                    onClick={() => handleAcknowledge(activeOperatorAlert.alert_id)}
                    className="px-3 py-1.5 rounded-xl bg-blue-600/30 border border-blue-500 text-blue-200 hover:bg-blue-600/50 font-mono text-xs font-bold flex items-center gap-1.5 transition-all shadow-md"
                  >
                    <Check className="w-3.5 h-3.5 text-blue-400" />
                    Acknowledge Alert
                  </button>
                )}

                <button
                  onClick={() => handleResolve(activeOperatorAlert.alert_id)}
                  className="px-3 py-1.5 rounded-xl bg-emerald-600/30 border border-emerald-500 text-emerald-200 hover:bg-emerald-600/50 font-mono text-xs font-bold flex items-center gap-1.5 transition-all shadow-md"
                >
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  Mark Resolved
                </button>
              </div>
            </div>

            {/* Primary Trigger & Evidence Details */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 text-xs font-sans">
              <div className="space-y-2">
                <span className="text-[11px] font-mono text-slate-400 uppercase font-semibold block">
                  Primary Trigger Rationale:
                </span>
                <p className="text-white font-medium bg-industrial-950/70 p-3 rounded-xl border border-industrial-800 leading-relaxed">
                  {activeOperatorAlert.primary_trigger}
                </p>
                <div className="flex gap-4 font-mono text-[11px] text-slate-400 pt-1">
                  <span>Created: <strong className="text-slate-200">{activeOperatorAlert.created_at}</strong></span>
                  <span>Updated: <strong className="text-slate-200">{activeOperatorAlert.updated_at}</strong></span>
                </div>
              </div>

              <div className="space-y-2">
                <span className="text-[11px] font-mono text-slate-400 uppercase font-semibold block">
                  Supporting Physical Evidence:
                </span>
                <div className="space-y-1.5 bg-industrial-950/70 p-3 rounded-xl border border-industrial-800">
                  {activeOperatorAlert.supporting_evidence.map((evItem, idx) => (
                    <div key={idx} className="flex items-start gap-2 text-slate-300 text-[11px]">
                      <div className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 shrink-0" />
                      <span>{evItem}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="text-[10px] text-slate-500 font-sans italic pt-1 border-t border-industrial-800/60">
              * Operator lifecycle actions (Acknowledge / Resolve) update workflow state and incident audits without modifying real-time ML feature telemetry inference.
            </div>
          </div>
        ) : (
          <div className="bg-industrial-900/60 p-5 rounded-2xl border border-emerald-500/20 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <ShieldCheck className="w-8 h-8 text-emerald-400 shrink-0" />
              <div>
                <strong className="text-sm font-bold text-white block">System Operating Within Nominal Envelope</strong>
                <p className="text-xs text-slate-400 font-sans">
                  No active operator alerts or critical failure risks detected. Telemetry conforms to normal baseline parameters.
                </p>
              </div>
            </div>
            <span className="px-3 py-1 rounded-xl bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs font-mono font-bold shrink-0">
              STATUS: NOMINAL
            </span>
          </div>
        )}

        {/* Prescriptive Maintenance Recommendation Panel */}
        <div className="bg-industrial-900/90 rounded-2xl p-5 border border-industrial-700/60 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-industrial-700/50 pb-3">
            <div className="flex items-center gap-2">
              <Wrench className="w-5 h-5 text-blue-400" />
              <h4 className="text-base font-bold text-white">
                Prescriptive Maintenance Action & Inspection Checklist
              </h4>
            </div>
            <div className="flex items-center gap-2 font-mono text-xs">
              <span className={`px-2.5 py-0.5 rounded font-bold ${
                prescriptiveRec.priority === 'Immediate Attention' 
                  ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' 
                  : prescriptiveRec.priority === 'Inspect Soon' 
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' 
                  : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
              }`}>
                {prescriptiveRec.priority}
              </span>
              <span className="px-2.5 py-0.5 rounded font-bold bg-industrial-800 text-slate-300 border border-industrial-700">
                {prescriptiveRec.evidence_strength}
              </span>
            </div>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <strong className="text-white text-sm font-bold block mb-1">
                {prescriptiveRec.action}
              </strong>
              <p className="text-slate-300 font-sans text-xs">
                <strong>Prescriptive Reason:</strong> {prescriptiveRec.reason}
              </p>
            </div>

            {/* Checklist */}
            <div className="space-y-2 pt-1">
              <span className="text-[11px] font-mono text-slate-400 uppercase font-semibold block">
                Required Depot Inspection Checklist:
              </span>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {prescriptiveRec.inspection_checklist.map((item, cIdx) => (
                  <button
                    key={cIdx}
                    onClick={() => toggleCheckItem(cIdx)}
                    className={`p-2.5 rounded-xl border text-left flex items-start gap-2.5 transition-all ${
                      checkedItems[cIdx]
                        ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-200'
                        : 'bg-industrial-950/60 border-industrial-800 text-slate-300 hover:bg-industrial-800'
                    }`}
                  >
                    {checkedItems[cIdx] ? (
                      <CheckSquare className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                    ) : (
                      <Square className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
                    )}
                    <span className={`text-[11px] font-sans ${checkedItems[cIdx] ? 'line-through text-slate-400' : ''}`}>
                      {item}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Chronological Alert Lifecycle History Log */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-bold text-white uppercase font-mono tracking-wide flex items-center gap-2">
              <History className="w-4 h-4 text-purple-400" />
              Operator Incident History Log ({operatorAlertHistory.length} Recorded)
            </h4>
            <span className="text-[11px] text-slate-400 font-mono">
              Deduplicated & State-Tracked
            </span>
          </div>

          {operatorAlertHistory.length > 0 ? (
            <div className="space-y-2 font-mono text-xs max-h-64 overflow-y-auto pr-1">
              {operatorAlertHistory.map((al, aIdx) => (
                <div 
                  key={aIdx} 
                  className="bg-industrial-900/80 p-3.5 rounded-xl border border-industrial-700/60 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2.5">
                      <strong className="text-blue-300 font-bold">{al.alert_id}</strong>
                      <span className="text-slate-400 text-[11px]">{al.created_at}</span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        al.priority === 'CRITICAL' ? 'bg-rose-500/20 text-rose-300' : al.priority === 'HIGH' ? 'bg-amber-500/20 text-amber-300' : 'bg-cyan-500/20 text-cyan-300'
                      }`}>
                        {al.priority}
                      </span>
                      <StatusBadge status={al.alert_level} size="sm" />
                    </div>
                    <p className="text-[11px] text-slate-300 font-sans line-clamp-1">
                      {al.primary_trigger}
                    </p>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    <span className={`px-2.5 py-1 rounded-lg text-[11px] font-bold border ${
                      al.status === 'ACTIVE' 
                        ? 'bg-rose-500/20 text-rose-300 border-rose-500/30' 
                        : al.status === 'ACKNOWLEDGED' 
                        ? 'bg-blue-500/20 text-blue-300 border-blue-500/30' 
                        : al.status === 'ESCALATED' 
                        ? 'bg-purple-500/20 text-purple-300 border-purple-500/30' 
                        : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                    }`}>
                      {al.status}
                    </span>

                    {al.status === 'ACTIVE' && (
                      <button
                        onClick={() => handleAcknowledge(al.alert_id)}
                        className="px-2.5 py-1 rounded bg-blue-600/30 border border-blue-500 text-blue-200 text-[10px] hover:bg-blue-600/50"
                      >
                        Acknowledge
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-xs text-slate-400 font-sans italic bg-industrial-900/50 p-6 rounded-xl border border-industrial-700/30 text-center">
              No incident alerts generated yet. Machine operating under nominal baseline.
            </div>
          )}
        </div>
      </div>

      {/* 3. REAL-TIME AI INTELLIGENCE & DECISION BANNER */}
      <div className="bg-gradient-to-r from-industrial-850 via-industrial-800 to-industrial-850 p-5 rounded-2xl border border-industrial-700/60 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-industrial-700/50 pb-3">
          <div className="flex items-center gap-3">
            <span className="text-xs font-mono text-slate-400 uppercase font-semibold">Active Operational State:</span>
            <StatusBadge status={alert.level || 'NORMAL'} size="lg" />
          </div>

          <div className="flex items-center gap-4 font-mono text-xs">
            <div className="flex items-center gap-1.5 text-slate-300">
              <span className="text-slate-500">Tier 1 (XGB):</span>
              <strong className={streamState?.xgboost?.risk_percentage > 10 ? 'text-rose-400' : 'text-white'}>
                {streamState?.xgboost?.risk_percentage !== undefined ? `${streamState.xgboost.risk_percentage}%` : '0.00%'}
              </strong>
            </div>

            <div className="flex items-center gap-1.5 text-slate-300">
              <span className="text-slate-500">Tier 2 (IF):</span>
              <strong className={streamState?.anomaly?.score >= 0.5040 ? 'text-amber-300' : 'text-cyan-300'}>
                {streamState?.anomaly?.score !== undefined ? streamState.anomaly.score.toFixed(4) : '0.0000'}
              </strong>
            </div>

            <div className="flex items-center gap-1.5 text-slate-300">
              <span className="text-slate-500">Severity:</span>
              <strong className={severityScore >= 50 ? 'text-rose-400' : 'text-emerald-400'}>
                {severityScore}/100 ({severityLabel})
              </strong>
            </div>

            <div className="flex items-center gap-1.5 text-slate-300">
              <span className="text-slate-500">Trajectory:</span>
              <strong className={
                trajectory === 'WORSENING' ? 'text-rose-400' : trajectory === 'RECOVERING' ? 'text-emerald-400' : 'text-slate-300'
              }>
                {trajectory === 'WORSENING' ? '↑ WORSENING' : trajectory === 'RECOVERING' ? '↓ RECOVERING' : '→ STABLE'}
              </strong>
            </div>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs font-sans">
          <div className="flex items-center gap-2 text-slate-200">
            <Info className="w-4 h-4 text-blue-400 shrink-0" />
            <span>
              <strong>Primary Alert Reason:</strong> {alert.reason || 'Nominal operating baseline.'}
            </span>
          </div>
          <span className="text-[11px] font-mono text-slate-400">
            {evidence.length} Active Physical Deviation(s)
          </span>
        </div>
      </div>

      {/* 4. LIVE SENSOR STATS CARDS */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 font-mono text-xs">
        {/* TP2 */}
        <div className="bg-industrial-850 p-4 rounded-xl border border-industrial-700/60 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-[10px]">
            <span>TP2 OUTPUT</span>
            <span className="text-blue-400 font-bold">bar</span>
          </div>
          <span className="text-2xl font-extrabold text-white">
            {sensors.TP2?.value !== undefined ? sensors.TP2.value : '—'}
          </span>
          <span className="text-[10px] text-slate-400 block truncate">Compressor Output</span>
        </div>

        {/* H1 */}
        <div className="bg-industrial-850 p-4 rounded-xl border border-industrial-700/60 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-[10px]">
            <span>H1 SEPARATOR</span>
            <span className="text-amber-400 font-bold">bar</span>
          </div>
          <span className="text-2xl font-extrabold text-white">
            {sensors.H1?.value !== undefined ? sensors.H1.value : '—'}
          </span>
          <span className="text-[10px] text-slate-400 block truncate">Filter Pressure Drop</span>
        </div>

        {/* Oil Temperature */}
        <div className="bg-industrial-850 p-4 rounded-xl border border-industrial-700/60 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-[10px]">
            <span>OIL TEMP</span>
            <span className="text-rose-400 font-bold">°C</span>
          </div>
          <span className={`text-2xl font-extrabold ${
            (sensors.Oil_temperature?.value || 0) >= 75 ? 'text-rose-400' : 'text-white'
          }`}>
            {sensors.Oil_temperature?.value !== undefined ? sensors.Oil_temperature.value : '—'}
          </span>
          <span className="text-[10px] text-slate-400 block truncate">Thermal Baseline 58.7°C</span>
        </div>

        {/* Reservoirs */}
        <div className="bg-industrial-850 p-4 rounded-xl border border-industrial-700/60 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-[10px]">
            <span>RESERVOIRS</span>
            <span className="text-emerald-400 font-bold">bar</span>
          </div>
          <span className="text-2xl font-extrabold text-white">
            {sensors.Reservoirs?.value !== undefined ? sensors.Reservoirs.value : '—'}
          </span>
          <span className="text-[10px] text-slate-400 block truncate">Main Air Storage</span>
        </div>

        {/* Motor Current */}
        <div className="bg-industrial-850 p-4 rounded-xl border border-industrial-700/60 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-[10px]">
            <span>MOTOR CURRENT</span>
            <span className="text-purple-400 font-bold">A</span>
          </div>
          <span className="text-2xl font-extrabold text-white">
            {sensors.Motor_current?.value !== undefined ? sensors.Motor_current.value : '—'}
          </span>
          <span className="text-[10px] text-slate-400 block truncate">Electrical Load</span>
        </div>

        {/* Drying Tower */}
        <div className="bg-industrial-850 p-4 rounded-xl border border-industrial-700/60 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-[10px]">
            <span>DV PRESSURE</span>
            <span className="text-cyan-400 font-bold">bar</span>
          </div>
          <span className="text-2xl font-extrabold text-white">
            {sensors.DV_pressure?.value !== undefined ? sensors.DV_pressure.value : '—'}
          </span>
          <span className="text-[10px] text-slate-400 block truncate">Desiccant Tower</span>
        </div>
      </div>

      {/* 5. REAL-TIME MULTI-CHANNEL TIME-SERIES CHART */}
      <div className="bg-industrial-850 p-6 rounded-2xl border border-industrial-700/60 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-industrial-700/60 pb-3">
          <div>
            <div className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-blue-400" />
              <h3 className="text-lg font-bold text-white">
                Live Multi-Channel Telemetry Stream (Rolling 60 Points)
              </h3>
            </div>
            <p className="text-xs text-slate-400">
              Live updating rolling waveform displaying pressure cycles, filter jitter, and thermal gradients.
            </p>
          </div>

          {/* Channel Selector */}
          <div className="flex items-center rounded-xl bg-industrial-900 border border-industrial-700 p-0.5 text-xs font-mono">
            <button
              onClick={() => setChartChannel('pressures')}
              className={`px-3 py-1 rounded-lg transition-all ${
                chartChannel === 'pressures' ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:text-white'
              }`}
            >
              Pressures (TP2 / H1 / Reservoirs)
            </button>
            <button
              onClick={() => setChartChannel('thermal')}
              className={`px-3 py-1 rounded-lg transition-all ${
                chartChannel === 'thermal' ? 'bg-amber-600 text-white font-bold' : 'text-slate-400 hover:text-white'
              }`}
            >
              Oil Temp (°C) & Motor (A)
            </button>
            <button
              onClick={() => setChartChannel('risk')}
              className={`px-3 py-1 rounded-lg transition-all ${
                chartChannel === 'risk' ? 'bg-purple-600 text-white font-bold' : 'text-slate-400 hover:text-white'
              }`}
            >
              AI Risk % & Severity (0-100)
            </button>
          </div>
        </div>

        <div className="h-64 sm:h-72 w-full font-mono text-xs">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartHistory} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
              <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 10 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.75rem', fontSize: '11px' }} 
              />
              <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />

              {chartChannel === 'pressures' && (
                <>
                  <Line type="monotone" dataKey="TP2" name="Compressor Pressure (TP2, bar)" stroke="#3b82f6" strokeWidth={2} dot={false} isAnimationActive={false} />
                  <Line type="monotone" dataKey="H1" name="Separator Drop (H1, bar)" stroke="#f59e0b" strokeWidth={2} dot={false} isAnimationActive={false} />
                  <Line type="monotone" dataKey="Reservoirs" name="Reservoirs (bar)" stroke="#10b981" strokeWidth={2} dot={false} isAnimationActive={false} />
                </>
              )}

              {chartChannel === 'thermal' && (
                <>
                  <Line type="monotone" dataKey="Oil_temperature" name="Oil Temp (°C)" stroke="#ef4444" strokeWidth={2.5} dot={false} isAnimationActive={false} />
                  <Line type="monotone" dataKey="Motor_current" name="Motor Current (A)" stroke="#8b5cf6" strokeWidth={2} dot={false} isAnimationActive={false} />
                </>
              )}

              {chartChannel === 'risk' && (
                <>
                  <Line type="monotone" dataKey="risk_percentage" name="XGBoost Known Risk (%)" stroke="#f43f5e" strokeWidth={2.5} dot={false} isAnimationActive={false} />
                  <Line type="monotone" dataKey="anomaly_severity" name="Anomaly Severity Index (0-100)" stroke="#06b6d4" strokeWidth={2} dot={false} isAnimationActive={false} />
                </>
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 6. EXPLAINABLE ANOMALY INTELLIGENCE ("Why is this abnormal?") */}
      <div className="bg-industrial-850 rounded-2xl p-6 border border-cyan-500/30 shadow-2xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-industrial-700/60 pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Compass className="w-5 h-5 text-cyan-400" />
              <h3 className="text-xl font-extrabold text-white tracking-tight">
                Explainable Anomaly Intelligence ("Why is this abnormal?")
              </h3>
            </div>
            <p className="text-xs text-slate-300">
              Multi-signal anomaly decomposition translating raw Isolation Forest distance metrics into calibrated severity, physical sensor deviations, persistence tracking, and operational hypotheses.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-xl bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 text-xs font-mono font-bold">
              Unsupervised Tier 2 Deep Explainability
            </span>
          </div>
        </div>

        {/* 4-Card Anomaly Intelligence Scorecard */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 font-mono text-xs">
          {/* Card 1: Calibrated Severity */}
          <div className="bg-industrial-900/90 p-4 rounded-xl border border-industrial-700/60 space-y-2">
            <span className="text-slate-400 text-[11px] block font-semibold">CALIBRATED SEVERITY</span>
            <div className="flex items-baseline justify-between">
              <span className={`text-2xl font-black ${
                severityScore >= 75 ? 'text-rose-400' : severityScore >= 50 ? 'text-amber-400' : severityScore >= 25 ? 'text-cyan-300' : 'text-emerald-400'
              }`}>
                {severityScore} <span className="text-xs text-slate-400 font-normal">/ 100</span>
              </span>
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                severityScore >= 75 ? 'bg-rose-500/20 text-rose-300' : severityScore >= 50 ? 'bg-amber-500/20 text-amber-300' : severityScore >= 25 ? 'bg-cyan-500/20 text-cyan-300' : 'bg-emerald-500/20 text-emerald-300'
              }`}>
                {severityLabel}
              </span>
            </div>
            <div className="w-full bg-industrial-800 rounded-full h-1.5 overflow-hidden">
              <div 
                className={`h-full ${severityScore >= 75 ? 'bg-rose-500' : severityScore >= 50 ? 'bg-amber-500' : severityScore >= 25 ? 'bg-cyan-400' : 'bg-emerald-500'}`}
                style={{ width: `${Math.min(100, Math.max(5, severityScore))}%` }}
              />
            </div>
            <span className="text-[10px] text-slate-400 block pt-0.5">
              Score: {streamState?.anomaly?.score || 0} (τ = 0.5040)
            </span>
          </div>

          {/* Card 2: Trajectory */}
          <div className="bg-industrial-900/90 p-4 rounded-xl border border-industrial-700/60 space-y-2">
            <span className="text-slate-400 text-[11px] block font-semibold">ANOMALY TRAJECTORY</span>
            <div className="flex items-center gap-2 pt-1">
              {trajectory === 'WORSENING' && (
                <div className="flex items-center gap-1.5 text-rose-400 font-bold text-base">
                  <TrendingUp className="w-5 h-5 text-rose-400" />
                  <span>WORSENING</span>
                </div>
              )}
              {trajectory === 'RECOVERING' && (
                <div className="flex items-center gap-1.5 text-emerald-400 font-bold text-base">
                  <TrendingDown className="w-5 h-5 text-emerald-400" />
                  <span>RECOVERING</span>
                </div>
              )}
              {trajectory === 'STABLE' && (
                <div className="flex items-center gap-1.5 text-slate-300 font-bold text-base">
                  <Minus className="w-5 h-5 text-slate-400" />
                  <span>STABLE</span>
                </div>
              )}
            </div>
            <span className="text-[10px] text-slate-400 block pt-1">
              Slope over trailing 15 observations
            </span>
          </div>

          {/* Card 3: Persistence */}
          <div className="bg-industrial-900/90 p-4 rounded-xl border border-industrial-700/60 space-y-2">
            <span className="text-slate-400 text-[11px] block font-semibold">TEMPORAL PERSISTENCE</span>
            <div className="flex items-baseline justify-between pt-1">
              <span className={`text-base font-bold ${
                persistence.status === 'PERSISTENT' ? 'text-amber-300' : 'text-slate-300'
              }`}>
                {persistence.status}
              </span>
              <span className="text-xs text-slate-400">
                {persistence.abnormal_count} / {persistence.window_size} obs
              </span>
            </div>
            <div className="w-full bg-industrial-800 rounded-full h-1.5 overflow-hidden">
              <div 
                className="bg-amber-400 h-full"
                style={{ width: `${Math.min(100, (persistence.abnormal_count / Math.max(1, persistence.window_size)) * 100)}%` }}
              />
            </div>
            <span className="text-[10px] text-slate-400 block pt-0.5">
              Persistence threshold: ≥3 anomalies in 5m
            </span>
          </div>

          {/* Card 4: Model Synergy */}
          <div className="bg-industrial-900/90 p-4 rounded-xl border border-industrial-700/60 space-y-1.5">
            <span className="text-slate-400 text-[11px] block font-semibold">DUAL-TIER SYNTHESIS</span>
            <div className="space-y-1 pt-0.5">
              <div className="flex justify-between text-[11px]">
                <span className="text-slate-400">XGBoost Risk:</span>
                <strong className={streamState?.xgboost?.risk_percentage > 10 ? 'text-rose-400' : 'text-white'}>
                  {streamState?.xgboost?.risk_percentage || 0}%
                </strong>
              </div>
              <div className="flex justify-between text-[11px]">
                <span className="text-slate-400">Anomaly Index:</span>
                <strong className={severityScore >= 50 ? 'text-amber-300' : 'text-cyan-300'}>
                  {severityLabel}
                </strong>
              </div>
            </div>
            <span className="text-[10px] text-blue-300 block pt-1 truncate">
              {currentScenario === 'unseen_anomaly' ? '★ Unseen Regime Shift Detected' : 'Orthogonal Multi-Signal Defense'}
            </span>
          </div>
        </div>

        {/* Top Contributing Sensor Deviations Table */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-bold text-white uppercase font-mono tracking-wide flex items-center gap-2">
              <FileSearch className="w-4 h-4 text-cyan-400" />
              Top Contributing Sensor Deviations (Physical Evidence vs Baseline)
            </h4>
            <span className="text-[11px] text-slate-400 font-mono">
              Ranked by Absolute Statistical Z-Score
            </span>
          </div>

          {topDeviations && topDeviations.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 font-mono text-xs">
              {topDeviations.map((dev, dIdx) => (
                <div 
                  key={dIdx} 
                  className={`p-3.5 rounded-xl border transition-all space-y-2 ${
                    dev.abs_z >= 2.5 
                      ? 'bg-industrial-900/90 border-rose-500/30' 
                      : dev.abs_z >= 1.5 
                      ? 'bg-industrial-900/80 border-amber-500/30' 
                      : 'bg-industrial-900/50 border-industrial-700/40'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <strong className="text-white font-bold block truncate">{dev.name}</strong>
                      <span className="text-[10px] text-slate-400 font-sans">{dev.system}</span>
                    </div>
                    <span className={`px-2 py-0.5 rounded text-[11px] font-bold shrink-0 ${
                      dev.z_score > 0 ? 'bg-amber-500/20 text-amber-300' : 'bg-blue-500/20 text-blue-300'
                    }`}>
                      {dev.z_score > 0 ? `+${dev.z_score}σ` : `${dev.z_score}σ`}
                    </span>
                  </div>

                  <div className="grid grid-cols-3 gap-1 text-[11px] bg-industrial-950/60 p-2 rounded-lg border border-industrial-800">
                    <div>
                      <span className="text-slate-500 text-[10px] block">Current</span>
                      <strong className="text-slate-100">{dev.current_value} {dev.unit}</strong>
                    </div>
                    <div>
                      <span className="text-slate-500 text-[10px] block">Baseline</span>
                      <span className="text-slate-300">{dev.baseline_median}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 text-[10px] block">Delta</span>
                      <strong className={dev.deviation > 0 ? 'text-amber-400' : 'text-blue-400'}>
                        {dev.deviation > 0 ? `+${dev.deviation}` : dev.deviation}
                      </strong>
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-[10px] pt-0.5">
                    <span className="text-slate-400">Trend:</span>
                    <span className={`font-bold flex items-center gap-1 ${
                      dev.trend === 'RISING' ? 'text-rose-400' : dev.trend === 'FALLING' ? 'text-blue-400' : 'text-slate-400'
                    }`}>
                      {dev.trend === 'RISING' ? '↑ Rising' : dev.trend === 'FALLING' ? '↓ Falling' : '→ Stable'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-xs text-slate-400 font-sans italic bg-industrial-900/50 p-4 rounded-xl border border-industrial-700/30 text-center">
              All monitored sensor channels conform to nominal baseline operating distributions.
            </div>
          )}
        </div>
      </div>

      {/* 7. TASK 21: REMAINING USEFUL LIFE (RUL) FEASIBILITY AUDIT & SCIENTIFIC DECISION */}
      <div className="bg-industrial-850 rounded-2xl p-6 border border-industrial-700/80 shadow-2xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-industrial-700/60 pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-amber-400" />
              <h3 className="text-xl font-extrabold text-white tracking-tight">
                Remaining Useful Life (RUL) Feasibility Audit & Scientific Decision
              </h3>
            </div>
            <p className="text-xs text-slate-300">
              Rigorous data-sufficiency assessment determining whether continuous time-to-failure regression is scientifically defensible.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-xl bg-amber-500/20 text-amber-300 border border-amber-500/40 text-xs font-mono font-bold">
              OUTCOME B — SCIENTIFIC HONESTY PROTOCOL
            </span>
          </div>
        </div>

        {/* Scientific Verdict Banner */}
        <div className="bg-gradient-to-r from-industrial-900 via-industrial-950 to-industrial-900 p-5 rounded-2xl border border-amber-500/30 space-y-3">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />
            <strong className="text-sm font-bold text-amber-300 uppercase font-mono tracking-wide">
              Scientific Audit Decision: Continuous RUL Prediction is NOT Feasible with Current Data
            </strong>
          </div>
          <p className="text-xs text-slate-300 font-sans leading-relaxed">
            MetroGuard AI definitively concludes that continuous Remaining Useful Life (RUL) regression cannot be validated with scientific defensibility on the MetroPT-3 dataset due to extreme sample scarcity (only <strong className="text-white">N = 4 discrete failure cycles</strong> across 6 months on a single train unit) and significant failure mode heterogeneity. Rather than displaying an unvalidated, fabricated countdown clock, MetroGuard provides validated early risk classification, anomaly severity indices, persistence tracking, and evidence-backed prescriptive inspection workflows.
          </p>
        </div>

        {/* 4 Quantitative Limiting Factors */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 font-mono text-xs">
          <div className="bg-industrial-900/80 p-4 rounded-xl border border-industrial-700/60 space-y-2">
            <span className="text-amber-400 font-bold block text-[11px]">1. EXTREME SAMPLE SCARCITY</span>
            <strong className="text-white text-base block font-sans">N = 4 Total Cycles</strong>
            <p className="text-[11px] text-slate-400 font-sans">
              Single monitored asset (APU-TR-03). A leakage-safe split yields only N=2 train events, violating statistical sample requirements for regression.
            </p>
          </div>

          <div className="bg-industrial-900/80 p-4 rounded-xl border border-industrial-700/60 space-y-2">
            <span className="text-cyan-400 font-bold block text-[11px]">2. FAILURE MODE DIVERGENCE</span>
            <strong className="text-white text-base block font-sans">Spring vs Summer Physics</strong>
            <p className="text-[11px] text-slate-400 font-sans">
              Events #1 & #2 are spring pneumatic leaks; Event #4 occurred under extreme summer thermal stress (81.4°C oil temp). Trajectories do not share a common curve.
            </p>
          </div>

          <div className="bg-industrial-900/80 p-4 rounded-xl border border-industrial-700/60 space-y-2">
            <span className="text-purple-400 font-bold block text-[11px]">3. ABRUPT DYNAMICS</span>
            <strong className="text-white text-base block font-sans">Non-Monotonic Drop</strong>
            <p className="text-[11px] text-slate-400 font-sans">
              Pneumatic solenoid valves fail discretely within 30 minutes rather than exhibiting gradual multi-week mechanical wear (like turbofan bearings).
            </p>
          </div>

          <div className="bg-industrial-900/80 p-4 rounded-xl border border-industrial-700/60 space-y-2">
            <span className="text-emerald-400 font-bold block text-[11px]">4. UNLOGGED MAINTENANCE</span>
            <strong className="text-white text-base block font-sans">Unmetered Depot Resets</strong>
            <p className="text-[11px] text-slate-400 font-sans">
              Exact post-failure overhaul timestamps, component cleanouts, and oil refills were unrecorded in dataset metadata, precluding ground-truth reset baselines.
            </p>
          </div>
        </div>

        {/* Validated System Capabilities Matrix */}
        <div className="space-y-3">
          <h4 className="text-sm font-bold text-white uppercase font-mono tracking-wide flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            System Capability Matrix: Validated vs Unsupported Features
          </h4>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
            <div className="p-3.5 bg-industrial-900/80 rounded-xl border border-emerald-500/30 flex items-start gap-3">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <strong className="text-white font-bold block">Early Failure Risk Assessment</strong>
                <span className="text-slate-300 text-[11px] font-sans">
                  Graduated probability of failure within 30 minutes via frozen supervised XGBoost (100% recall on spring failures).
                </span>
              </div>
            </div>

            <div className="p-3.5 bg-industrial-900/80 rounded-xl border border-emerald-500/30 flex items-start gap-3">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <strong className="text-white font-bold block">Piecewise Calibrated Anomaly Severity</strong>
                <span className="text-slate-300 text-[11px] font-sans">
                  Normalized 0–100 severity index derived from 99th training percentiles via Isolation Forest (33.15% recall on summer holdout).
                </span>
              </div>
            </div>

            <div className="p-3.5 bg-industrial-900/80 rounded-xl border border-emerald-500/30 flex items-start gap-3">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <strong className="text-white font-bold block">Physical Baseline Deviation & Persistence Tracking</strong>
                <span className="text-slate-300 text-[11px] font-sans">
                  Real-time statistical Z-score attribution on engineered features relative to verified normal operating medians.
                </span>
              </div>
            </div>

            <div className="p-3.5 bg-industrial-900/80 rounded-xl border border-industrial-700/60 flex items-start gap-3 opacity-75">
              <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <div className="flex items-center gap-2">
                  <strong className="text-slate-300 font-bold">Continuous RUL Countdown Clock</strong>
                  <span className="text-[10px] font-mono px-2 py-0.5 bg-amber-500/20 text-amber-300 rounded">
                    NOT SUPPORTED
                  </span>
                </div>
                <span className="text-slate-400 text-[11px] font-sans">
                  Precluded by sample scarcity (N=4). MetroGuard strictly rejects fabricated countdowns in favor of scientific transparency.
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
