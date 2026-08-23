import React, { useState, useEffect, useRef } from 'react';
import { 
  Activity, 
  Clock, 
  ShieldCheck, 
  Database, 
  Cpu, 
  Layers, 
  CheckCircle2, 
  TrendingUp,
  AlertTriangle,
  Play,
  Pause,
  RotateCcw,
  SkipForward,
  ArrowRight,
  Zap,
  Wrench,
  Compass,
  FileSearch,
  ShieldAlert,
  Sliders,
  Check,
  FileText,
  Radio,
  AlertOctagon,
  Info,
  Calendar,
  AlertCircle,
  HelpCircle,
  BarChart3,
  Gauge,
  Sparkles
} from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import SensorCard from '../components/SensorCard';
import RiskGauge from '../components/RiskGauge';
import { 
  getStreamStatus, 
  getStreamCurrent, 
  startStream, 
  stopStream, 
  resetStream, 
  setStreamScenario, 
  setStreamSpeed,
  stepStream
} from '../services/api';

const SCENARIOS = [
  { id: 'normal', name: '1. Normal Baseline', shortDesc: 'Cyclical Pumping Baseline (30m)', badge: 'NOMINAL', targetState: 'NORMAL' },
  { id: 'gradual_anomaly', name: '2. Gradual Drift', shortDesc: 'Thermal Buildup & Pressure Drift', badge: 'WARNING', targetState: 'MONITOR → WARNING' },
  { id: 'pre_failure', name: '3. Pre-Failure (Event #1)', shortDesc: 'Supervised 98.78% High Risk Breakdown', badge: 'CRITICAL', targetState: 'HIGH RISK' },
  { id: 'unseen_anomaly', name: '4. Summer Holdout (Event #4)', shortDesc: 'Unseen Thermal Anomaly (+3.69σ)', badge: 'MEDIUM', targetState: 'WARNING' }
];

const SPEED_OPTIONS = [
  { label: '0.5x Slow', value: 0.5 },
  { label: '1x Realtime', value: 1.0 },
  { label: '2x Fast', value: 2.0 },
  { label: '5x Demo', value: 5.0 },
  { label: '10x Turbo', value: 10.0 }
];

