import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import OverviewPage from './pages/OverviewPage';
import LiveMonitoringPage from './pages/LiveMonitoringPage';
import RiskAssessmentPage from './pages/RiskAssessmentPage';
import SensorAnalysisPage from './pages/SensorAnalysisPage';
import ModelPerformancePage from './pages/ModelPerformancePage';
import CaseStudyPage from './pages/CaseStudyPage';
import { getLatestReading, getHealth } from './services/api';

export default function App() {
  const getTabFromPath = () => {
    const p = window.location.pathname.replace(/^\//, '').toLowerCase();
    if (p === 'overview' || p === '') return 'overview';
    if (p === 'risk' || p === 'risk-assessment') return 'risk';
    if (p === 'monitoring' || p === 'live') return 'monitoring';
    if (p === 'sensors' || p === 'sensor-analysis') return 'sensor-analysis';
    if (p === 'performance' || p === 'model-performance') return 'model-performance';
    if (p === 'case-study' || p === 'case-studies' || p === 'casestudy') return 'case-study';
    return 'overview';
  };

  const [activeTab, setActiveTab] = useState(getTabFromPath);
  const [latestData, setLatestData] = useState(null);
  const [systemHealth, setSystemHealth] = useState('ONLINE');
  const [isLivePolling, setIsLivePolling] = useState(true);

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    const route = tab === 'overview' ? '/overview' : `/${tab}`;
    if (window.location.pathname !== route && (tab !== 'overview' || window.location.pathname !== '/')) {
      window.history.pushState(null, '', route);
    }
  };

  useEffect(() => {
    const onPopState = () => {
      setActiveTab(getTabFromPath());
    };
    window.addEventListener('popstate', onPopState);
    return () => window.removeEventListener('popstate', onPopState);
  }, []);

  useEffect(() => {
    // Initial fetch
    fetchLatest();

    // 5-second telemetry polling
    const interval = setInterval(() => {
      if (isLivePolling) {
        fetchLatest();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [isLivePolling]);

  const fetchLatest = async () => {
    try {
      const data = await getLatestReading();
      if (data && data.timestamp) {
        setLatestData(data);
        setSystemHealth('ONLINE');
      }
    } catch (err) {
      console.warn('Backend polling warning:', err.message);
    }
  };

  return (
    <div className="min-h-screen bg-[#0b0f17] text-slate-100 flex flex-col antialiased">
      {/* Global Control Center Header */}
      <Header 
        systemHealth={systemHealth} 
        lastTimestamp={latestData?.timestamp}
        isSimulating={false}
      />

      {/* Main Layout Body */}
      <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
        {/* Sidebar Navigation */}
        <Sidebar activeTab={activeTab} setActiveTab={handleTabChange} />

        {/* Dynamic Page Container */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full">
          {activeTab === 'overview' && (
            <OverviewPage 
              latestData={latestData} 
              onNavigate={handleTabChange}
            />
          )}

          {activeTab === 'monitoring' && (
            <LiveMonitoringPage 
              latestData={latestData} 
            />
          )}

          {activeTab === 'risk' && (
            <RiskAssessmentPage 
              latestData={latestData} 
            />
          )}

          {activeTab === 'sensor-analysis' && (
            <SensorAnalysisPage 
              latestData={latestData} 
            />
          )}

          {activeTab === 'model-performance' && (
            <ModelPerformancePage />
          )}

          {activeTab === 'case-study' && (
            <CaseStudyPage onNavigate={handleTabChange} />
          )}
        </main>
      </div>
    </div>
  );
}
