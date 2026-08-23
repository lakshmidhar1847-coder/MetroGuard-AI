"""
MetroGuard AI - Real-Time Sensor Streaming & Replay Engine
Replays authentic continuous MetroPT-3 telemetry through the live feature pipeline,
XGBoost, Isolation Forest, Physical Evidence Engine, Persistence Tracking,
and Smart Alerts decision layer.
"""

import os
import time
import pickle
import threading
import collections
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

from backend.hybrid_predictor import get_hybrid_predictor
from backend.data_service import FEATURE_NAMES

class SensorStreamingEngine:
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.features_csv = os.path.join(base_dir, "data", "processed", "metropt3_features.csv")
        self.cache_pkl = os.path.join(base_dir, "data", "processed", "streaming_scenarios_cache.pkl")
        
        self.scenarios_meta = {
            "normal": {
                "id": "normal",
                "label": "1. Normal Operation Baseline",
                "desc": "Stable cyclical compressor pumping and nominal thermal equilibrium.",
                "start": "2020-03-01 12:00:00",
                "end": "2020-03-01 12:45:00",
                "expected_alert": "NORMAL"
            },
            "gradual_anomaly": {
                "id": "gradual_anomaly",
                "label": "2. Gradual Thermal & Pressure Drift",
                "desc": "Real summer operational sequence showing gradual thermal buildup into abnormal dynamics.",
                "start": "2020-07-15 13:00:00",
                "end": "2020-07-15 14:30:00",
                "expected_alert": "NORMAL → MONITOR → WARNING"
            },
            "pre_failure": {
                "id": "pre_failure",
                "label": "3. Known Pre-Failure Sequence (Event #1)",
                "desc": "Real chronological pre-failure sequence where supervised XGBoost escalates to 98.78% High Risk.",
                "start": "2020-04-17 22:30:00",
                "end": "2020-04-18 00:00:00",
                "expected_alert": "NORMAL → MONITOR → WARNING → HIGH RISK"
            },
            "unseen_anomaly": {
                "id": "unseen_anomaly",
                "label": "4. Unseen Summer Anomaly (Event #4 Comparison)",
                "desc": "Demonstrates Dual-Tier synergy: XGBoost at 0.03% while Isolation Forest & Physical Evidence flag WARNING.",
                "start": "2020-07-15 13:55:00",
                "end": "2020-07-15 14:35:00",
                "expected_alert": "MONITOR → WARNING"
            }
        }
        
        self.hybrid_predictor = get_hybrid_predictor()
        self.lock = threading.RLock()
        
        # Pre-calculated scenario snapshots for fast, non-blocking execution
        self.scenario_records: Dict[str, List[Dict[str, Any]]] = {}
        self.load_and_preprocess_scenarios()
        
        # Streaming timeline state
        self.current_scenario_id = "normal"
        self.is_running = True
        self.playback_speed = 1.0  # 1x, 2x, 5x, 10x
        self.start_time = time.time()
        self.accumulated_offset = 0.0
        self.manual_index: Optional[int] = None
        
        # History buffers
        self.alert_history: Dict[str, List[Dict[str, Any]]] = {k: [] for k in self.scenarios_meta}
        self.build_alert_histories()

    def load_and_preprocess_scenarios(self):
        """Loads and pre-evaluates authentic continuous slices through the live pipeline."""
        if os.path.exists(self.cache_pkl):
            try:
                with open(self.cache_pkl, 'rb') as f:
                    self.scenario_records = pickle.load(f)
                print(f"[StreamingEngine] Loaded pre-computed scenario records from cache ({len(self.scenario_records)} scenarios).")
                return
            except Exception as e:
                print(f"[StreamingEngine] Error loading scenario cache: {e}. Rebuilding...")

        if not os.path.exists(self.features_csv):
            print(f"[StreamingEngine] Warning: Features CSV not found at {self.features_csv}")
            return
            
        print(f"[StreamingEngine] Loading scenario telemetry slices from {self.features_csv}...")
        df = pd.read_csv(self.features_csv)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        for sc_id, meta in self.scenarios_meta.items():
            mask = (df['timestamp'] >= meta['start']) & (df['timestamp'] <= meta['end'])
            slice_df = df[mask].sort_values('timestamp').reset_index(drop=True)
            
            # Vectorized model scoring
            X_slice = slice_df[FEATURE_NAMES].values
            xgb_probs = self.hybrid_predictor.xgb_predictor.model.predict_proba(X_slice)[:, 1]
            anom_scores = -self.hybrid_predictor.anomaly_model.score_samples(X_slice)
            
            records = []
            trailing_anomalies = collections.deque(maxlen=30)
            
            for idx in range(len(slice_df)):
                row = slice_df.iloc[idx]
                ts_str = str(row['timestamp'])
                
                feat_dict = {f: float(row[f]) for f in FEATURE_NAMES if f in row}
                
                sensors = {
                    "TP2": {"value": round(float(row.get("TP2", 0.0)), 2), "unit": "bar", "name": "Compressor Output Pressure"},
                    "TP3": {"value": round(float(row.get("TP3", 0.0)), 2), "unit": "bar", "name": "Pneumatic Panel Pressure"},
                    "H1": {"value": round(float(row.get("H1", 0.0)), 2), "unit": "bar", "name": "Cyclonic Separator"},
                    "DV_pressure": {"value": round(float(row.get("DV_pressure", 0.0)), 2), "unit": "bar", "name": "Drying Tower Pressure"},
                    "Reservoirs": {"value": round(float(row.get("Reservoirs", 0.0)), 2), "unit": "bar", "name": "Reservoir Storage"},
                    "Motor_current": {"value": round(float(row.get("Motor_current", 0.0)), 2), "unit": "A", "name": "Motor Current"},
                    "Oil_temperature": {"value": round(float(row.get("Oil_temperature", 0.0)), 1), "unit": "°C", "name": "Oil Temperature"},
                    "COMP": {"value": round(float(row.get("COMP", 0.0)), 0), "unit": "state", "name": "Compressor State"}
                }
                
                # XGBoost classification
                prob = float(xgb_probs[idx])
                pct = round(prob * 100, 2)
                if prob >= 0.70:
                    xgb_status = "HIGH RISK"
                elif prob >= 0.10:
                    xgb_status = "WARNING"
                else:
                    xgb_status = "NORMAL"
                    
                # Anomaly classification
                anom_s = float(anom_scores[idx])
                if anom_s >= self.hybrid_predictor.anomaly_high_threshold:
                    anom_status = "HIGH"
                elif anom_s >= self.hybrid_predictor.anomaly_threshold:
                    anom_status = "ELEVATED"
                else:
                    anom_status = "NORMAL"
                    
                trailing_anomalies.append(anom_s >= self.hybrid_predictor.anomaly_threshold)
                is_sustained = sum(trailing_anomalies) >= 3
                
                # Physical evidence
                evidence = self.hybrid_predictor.extract_physical_evidence(feat_dict)
                
                # Hybrid decision
                if xgb_status == "HIGH RISK":
                    hyb_status = "HIGH RISK"
                    hyb_reason = "Supervised XGBoost indicates severe known failure risk (>70%)."
                elif xgb_status == "WARNING" and anom_status in ["ELEVATED", "HIGH"]:
                    hyb_status = "HIGH RISK"
                    hyb_reason = "Concurrent alert: Supervised failure probability elevated alongside strong multidimensional anomaly."
                elif xgb_status == "WARNING":
                    hyb_status = "FAILURE WARNING"
                    hyb_reason = "Supervised model detected recurring pre-failure pneumatic pattern."
                elif anom_status == "HIGH" or (anom_status == "ELEVATED" and is_sustained):
                    hyb_status = "ANOMALY WARNING"
                    hyb_reason = f"Unsupervised detector flags significant out-of-distribution operation (Score {anom_s:.4f} >= {self.hybrid_predictor.anomaly_threshold:.4f})."
                elif anom_status == "ELEVATED":
                    hyb_status = "MONITOR"
                    hyb_reason = "Isolated abnormal sensor reading detected. Telemetry flagged for persistence monitoring."
                else:
                    hyb_status = "NORMAL"
                    hyb_reason = "All signals conform to nominal baseline operating distributions."
                    
                # Alert
                alert = self.hybrid_predictor.determine_alert(
                    xgb_status=xgb_status,
                    xgb_prob=prob,
                    anom_score=anom_s,
                    anom_status=anom_status,
                    hybrid_status=hyb_status,
                    evidence=evidence,
                    is_sustained_anomaly=is_sustained
                )
                
                # Explainable Anomaly Intelligence Layer
                from backend.anomaly_explainer import explain_current_anomaly
                anomaly_intelligence = explain_current_anomaly(
                    feat_dict=feat_dict,
                    raw_anomaly_score=anom_s,
                    normal_baselines=self.hybrid_predictor.baseline_stats,
                    trailing_history=records[max(0, idx - 15):idx] if records else [],
                    trailing_anomalies_count=sum(trailing_anomalies),
                    window_size=30
                )
                
                chart_point = {
                    "time": ts_str.split()[1] if ' ' in ts_str else ts_str,
                    "timestamp": ts_str,
                    "TP2": sensors["TP2"]["value"],
                    "H1": sensors["H1"]["value"],
                    "Oil_temperature": sensors["Oil_temperature"]["value"],
                    "Reservoirs": sensors["Reservoirs"]["value"],
                    "Motor_current": sensors["Motor_current"]["value"],
                    "risk_percentage": pct,
                    "anomaly_score": round(anom_s, 4),
                    "anomaly_severity": anomaly_intelligence["anomaly_severity"]
                }
                
                records.append({
                    "index": idx,
                    "timestamp": ts_str,
                    "sensors": sensors,
                    "xgboost": {
                        "risk_probability": prob,
                        "risk_percentage": pct,
                        "status": xgb_status,
                        "threshold": self.hybrid_predictor.xgb_predictor.selected_threshold
                    },
                    "anomaly": {
                        "score": round(anom_s, 4),
                        "severity": anomaly_intelligence["anomaly_severity"],
                        "severity_label": anomaly_intelligence["severity_label"],
                        "threshold": round(self.hybrid_predictor.anomaly_threshold, 4),
                        "high_threshold": round(self.hybrid_predictor.anomaly_high_threshold, 4),
                        "status": anom_status
                    },
                    "anomaly_intelligence": anomaly_intelligence,
                    "hybrid": {
                        "status": hyb_status,
                        "reason": hyb_reason
                    },
                    "evidence": evidence,
                    "alert": alert,
                    "is_sustained_anomaly": is_sustained,
                    "chart_point": chart_point
                })
                
            self.scenario_records[sc_id] = records
            print(f"  • Vector-preprocessed Scenario '{sc_id}': {len(records):,} records ready for real-time streaming.")
            
        try:
            with open(self.cache_pkl, 'wb') as f:
                pickle.dump(self.scenario_records, f)
            print(f"[StreamingEngine] Successfully cached scenario records to {self.cache_pkl}.")
        except Exception as e:
            print(f"[StreamingEngine] Warning: Could not write scenario cache: {e}")

    def build_alert_histories(self):
        """Builds alert transition logs for each scenario."""
        for sc_id, records in self.scenario_records.items():
            history = []
            last_level = None
            for rec in records:
                lvl = rec["alert"]["level"]
                if last_level is not None and last_level != lvl:
                    history.insert(0, {
                        "timestamp": rec["timestamp"].split()[1] if ' ' in rec["timestamp"] else rec["timestamp"],
                        "full_timestamp": rec["timestamp"],
                        "from_level": last_level,
                        "to_level": lvl,
                        "title": rec["alert"]["title"],
                        "reason": rec["alert"]["reason"],
                        "xgb_risk": f"{rec['xgboost']['risk_percentage']}%",
                        "anomaly_score": f"{rec['anomaly']['score']:.4f}",
                        "evidence_count": len(rec["evidence"])
                    })
                last_level = lvl
            self.alert_history[sc_id] = history

    def _get_current_index(self) -> int:
        """Calculates current scenario index based on elapsed continuous playback time."""
        if self.manual_index is not None:
            return self.manual_index
            
        records = self.scenario_records.get(self.current_scenario_id, [])
        if not records:
            return 0
            
        if not self.is_running:
            return int(self.accumulated_offset) % len(records)
            
        elapsed_seconds = (time.time() - self.start_time) * self.playback_speed
        total_virtual_index = int(self.accumulated_offset + elapsed_seconds)
        return total_virtual_index % len(records)

    def get_current_state(self) -> Dict[str, Any]:
        with self.lock:
            records = self.scenario_records.get(self.current_scenario_id, [])
            if not records:
                return {}
                
            idx = self._get_current_index()
            current_rec = records[idx]
            
            # Extract rolling 60 points of chart history
            start_window = max(0, idx - 59)
            if idx < 59 and len(records) >= 60:
                # Wrap-around chart points if near beginning
                window_points = [r["chart_point"] for r in records[len(records) - (59 - idx):]] + [r["chart_point"] for r in records[:idx + 1]]
            else:
                window_points = [r["chart_point"] for r in records[start_window:idx + 1]]
                
            sc_meta = self.scenarios_meta[self.current_scenario_id]
            
            # Filter alert history up to current index
            full_history = self.alert_history.get(self.current_scenario_id, [])
            
            # Intelligent Alert Lifecycle & Prescriptive Recommendation Engine
            from backend.alert_service import get_alert_manager
            alert_mgr = get_alert_manager()
            lifecycle_res = alert_mgr.process_telemetry_alert(
                timestamp=current_rec["timestamp"],
                scenario=self.current_scenario_id,
                alert_info=current_rec["alert"],
                xgboost_info=current_rec["xgboost"],
                anomaly_info=current_rec["anomaly"],
                anomaly_intel=current_rec["anomaly_intelligence"],
                evidence=current_rec["evidence"]
            )
            
            return {
                "scenario": self.current_scenario_id,
                "scenario_label": sc_meta["label"],
                "scenario_desc": sc_meta["desc"],
                "is_running": self.is_running,
                "playback_speed": self.playback_speed,
                "current_index": idx,
                "total_records": len(records),
                "progress_percent": round((idx + 1) / len(records) * 100, 1),
                "timestamp": current_rec["timestamp"],
                "sensors": current_rec["sensors"],
                "xgboost": current_rec["xgboost"],
                "anomaly": current_rec["anomaly"],
                "hybrid": current_rec["hybrid"],
                "evidence": current_rec["evidence"],
                "alert": current_rec["alert"],
                "anomaly_intelligence": current_rec["anomaly_intelligence"],
                "active_operator_alert": lifecycle_res["active_alert"],
                "prescriptive_recommendation": lifecycle_res["current_recommendation"],
                "operator_alert_history": lifecycle_res["alert_history"][:10],
                "is_sustained_anomaly": current_rec["is_sustained_anomaly"],
                "alert_history": full_history[:10],
                "chart_history": window_points
            }

    def get_anomaly_explanation(self) -> Dict[str, Any]:
        with self.lock:
            state = self.get_current_state()
            if not state:
                return {}
            expl = state.get("anomaly_intelligence", {})
            return {
                "timestamp": state.get("timestamp"),
                "scenario": state.get("scenario"),
                "scenario_label": state.get("scenario_label"),
                **expl
            }

    def start(self):
        with self.lock:
            if not self.is_running:
                self.is_running = True
                self.start_time = time.time()
                self.manual_index = None
            return {"status": "started", "is_running": True}

    def stop(self):
        with self.lock:
            if self.is_running:
                # Save current virtual index position
                records = self.scenario_records.get(self.current_scenario_id, [])
                if records:
                    elapsed = (time.time() - self.start_time) * self.playback_speed
                    self.accumulated_offset = (self.accumulated_offset + elapsed) % len(records)
                self.is_running = False
                self.manual_index = int(self.accumulated_offset)
            return {"status": "stopped", "is_running": False}

    def reset(self):
        with self.lock:
            self.accumulated_offset = 0.0
            self.start_time = time.time()
            self.manual_index = 0
            if self.is_running:
                self.manual_index = None
            from backend.alert_service import get_alert_manager
            get_alert_manager().reset()
            return {"status": "reset", "current_index": 0}

    def set_scenario(self, scenario_id: str):
        with self.lock:
            if scenario_id not in self.scenarios_meta:
                raise ValueError(f"Unknown scenario '{scenario_id}'. Available: {list(self.scenarios_meta.keys())}")
            self.current_scenario_id = scenario_id
            self.accumulated_offset = 0.0
            self.start_time = time.time()
            self.manual_index = None
            from backend.alert_service import get_alert_manager
            get_alert_manager().reset()
            return {
                "status": "scenario_changed",
                "scenario": scenario_id,
                "label": self.scenarios_meta[scenario_id]["label"]
            }

    def set_speed(self, speed: float):
        with self.lock:
            # Rebase accumulated offset to avoid sudden jumps when changing speed
            records = self.scenario_records.get(self.current_scenario_id, [])
            if records and self.is_running:
                elapsed = (time.time() - self.start_time) * self.playback_speed
                self.accumulated_offset = (self.accumulated_offset + elapsed) % len(records)
                self.start_time = time.time()
                
            self.playback_speed = float(max(0.2, min(20.0, speed)))
            return {"status": "speed_updated", "playback_speed": self.playback_speed}

    def step_forward(self):
        with self.lock:
            records = self.scenario_records.get(self.current_scenario_id, [])
            if records:
                cur_idx = self._get_current_index()
                next_idx = (cur_idx + 1) % len(records)
                self.accumulated_offset = float(next_idx)
                self.manual_index = next_idx
                self.is_running = False
            return self.get_current_state()

    def get_status(self) -> Dict[str, Any]:
        with self.lock:
            records = self.scenario_records.get(self.current_scenario_id, [])
            total = len(records)
            idx = self._get_current_index()
            return {
                "scenario": self.current_scenario_id,
                "scenario_label": self.scenarios_meta[self.current_scenario_id]["label"],
                "is_running": self.is_running,
                "current_index": idx,
                "total_records": total,
                "progress_percent": round((idx + 1) / max(1, total) * 100, 1),
                "playback_speed": self.playback_speed,
                "available_scenarios": list(self.scenarios_meta.values())
            }

# Global singleton
_stream_engine_instance = None

def get_streaming_engine() -> SensorStreamingEngine:
    global _stream_engine_instance
    if _stream_engine_instance is None:
        _stream_engine_instance = SensorStreamingEngine()
    return _stream_engine_instance

if __name__ == "__main__":
    engine = get_streaming_engine()
    print("Streaming Engine initialized. Current snapshot:")
    print(engine.get_current_state()["timestamp"])
