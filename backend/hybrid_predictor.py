"""
MetroGuard AI - Updated Hybrid Predictor with Smart Alerts & Prescriptive Recommendations
"""

import os
import json
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Union

from backend.predict import get_predictor, MetroGuardPredictor
from backend.data_service import FEATURE_NAMES

class MetroGuardHybridPredictor:
    def __init__(self, model_dir: Optional[str] = None):
        if model_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            model_dir = os.path.join(base_dir, "models")
            
        self.xgb_predictor = get_predictor()
        
        self.anomaly_model_path = os.path.join(model_dir, "metroguard_anomaly_model.pkl")
        self.anomaly_meta_path = os.path.join(model_dir, "anomaly_metadata.json")
        
        if not os.path.exists(self.anomaly_model_path):
            raise FileNotFoundError(f"Anomaly model artifact not found at {self.anomaly_model_path}")
        if not os.path.exists(self.anomaly_meta_path):
            raise FileNotFoundError(f"Anomaly metadata not found at {self.anomaly_meta_path}")
            
        anomaly_bundle = joblib.load(self.anomaly_model_path)
        self.anomaly_model = anomaly_bundle["model"]
        self.feature_names = anomaly_bundle.get("features", FEATURE_NAMES)
        
        with open(self.anomaly_meta_path, 'r') as f:
            self.anomaly_meta = json.load(f)
            
        # Thresholds calibrated on normal training data (99th and 99.5th percentiles)
        self.anomaly_threshold = float(self.anomaly_meta.get("thresholds", {}).get("selected_threshold", 0.5040))
        self.anomaly_high_threshold = float(self.anomaly_meta.get("thresholds", {}).get("train_99_5th_percentile", 0.5350))
        
        # Normal baseline physical statistics for evidence attribution
        self.baseline_stats = {
            "Oil_temperature": {"median": 58.70, "std": 6.15, "unit": "°C", "desc": "Compressor oil temperature"},
            "Oil_temperature_roll_mean_5m": {"median": 58.86, "std": 6.11, "unit": "°C", "desc": "5-min oil temperature baseline"},
            "TP2": {"median": -0.01, "std": 3.75, "unit": "bar", "desc": "Compressor output pressure"},
            "TP2_roll_std_5m": {"median": 0.001, "std": 1.82, "unit": "bar", "desc": "Compressor pressure volatility"},
            "TP2_diff_5m": {"median": 0.00, "std": 3.80, "unit": "bar", "desc": "5-min compressor pressure change"},
            "H1": {"median": -0.01, "std": 3.76, "unit": "bar", "desc": "Cyclonic separator pressure drop"},
            "H1_roll_std_5m": {"median": 0.12, "std": 1.76, "unit": "bar", "desc": "Filter pressure turbulence"},
            "H1_diff_5m": {"median": -0.31, "std": 3.79, "unit": "bar", "desc": "Filter pressure rate-of-change"},
            "DV_pressure": {"median": -0.02, "std": 0.38, "unit": "bar", "desc": "Drying tower purge pressure"},
            "DV_pressure_roll_mean_5m": {"median": -0.02, "std": 0.35, "unit": "bar", "desc": "5-min drying tower pressure"},
            "Reservoirs": {"median": 8.97, "std": 0.72, "unit": "bar", "desc": "Air reservoir storage pressure"},
            "Reservoirs_roll_mean_1m": {"median": 8.97, "std": 0.72, "unit": "bar", "desc": "Reservoir charge level"},
            "Reservoirs_diff_1m": {"median": -0.06, "std": 0.29, "unit": "bar", "desc": "1-min reservoir air depletion"},
            "TP3": {"median": 8.97, "std": 0.72, "unit": "bar", "desc": "Pneumatic panel line pressure"},
            "TP3_roll_std_1m": {"median": 0.02, "std": 0.09, "unit": "bar", "desc": "Pneumatic panel line oscillation"},
            "TP3_diff_1m": {"median": -0.06, "std": 0.29, "unit": "bar", "desc": "1-min line pressure change"},
            "Motor_current": {"median": 0.00, "std": 3.65, "unit": "A", "desc": "Motor electrical current"},
            "Motor_current_roll_std_5m": {"median": 0.05, "std": 1.48, "unit": "A", "desc": "Motor load jitter"}
        }

    def compute_anomaly_score(self, feat_vec: np.ndarray) -> float:
        """Evaluates Isolation Forest outlier extremity (higher score = more anomalous)."""
        raw_score = -self.anomaly_model.score_samples(feat_vec)[0]
        return float(raw_score)

    def classify_anomaly_status(self, score: float) -> str:
        if score < self.anomaly_threshold:
            return "NORMAL"
        elif score < self.anomaly_high_threshold:
            return "ELEVATED"
        else:
            return "HIGH"

    def extract_physical_evidence(self, feat_dict: Dict[str, float]) -> List[Dict[str, Any]]:
        """Identifies physical features deviating beyond 2 standard deviations from normal."""
        evidence = []
        for feat, stats in self.baseline_stats.items():
            if feat in feat_dict:
                val = float(feat_dict[feat])
                med = stats["median"]
                std = stats["std"]
                z = (val - med) / std if std > 1e-6 else 0.0
                
                if abs(z) >= 2.0:
                    direction = "elevated" if z > 0 else "suppressed / dropped"
                    evidence.append({
                        "feature": feat,
                        "description": stats["desc"],
                        "actual_value": round(val, 3),
                        "baseline_median": round(med, 3),
                        "unit": stats["unit"],
                        "z_score": round(z, 2),
                        "reason": f"{stats['desc']} is {direction} ({round(z, 2)}σ vs normal baseline)"
                    })
                    
        # Sort evidence by absolute extremity
        evidence.sort(key=lambda x: abs(x["z_score"]), reverse=True)
        return evidence

    def generate_recommendations(self, evidence: List[Dict[str, Any]], alert_level: str) -> List[str]:
        """Generates deterministic prescriptive maintenance actions based on active physical signals."""
        recs = []
        seen = set()
        
        has_thermal = any("Oil_temperature" in ev["feature"] for ev in evidence)
        has_filter = any("H1" in ev["feature"] for ev in evidence)
        has_discharge = any("TP2" in ev["feature"] for ev in evidence)
        has_dryer = any("DV_pressure" in ev["feature"] for ev in evidence)
        has_reservoirs = any("Reservoirs" in ev["feature"] or "TP3" in ev["feature"] for ev in evidence)
        has_motor = any("Motor_current" in ev["feature"] for ev in evidence)
        
        if has_thermal:
            r = "Inspect compressor cooling circuit, radiator airflow, mechanical lubricant condition, and temperature probe."
            if r not in seen:
                recs.append(r)
                seen.add(r)
                
        if has_filter:
            r = "Inspect cyclonic moisture separator filter assembly, differential pressure sensor, and automatic drain solenoid valve."
            if r not in seen:
                recs.append(r)
                seen.add(r)
                
        if has_discharge:
            r = "Check compressor discharge non-return valve, pressure governor calibration, and high-pressure manifold sealing."
            if r not in seen:
                recs.append(r)
                seen.add(r)
                
        if has_dryer:
            r = "Inspect desiccant twin-tower switching valves, purge discharge exhaust port, and regeneration timing."
            if r not in seen:
                recs.append(r)
                seen.add(r)
                
        if has_reservoirs:
            r = "Inspect main reservoir pneumatic circuit and brake supply connections for downstream air leakage."
            if r not in seen:
                recs.append(r)
                seen.add(r)
                
        if has_motor:
            r = "Inspect motor electrical current symmetry, contactor condition, and compressor mechanical load resistance."
            if r not in seen:
                recs.append(r)
                seen.add(r)
                
        if alert_level in ["HIGH RISK", "WARNING"]:
            r_gen = "Schedule technical pneumatic leak inspection and pressure-decay verification at next depot maintenance stop."
            if r_gen not in seen and len(recs) < 3:
                recs.append(r_gen)
                seen.add(r_gen)
                
        if not recs and alert_level == "MONITOR":
            recs.append("Maintain continuous sensor logging and monitor rolling pressure stability.")
        elif not recs and alert_level == "NORMAL":
            recs.append("No maintenance intervention required. Continue routine operational monitoring.")
            
        return recs[:3]

    def determine_alert(
        self,
        xgb_status: str,
        xgb_prob: float,
        anom_score: float,
        anom_status: str,
        hybrid_status: str,
        evidence: List[Dict[str, Any]],
        is_sustained_anomaly: bool
    ) -> Dict[str, Any]:
        """
        Determines deterministic operational alert level (NORMAL, MONITOR, WARNING, HIGH RISK)
        and packages decision-support recommendations.
        """
        strong_evidence_count = sum(1 for ev in evidence if abs(ev.get("z_score", 0.0)) >= 2.5)
        
        if hybrid_status == "HIGH RISK" or xgb_status == "HIGH RISK":
            level = "HIGH RISK"
            title = "Critical Compressor Failure Risk Alert"
            reason = f"Supervised model indicates high probability ({round(xgb_prob * 100, 1)}%) of impending pneumatic failure within 30 minutes."
        elif (
            hybrid_status in ["FAILURE WARNING", "ANOMALY WARNING"]
            or xgb_status == "WARNING"
            or anom_status == "HIGH"
            or (anom_status == "ELEVATED" and is_sustained_anomaly)
            or strong_evidence_count >= 2
        ):
            level = "WARNING"
            if xgb_status == "WARNING":
                title = "Pneumatic Failure Warning Alert"
                reason = f"Supervised model detected known pre-failure signature ({round(xgb_prob * 100, 2)}% risk)."
            else:
                title = "Abnormal Compressor Dynamics Warning"
                reason = f"Multi-signal anomaly detected ({len(evidence)} physical metrics deviating >2.0σ from nominal baseline)."
        elif hybrid_status == "MONITOR" or anom_status == "ELEVATED" or len(evidence) >= 1:
            level = "MONITOR"
            title = "Operational Advisory & Persistence Monitoring"
            reason = "Isolated physical signal deviation detected. Telemetry flagged for persistence tracking."
        else:
            level = "NORMAL"
            title = "Compressor Nominal Operation"
            reason = "All physical sensor dynamics and model risk metrics remain within nominal operating distributions."
            
        recommendations = self.generate_recommendations(evidence, level)
        
        return {
            "level": level,
            "title": title,
            "reason": reason,
            "recommendations": recommendations
        }

    def evaluate_hybrid(
        self,
        feat_dict: Dict[str, float],
        is_sustained_anomaly: bool = False
    ) -> Dict[str, Any]:
        """
        Executes dual inference (XGBoost + Isolation Forest), applies hybrid decision logic,
        and derives smart alerts & prescriptive recommendations.
        """
        # Validate feature presence
        missing = [f for f in self.feature_names if f not in feat_dict]
        if missing:
            raise ValueError(f"Missing required feature(s): {missing[:5]} (total missing: {len(missing)})")
            
        # 1. Supervised XGBoost Inference
        xgb_res = self.xgb_predictor.predict(feat_dict)
        
        # 2. Unsupervised Isolation Forest Inference
        feat_array = np.array([[feat_dict[f] for f in self.feature_names]])
        anom_score = self.compute_anomaly_score(feat_array)
        anom_status = self.classify_anomaly_status(anom_score)
        
        # 3. Physical Evidence Extraction
        evidence = self.extract_physical_evidence(feat_dict)
        
        # 4. Hybrid Decision Logic Engine
        xgb_status = xgb_res["status"]
        xgb_prob = xgb_res["risk_probability"]
        
        if xgb_status == "HIGH RISK":
            hybrid_status = "HIGH RISK"
            reason = "Supervised XGBoost indicates severe known failure risk (>70%)."
        elif xgb_status == "WARNING" and anom_status in ["ELEVATED", "HIGH"]:
            hybrid_status = "HIGH RISK"
            reason = "Concurrent alert: Supervised failure probability elevated alongside strong multidimensional anomaly."
        elif xgb_status == "WARNING":
            hybrid_status = "FAILURE WARNING"
            reason = "Supervised model detected recurring pre-failure pneumatic pattern."
        elif anom_status == "HIGH" or (anom_status == "ELEVATED" and is_sustained_anomaly):
            hybrid_status = "ANOMALY WARNING"
            reason = f"Unsupervised detector flags significant out-of-distribution operation (Score {anom_score:.4f} >= {self.anomaly_threshold:.4f})."
        elif anom_status == "ELEVATED":
            hybrid_status = "MONITOR"
            reason = "Isolated abnormal sensor reading detected. Telemetry flagged for persistence monitoring."
        else:
            hybrid_status = "NORMAL"
            reason = "All signals conform to nominal baseline operating distributions."
            
        # 5. Operational Alert & Prescriptive Recommendations Layer
        alert = self.determine_alert(
            xgb_status=xgb_status,
            xgb_prob=xgb_prob,
            anom_score=anom_score,
            anom_status=anom_status,
            hybrid_status=hybrid_status,
            evidence=evidence,
            is_sustained_anomaly=is_sustained_anomaly
        )
            
        return {
            "xgboost": {
                "risk_probability": xgb_prob,
                "risk_percentage": xgb_res["risk_percentage"],
                "status": xgb_status,
                "threshold": self.xgb_predictor.selected_threshold
            },
            "anomaly": {
                "score": round(anom_score, 4),
                "threshold": round(self.anomaly_threshold, 4),
                "high_threshold": round(self.anomaly_high_threshold, 4),
                "status": anom_status
            },
            "hybrid": {
                "status": hybrid_status,
                "reason": reason
            },
            "evidence": evidence,
            "alert": alert,
            "features_analyzed": len(self.feature_names)
        }

# Global singleton helper
_hybrid_predictor_instance = None

def get_hybrid_predictor() -> MetroGuardHybridPredictor:
    global _hybrid_predictor_instance
    if _hybrid_predictor_instance is None:
        _hybrid_predictor_instance = MetroGuardHybridPredictor()
    return _hybrid_predictor_instance

if __name__ == "__main__":
    hp = get_hybrid_predictor()
    print("MetroGuard Hybrid Predictor initialized with Smart Alerts & Recommendations.")
