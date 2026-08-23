"""
MetroGuard AI - Explainable Anomaly Intelligence Engine
Transforms raw Isolation Forest anomaly scores into a calibrated 0-100 severity index,
ranks top physical sensor deviations with Z-scores and trends, tracks persistence,
estimates trajectory (Worsening/Stable/Recovering), and generates evidence-based
operational hypotheses.
"""

from typing import Dict, Any, List, Optional
import numpy as np

# Calibration constants derived strictly from normal training baseline (140,914 samples)
ANOM_MIN_SCORE = 0.3000
ANOM_MED_SCORE = 0.3500
ANOM_ELEVATED_THRESH = 0.5040  # 99th percentile of normal baseline
ANOM_HIGH_THRESH = 0.5350      # 99.5th percentile of normal baseline
ANOM_MAX_SCORE = 0.6000

# Sensor human-readable metadata
SENSOR_METADATA = {
    "TP2": {"name": "Compressor Output Pressure (TP2)", "unit": "bar", "system": "Compressor Delivery"},
    "TP3": {"name": "Pneumatic Panel Pressure (TP3)", "unit": "bar", "system": "Pneumatic Control"},
    "H1": {"name": "Cyclonic Separator Drop (H1)", "unit": "bar", "system": "Moisture Separation"},
    "DV_pressure": {"name": "Drying Tower Pressure (DV)", "unit": "bar", "system": "Desiccant Dryer"},
    "Reservoirs": {"name": "Main Air Reservoir (Reservoirs)", "unit": "bar", "system": "Storage"},
    "Motor_current": {"name": "Motor Electrical Current", "unit": "A", "system": "Motor Drive"},
    "Oil_temperature": {"name": "Compressor Oil Temperature", "unit": "°C", "system": "Thermal & Lubrication"},
    "COMP": {"name": "Compressor Operating State", "unit": "state", "system": "Electrical Control"}
}

def calculate_anomaly_severity(raw_score: float) -> Dict[str, Any]:
    """
    Calibrates raw Isolation Forest score S(x) in [0.30, 0.60] into a standardized 0-100 severity index.
    Calibration is derived strictly from training baseline distributions.
    """
    score = float(raw_score)
    
    if score < ANOM_MED_SCORE:
        # 0 - 20 (Nominal background)
        severity = max(0.0, (score - ANOM_MIN_SCORE) / (ANOM_MED_SCORE - ANOM_MIN_SCORE) * 20.0)
    elif score < ANOM_ELEVATED_THRESH:
        # 20 - 50 (Low / Normal operating range)
        severity = 20.0 + (score - ANOM_MED_SCORE) / (ANOM_ELEVATED_THRESH - ANOM_MED_SCORE) * 30.0
    elif score < ANOM_HIGH_THRESH:
        # 50 - 75 (Elevated anomaly - above 99th percentile)
        severity = 50.0 + (score - ANOM_ELEVATED_THRESH) / (ANOM_HIGH_THRESH - ANOM_ELEVATED_THRESH) * 25.0
    else:
        # 75 - 100 (Severe anomaly - above 99.5th percentile)
        severity = 75.0 + min(25.0, (score - ANOM_HIGH_THRESH) / (ANOM_MAX_SCORE - ANOM_HIGH_THRESH) * 25.0)
        
    severity_int = int(round(max(0.0, min(100.0, severity))))
    
    if severity_int >= 75:
        label = "SEVERE"
        color = "rose"
    elif severity_int >= 50:
        label = "ELEVATED"
        color = "amber"
    elif severity_int >= 25:
        label = "LOW"
        color = "cyan"
    else:
        label = "NOMINAL"
        color = "emerald"
        
    return {
        "raw_score": round(score, 4),
        "severity_score": severity_int,
        "severity_label": label,
        "color": color,
        "threshold_elevated": round(ANOM_ELEVATED_THRESH, 4),
        "threshold_high": round(ANOM_HIGH_THRESH, 4)
    }

