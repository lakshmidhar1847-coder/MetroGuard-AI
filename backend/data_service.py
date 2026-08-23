"""
MetroGuard AI - High Performance Backend Data Service
Caches and serves real MetroPT-3 sensor telemetry, time-series intervals,
simulation feeds, and complete 65-feature engineered vectors for inference.
"""

import os
import json
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "processed")
MODELS_DIR = os.path.join(BASE_DIR, "models")
CACHE_FILE = os.path.join(DATA_DIR, "dashboard_telemetry_cache.joblib")

FEATURE_NAMES = [
    "TP2", "TP2_roll_mean_1m", "TP2_roll_std_1m", "TP2_roll_mean_5m", "TP2_roll_std_5m", "TP2_diff_1m", "TP2_diff_5m",
    "TP3", "TP3_roll_mean_1m", "TP3_roll_std_1m", "TP3_roll_mean_5m", "TP3_roll_std_5m", "TP3_diff_1m", "TP3_diff_5m",
    "H1", "H1_roll_mean_1m", "H1_roll_std_1m", "H1_roll_mean_5m", "H1_roll_std_5m", "H1_diff_1m", "H1_diff_5m",
    "DV_pressure", "DV_pressure_roll_mean_1m", "DV_pressure_roll_std_1m", "DV_pressure_roll_mean_5m", "DV_pressure_roll_std_5m", "DV_pressure_diff_1m", "DV_pressure_diff_5m",
    "Reservoirs", "Reservoirs_roll_mean_1m", "Reservoirs_roll_std_1m", "Reservoirs_roll_mean_5m", "Reservoirs_roll_std_5m", "Reservoirs_diff_1m", "Reservoirs_diff_5m",
    "Oil_temperature", "Oil_temperature_roll_mean_1m", "Oil_temperature_roll_std_1m", "Oil_temperature_roll_mean_5m", "Oil_temperature_roll_std_5m", "Oil_temperature_diff_1m", "Oil_temperature_diff_5m",
    "Motor_current", "Motor_current_roll_mean_1m", "Motor_current_roll_std_1m", "Motor_current_roll_mean_5m", "Motor_current_roll_std_5m", "Motor_current_diff_1m", "Motor_current_diff_5m",
    "COMP", "COMP_changes_5m",
    "DV_eletric", "DV_eletric_changes_5m",
    "Towers", "Towers_changes_5m",
    "MPG", "MPG_changes_5m",
    "LPS", "LPS_changes_5m",
    "Pressure_switch", "Pressure_switch_changes_5m",
    "Oil_level", "Oil_level_changes_5m",
    "Caudal_impulses", "Caudal_impulses_changes_5m"
]

