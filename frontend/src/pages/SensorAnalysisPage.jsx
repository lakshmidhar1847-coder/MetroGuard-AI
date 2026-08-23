import React, { useState, useEffect } from 'react';
import { 
  LineChart as LineChartIcon, 
  Activity, 
  Layers, 
  CheckCircle2, 
  AlertTriangle, 
  TrendingUp,
  Cpu,
  Radio,
  Sliders,
  Filter,
  Flame,
  Gauge,
  Zap,
  ShieldCheck,
  Search
} from 'lucide-react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer, 
  CartesianGrid, 
  Legend 
} from 'recharts';
import { getSensors, getTimeseries } from '../services/api';
import SensorCard from '../components/SensorCard';

export default function SensorAnalysisPage({ latestData }) {
  const [sensorsList, setSensorsList] = useState([]);
  const [selectedSensorId, setSelectedSensorId] = useState('TP2');
  const [activeCategory, setActiveCategory] = useState('ALL'); // 'ALL' | 'PNEUMATIC' | 'THERMAL' | 'ELECTRICAL' | 'CONTROL'
  const [chartData, setChartData] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    fetchSensors();
  }, []);

  useEffect(() => {
    fetchSensorChart(selectedSensorId);
  }, [selectedSensorId]);

  const fetchSensors = async () => {
    try {
      const res = await getSensors();
      setSensorsList(res || []);
    } catch (err) {
      console.error('Error fetching sensors:', err);
    }
  };

  const fetchSensorChart = async (sid) => {
    setIsLoading(true);
    try {
      const res = await getTimeseries(sid, null, null, 250);
      setChartData(res.data || []);
    } catch (err) {
      console.error('Error fetching sensor timeseries:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const analogueSensors = sensorsList.filter(s => s.unit !== 'state');
  const digitalSensors = sensorsList.filter(s => s.unit === 'state');

  const filteredSensors = sensorsList.filter(s => {
    if (activeCategory === 'ALL') return true;
    if (activeCategory === 'PNEUMATIC') return s.category === 'Pneumatic';
    if (activeCategory === 'THERMAL') return s.category === 'Thermal';
    if (activeCategory === 'ELECTRICAL') return s.category === 'Electrical';
    if (activeCategory === 'CONTROL') return s.unit === 'state' || s.category === 'Control' || s.category === 'Safety';
    return true;
  });

  const activeSensorMeta = sensorsList.find(s => s.id === selectedSensorId) || analogueSensors[0] || {
    id: 'TP2',
    name: 'Compressor Pressure',
    unit: 'bar',
    category: 'Pneumatic',
    description: 'Pressure measured directly at compressor output'
  };

  const liveSensorObj = latestData?.sensors?.[selectedSensorId] || {};

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* 1. Page Header Banner */}
      <div className="bg-gradient-to-r from-industrial-850 via-industrial-800 to-industrial-850 p-6 rounded-2xl border border-industrial-700/60 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded bg-purple-500/20 border border-purple-500/30 text-purple-400 text-xs font-mono font-bold flex items-center gap-1.5">
              <LineChartIcon className="w-3.5 h-3.5" />
              TELEMETRY & SENSOR SUITE
            </span>
            <span className="text-xs font-mono text-slate-400">15 Monitored MetroPT-3 Signals</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Comprehensive Sensor & Signal Analysis
          </h2>
          <p className="text-xs sm:text-sm text-slate-300 max-w-3xl leading-relaxed">
            Multi-scale rolling analytics, signal stability distributions, and digital pneumatic control states across 65 engineered time-series features.
          </p>
        </div>

        {/* Category Filter Pills */}
        <div className="flex flex-wrap items-center gap-1.5 bg-industrial-900/90 p-1.5 rounded-xl border border-industrial-700 font-mono text-xs">
          {['ALL', 'PNEUMATIC', 'THERMAL', 'ELECTRICAL', 'CONTROL'].map(cat => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-bold transition-all ${
                activeCategory === cat
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* 2. Selected Sensor Analytics & Multi-Scale Waveform */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sensor Selector Menu */}
        <div className="bg-industrial-850 p-5 rounded-2xl border border-industrial-700/60 space-y-3 shadow-xl flex flex-col justify-between">
          <div className="space-y-3">
            <div className="flex items-center justify-between border-b border-industrial-700/60 pb-2">
              <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400">
                Signals ({filteredSensors.length})
              </h3>
              <span className="text-[10px] text-blue-400 font-mono">10s Rate</span>
            </div>

            <div className="space-y-1.5 max-h-96 overflow-y-auto pr-1">
              {filteredSensors.map((s) => {
                const isSelected = selectedSensorId === s.id;
                const liveVal = latestData?.sensors?.[s.id]?.value;
                return (
                  <button
                    key={s.id}
                    onClick={() => setSelectedSensorId(s.id)}
                    className={`w-full flex items-center justify-between p-2.5 rounded-xl text-left font-mono transition-all ${
                      isSelected
                        ? 'bg-blue-600/20 border border-blue-500/50 text-blue-300 shadow-md'
                        : 'bg-industrial-900/60 hover:bg-industrial-700/50 text-slate-300 border border-transparent'
                    }`}
                  >
                    <div>
                      <span className="text-xs font-bold block truncate">{s.name}</span>
                      <span className="text-[10px] text-slate-400">{s.id} • {s.category}</span>
                    </div>
                    <span className="text-xs font-bold text-slate-200 shrink-0">
                      {liveVal !== undefined ? `${liveVal} ${s.unit}` : '—'}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="pt-3 border-t border-industrial-700/40 text-[10px] font-mono text-slate-400">
            Selected: <strong className="text-blue-300">{selectedSensorId}</strong>
          </div>
        </div>

        {/* Multi-Scale Rolling Analytics Waveform */}
        <div className="lg:col-span-3 bg-industrial-850 p-6 rounded-2xl border border-industrial-700/60 shadow-xl space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-industrial-700/60 pb-4">
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-white">{activeSensorMeta.name}</h3>
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30 font-bold">
                  {activeSensorMeta.id}
                </span>
                <span className="text-xs font-mono text-slate-400">({activeSensorMeta.category})</span>
              </div>
              <p className="text-xs text-slate-300 mt-1 font-sans">
                {activeSensorMeta.description}
              </p>
            </div>

            <div className="flex items-center gap-3 text-xs font-mono">
              <div className="bg-industrial-900 px-3.5 py-1.5 rounded-xl border border-industrial-700">
                <span className="text-slate-400 text-[10px] block">Current Value</span>
                <strong className="text-white text-sm">{liveSensorObj.value !== undefined ? `${liveSensorObj.value} ${activeSensorMeta.unit}` : '—'}</strong>
              </div>
              <div className="bg-industrial-900 px-3.5 py-1.5 rounded-xl border border-industrial-700">
                <span className="text-slate-400 text-[10px] block">5m Shift Delta</span>
                <strong className="text-blue-400 text-sm">{liveSensorObj.diff_5m !== undefined ? `${liveSensorObj.diff_5m} ${activeSensorMeta.unit}` : '—'}</strong>
              </div>
            </div>
          </div>

          {/* Recharts Multi-Scale Chart */}
          <div className="h-72 w-full font-mono text-xs">
            {isLoading ? (
              <div className="h-full flex items-center justify-center text-slate-400 font-mono text-xs">
                <Activity className="w-5 h-5 animate-spin mr-2 text-blue-400" />
                Loading multi-scale time-series...
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.4} />
                  <XAxis 
                    dataKey="timestamp" 
                    stroke="#64748b" 
                    tick={{ fill: '#64748b', fontSize: 10, fontFamily: 'monospace' }}
                  />
                  <YAxis 
                    stroke="#64748b" 
                    tick={{ fill: '#64748b', fontSize: 10, fontFamily: 'monospace' }}
                    domain={['auto', 'auto']}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderColor: '#334155',
                      borderRadius: '0.75rem',
                      fontSize: '0.75rem',
                      fontFamily: 'monospace',
                      color: '#f1f5f9'
                    }}
                  />
                  <Legend verticalAlign="top" height={30} wrapperStyle={{ fontSize: '11px', fontFamily: 'monospace' }} />
                  <Line 
                    type="monotone" 
                    dataKey="value" 
                    name={`Raw Reading (${activeSensorMeta.id})`} 
                    stroke="#3b82f6" 
                    strokeWidth={2} 
                    dot={false} 
                    isAnimationActive={false}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="roll_mean_1m" 
                    name="1-Minute Rolling Mean" 
                    stroke="#06b6d4" 
                    strokeWidth={1.5} 
                    dot={false} 
                    isAnimationActive={false}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="roll_mean_5m" 
                    name="5-Minute Rolling Baseline" 
                    stroke="#10b981" 
                    strokeWidth={1.5} 
                    strokeDasharray="4 4" 
                    dot={false} 
                    isAnimationActive={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>

      {/* 3. Digital Control Signals & Interlocks Status Matrix */}
      <div className="bg-industrial-850 p-6 rounded-2xl border border-industrial-700/60 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-industrial-700/60 pb-3">
          <div className="flex items-center gap-2">
            <Cpu className="w-5 h-5 text-cyan-400" />
            <h3 className="text-base font-bold text-white">Digital Control Signals & Safety Interlocks</h3>
          </div>
          <span className="text-xs font-mono text-slate-400 bg-industrial-700/50 px-2.5 py-1 rounded border border-industrial-600/40">
            8 Binary Channels
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs font-mono">
          {digitalSensors.map((ds) => {
            const rawVal = latestData?.sensors?.[ds.id]?.value;
            const isActive = rawVal === 1 || rawVal === 1.0;
            return (
              <div 
                key={ds.id}
                className={`p-4 rounded-xl border transition-all ${
                  isActive
                    ? 'bg-blue-600/10 border-blue-500/40 text-blue-300'
                    : 'bg-industrial-900/60 border-industrial-700/40 text-slate-400'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <strong className="text-white font-bold">{ds.name}</strong>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    isActive ? 'bg-blue-500 text-white' : 'bg-industrial-800 text-slate-400'
                  }`}>
                    {isActive ? 'HIGH (1)' : 'LOW (0)'}
                  </span>
                </div>
                <span className="text-[10px] text-slate-400 block mb-1">Channel ID: {ds.id}</span>
                <p className="text-[11px] text-slate-300 leading-snug font-sans">
                  {ds.description}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