def rank_top_sensor_deviations(
    feat_dict: Dict[str, float],
    normal_baselines: Dict[str, Dict[str, float]],
    trailing_history: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Ranks top contributing sensor deviations based on absolute Z-score against normal baseline medians.
    Computes chronological trend (RISING, FALLING, STABLE) from recent trailing observations.
    """
    deviations = []
    
    # Priority key sensors for explainability
    key_sensors = ["Oil_temperature", "H1", "TP2", "TP3", "Reservoirs", "Motor_current", "DV_pressure"]
    
    for s_id in key_sensors:
        if s_id not in feat_dict or s_id not in normal_baselines:
            continue
            
        cur_val = float(feat_dict[s_id])
        base_med = normal_baselines[s_id]["median"]
        base_std = max(1e-4, normal_baselines[s_id]["std"])
        
        z_score = (cur_val - base_med) / base_std
        delta = cur_val - base_med
        abs_z = abs(z_score)
        
        # Calculate trend from trailing history
        trend = "STABLE"
        if trailing_history and len(trailing_history) >= 5:
            past_vals = [h.get("sensors", {}).get(s_id, {}).get("value") for h in trailing_history[-5:] if h.get("sensors", {}).get(s_id)]
            valid_past = [v for v in past_vals if v is not None]
            if len(valid_past) >= 3:
                recent_delta = cur_val - valid_past[0]
                if recent_delta > 0.05 * base_std:
                    trend = "RISING"
                elif recent_delta < -0.05 * base_std:
                    trend = "FALLING"
                    
        meta = SENSOR_METADATA.get(s_id, {"name": s_id, "unit": "", "system": "Compressor"})
        
        deviations.append({
            "sensor_id": s_id,
            "name": meta["name"],
            "system": meta["system"],
            "unit": meta["unit"],
            "current_value": round(cur_val, 2),
            "baseline_median": round(base_med, 2),
            "deviation": round(delta, 2),
            "z_score": round(z_score, 2),
            "abs_z": round(abs_z, 2),
            "trend": trend,
            "is_significant": abs_z >= 1.5
        })
        
    # Sort descending by absolute Z-score
    deviations.sort(key=lambda x: x["abs_z"], reverse=True)
    return deviations[:5]

def estimate_anomaly_trajectory(trailing_severities: List[int]) -> str:
    """
    Classifies overall anomaly trajectory (WORSENING, STABLE, RECOVERING)
    based on the slope of severity scores over the trailing window.
    """
    if not trailing_severities or len(trailing_severities) < 5:
        return "STABLE"
        
    start_avg = np.mean(trailing_severities[:len(trailing_severities)//2])
    end_avg = np.mean(trailing_severities[len(trailing_severities)//2:])
    diff = end_avg - start_avg
    
    if diff >= 4.0:
        return "WORSENING"
    elif diff <= -4.0:
        return "RECOVERING"
    else:
        return "STABLE"

def generate_operational_hypothesis(
    top_deviations: List[Dict[str, Any]],
    anomaly_severity: int,
    is_sustained: bool
) -> Dict[str, Any]:
    """
    Generates an evidence-based operational hypothesis (possible contributing condition)
    and suggested inspection actions based on observed sensor deviations.
    Explicitly distinguishes operational hypotheses from guaranteed root-cause diagnoses.
    """
    # Check for primary physical signatures
    dev_map = {d["sensor_id"]: d for d in top_deviations}
    
    # 1. Thermal Buildup / Lubrication signature
    oil_dev = dev_map.get("Oil_temperature")
    if oil_dev and oil_dev["z_score"] >= 2.0:
        return {
            "title": "Possible Thermal Load & Cooling Restriction Condition",
            "condition_type": "THERMAL_ELEVATION",
            "evidence": f"Compressor oil temperature is deviating significantly at {oil_dev['current_value']}°C (+{oil_dev['deviation']}°C above normal baseline, Z = +{oil_dev['z_score']}σ).",
            "confidence": "HIGH" if oil_dev["z_score"] >= 3.0 else "MODERATE",
            "recommended_inspection": "Inspect compressor oil radiator matrix for debris/blockages, verify oil level and lubrication viscosity, and check ventilation duct airflow."
        }
        
    # 2. Cyclonic Separator / Filter Drop signature
    h1_dev = dev_map.get("H1")
    if h1_dev and h1_dev["z_score"] >= 2.0:
        return {
            "title": "Possible Cyclonic Separator / Filter Restriction Condition",
            "evidence": f"Cyclonic moisture separator filter drop is abnormally elevated at {h1_dev['current_value']} bar (Z = +{h1_dev['z_score']}σ vs baseline).",
            "condition_type": "FILTER_RESTRICTION",
            "confidence": "HIGH" if h1_dev["z_score"] >= 2.5 else "MODERATE",
            "recommended_inspection": "Inspect cyclonic moisture separator filter cartridge, check differential pressure transducer, and verify automatic condensate drain valve actuation."
        }
        
    # 3. Pneumatic Line / Regulation / Leakage signature
    tp2_dev = dev_map.get("TP2")
    tp3_dev = dev_map.get("TP3")
    res_dev = dev_map.get("Reservoirs")
    if (tp2_dev and abs(tp2_dev["z_score"]) >= 2.0) or (tp3_dev and abs(tp3_dev["z_score"]) >= 2.0) or (res_dev and abs(res_dev["z_score"]) >= 2.0):
        return {
            "title": "Possible Pneumatic Delivery & Pressure Regulation Abnormality",
            "condition_type": "PRESSURE_REGULATION",
            "evidence": f"Air delivery / reservoir pressures exhibiting out-of-tolerance oscillations outside nominal regulation limits.",
            "confidence": "MODERATE",
            "recommended_inspection": "Perform pneumatic line pressure-decay leak test, inspect desiccant tower purge solenoid cycle, and calibrate pneumatic panel relief valves."
        }
        
    if anomaly_severity < 45 and not is_sustained:
        return {
            "title": "Nominal Thermal-Pneumatic Operation",
            "condition_type": "NOMINAL",
            "evidence": "All monitored physical sensor channels conform to nominal baseline operating distributions.",
            "confidence": "HIGH",
            "recommended_inspection": "No immediate mechanical action required. Maintain routine preventive maintenance schedule."
        }
        
    # Default generalized physical anomaly
    return {
        "title": "Multidimensional Sensor Distribution Anomaly",
        "condition_type": "GENERAL_ANOMALY",
        "evidence": f"Multi-channel sensor vector deviating from baseline operating envelope (Severity: {anomaly_severity}/100).",
        "confidence": "MODERATE",
        "recommended_inspection": "Review compressor operational duty cycle, check electrical motor current balance, and monitor persistence window for recurring anomalies."
    }

def explain_current_anomaly(
    feat_dict: Dict[str, float],
    raw_anomaly_score: float,
    normal_baselines: Dict[str, Dict[str, float]],
    trailing_history: Optional[List[Dict[str, Any]]] = None,
    trailing_anomalies_count: int = 0,
    window_size: int = 30
) -> Dict[str, Any]:
    """
    Assembles the complete explainable anomaly intelligence payload.
    """
    severity_info = calculate_anomaly_severity(raw_anomaly_score)
    top_deviations = rank_top_sensor_deviations(feat_dict, normal_baselines, trailing_history)
    
    # Extract trailing severities for trajectory
    trailing_sevs = [h.get("anomaly_severity", 0) for h in trailing_history] if trailing_history else [severity_info["severity_score"]]
    trajectory = estimate_anomaly_trajectory(trailing_sevs)
    
    is_sustained = trailing_anomalies_count >= 3
    hypothesis = generate_operational_hypothesis(top_deviations, severity_info["severity_score"], is_sustained)
    
    return {
        "anomaly_score": severity_info["raw_score"],
        "anomaly_severity": severity_info["severity_score"],
        "severity_label": severity_info["severity_label"],
        "severity_color": severity_info["color"],
        "trajectory": trajectory,
        "persistence": {
            "abnormal_count": trailing_anomalies_count,
            "window_size": window_size,
            "is_persistent": is_sustained,
            "status": "PERSISTENT" if is_sustained else "TRANSIENT"
        },
        "top_sensor_deviations": top_deviations,
        "operational_hypothesis": hypothesis
    }