SENSOR_METADATA = [
    {
        "id": "TP2",
        "name": "Compressor Pressure",
        "unit": "bar",
        "category": "Pneumatic",
        "description": "Pressure measured directly at the compressor output port",
        "normal_min": -0.05,
        "normal_max": 10.5,
        "critical_threshold": 10.0
    },
    {
        "id": "TP3",
        "name": "Pneumatic Panel Pressure",
        "unit": "bar",
        "category": "Pneumatic",
        "description": "Internal pneumatic control circuit pressure",
        "normal_min": 7.5,
        "normal_max": 10.2,
        "critical_threshold": 8.0
    },
    {
        "id": "H1",
        "name": "Cyclonic Separator Pressure",
        "unit": "bar",
        "category": "Filtration",
        "description": "Pressure drop across the cyclonic moisture/oil separator filter",
        "normal_min": -0.05,
        "normal_max": 10.5,
        "critical_threshold": 9.5
    },
    {
        "id": "DV_pressure",
        "name": "Drying Tower Pressure",
        "unit": "bar",
        "category": "Pneumatic",
        "description": "Pressure inside the twin-tower desiccant air drying unit",
        "normal_min": -0.05,
        "normal_max": 3.0,
        "critical_threshold": 2.5
    },
    {
        "id": "Reservoirs",
        "name": "Air Reservoir Pressure",
        "unit": "bar",
        "category": "Storage",
        "description": "Main train pneumatic braking and suspension reservoir pressure",
        "normal_min": 7.8,
        "normal_max": 10.2,
        "critical_threshold": 8.0
    },
    {
        "id": "Oil_temperature",
        "name": "Oil Temperature",
        "unit": "°C",
        "category": "Thermal",
        "description": "Compressor mechanical lubricating oil temperature",
        "normal_min": 40.0,
        "normal_max": 85.0,
        "critical_threshold": 90.0
    },
    {
        "id": "Motor_current",
        "name": "Motor Current",
        "unit": "A",
        "category": "Electrical",
        "description": "Electrical current draw of the three-phase AC induction motor",
        "normal_min": 0.0,
        "normal_max": 9.5,
        "critical_threshold": 8.5
    },
    {
        "id": "COMP",
        "name": "Compressor Command",
        "unit": "state",
        "category": "Control",
        "description": "Digital control command to activate the compressor motor",
        "normal_min": 0,
        "normal_max": 1
    },
    {
        "id": "DV_eletric",
        "name": "Drain Valve Electric Command",
        "unit": "state",
        "category": "Control",
        "description": "Solenoid valve activation to drain moisture from drying towers",
        "normal_min": 0,
        "normal_max": 1
    },
    {
        "id": "Towers",
        "name": "Drying Towers Active",
        "unit": "state",
        "category": "Control",
        "description": "Active column of the air desiccant twin-tower system",
        "normal_min": 0,
        "normal_max": 1
    },
    {
        "id": "MPG",
        "name": "Main Pressure Gauge",
        "unit": "state",
        "category": "Control",
        "description": "Digital signal indicating compressor cut-in / cut-out threshold",
        "normal_min": 0,
        "normal_max": 1
    },
    {
        "id": "LPS",
        "name": "Low Pressure Switch",
        "unit": "state",
        "category": "Safety",
        "description": "Emergency low pressure safety switch (< 7.0 bar warning)",
        "normal_min": 0,
        "normal_max": 1
    },
    {
        "id": "Pressure_switch",
        "name": "Pressure Switch Contact",
        "unit": "state",
        "category": "Control",
        "description": "Governor pressure switch signal regulating pneumatic cycling",
        "normal_min": 0,
        "normal_max": 1
    },
    {
        "id": "Oil_level",
        "name": "Oil Level Switch",
        "unit": "state",
        "category": "Safety",
        "description": "Oil reservoir minimum level safety interlock",
        "normal_min": 0,
        "normal_max": 1
    },
    {
        "id": "Caudal_impulses",
        "name": "Air Flow Impulses",
        "unit": "pulses",
        "category": "Pneumatic",
        "description": "Flow meter pulse counter indicating volumetric air delivery",
        "normal_min": 0,
        "normal_max": 1
    }
]

DOCUMENTED_EVENTS = [
    {
        "id": "event_1",
        "name": "Event #1: Air Leakage Incident",
        "type": "Air Leakage (Moderate)",
        "start": "2020-04-18 00:00:00",
        "end": "2020-04-18 23:59:00",
        "warning_start": "2020-04-17 23:30:00",
        "warning_end": "2020-04-18 00:00:00",
        "partition": "TRAIN",
        "description": "Air leak causing prolonged compressor duty cycles and pressure drop across cyclonic filter H1."
    },
    {
        "id": "event_2",
        "name": "Event #2: Air Leakage Incident",
        "type": "Air Leakage (Intermittent)",
        "start": "2020-05-29 23:30:00",
        "end": "2020-05-30 06:00:00",
        "warning_start": "2020-05-29 23:00:00",
        "warning_end": "2020-05-29 23:30:00",
        "partition": "TRAIN",
        "description": "Late-night pneumatic pressure degradation with elevated drying tower oscillation."
    },
    {
        "id": "event_3",
        "name": "Event #3: Air Leakage Episode",
        "type": "Air Leakage (Major Weekend Failure)",
        "start": "2020-06-05 10:00:00",
        "end": "2020-06-07 14:30:00",
        "warning_start": "2020-06-05 09:30:00",
        "warning_end": "2020-06-05 10:00:00",
        "partition": "VALIDATION",
        "description": "Multi-day persistent air leak requiring maintenance intervention on the train pneumatic panel."
    },
    {
        "id": "event_4",
        "name": "Event #4: Air Leakage Episode",
        "type": "Air Leakage (High-Stress Summer Event)",
        "start": "2020-07-15 14:30:00",
        "end": "2020-07-15 19:00:00",
        "warning_start": "2020-07-15 14:00:00",
        "warning_end": "2020-07-15 14:30:00",
        "partition": "FINAL TEST",
        "description": "Mid-summer rupture under continuous high pressure load and elevated ambient temperatures."
    }
]