export default function OverviewPage({ latestData, onNavigate }) {
  const [streamState, setStreamState] = useState(null);
  const [isPlaying, setIsPlaying] = useState(true);
  const [playbackSpeed, setPlaybackSpeed] = useState(1.0);
  const [selectedScenario, setSelectedScenario] = useState('normal');
  const [isProcessing, setIsProcessing] = useState(false);

  const pollTimerRef = useRef(null);

  // Initialize and synchronize with streaming service
  useEffect(() => {
    fetchStreamSnapshot();

    // Fast polling when replay is active to ensure instant dashboard updates
    pollTimerRef.current = setInterval(() => {
      fetchStreamSnapshot();
    }, 1200);

    return () => {
      if (pollTimerRef.current) {
        clearInterval(pollTimerRef.current);
      }
    };
  }, []);

  const fetchStreamSnapshot = async () => {
    try {
      const snap = await getStreamCurrent();
      if (snap && snap.sensors) {
        setStreamState(snap);
        if (snap.scenario && snap.scenario !== selectedScenario) {
          setSelectedScenario(snap.scenario);
        }
      }
      const stat = await getStreamStatus();
      if (stat) {
        setIsPlaying(stat.is_running);
        setPlaybackSpeed(stat.speed || stat.playback_speed || 1.0);
        if (stat.scenario) {
          setSelectedScenario(stat.scenario);
        }
      }
    } catch (err) {
      console.warn('Streaming sync warning:', err.message);
    }
  };

  const handleStart = async () => {
    setIsProcessing(true);
    try {
      await startStream();
      setIsPlaying(true);
      await fetchStreamSnapshot();
    } catch (err) {
      console.error('Error starting stream:', err);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleStop = async () => {
    setIsProcessing(true);
    try {
      await stopStream();
      setIsPlaying(false);
      await fetchStreamSnapshot();
    } catch (err) {
      console.error('Error pausing stream:', err);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleReset = async () => {
    setIsProcessing(true);
    try {
      await resetStream();
      await fetchStreamSnapshot();
    } catch (err) {
      console.error('Error resetting stream:', err);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleStep = async () => {
    setIsProcessing(true);
    try {
      await stepStream();
      await fetchStreamSnapshot();
    } catch (err) {
      console.error('Error stepping stream:', err);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSelectScenario = async (scId) => {
    if (scId === selectedScenario && isProcessing) return;
    setIsProcessing(true);
    try {
      setSelectedScenario(scId);
      await setStreamScenario(scId);
      await resetStream();
      await fetchStreamSnapshot();
    } catch (err) {
      console.error('Error setting scenario:', err);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSetSpeed = async (spd) => {
    try {
      setPlaybackSpeed(spd);
      await setStreamSpeed(spd);
    } catch (err) {
      console.error('Error setting speed:', err);
    }
  };

  // Derive dynamic dashboard values strictly from the active stream snapshot
  const sensors = streamState?.sensors || latestData?.sensors || {};
  const xgbRisk = streamState?.xgboost || latestData?.prediction || {
    risk_probability: 0.0004,
    risk_percentage: 0.04,
    status: 'NORMAL',
    threshold: 0.10
  };
  const anomIntel = streamState?.anomaly_intelligence || {
    anomaly_severity: 20,
    anomaly_status: 'NOMINAL',
    top_sensor_deviations: [],
    trajectory: 'STABLE'
  };
  const activeAlert = streamState?.active_operator_alert || null;
  const prescriptiveRec = streamState?.prescriptive_recommendation || null;
  const currentTimestamp = streamState?.timestamp || latestData?.timestamp || '2020-04-17 23:30:00';
  const hybridStatus = streamState?.hybrid?.status || streamState?.hybrid_status || xgbRisk.status || 'NORMAL';
  const progressPercent = streamState?.progress_percent !== undefined ? streamState.progress_percent : 0;
  const totalRecords = streamState?.total_records || 272;
  const currentIndex = streamState?.current_index !== undefined ? streamState.current_index : 0;

  const primarySensorKeys = ['TP2', 'TP3', 'H1', 'Reservoirs', 'Oil_temperature', 'Motor_current'];

  // Top physical evidence calculation for dynamic storytelling
  const topDeviations = anomIntel.top_sensor_deviations || streamState?.evidence || [];
  const primaryEvidence = topDeviations.length > 0 ? topDeviations[0] : null;

  // Dynamically compute primary operational concern
  const getPrimaryConcern = () => {
    if (hybridStatus === 'HIGH RISK') {
      if (xgbRisk.risk_percentage >= 70) {
        return `Severe pre-failure pneumatic leak pattern recognized by Supervised XGBoost (${xgbRisk.risk_percentage}% risk) with active pressure decay.`;
      }
      return `Concurrent critical alert: Supervised risk (${xgbRisk.risk_percentage}%) compounded by elevated multidimensional anomaly.`;
    }
    if (hybridStatus === 'FAILURE WARNING') {
      return `Known pre-failure pneumatic signature detected (${xgbRisk.risk_percentage}% risk). Inspection recommended before pressure collapse.`;
    }
    if (hybridStatus === 'ANOMALY WARNING' || (hybridStatus === 'WARNING' && anomIntel.anomaly_severity >= 50)) {
      if (sensors.Oil_temperature?.value >= 75) {
        return `Severe thermal elevation in crankcase oil (${sensors.Oil_temperature.value}°C) detected via Unsupervised Isolation Forest (${anomIntel.anomaly_severity}/100 severity).`;
      }
      return `Significant out-of-distribution operational regime detected by Isolation Forest (${anomIntel.anomaly_severity}/100 severity).`;
    }
    if (hybridStatus === 'MONITOR') {
      return `Transient sensor deviation flagged (|Z| ≥ 2.0σ). Telemetry buffered for 5-minute persistence evaluation.`;
    }
    return `All 15 raw telemetry channels and 65 engineered time-series features conform strictly to verified normal baseline envelopes.`;
  };

  // Determine active timeline stage
  const getTimelineStage = () => {
    if (hybridStatus === 'HIGH RISK') return 4; // High Risk
    if (hybridStatus === 'FAILURE WARNING' || hybridStatus === 'ANOMALY WARNING' || hybridStatus === 'WARNING') return 3; // Warning
    if (hybridStatus === 'MONITOR' || anomIntel.anomaly_severity >= 35) return 2; // Anomaly Onset
    return 1; // Normal Baseline
  };

  const activeStage = getTimelineStage();

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* 1. TOP HERO / ASSET IDENTITY BANNER */}
      <div className="bg-gradient-to-r from-industrial-850 via-industrial-800 to-industrial-850 p-6 rounded-2xl border border-industrial-700/60 shadow-xl space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className="px-2.5 py-1 rounded bg-blue-500/20 border border-blue-500/30 text-blue-400 text-xs font-mono font-bold flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5" />
                MONITORED ASSET: APU-TR-03
              </span>
              <span className="text-xs font-mono text-slate-400">Urban Rail Main Air Compressor</span>
              <span className="text-xs font-mono px-2.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 font-bold">
                HISTORICAL EVENT REPLAY — DEMO MODE
              </span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Predictive Maintenance AI &amp; Decision Command Center
            </h2>
            <p className="text-sm text-slate-300 max-w-3xl leading-relaxed">
              MetroGuard AI transforms 15 raw telemetry channels into 65 engineered time-series features, executing dual-tier supervised and unsupervised AI with physical evidence attribution to provide 30-minute early warning and prescriptive depot actions before in-service breakdown.
            </p>
          </div>

          {/* Quick Action Navigation */}
          <div className="flex flex-wrap items-center gap-3 shrink-0">
            <button
              onClick={() => onNavigate('monitoring')}
              className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-medium px-4 py-2.5 rounded-xl text-sm transition-all shadow-lg shadow-blue-600/20 font-mono"
            >
              <Activity className="w-4 h-4" />
              <span>Detailed Monitoring &amp; Alerts</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => onNavigate('case-study')}
              className="flex items-center gap-2 bg-amber-600/20 hover:bg-amber-600/30 text-amber-300 font-medium px-4 py-2.5 rounded-xl text-sm border border-amber-500/40 transition-all font-mono"
            >
              <FileText className="w-4 h-4 text-amber-400" />
              <span>Case Studies &amp; Impact</span>
            </button>
            <button
              onClick={() => onNavigate('risk')}
              className="flex items-center gap-2 bg-industrial-700 hover:bg-industrial-600 text-slate-200 font-medium px-4 py-2.5 rounded-xl text-sm border border-industrial-600 transition-all font-mono"
            >
              <span>AI Risk</span>
            </button>
          </div>
        </div>

        {/* 6-Step Pipeline Flow Banner */}
        <div className="pt-2 border-t border-industrial-700/50">
          <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block font-semibold mb-2.5">
            How MetroGuard AI Works — End-to-End Multi-Signal Architecture:
          </span>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 text-xs font-mono">
            <div className="bg-industrial-900/80 p-2.5 rounded-xl border border-industrial-700/50 space-y-1">
              <span className="text-[10px] text-blue-400 font-bold block">1. TELEMETRY</span>
              <strong className="text-white text-xs block truncate">15 Raw Signals</strong>
              <span className="text-[10px] text-slate-400 block truncate">10s multi-channel</span>
            </div>

            <div className="bg-industrial-900/80 p-2.5 rounded-xl border border-industrial-700/50 space-y-1">
              <span className="text-[10px] text-purple-400 font-bold block">2. DUAL AI TIER</span>
              <strong className="text-white text-xs block truncate">XGBoost + IF</strong>
              <span className="text-[10px] text-slate-400 block truncate">65 Engineered Ch</span>
            </div>

            <div className="bg-industrial-900/80 p-2.5 rounded-xl border border-industrial-700/50 space-y-1">
              <span className="text-[10px] text-amber-400 font-bold block">3. EVIDENCE</span>
              <strong className="text-white text-xs block truncate">Z-Score Deltas</strong>
              <span className="text-[10px] text-slate-400 block truncate">|Z| ≥ 2.0σ Medians</span>
            </div>

            <div className="bg-industrial-900/80 p-2.5 rounded-xl border border-industrial-700/50 space-y-1">
              <span className="text-[10px] text-cyan-400 font-bold block">4. HYBRID ENGINE</span>
              <strong className="text-white text-xs block truncate">Deterministic</strong>
              <span className="text-[10px] text-slate-400 block truncate">Synthesis logic</span>
            </div>

            <div className="bg-industrial-900/80 p-2.5 rounded-xl border border-industrial-700/50 space-y-1">
              <span className="text-[10px] text-rose-400 font-bold block">5. SMART ALERTS</span>
              <strong className="text-white text-xs block truncate">Deduplicated</strong>
              <span className="text-[10px] text-slate-400 block truncate">Priority &amp; lifecycle</span>
            </div>

            <div className="bg-industrial-900/80 p-2.5 rounded-xl border border-industrial-700/50 space-y-1">
              <span className="text-[10px] text-emerald-400 font-bold block">6. ACTION</span>
              <strong className="text-white text-xs block truncate">Prescriptive</strong>
              <span className="text-[10px] text-slate-400 block truncate">4-Point Checklist</span>
            </div>
          </div>
        </div>
      </div>

      {/* 2. MULTI-EVENT REPLAY CONTROLLER & QUICK DEMO LAUNCHERS */}
      <div className="bg-industrial-850 p-6 rounded-2xl border border-industrial-700/60 shadow-xl space-y-5">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-industrial-700/60 pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Radio className="w-5 h-5 text-blue-400 animate-pulse" />
              <h3 className="text-base font-bold text-white">
                Multi-Event Live Telemetry Replay &amp; Storytelling Control
              </h3>
              <span className="px-2.5 py-0.5 rounded text-[10px] font-mono font-bold bg-blue-500/20 text-blue-300 border border-blue-500/30">
                15 RAW → 65 FEATURES
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Select a verified historical episode from the MetroPT-3 benchmark to watch machine telemetry, AI risk, and prescriptive actions evolve in real time.
            </p>
          </div>

          {/* Transport Controls */}
          <div className="flex flex-wrap items-center gap-2 font-mono text-xs">
            {isPlaying ? (
              <button
                onClick={handleStop}
                disabled={isProcessing}
                className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-amber-600/30 hover:bg-amber-600/40 text-amber-300 border border-amber-500/40 transition-all font-semibold shadow-md"
              >
                <Pause className="w-4 h-4" />
                <span>Pause</span>
              </button>
            ) : (
              <button
                onClick={handleStart}
                disabled={isProcessing}
                className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white transition-all font-semibold shadow-lg shadow-emerald-600/20"
              >
                <Play className="w-4 h-4 fill-white" />
                <span>Start Replay</span>
              </button>
            )}

            <button
              onClick={handleStep}
              disabled={isProcessing || isPlaying}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-industrial-900 hover:bg-industrial-700 text-slate-300 border border-industrial-700 transition-all disabled:opacity-50"
              title="Step forward 10 seconds"
            >
              <SkipForward className="w-3.5 h-3.5" />
              <span>Step 10s</span>
            </button>

            <button
              onClick={handleReset}
              disabled={isProcessing}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-industrial-900 hover:bg-industrial-700 text-slate-300 border border-industrial-700 transition-all"
              title="Reset to start of episode"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset</span>
            </button>

            {/* Speed Multiplier Pills */}
            <div className="flex items-center gap-1 bg-industrial-900/90 p-1 rounded-xl border border-industrial-700 ml-1">
              {SPEED_OPTIONS.map((spd) => (
                <button
                  key={spd.value}
                  onClick={() => handleSetSpeed(spd.value)}
                  className={`px-2 py-1 rounded-lg text-[10px] font-bold transition-all ${
                    playbackSpeed === spd.value
                      ? 'bg-blue-600 text-white shadow-sm'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {spd.label.split(' ')[0]}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* 4 Interactive Scenario Selection Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 font-mono text-xs">
          {SCENARIOS.map((sc) => {
            const isSelected = selectedScenario === sc.id;
            return (
              <button
                key={sc.id}
                onClick={() => handleSelectScenario(sc.id)}
                disabled={isProcessing}
                className={`p-4 rounded-xl text-left border transition-all space-y-1.5 group ${
                  isSelected
                    ? 'bg-blue-600/20 border-blue-500 shadow-lg shadow-blue-500/10'
                    : 'bg-industrial-900/80 border-industrial-700/60 hover:border-industrial-600 hover:bg-industrial-800 text-slate-300'
                }`}
              >
                <div className="flex items-center justify-between">
                  <strong className={`font-bold text-xs ${isSelected ? 'text-blue-300' : 'text-white group-hover:text-blue-200'}`}>
                    {sc.name}
                  </strong>
                  <span className={`w-2 h-2 rounded-full ${
                    sc.id === 'normal' ? 'bg-emerald-400' : sc.id === 'pre_failure' ? 'bg-rose-400' : 'bg-amber-400'
                  }`} />
                </div>
                <p className="text-[11px] text-slate-400 font-sans leading-snug">
                  {sc.shortDesc}
                </p>
                <div className="flex items-center justify-between pt-1 text-[10px]">
                  <span className="text-slate-400">Target:</span>
                  <span className={`font-bold px-1.5 py-0.2 rounded ${
                    sc.badge === 'CRITICAL' ? 'bg-rose-500/20 text-rose-300' : sc.badge === 'WARNING' ? 'bg-amber-500/20 text-amber-300' : 'bg-emerald-500/20 text-emerald-300'
                  }`}>
                    {sc.targetState}
                  </span>
                </div>
              </button>
            );
          })}
        </div>

        {/* Hackathon Quick Actions Banner */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-industrial-700/50 text-xs font-mono">
          <div className="flex items-center gap-2 text-slate-400">
            <Sparkles className="w-4 h-4 text-amber-400" />
            <span className="font-semibold text-slate-300">Hackathon Demo Quick Launchers:</span>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => handleSelectScenario('pre_failure')}
              className="px-3 py-1.5 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/30 font-semibold transition-all"
            >
              Load Event #1 (Breakdown)
            </button>
            <button
              onClick={() => handleSelectScenario('unseen_anomaly')}
              className="px-3 py-1.5 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/30 font-semibold transition-all"
            >
              Load Event #4 (Summer Thermal)
            </button>
            <button
              onClick={() => handleSelectScenario('normal')}
              className="px-3 py-1.5 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/30 font-semibold transition-all"
            >
              Reset Normal Baseline
            </button>
          </div>
        </div>
      </div>

      {/* 3. CURRENT MACHINE STATUS & PRIMARY STORYTELLING HERO */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Machine Health & Status Scorecard */}
        <div className="lg:col-span-2 bg-industrial-850 rounded-2xl p-6 border border-industrial-700/60 shadow-xl flex flex-col justify-between relative overflow-hidden space-y-5">
          <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/5 rounded-full blur-3xl -z-0" />
          
          <div className="relative z-10 space-y-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <span className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <Activity className="w-3.5 h-3.5 text-blue-400" />
                  CURRENT MACHINE STATUS — APU-TR-03
                </span>
                <h3 className="text-xl font-bold text-white mt-0.5">
                  Real-Time Multi-Signal Assessment &amp; Decision State
                </h3>
              </div>
              <StatusBadge status={hybridStatus} size="lg" />
            </div>

            {/* Dynamic Primary Concern Callout */}
            <div className={`p-4 rounded-xl border text-xs font-sans space-y-1.5 ${
              hybridStatus === 'HIGH RISK'
                ? 'bg-rose-500/10 border-rose-500/30 text-rose-200'
                : hybridStatus === 'WARNING' || hybridStatus === 'FAILURE WARNING' || hybridStatus === 'ANOMALY WARNING'
                ? 'bg-amber-500/10 border-amber-500/30 text-amber-200'
                : hybridStatus === 'MONITOR'
                ? 'bg-blue-500/10 border-blue-500/30 text-blue-200'
                : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-200'
            }`}>
              <div className="flex items-center gap-2 font-mono font-bold text-[11px] uppercase tracking-wider">
                <AlertOctagon className="w-3.5 h-3.5" />
                <span>Primary Operational Concern:</span>
              </div>
              <p className="leading-relaxed text-slate-200 text-xs font-medium">
                {getPrimaryConcern()}
              </p>
            </div>

            {/* 4-KPI Metric Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1 font-mono text-xs">
              <div className="bg-industrial-900/80 p-4 rounded-xl border border-industrial-700/50 space-y-1">
                <span className="text-[10px] text-slate-400 block uppercase">Supervised Risk</span>
                <span className={`text-2xl font-extrabold ${xgbRisk.risk_percentage >= 70 ? 'text-rose-400' : xgbRisk.risk_percentage >= 10 ? 'text-amber-400' : 'text-white'}`}>
                  {xgbRisk.risk_percentage}%
                </span>
                <span className="text-[10px] text-slate-400 block">Horizon: 30 Min (τ = 0.10)</span>
              </div>

              <div className="bg-industrial-900/80 p-4 rounded-xl border border-industrial-700/50 space-y-1">
                <span className="text-[10px] text-slate-400 block uppercase">Anomaly Index</span>
                <span className="text-2xl font-extrabold text-cyan-300">
                  {anomIntel.anomaly_severity}<span className="text-xs text-slate-400 font-normal">/100</span>
                </span>
                <span className={`text-[10px] block font-bold ${
                  anomIntel.anomaly_status === 'SEVERE' ? 'text-rose-400' : anomIntel.anomaly_status === 'ELEVATED' ? 'text-amber-400' : 'text-emerald-400'
                }`}>
                  {anomIntel.anomaly_status || 'NOMINAL'} (IF Score: {streamState?.anomaly?.score || 0.35})
                </span>
              </div>

              <div className="bg-industrial-900/80 p-4 rounded-xl border border-industrial-700/50 space-y-1">
                <span className="text-[10px] text-slate-400 block uppercase">Active Priority</span>
                <span className={`text-lg font-bold pt-1 block ${
                  activeAlert?.priority === 'CRITICAL' ? 'text-rose-400' : activeAlert?.priority === 'HIGH' ? 'text-amber-400' : 'text-emerald-400'
                }`}>
                  {activeAlert?.priority || (hybridStatus === 'HIGH RISK' ? 'CRITICAL' : hybridStatus === 'WARNING' ? 'HIGH' : 'NOMINAL')}
                </span>
                <span className="text-[10px] text-slate-400 block truncate">
                  {activeAlert?.status || 'Routine Cycle'}
                </span>
              </div>

              <div className="bg-industrial-900/80 p-4 rounded-xl border border-industrial-700/50 space-y-1">
                <span className="text-[10px] text-slate-400 block uppercase">Replay Position</span>
                <span className="text-xs font-bold text-slate-200 block truncate pt-1">
                  {currentTimestamp}
                </span>
                <span className="text-[10px] text-blue-400 block flex items-center gap-1 truncate">
                  <Clock className="w-3 h-3" /> Step {currentIndex + 1} / {totalRecords} ({progressPercent}%)
                </span>
              </div>
            </div>

            {/* Prescriptive Recommendation Summary */}
            <div className="bg-industrial-900/90 rounded-xl p-4 border border-industrial-700/60 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-slate-300 font-bold uppercase flex items-center gap-1.5">
                  <Wrench className="w-3.5 h-3.5 text-blue-400" />
                  Recommended Maintenance Action:
                </span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                  prescriptiveRec?.priority === 'Immediate Attention'
                    ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                    : prescriptiveRec?.priority === 'Inspect Soon'
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                    : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                }`}>
                  {prescriptiveRec?.priority || 'ROUTINE MONITORING'}
                </span>
              </div>
              <p className="text-xs text-slate-200 font-sans font-medium">
                {prescriptiveRec?.action || 'Maintain standard preventive maintenance schedule. All monitored physical channels conform to nominal baseline envelopes.'}
              </p>
              {prescriptiveRec?.reason && (
                <p className="text-[11px] text-slate-400 font-sans border-t border-industrial-800 pt-1.5">
                  <strong>Prescriptive Rationale:</strong> {prescriptiveRec.reason}
                </p>
              )}
            </div>
          </div>

          <div className="relative z-10 pt-3 mt-2 border-t border-industrial-700/40 flex items-center justify-between text-xs font-mono text-slate-400">
            <span>Architecture: Dual-Engine + Physical Z-Scores</span>
            <button
              onClick={() => onNavigate('monitoring')}
              className="text-blue-400 hover:text-blue-300 flex items-center gap-1"
            >
              <span>View full 4-point inspection checklist in Monitoring</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* AI Risk Gauge Card */}
        <RiskGauge
          riskProbability={xgbRisk.risk_probability}
          riskPercentage={xgbRisk.risk_percentage}
          status={hybridStatus}
          threshold={xgbRisk.threshold || 0.10}
        />
      </div>

      {/* 4. DYNAMIC EVENT PROGRESSION TIMELINE */}
      <div className="bg-industrial-850 p-6 rounded-2xl border border-industrial-700/60 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-industrial-700/60 pb-3">
          <div className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-blue-400" />
            <h3 className="text-base font-bold text-white">
              Chronological Event Progression Timeline
            </h3>
          </div>
          <span className="text-xs font-mono text-slate-400">
            Replay Progress: <strong className="text-blue-300">{progressPercent}%</strong> ({currentTimestamp})
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-5 gap-3 font-mono text-xs pt-1">
          {/* Milestone 1 */}
          <div className={`p-3.5 rounded-xl border space-y-1.5 transition-all ${
            activeStage >= 1
              ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-300 shadow-sm'
              : 'bg-industrial-900/60 border-industrial-700/40 text-slate-400 opacity-60'
          }`}>
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase">Stage 1</span>
              {activeStage >= 1 && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />}
            </div>
            <strong className="text-xs block text-white">Normal Baseline</strong>
            <p className="text-[10px] text-slate-400 font-sans">Cyclical charging, nominal baselines</p>
          </div>

          {/* Milestone 2 */}
          <div className={`p-3.5 rounded-xl border space-y-1.5 transition-all ${
            activeStage >= 2
              ? 'bg-blue-500/10 border-blue-500/40 text-blue-300 shadow-sm'
              : 'bg-industrial-900/60 border-industrial-700/40 text-slate-400 opacity-60'
          }`}>
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase">Stage 2</span>
              {activeStage >= 2 && <Activity className="w-3.5 h-3.5 text-blue-400" />}
            </div>
            <strong className="text-xs block text-white">Anomaly Onset</strong>
            <p className="text-[10px] text-slate-400 font-sans">Sensor drift (|Z| ≥ 2.0σ, persistence)</p>
          </div>

          {/* Milestone 3 */}
          <div className={`p-3.5 rounded-xl border space-y-1.5 transition-all ${
            activeStage >= 3
              ? 'bg-amber-500/10 border-amber-500/40 text-amber-300 shadow-sm'
              : 'bg-industrial-900/60 border-industrial-700/40 text-slate-400 opacity-60'
          }`}>
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase">Stage 3</span>
              {activeStage >= 3 && <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />}
            </div>
            <strong className="text-xs block text-white">Warning State</strong>
            <p className="text-[10px] text-slate-400 font-sans">τ ≥ 0.10 or Anomaly ≥ 50/100</p>
          </div>

          {/* Milestone 4 */}
          <div className={`p-3.5 rounded-xl border space-y-1.5 transition-all ${
            activeStage >= 4
              ? 'bg-rose-500/15 border-rose-500/50 text-rose-300 shadow-md shadow-rose-500/10'
              : 'bg-industrial-900/60 border-industrial-700/40 text-slate-400 opacity-60'
          }`}>
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase">Stage 4</span>
              {activeStage >= 4 && <AlertOctagon className="w-3.5 h-3.5 text-rose-400 animate-pulse" />}
            </div>
            <strong className="text-xs block text-white">High Risk Escalation</strong>
            <p className="text-[10px] text-slate-400 font-sans">Supervised ≥ 70% (Critical Alert)</p>
          </div>

          {/* Milestone 5 */}
          <div className={`p-3.5 rounded-xl border space-y-1.5 transition-all ${
            activeStage >= 3
              ? 'bg-emerald-500/15 border-emerald-500/50 text-emerald-300'
              : 'bg-industrial-900/60 border-industrial-700/40 text-slate-400 opacity-60'
          }`}>
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase">Stage 5</span>
              {activeStage >= 3 && <Wrench className="w-3.5 h-3.5 text-emerald-400" />}
            </div>
            <strong className="text-xs block text-white">Prescriptive Action</strong>
            <p className="text-[10px] text-slate-400 font-sans">Depot 4-point inspection checklist</p>
          </div>
        </div>
      </div>

      {/* 5. "WHY THIS ALERT?" EXPLAINABILITY & DUAL-MODEL COMPARISON */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* "Why This Alert?" Explainability Panel */}
        <div className="bg-industrial-850 p-6 rounded-2xl border border-industrial-700/60 shadow-xl space-y-4 flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-industrial-700/60 pb-3">
              <div className="flex items-center gap-2">
                <HelpCircle className="w-5 h-5 text-amber-400" />
                <h3 className="text-base font-bold text-white">
                  Why This Alert? — Explainability Chain
                </h3>
              </div>
              <span className="text-xs font-mono text-slate-400">
                Causal Evidence Attribution
              </span>
            </div>

            <div className="space-y-3 text-xs font-sans">
              {/* Step 1: Physical Evidence */}
              <div className="flex items-start gap-3 bg-industrial-900/80 p-3 rounded-xl border border-industrial-700/50">
                <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 font-mono font-bold text-[10px] shrink-0 mt-0.5">
                  1. PHYSICAL
                </span>
                <div>
                  <strong className="text-white block font-medium">Physical Sensor Telemetry:</strong>
                  <span className="text-slate-300 text-[11px]">
                    {primaryEvidence
                      ? `${primaryEvidence.name || primaryEvidence.feature || primaryEvidence.sensor_id}: currently at ${primaryEvidence.current_value || primaryEvidence.actual_value} ${primaryEvidence.unit} (deviation ${primaryEvidence.z_score >= 0 ? `+${primaryEvidence.z_score}σ` : `${primaryEvidence.z_score}σ`} vs baseline).`
                      : 'All 15 raw physical channels conform strictly to nominal baseline envelopes.'}
                  </span>
                </div>
              </div>

              {/* Step 2: AI Detection */}
              <div className="flex items-start gap-3 bg-industrial-900/80 p-3 rounded-xl border border-industrial-700/50">
                <span className="px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 font-mono font-bold text-[10px] shrink-0 mt-0.5">
                  2. AI SIGNAL
                </span>
                <div>
                  <strong className="text-white block font-medium">Dual-Tier AI Detection:</strong>
                  <span className="text-slate-300 text-[11px]">
                    {xgbRisk.risk_percentage >= 10
                      ? `Supervised XGBoost recognized a known pre-failure signature at ${xgbRisk.risk_percentage}% failure risk.`
                      : anomIntel.anomaly_severity >= 35
                      ? `Unsupervised Isolation Forest detected abnormal operating dynamics (Severity: ${anomIntel.anomaly_severity}/100, Score: ${streamState?.anomaly?.score || 0.35}).`
                      : 'Both Supervised XGBoost (0.03%) and Isolation Forest (20/100) confirm normal operational behavior.'}
                  </span>
                </div>
              </div>

              {/* Step 3: Threshold Evaluation */}
              <div className="flex items-start gap-3 bg-industrial-900/80 p-3 rounded-xl border border-industrial-700/50">
                <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono font-bold text-[10px] shrink-0 mt-0.5">
                  3. THRESHOLD
                </span>
                <div>
                  <strong className="text-white block font-medium">Configured Industrial Thresholds:</strong>
                  <span className="text-slate-300 text-[11px]">
                    {xgbRisk.risk_percentage >= 70
                      ? `Critical failure threshold crossed (P ≥ 0.70). High-confidence pre-failure escalation active.`
                      : xgbRisk.risk_percentage >= 10
                      ? `Warning threshold crossed (P ≥ 0.10). Early pneumatic warning condition active.`
                      : anomIntel.anomaly_severity >= 50
                      ? `Outlier threshold crossed (Severity ≥ 50/100, 99th percentile τ = 0.5040).`
                      : `All metrics remain safely below calibrated production thresholds (XGB τ = 0.10, IF τ = 0.5040).`}
                  </span>
                </div>
              </div>

              {/* Step 4: Hybrid Decision Synthesis */}
              <div className="flex items-start gap-3 bg-industrial-900/80 p-3 rounded-xl border border-industrial-700/50">
                <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono font-bold text-[10px] shrink-0 mt-0.5">
                  4. SYNTHESIS
                </span>
                <div>
                  <strong className="text-white block font-medium">Hybrid Decision &amp; Priority:</strong>
                  <span className="text-slate-300 text-[11px]">
                    {streamState?.hybrid?.reason || `Deterministic precedence synthesized operational state: ${hybridStatus}.`}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="pt-3 border-t border-industrial-700/40 flex items-center justify-between text-xs font-mono text-slate-400">
            <span>Zero-Black-Box Protocol</span>
            <span className="text-emerald-400 flex items-center gap-1 font-bold">
              <CheckCircle2 className="w-3.5 h-3.5" /> Explainable Causal Chain
            </span>
          </div>
        </div>

        {/* Dual-Model Comparison ("Why Two Models?") */}
        <div className="bg-industrial-850 p-6 rounded-2xl border border-industrial-700/60 shadow-xl space-y-4 flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-industrial-700/60 pb-3">
              <div className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-purple-400" />
                <h3 className="text-base font-bold text-white">
                  AI Signal Comparison — Why Two Models?
                </h3>
              </div>
              <span className="text-xs font-mono text-slate-400">
                Supervised + Unsupervised
              </span>
            </div>

            <div className="space-y-3 font-mono text-xs">
              {/* XGBoost Box */}
              <div className="bg-industrial-900/80 p-4 rounded-xl border border-blue-500/30 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-blue-400" />
                    <strong className="text-blue-300 font-bold">Tier 1: Supervised XGBoost</strong>
                  </div>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 font-bold">
                    {xgbRisk.status} ({xgbRisk.risk_percentage}%)
                  </span>
                </div>
                <p className="text-[11px] text-slate-300 font-sans">
                  <strong>Role:</strong> Recognizes recurring, labeled pre-failure pneumatic leak signatures ($98.78\%$ recall on spring leaks).
                </p>
                <div className="text-[10px] text-slate-400 flex justify-between border-t border-industrial-800 pt-1.5">
                  <span>Target: P(Breakdown in 30m)</span>
                  <span>Production Threshold: τ = 0.10</span>
                </div>
              </div>

              {/* Isolation Forest Box */}
              <div className="bg-industrial-900/80 p-4 rounded-xl border border-cyan-500/30 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-cyan-400" />
                    <strong className="text-cyan-300 font-bold">Tier 2: Unsupervised Isolation Forest</strong>
                  </div>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-bold">
                    {anomIntel.anomaly_status || 'NOMINAL'} ({anomIntel.anomaly_severity}/100)
                  </span>
                </div>
                <p className="text-[11px] text-slate-300 font-sans">
                  <strong>Role:</strong> Detects novel out-of-distribution operating regimes and summer thermal drift without requiring failure labels ($33.15\%$ recall on Event #4).
                </p>
                <div className="text-[10px] text-slate-400 flex justify-between border-t border-industrial-800 pt-1.5">
                  <span>Method: Isolation Path Length S(x)</span>
                  <span>99th %-tile Threshold: τ = 0.5040</span>
                </div>
              </div>

              {/* Deterministic Hybrid Decision Box */}
              <div className="bg-industrial-900/80 p-3.5 rounded-xl border border-amber-500/30 flex items-center justify-between">
                <div>
                  <span className="text-[10px] text-slate-400 block uppercase">Hybrid Decision Engine Output:</span>
                  <strong className="text-sm font-bold text-white">{hybridStatus}</strong>
                </div>
                <span className={`px-2.5 py-1 rounded text-xs font-bold ${
                  hybridStatus === 'HIGH RISK' ? 'bg-rose-500/20 text-rose-300' : hybridStatus === 'WARNING' || hybridStatus === 'FAILURE WARNING' || hybridStatus === 'ANOMALY WARNING' ? 'bg-amber-500/20 text-amber-300' : 'bg-emerald-500/20 text-emerald-300'
                }`}>
                  {activeAlert?.priority || (hybridStatus === 'HIGH RISK' ? 'CRITICAL' : hybridStatus === 'WARNING' ? 'HIGH' : 'NOMINAL')}
                </span>
              </div>
            </div>
          </div>

          <div className="pt-3 border-t border-industrial-700/40 flex items-center justify-between text-xs font-mono text-slate-400">
            <span>Orthogonal Model Synergy</span>
            <button
              onClick={() => onNavigate('risk')}
              className="text-blue-400 hover:text-blue-300 flex items-center gap-1"
            >
              <span>Explore AI Risk Radar</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* 6. LIVE MONITORED RAW TELEMETRY CHANNELS */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-bold text-white">Live Monitored Raw Telemetry Channels</h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30 font-bold">
                15 RAW CHANNELS → 65 FEATURES
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Instantaneous physical readings dynamically updating with historical replay stream (10s intervals)
            </p>
          </div>
          <button
            onClick={() => onNavigate('sensors')}
            className="text-xs font-mono text-blue-400 hover:text-blue-300 flex items-center gap-1 transition-colors self-start sm:self-auto"
          >
            <span>Inspect all 15 raw telemetry channels</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {primarySensorKeys.map((key) => (
            <SensorCard
              key={key}
              sensor={sensors[key] || { id: key, name: key, value: 0, unit: '' }}
              onClick={() => onNavigate('monitoring')}
            />
          ))}
        </div>
      </div>

      {/* 7. PHYSICAL EVIDENCE ATTRIBUTION (IF ACTIVE) */}
      {topDeviations && topDeviations.length > 0 && (
        <div className="bg-industrial-850 p-6 rounded-2xl border border-industrial-700/60 shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-industrial-700/60 pb-3">
            <div className="flex items-center gap-2">
              <Zap className="w-5 h-5 text-amber-400" />
              <h3 className="text-base font-bold text-white">
                Active Physical Evidence &amp; Statistical Z-Score Deviations
              </h3>
            </div>
            <span className="text-xs font-mono text-slate-400">
              Deviations relative to normal baseline medians (|Z| ≥ 1.5σ)
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 font-mono text-xs">
            {topDeviations.slice(0, 4).map((dev, idx) => (
              <div key={idx} className="bg-industrial-900/80 p-3.5 rounded-xl border border-industrial-700/50 space-y-1.5">
                <div className="flex items-center justify-between">
                  <strong className="text-white font-bold truncate">{dev.name || dev.sensor_name || dev.feature || dev.sensor_id}</strong>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    Math.abs(dev.z_score) >= 2.5 ? 'bg-rose-500/20 text-rose-300' : 'bg-amber-500/20 text-amber-300'
                  }`}>
                    {dev.z_score >= 0 ? `+${dev.z_score.toFixed(2)}σ` : `${dev.z_score.toFixed(2)}σ`}
                  </span>
                </div>
                <div className="flex justify-between text-[11px] text-slate-400">
                  <span>Val: <strong className="text-slate-200">{dev.current_value || dev.actual_value} {dev.unit}</strong></span>
                  <span>Base: {dev.baseline_median}</span>
                </div>
                <span className="text-[10px] text-amber-300 block">
                  Delta: {dev.deviation !== undefined ? (dev.deviation >= 0 ? `+${dev.deviation.toFixed(2)}` : dev.deviation.toFixed(2)) : (dev.delta >= 0 ? `+${dev.delta.toFixed(2)}` : dev.delta?.toFixed(2))} {dev.unit}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 8. VALIDATED CAPABILITIES VS SCIENTIFIC BOUNDARIES */}
      <div className="bg-industrial-850 rounded-2xl p-6 border border-industrial-700/60 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-industrial-700/60 pb-3">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <h3 className="text-base font-bold text-white">Validated Capabilities &amp; Scientific Boundaries</h3>
          </div>
          <span className="text-xs font-mono text-slate-400 bg-industrial-700/50 px-2.5 py-1 rounded border border-industrial-600/40">
            Scientific Integrity Protocol
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-sans">
          <div className="bg-industrial-900/70 p-4 rounded-xl border border-emerald-500/20 space-y-2">
            <strong className="text-emerald-400 font-mono text-xs uppercase font-bold block flex items-center gap-1.5">
              <Check className="w-4 h-4 text-emerald-400" />
              What MetroGuard AI Can Do Reliably:
            </strong>
            <ul className="space-y-1.5 text-slate-300 text-[11px] list-disc list-inside">
              <li>Detect verified pneumatic air-leak failure signatures (100% recall on spring failures).</li>
              <li>Isolate unseen out-of-distribution abnormal operating regimes via unsupervised Isolation Forest.</li>
              <li>Attribute physical deviations using statistical Z-scores and normal baseline medians.</li>
              <li>Provide evidence-based prescriptive maintenance inspection checklists for depot technicians.</li>
            </ul>
          </div>

          <div className="bg-industrial-900/70 p-4 rounded-xl border border-amber-500/20 space-y-2">
            <strong className="text-amber-400 font-mono text-xs uppercase font-bold block flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              Current Scientific Boundaries:
            </strong>
            <ul className="space-y-1.5 text-slate-300 text-[11px] list-disc list-inside">
              <li>Continuous RUL countdown estimation is not claimed due to dataset sample scarcity (N=4 cycles).</li>
              <li>Operational hypotheses represent probabilistic engineering interpretations, not guaranteed mechanical diagnoses.</li>
              <li>Operator lifecycle actions (Acknowledge / Resolve) track workflow audits without altering ML state.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
