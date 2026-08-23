import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Cpu, 
  Activity, 
  ShieldAlert, 
  ShieldCheck, 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle2, 
  Wrench, 
  Clock, 
  Calendar, 
  Zap, 
  Layers, 
  CheckSquare, 
  Square, 
  ArrowRight,
  Info,
  Sliders,
  Check,
  AlertCircle,
  HelpCircle,
  ExternalLink,
  Target
} from 'lucide-react';
import { getCaseStudies, getCaseStudy } from '../services/api';
import StatusBadge from '../components/StatusBadge';

export default function CaseStudyPage({ onNavigate }) {
  const [caseStudies, setCaseStudies] = useState([]);
  const [selectedCaseId, setSelectedCaseId] = useState('pre_failure_event_1');
  const [activeCase, setActiveCase] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [checkedChecklist, setCheckedChecklist] = useState({});

  useEffect(() => {
    fetchInitialData();
  }, []);

  useEffect(() => {
    if (selectedCaseId) {
      loadCase(selectedCaseId);
    }
  }, [selectedCaseId]);

  const fetchInitialData = async () => {
    setIsLoading(true);
    try {
      const data = await getCaseStudies();
      setCaseStudies(data || []);
      if (data && data.length > 0) {
        setActiveCase(data[0]);
        setSelectedCaseId(data[0].case_id);
      }
    } catch (err) {
      console.error('Error fetching case studies:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadCase = async (cid) => {
    try {
      const data = await getCaseStudy(cid);
      if (data) {
        setActiveCase(data);
        setCheckedChecklist({});
      }
    } catch (err) {
      console.error(`Error loading case ${cid}:`, err);
    }
  };

  const toggleCheck = (idx) => {
    setCheckedChecklist(prev => ({
      ...prev,
      [idx]: !prev[idx]
    }));
  };

  if (isLoading || !activeCase) {
    return (
      <div className="flex items-center justify-center p-16 font-mono text-xs text-slate-400">
        <Activity className="w-5 h-5 animate-spin mr-2 text-blue-400" />
        Loading Case Study Investigation Reports...
      </div>
    );
  }

  const timeline = activeCase.timeline || [];
  const detections = activeCase.detection_mechanisms || {};
  const recommendation = activeCase.prescriptive_recommendation || {};
  const impactAnalysis = activeCase.impact_analysis || {};
  const topDeviations = detections.top_deviating_sensors || [];

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* 1. HERO HEADER BANNER */}
      <div className="bg-gradient-to-r from-industrial-850 via-industrial-800 to-industrial-850 p-6 rounded-2xl border border-industrial-700/60 shadow-xl space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className="px-2.5 py-1 rounded bg-blue-500/20 border border-blue-500/30 text-blue-400 text-xs font-mono font-bold flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5" />
                EXECUTIVE INVESTIGATION REPORT
              </span>
              <span className="text-xs font-mono text-slate-400">Asset: APU-TR-03 (Urban Rail Air Compressor)</span>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-industrial-700/70 text-slate-300 border border-industrial-600/40">
                MetroPT-3 Real Telemetry
              </span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Real-World Case Studies & Operational Impact Analysis
            </h2>
            <p className="text-xs sm:text-sm text-slate-300 max-w-3xl leading-relaxed">
              How MetroGuard AI converts raw multi-channel compressor telemetry into early warning lead times, explainable physical evidence, and targeted prescriptive maintenance workflows.
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <button
              onClick={() => onNavigate('monitoring')}
              className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-medium px-4 py-2.5 rounded-xl text-xs font-mono transition-all shadow-lg shadow-blue-600/20"
            >
              <Activity className="w-4 h-4" />
              <span>Launch Live Replay</span>
            </button>
          </div>
        </div>

        {/* 2. CASE STUDY SELECTOR TABS */}
        <div className="pt-2 border-t border-industrial-700/50">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {caseStudies.map((cs) => {
              const isSelected = selectedCaseId === cs.case_id;
              return (
                <button
                  key={cs.case_id}
                  onClick={() => setSelectedCaseId(cs.case_id)}
                  className={`p-4 rounded-xl text-left border transition-all space-y-1.5 ${
                    isSelected
                      ? 'bg-blue-600/20 border-blue-500 text-white shadow-lg shadow-blue-500/10'
                      : 'bg-industrial-900/60 border-industrial-700/60 text-slate-300 hover:bg-industrial-800'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className={`text-xs font-mono font-bold uppercase ${isSelected ? 'text-blue-300' : 'text-slate-400'}`}>
                      {cs.title.split(':')[0]}
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-industrial-800 border border-industrial-700 text-slate-300">
                      {cs.asset.operating_regime.split('(')[0]}
                    </span>
                  </div>
                  <strong className="text-sm font-bold text-white block">
                    {cs.title.split(':')[1] || cs.title}
                  </strong>
                  <p className="text-xs text-slate-400 font-sans line-clamp-1">
                    {cs.subtitle}
                  </p>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* 3. OPERATIONAL PROBLEM DEFINITION CARD */}
      <div className="bg-industrial-850 p-6 rounded-2xl border border-industrial-700/60 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-industrial-700/60 pb-3">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            <h3 className="text-base font-bold text-white">
              Operational Problem & Potential Risk Context
            </h3>
          </div>
          <span className="text-xs font-mono text-slate-400 bg-industrial-700/50 px-2.5 py-1 rounded border border-industrial-600/40">
            {activeCase.asset.unit_id}
          </span>
        </div>

        <div className="space-y-2 text-xs font-sans">
          <strong className="text-sm font-bold text-white block font-mono">
            {activeCase.operational_problem.title}
          </strong>
          <p className="text-slate-300 leading-relaxed">
            {activeCase.operational_problem.context}
          </p>
          <div className="bg-industrial-900/80 p-3.5 rounded-xl border border-amber-500/30 text-amber-200 flex items-start gap-2.5 mt-2">
            <Info className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <span className="leading-relaxed">
              <strong>Illustrative Operational Consequence:</strong> {activeCase.operational_problem.illustrative_risk}
            </span>
          </div>
        </div>
      </div>

      {/* 4. INCIDENT STORY TIMELINE */}
      <div className="bg-industrial-850 p-6 rounded-2xl border border-industrial-700/60 shadow-xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-industrial-700/60 pb-3">
          <div className="flex items-center gap-2">
            <Clock className="w-5 h-5 text-blue-400" />
            <h3 className="text-base font-bold text-white">
              Chronological Incident Timeline & Detection Progression
            </h3>
          </div>
          <span className="text-xs font-mono text-slate-400">
            {timeline.length} Documented Milestone Stages
          </span>
        </div>

        <div className="space-y-4">
          {timeline.map((stg, sIdx) => (
            <div 
              key={sIdx}
              className="bg-industrial-900/80 p-4 rounded-xl border border-industrial-700/60 space-y-2.5 transition-all hover:border-industrial-600"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-industrial-800/80 pb-2">
                <div className="flex items-center gap-2.5">
                  <span className="w-6 h-6 rounded-full bg-blue-500/20 text-blue-400 font-mono font-bold flex items-center justify-center text-xs">
                    {sIdx + 1}
                  </span>
                  <strong className="text-white font-bold font-mono text-xs">{stg.stage}</strong>
                </div>
                <div className="flex items-center gap-3 font-mono text-xs">
                  <span className="text-slate-400 text-[11px]">{stg.timing}</span>
                  <span className="px-2 py-0.5 rounded bg-industrial-800 text-blue-300 font-bold border border-industrial-700 text-[10px]">
                    {stg.system_state}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-sans">
                <div className="space-y-1">
                  <span className="text-[10px] font-mono text-slate-400 uppercase font-semibold block">AI Observation:</span>
                  <p className="text-slate-200 bg-industrial-950/60 p-2.5 rounded-lg border border-industrial-800 leading-snug">
                    {stg.ai_observation}
                  </p>
                </div>

                <div className="space-y-1">
                  <span className="text-[10px] font-mono text-amber-300 uppercase font-semibold block">Physical Telemetry Evidence:</span>
                  <p className="text-slate-200 bg-industrial-950/60 p-2.5 rounded-lg border border-industrial-800 leading-snug font-mono text-[11px]">
                    {stg.physical_evidence}
                  </p>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pt-1 text-xs font-sans text-slate-300">
                <div>
                  <strong className="text-blue-300 font-mono text-[11px]">Interpretation: </strong>
                  <span>{stg.interpretation}</span>
                </div>
                <div className="text-[11px] font-mono text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded border border-emerald-500/20 shrink-0">
                  Action: {stg.operator_action}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 5. WHY METROGUARD DETECTED IT (DUAL-TIER VALUE BREAKDOWN) */}
      <div className="bg-industrial-850 p-6 rounded-2xl border border-industrial-700/60 shadow-xl space-y-5">
        <div className="flex items-center justify-between border-b border-industrial-700/60 pb-3">
          <div className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-amber-400" />
            <h3 className="text-base font-bold text-white">
              Why MetroGuard Detected It — Dual-Tier System Evidence
            </h3>
          </div>
          <span className="text-xs font-mono text-blue-400 bg-blue-500/10 px-2.5 py-1 rounded border border-blue-500/20 font-bold">
            {detections.primary_engine}
          </span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 font-mono text-xs">
          {/* Card 1: Supervised ML */}
          <div className="bg-industrial-900/90 p-4 rounded-xl border border-industrial-700/60 space-y-2">
            <span className="text-[11px] text-blue-300 font-bold uppercase block">1. Supervised Known Risk (XGB)</span>
            <span className="text-2xl font-bold text-white block">
              {detections.peak_risk_percentage !== undefined ? `${detections.peak_risk_percentage}%` : `${((detections.supervised_xgboost_risk || 0) * 100).toFixed(2)}%`}
            </span>
            <p className="text-[11px] text-slate-400 font-sans leading-relaxed">
              {detections.supervised_limitation_explanation || "Supervised model recognizes verified pneumatic air-leak failure pattern."}
            </p>
          </div>

          {/* Card 2: Anomaly Intelligence */}
          <div className="bg-industrial-900/90 p-4 rounded-xl border border-industrial-700/60 space-y-2">
            <span className="text-[11px] text-cyan-300 font-bold uppercase block">2. Anomaly Severity (IF)</span>
            <span className="text-2xl font-bold text-cyan-300 block">
              {detections.calibrated_severity !== undefined ? `${detections.calibrated_severity} / 100` : `${detections.anomaly_severity} / 100`}
            </span>
            <p className="text-[11px] text-slate-400 font-sans leading-relaxed">
              Isolation Forest measures multi-channel divergence without relying on supervised failure labels.
            </p>
          </div>

          {/* Card 3: Hybrid Alert */}
          <div className="bg-industrial-900/90 p-4 rounded-xl border border-industrial-700/60 space-y-2">
            <span className="text-[11px] text-amber-300 font-bold uppercase block">3. Hybrid Incident Status</span>
            <div className="flex items-center gap-2 pt-1">
              <StatusBadge status={detections.alert_level || 'WARNING'} size="md" />
              <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                {detections.alert_priority}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-sans leading-relaxed pt-1">
              Deterministic synthesis triggers prioritized smart incident for depot maintenance dispatch.
            </p>
          </div>
        </div>

        {/* Top Contributing Sensor Evidence */}
        <div className="space-y-2 pt-2">
          <span className="text-xs font-mono text-slate-300 uppercase font-semibold block">
            Observed Physical Sensor Deviations at Peak Detection:
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono text-xs">
            {topDeviations.map((dev, dIdx) => (
              <div key={dIdx} className="bg-industrial-900/80 p-3 rounded-xl border border-industrial-700/50 space-y-1">
                <div className="flex items-center justify-between">
                  <strong className="text-white font-bold truncate">{dev.name}</strong>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-bold">
                    {dev.z_score}
                  </span>
                </div>
                <div className="flex justify-between text-[11px] text-slate-400">
                  <span>Reading: <strong className="text-slate-200">{dev.reading}</strong></span>
                  <span>Base: {dev.baseline}</span>
                </div>
                <span className="text-[10px] text-amber-400 block">Delta: {dev.delta}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 6. OPERATOR RESPONSE & PRESCRIPTIVE 4-POINT CHECKLIST */}
      <div className="bg-industrial-850 p-6 rounded-2xl border border-industrial-700/60 shadow-xl space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-industrial-700/60 pb-3">
          <div className="flex items-center gap-2">
            <Wrench className="w-5 h-5 text-blue-400" />
            <h3 className="text-base font-bold text-white">
              Prescriptive Maintenance Response & Inspection Checklist
            </h3>
          </div>
          <div className="flex items-center gap-2 font-mono text-xs">
            <span className="px-2.5 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30 font-bold">
              {recommendation.priority}
            </span>
            <span className="px-2.5 py-0.5 rounded bg-industrial-800 text-slate-300 border border-industrial-700 font-bold">
              {recommendation.evidence_strength}
            </span>
          </div>
        </div>

        <div className="space-y-3 text-xs">
          <div>
            <strong className="text-white text-sm font-bold block mb-1">
              {recommendation.action}
            </strong>
            <p className="text-slate-300 font-sans text-xs">
              <strong>Prescriptive Rationale:</strong> {recommendation.reason}
            </p>
          </div>

          {/* Interactive Checklist */}
          <div className="space-y-2 pt-1">
            <span className="text-[11px] font-mono text-slate-400 uppercase font-semibold block">
              Required Depot Inspection Checklist:
            </span>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
              {(recommendation.inspection_checklist || []).map((item, cIdx) => (
                <button
                  key={cIdx}
                  onClick={() => toggleCheck(cIdx)}
                  className={`p-3 rounded-xl border text-left flex items-start gap-2.5 transition-all ${
                    checkedChecklist[cIdx]
                      ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-200'
                      : 'bg-industrial-900/60 border-industrial-700/60 text-slate-300 hover:bg-industrial-800'
                  }`}
                >
                  {checkedChecklist[cIdx] ? (
                    <CheckSquare className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  ) : (
                    <Square className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
                  )}
                  <span className={`text-xs font-sans ${checkedChecklist[cIdx] ? 'line-through text-slate-400' : ''}`}>
                    {item}
                  </span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 7. ILLUSTRATIVE POTENTIAL OPERATIONAL IMPACT */}
      <div className="bg-industrial-850 p-6 rounded-2xl border border-industrial-700/60 shadow-xl space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-industrial-700/60 pb-3">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-emerald-400" />
            <h3 className="text-base font-bold text-white">
              Illustrative Potential Operational Impact
            </h3>
          </div>
          <span className="text-[10px] font-mono px-2.5 py-1 rounded bg-amber-500/10 text-amber-300 border border-amber-500/30 font-bold">
            QUALITATIVE / EVIDENCE-ALIGNED
          </span>
        </div>

        {/* Prominent Scientific Disclaimer */}
        <div className="bg-industrial-900/90 p-3.5 rounded-xl border border-amber-500/30 text-amber-200 text-xs font-mono flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <span className="leading-relaxed">
            <strong>DISCLAIMER:</strong> {impactAnalysis.disclaimer || "ILLUSTRATIVE POTENTIAL IMPACT — NOT MEASURED FINANCIAL OR OPERATIONAL OUTCOMES. MetroGuard demonstrates model-driven early warning on historical telemetry but does not claim guaranteed mechanical outcomes or unverified dollar savings."}
          </span>
        </div>

        {/* 5 Impact Dimension Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 font-mono text-xs">
          {(impactAnalysis.dimensions || []).map((dim, dIdx) => (
            <div 
              key={dIdx} 
              className="bg-industrial-900/80 p-4 rounded-xl border border-industrial-700/60 space-y-2 flex flex-col justify-between"
            >
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <strong className="text-white font-bold text-xs">{dim.category}</strong>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    dim.level === 'HIGH' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                  }`}>
                    {dim.level}
                  </span>
                </div>
                <p className="text-[11px] text-slate-300 font-sans leading-relaxed">
                  {dim.evidence_rationale}
                </p>
              </div>
              <div className="pt-2 border-t border-industrial-800 text-[10px] text-slate-400">
                Evaluation: Based on verified telemetry evidence
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 8. SCIENTIFIC INTEGRITY: WHAT METROGUARD CAN AND CANNOT CLAIM */}
      <div className="bg-industrial-850 rounded-2xl p-6 border border-industrial-700/60 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-industrial-700/60 pb-3">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <h3 className="text-base font-bold text-white">
              Scientific Boundaries: Verified Claims vs Non-Claimed Outputs
            </h3>
          </div>
          <span className="text-xs font-mono text-slate-400 bg-industrial-700/50 px-2.5 py-1 rounded border border-industrial-600/40">
            Integrity Protocol
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-sans">
          <div className="bg-industrial-900/70 p-4 rounded-xl border border-emerald-500/20 space-y-2">
            <strong className="text-emerald-400 font-mono text-xs uppercase font-bold block flex items-center gap-1.5">
              <Check className="w-4 h-4 text-emerald-400" />
              What MetroGuard AI Can Claim Scientifically:
            </strong>
            <ul className="space-y-1.5 text-slate-300 text-[11px] list-disc list-inside">
              <li>Detected documented abnormal pneumatic & thermal patterns across historical MetroPT-3 episodes.</li>
              <li>Produced calibrated multi-tier risk and anomaly indices without future data leakage.</li>
              <li>Generated actionable, evidence-based prescriptive inspection checklists for maintenance crews.</li>
              <li>Demonstrated unsupervised anomaly isolation on an untouched 62-day summer test holdout.</li>
            </ul>
          </div>

          <div className="bg-industrial-900/70 p-4 rounded-xl border border-amber-500/20 space-y-2">
            <strong className="text-amber-400 font-mono text-xs uppercase font-bold block flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              What MetroGuard AI Does NOT Claim:
            </strong>
            <ul className="space-y-1.5 text-slate-300 text-[11px] list-disc list-inside">
              <li>Guaranteed failure prevention or unmeasured downtime reduction in commercial transit.</li>
              <li>Fabricated dollar figures, commercial ROI, or passenger safety metrics.</li>
              <li>Validated continuous RUL countdown timers (honestly declared Outcome B due to N=4 sample limits).</li>
              <li>Guaranteed mechanical root-cause diagnosis without physical technician inspection.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