class DataService:
    def __init__(self):
        self.telemetry_df: Optional[pd.DataFrame] = None
        self._initialize_cache()
        
    def _initialize_cache(self):
        """Prepares or loads high-efficiency joblib cache with all 65 engineered features."""
        features_csv = os.path.join(DATA_DIR, "metropt3_features.csv")
        
        # Check if cache is up-to-date with complete 65 features
        rebuild_needed = True
        if os.path.exists(CACHE_FILE):
            try:
                cached = joblib.load(CACHE_FILE)
                if all(f in cached.columns for f in FEATURE_NAMES) and len(cached) > 100000:
                    self.telemetry_df = cached
                    rebuild_needed = False
                    print(f"[DataService] Loaded verified 65-feature telemetry cache ({len(self.telemetry_df):,} rows).")
            except Exception as e:
                print(f"[DataService] Cache validation failed: {e}. Rebuilding...")
                
        if rebuild_needed:
            print("[DataService] Generating optimized 65-feature telemetry cache from metropt3_features.csv...")
            if not os.path.exists(features_csv):
                raise FileNotFoundError(f"Missing features dataset at {features_csv}")
                
            df = pd.read_csv(features_csv)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Sampling: 1-minute cadence (every 6th row) for normal + full 10-second for all 694 pre-failure intervals
            pos_mask = (df['target'] == 1)
            step_mask = (df.index % 6 == 0)
            sampled_df = df[pos_mask | step_mask].copy().reset_index(drop=True)
            
            joblib.dump(sampled_df, CACHE_FILE, compress=3)
            self.telemetry_df = sampled_df
            print(f"[DataService] Created verified cache with {len(sampled_df):,} rows ({os.path.getsize(CACHE_FILE)/(1024*1024):.2f} MB).")

    def get_features_by_timestamp(self, timestamp_str: str, tolerance_seconds: int = 180) -> Optional[Dict[str, Any]]:
        """
        Deterministic nearest-timestamp lookup retrieving the complete 65-feature vector.
        Returns None if no observation exists within tolerance_seconds.
        """
        if self.telemetry_df is None or len(self.telemetry_df) == 0:
            return None
            
        try:
            target_dt = pd.to_datetime(timestamp_str)
        except Exception:
            return None
            
        deltas = (self.telemetry_df['timestamp'] - target_dt).abs()
        nearest_idx = deltas.idxmin()
        min_delta_s = float(deltas.loc[nearest_idx].total_seconds())
        
        if min_delta_s > tolerance_seconds:
            return None
            
        row = self.telemetry_df.loc[nearest_idx]
        
        # Build exact 65-feature dictionary
        features = {f: float(row[f]) for f in FEATURE_NAMES}
        
        # Build 15 raw sensor info objects for UI
        sensors = {}
        for sm in SENSOR_METADATA:
            sid = sm["id"]
            cur_val = float(row.get(sid, 0.0))
            sensors[sid] = {
                "id": sid,
                "name": sm["name"],
                "value": round(cur_val, 2),
                "unit": sm.get("unit", ""),
                "category": sm.get("category", ""),
                "roll_mean_1m": round(float(row.get(f"{sid}_roll_mean_1m", cur_val)), 2),
                "roll_mean_5m": round(float(row.get(f"{sid}_roll_mean_5m", cur_val)), 2),
            }
            
        return {
            "timestamp_requested": str(timestamp_str),
            "timestamp_matched": str(row["timestamp"]),
            "time_difference_seconds": round(min_delta_s, 2),
            "target": int(row.get("target", 0)),
            "failure_status": str(row.get("failure_status", "normal")),
            "features": features,
            "sensors": sensors
        }

    def get_latest_reading(self) -> Dict[str, Any]:
        """Returns the latest telemetry record with sensor values, units, and complete 65 features."""
        if self.telemetry_df is None or len(self.telemetry_df) == 0:
            return {}
        latest_row = self.telemetry_df.iloc[-1].to_dict()
        prev_row = self.telemetry_df.iloc[-2].to_dict() if len(self.telemetry_df) > 1 else latest_row
        
        sensors = {}
        for sm in SENSOR_METADATA:
            sid = sm["id"]
            cur_val = float(latest_row.get(sid, 0.0))
            prev_val = float(prev_row.get(sid, cur_val))
            delta = round(cur_val - prev_val, 3)
            
            sensors[sid] = {
                "id": sid,
                "name": sm["name"],
                "value": round(cur_val, 2),
                "unit": sm.get("unit", ""),
                "category": sm.get("category", ""),
                "delta": delta,
                "normal_min": sm.get("normal_min"),
                "normal_max": sm.get("normal_max"),
                "roll_mean_1m": round(float(latest_row.get(f"{sid}_roll_mean_1m", cur_val)), 2),
                "roll_mean_5m": round(float(latest_row.get(f"{sid}_roll_mean_5m", cur_val)), 2),
                "diff_5m": round(float(latest_row.get(f"{sid}_diff_5m", 0.0)), 2)
            }
            
        features = {f: float(latest_row.get(f, 0.0)) for f in FEATURE_NAMES}
            
        return {
            "timestamp": str(latest_row["timestamp"]),
            "failure_status": latest_row.get("failure_status", "normal"),
            "target": int(latest_row.get("target", 0)),
            "sensors": sensors,
            "features": features
        }

    def get_reading_at_index(self, index: int) -> Dict[str, Any]:
        """Returns telemetry record at exact index for live simulation playback."""
        if self.telemetry_df is None:
            return {}
        idx = max(0, min(index, len(self.telemetry_df) - 1))
        row = self.telemetry_df.iloc[idx].to_dict()
        prev_row = self.telemetry_df.iloc[max(0, idx - 1)].to_dict()
        
        sensors = {}
        for sm in SENSOR_METADATA:
            sid = sm["id"]
            cur_val = float(row.get(sid, 0.0))
            prev_val = float(prev_row.get(sid, cur_val))
            sensors[sid] = {
                "id": sid,
                "name": sm["name"],
                "value": round(cur_val, 2),
                "unit": sm.get("unit", ""),
                "category": sm.get("category", ""),
                "delta": round(cur_val - prev_val, 3),
                "roll_mean_1m": round(float(row.get(f"{sid}_roll_mean_1m", cur_val)), 2),
                "roll_mean_5m": round(float(row.get(f"{sid}_roll_mean_5m", cur_val)), 2),
            }
            
        features = {f: float(row.get(f, 0.0)) for f in FEATURE_NAMES}
            
        return {
            "index": idx,
            "total_records": len(self.telemetry_df),
            "timestamp": str(row["timestamp"]),
            "failure_status": row.get("failure_status", "normal"),
            "target": int(row.get("target", 0)),
            "sensors": sensors,
            "features": features
        }

    def get_timeseries(self, sensor: str = "TP2", start: Optional[str] = None, end: Optional[str] = None, limit: int = 300) -> List[Dict[str, Any]]:
        """Extracts chronological telemetry time-series points with rolling metrics."""
        if self.telemetry_df is None:
            return []
            
        sub_df = self.telemetry_df
        if start:
            try:
                sub_df = sub_df[sub_df['timestamp'] >= pd.to_datetime(start)]
            except Exception:
                pass
        if end:
            try:
                sub_df = sub_df[sub_df['timestamp'] <= pd.to_datetime(end)]
            except Exception:
                pass
            
        if len(sub_df) > limit:
            step = max(1, len(sub_df) // limit)
            sub_df = sub_df.iloc[::step]
            
        result = []
        for _, r in sub_df.iterrows():
            item = {
                "timestamp": r["timestamp"].strftime("%Y-%m-%d %H:%M"),
                "value": round(float(r.get(sensor, 0.0)), 2),
                "target": int(r.get("target", 0)),
                "failure_status": r.get("failure_status", "normal")
            }
            if f"{sensor}_roll_mean_1m" in r:
                item["roll_mean_1m"] = round(float(r[f"{sensor}_roll_mean_1m"]), 2)
            if f"{sensor}_roll_mean_5m" in r:
                item["roll_mean_5m"] = round(float(r[f"{sensor}_roll_mean_5m"]), 2)
            result.append(item)
            
        return result

    def get_multisensor_series(self, sensors: List[str], start: Optional[str] = None, end: Optional[str] = None, limit: int = 250) -> List[Dict[str, Any]]:
        """Returns synchronized multi-sensor time-series for comparative charts."""
        if self.telemetry_df is None:
            return []
        sub_df = self.telemetry_df
        if start:
            try:
                sub_df = sub_df[sub_df['timestamp'] >= pd.to_datetime(start)]
            except Exception:
                pass
        if end:
            try:
                sub_df = sub_df[sub_df['timestamp'] <= pd.to_datetime(end)]
            except Exception:
                pass
            
        if len(sub_df) > limit:
            step = max(1, len(sub_df) // limit)
            sub_df = sub_df.iloc[::step]
            
        result = []
        for _, r in sub_df.iterrows():
            item = {
                "timestamp": r["timestamp"].strftime("%Y-%m-%d %H:%M"),
                "target": int(r.get("target", 0)),
                "failure_status": r.get("failure_status", "normal")
            }
            for s in sensors:
                item[s] = round(float(r.get(s, 0.0)), 2)
            result.append(item)
            
        return result

    def check_sustained_anomaly(self, timestamp_str: str, window_minutes: int = 5, anomaly_threshold: float = 0.5040, anomaly_model = None) -> bool:
        """
        Checks whether >= 3 observations in the trailing window_minutes exceed anomaly_threshold.
        Uses cached features only (no future leakage).
        """
        if self.telemetry_df is None or anomaly_model is None:
            return False
        try:
            target_dt = pd.to_datetime(timestamp_str)
            start_dt = target_dt - pd.Timedelta(minutes=window_minutes)
            
            sub = self.telemetry_df[(self.telemetry_df['timestamp'] >= start_dt) & (self.telemetry_df['timestamp'] <= target_dt)]
            if len(sub) < 3:
                return False
                
            feat_matrix = sub[FEATURE_NAMES].values
            scores = -anomaly_model.score_samples(feat_matrix)
            anom_count = int((scores >= anomaly_threshold).sum())
            return anom_count >= 3
        except Exception:
            return False

# Global singleton
_data_service = None

def get_data_service() -> DataService:
    global _data_service
    if _data_service is None:
        _data_service = DataService()
    return _data_service

if __name__ == "__main__":
    ds = get_data_service()
    res = ds.get_features_by_timestamp("2020-04-17 23:30:00")
    print("Timestamp Lookup Result:")
    if res:
        print("Requested:", res["timestamp_requested"], "Matched:", res["timestamp_matched"])
        print("Feature count:", len(res["features"]))
        print("H1_roll_std_1m:", res["features"].get("H1_roll_std_1m"))
    else:
        print("Lookup returned None")
