import axios from 'axios';

const API_BASE_URL = '/api';

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
});

export const getHealth = async () => {
  const res = await client.get('/health');
  return res.data;
};

export const getLatestReading = async () => {
  const res = await client.get('/latest');
  return res.data;
};

export const getSensors = async () => {
  const res = await client.get('/sensors');
  return res.data;
};

export const getTimeseries = async (sensor = 'TP2', start = null, end = null, limit = 300) => {
  const params = { sensor, limit };
  if (start) params.start = start;
  if (end) params.end = end;
  const res = await client.get('/timeseries', { params });
  return res.data;
};

export const getMultisensorSeries = async (sensors = 'TP2,TP3,Reservoirs,Oil_temperature,Motor_current,DV_pressure', start = null, end = null, limit = 250) => {
  const params = { sensors, limit };
  if (start) params.start = start;
  if (end) params.end = end;
  const res = await client.get('/multisensor', { params });
  return res.data;
};

export const getSimulationStep = async (index = 0) => {
  const res = await client.get('/simulation/step', { params: { index } });
  return res.data;
};

export const predictRisk = async (payload = {}) => {
  const res = await client.post('/predict', payload);
  return res.data;
};

export const predictHybridRisk = async (payload = {}) => {
  const res = await client.post('/hybrid-predict', payload);
  return res.data;
};

export const getFeatureImportance = async () => {
  const res = await client.get('/feature-importance');
  return res.data;
};

export const getModelInfo = async () => {
  const res = await client.get('/model-info');
  return res.data;
};

export const getModelEvaluation = async () => {
  const res = await client.get('/model/evaluation');
  return res.data;
};

export const getDocumentedEvents = async () => {
  const res = await client.get('/events');
  return res.data;
};

// Real-Time Sensor Streaming & Replay API
export const getStreamStatus = async () => {
  const res = await client.get('/stream/status');
  return res.data;
};

export const getStreamCurrent = async () => {
  const res = await client.get('/stream/current');
  return res.data;
};

export const startStream = async () => {
  const res = await client.post('/stream/start');
  return res.data;
};

export const stopStream = async () => {
  const res = await client.post('/stream/stop');
  return res.data;
};

export const resetStream = async () => {
  const res = await client.post('/stream/reset');
  return res.data;
};

export const setStreamScenario = async (scenario) => {
  const res = await client.post('/stream/scenario', { scenario });
  return res.data;
};

export const setStreamSpeed = async (speed) => {
  const res = await client.post('/stream/speed', { speed });
  return res.data;
};

export const stepStream = async () => {
  const res = await client.post('/stream/step');
  return res.data;
};

export const getAnomalyExplanation = async () => {
  const res = await client.get('/anomaly/explanation');
  return res.data;
};

// Intelligent Alert & Maintenance Recommendation Workflow API
export const getAllAlerts = async () => {
  const res = await client.get('/alerts');
  return res.data;
};

export const getActiveAlerts = async () => {
  const res = await client.get('/alerts/active');
  return res.data;
};

export const acknowledgeAlert = async (alertId) => {
  const res = await client.post(`/alerts/${alertId}/acknowledge`);
  return res.data;
};

export const resolveAlert = async (alertId) => {
  const res = await client.post(`/alerts/${alertId}/resolve`);
  return res.data;
};

export const getCurrentRecommendation = async () => {
  const res = await client.get('/recommendations/current');
  return res.data;
};

// Remaining Useful Life (RUL) Feasibility Audit API
export const getRulStatus = async () => {
  const res = await client.get('/rul/status');
  return res.data;
};

// Real-World Case Studies & Operational Impact API
export const getCaseStudies = async () => {
  const res = await client.get('/case-studies');
  return res.data;
};

export const getCaseStudy = async (caseId) => {
  const res = await client.get(`/case-studies/${caseId}`);
  return res.data;
};

export const getCaseStudiesSummary = async () => {
  const res = await client.get('/case-studies/summary');
  return res.data;
};

export default client;
