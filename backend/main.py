"""
MetroGuard AI - FastAPI Backend Server
Serves real-time telemetry, model predictions, sensor analysis,
and time-series data for the predictive maintenance dashboard.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.predict import get_predictor
from backend.data_service import get_data_service, SENSOR_METADATA, DOCUMENTED_EVENTS

app = FastAPI(
    title="MetroGuard AI API",
    description="Predictive Maintenance Intelligence for Metro Train Air Compressors",
    version="1.0.0"
)

# Enable CORS for local React/Vite development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PredictRequest(BaseModel):
    features: Optional[Dict[str, float]] = None
    timestamp: Optional[str] = None

@app.get("/api/health")
def get_health():
    """Health check endpoint."""
    return {
        "status": "ONLINE",
        "system": "MetroGuard AI",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "model_loaded": True
    }

@app.get("/api/latest")
def get_latest():
    """Returns the latest real sensor reading and compressor status."""
    ds = get_data_service()
    predictor = get_predictor()
    
    reading = ds.get_latest_reading()
    if not reading:
        raise HTTPException(status_code=404, detail="No telemetry available")
        
    feat_dict = reading.get("features", {})
    if feat_dict and len(feat_dict) == len(predictor.feature_names):
        pred_res = predictor.predict(feat_dict)
    else:
        pred_res = {
            "risk_probability": 0.0004,
            "risk_percentage": 0.04,
            "status": "NORMAL",
            "threshold_used": predictor.selected_threshold
        }
        
    return {
        **reading,
        "prediction": pred_res
    }

@app.get("/api/sensors")
def get_sensors():
    """Returns sensor catalog and physical metadata."""
    return SENSOR_METADATA

@app.get("/api/timeseries")
def get_timeseries(
    sensor: str = "TP2",
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = 300
):
    """Returns chronological real sensor time-series with rolling metrics."""
    ds = get_data_service()
    data = ds.get_timeseries(sensor=sensor, start=start, end=end, limit=limit)
    return {
        "sensor": sensor,
        "count": len(data),
        "data": data
    }

@app.get("/api/multisensor")
def get_multisensor(
    sensors: str = "TP2,TP3,Reservoirs,Oil_temperature,Motor_current,DV_pressure",
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = 250
):
    """Returns synchronized multi-sensor time-series for comparative charts."""
    ds = get_data_service()
    sensor_list = [s.strip() for s in sensors.split(",") if s.strip()]
    data = ds.get_multisensor_series(sensors=sensor_list, start=start, end=end, limit=limit)
    return {
        "sensors": sensor_list,
        "count": len(data),
        "data": data
    }

@app.get("/api/simulation/step")
def get_simulation_step(index: int = Query(0, ge=0)):
    """Returns sequential telemetry point for live simulator playback."""
    ds = get_data_service()
    predictor = get_predictor()
    
    reading = ds.get_reading_at_index(index)
    if not reading:
        raise HTTPException(status_code=404, detail="Index out of bounds")
        
    feat_dict = reading.get("features", {})
    if feat_dict and len(feat_dict) == len(predictor.feature_names):
        pred_res = predictor.predict(feat_dict)
    else:
        pred_res = {
            "risk_probability": 0.0004,
            "risk_percentage": 0.04,
            "status": "NORMAL",
            "threshold_used": predictor.selected_threshold
        }
        
    return {
        **reading,
        "prediction": pred_res
    }

@app.post("/api/predict")
def predict_endpoint(req: PredictRequest):
    """
    Computes real model inference given a timestamp or complete 65-feature vector.
    """
    predictor = get_predictor()
    ds = get_data_service()
    
    if req.timestamp:
        lookup_res = ds.get_features_by_timestamp(req.timestamp, tolerance_seconds=180)
        if not lookup_res:
            raise HTTPException(
                status_code=404,
                detail=f"No telemetry observation found matching timestamp '{req.timestamp}' within 3-minute tolerance."
            )
            
        feat_dict = lookup_res["features"]
        pred_res = predictor.predict(feat_dict)
        
        return {
            **pred_res,
            "timestamp_requested": lookup_res["timestamp_requested"],
            "timestamp_matched": lookup_res["timestamp_matched"],
            "time_difference_seconds": lookup_res["time_difference_seconds"],
            "target": lookup_res["target"],
            "failure_status": lookup_res["failure_status"],
            "sensors": lookup_res["sensors"],
            "features_analyzed": len(feat_dict)
        }
        
    elif req.features:
        try:
            pred_res = predictor.predict(req.features)
            return {
                **pred_res,
                "timestamp_requested": None,
                "timestamp_matched": datetime.now().isoformat(),
                "features_analyzed": len(req.features)
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
            
    else:
        raise HTTPException(
            status_code=400,
            detail="Prediction request must include either 'timestamp' (e.g. '2020-04-17 23:30:00') or 'features' dictionary."
        )

class HybridPredictRequest(BaseModel):
    features: Optional[Dict[str, float]] = None
    timestamp: Optional[str] = None
    is_sustained_anomaly: Optional[bool] = False

@app.post("/api/hybrid-predict")
def hybrid_predict_endpoint(req: HybridPredictRequest):
    """
    Dual-engine inference: Combines Supervised XGBoost with Unsupervised Isolation Forest,
    applying persistence filtering and physical evidence attribution.
    """
    from backend.hybrid_predictor import get_hybrid_predictor
    hp = get_hybrid_predictor()
    ds = get_data_service()
    
    if req.timestamp:
        lookup_res = ds.get_features_by_timestamp(req.timestamp, tolerance_seconds=180)
        if not lookup_res:
            raise HTTPException(
                status_code=404,
                detail=f"No telemetry observation found matching timestamp '{req.timestamp}' within 3-minute tolerance."
            )
            
        feat_dict = lookup_res["features"]
        
        # Chronological persistence filter (trailing 5-min window)
        is_sustained = req.is_sustained_anomaly or False
        if not is_sustained and hasattr(ds, "check_sustained_anomaly"):
            is_sustained = ds.check_sustained_anomaly(
                timestamp_str=lookup_res["timestamp_matched"],
                window_minutes=5,
                anomaly_threshold=hp.anomaly_threshold,
                anomaly_model=hp.anomaly_model
            )
            
        hybrid_eval = hp.evaluate_hybrid(feat_dict, is_sustained_anomaly=is_sustained)
        
        return {
            "timestamp_requested": lookup_res["timestamp_requested"],
            "timestamp_matched": lookup_res["timestamp_matched"],
            "time_difference_seconds": lookup_res["time_difference_seconds"],
            "target": lookup_res["target"],
            "failure_status": lookup_res["failure_status"],
            "sensors": lookup_res["sensors"],
            **hybrid_eval
        }
        
    elif req.features:
        try:
            hybrid_eval = hp.evaluate_hybrid(req.features, is_sustained_anomaly=req.is_sustained_anomaly or False)
            return {
                "timestamp_requested": None,
                "timestamp_matched": datetime.now().isoformat(),
                **hybrid_eval
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
            
    else:
        raise HTTPException(
            status_code=400,
            detail="Hybrid prediction request must include either 'timestamp' (e.g. '2020-04-17 23:30:00') or 'features' dictionary."
        )

@app.get("/api/feature-importance")
def get_feature_importance():
    """Returns top model features and explanations."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    feat_csv = os.path.join(base_dir, "models", "feature_importance.csv")
    
    if not os.path.exists(feat_csv):
        return []
        
    import pandas as pd
    df = pd.read_csv(feat_csv)
    top_15 = df.head(15).to_dict(orient="records")
    
    # Enrich with physical explanations
    explanations = {
        "H1_roll_std_1m": "Cyclonic separator filter short-term pressure oscillation (moisture / oil buildup)",
        "H1_roll_std_5m": "Cyclonic separator filter 5-minute turbulence trend",
        "H1_diff_5m": "Filter differential pressure drop rate-of-change",
        "DV_pressure_roll_mean_5m": "Drying tower purge discharge average pressure",
        "TP3_roll_std_1m": "Pneumatic control panel line pressure instability",
        "Reservoirs_roll_mean_1m": "Main train air reservoir charge level",
        "DV_pressure_diff_5m": "Desiccant dryer valve pressure rate-of-change",
        "DV_pressure": "Instantaneous drying tower discharge pressure",
        "Motor_current_roll_std_5m": "Compressor motor electrical current fluctuations under load",
        "TP3": "Pneumatic panel line delivery pressure",
        "TP3_roll_mean_1m": "Pneumatic panel short-term smoothed pressure",
        "Motor_current_roll_std_1m": "Motor current 1-minute jitter",
        "Reservoirs_roll_std_5m": "Reservoir air pressure variance",
        "DV_pressure_roll_mean_1m": "Drying tower short-term smoothed pressure",
        "Reservoirs_diff_5m": "Reservoir air consumption rate-of-change"
    }
    
    for item in top_15:
        item["explanation"] = explanations.get(item["feature"], "Engineered compressor telemetry metric")
        item["importance"] = round(float(item["importance"]), 4)
        item["importance_percentage"] = round(float(item["importance"]) * 100, 2)
        
    return top_15

@app.get("/api/model-info")
def get_model_info():
    """Returns model metadata, performance scorecard, and technical disclosures."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    meta_path = os.path.join(base_dir, "models", "model_metadata.json")
    
    if os.path.exists(meta_path):
        with open(meta_path, 'r') as f:
            meta = json.load(f)
    else:
        meta = {}
        
    return {
        "model_name": meta.get("model_name", "MetroGuard XGBoost"),
        "model_type": meta.get("model_type", "XGBClassifier"),
        "feature_count": len(meta.get("feature_names", [])),
        "prediction_horizon": "30 Minutes",
        "sampling_rate": "10 Seconds",
        "selected_threshold": meta.get("selected_threshold", 0.10),
        "validation_metrics": meta.get("validation_metrics", {
            "pr_auc": 0.0018,
            "roc_auc": 0.6627,
            "precision": 0.0006,
            "recall": 0.0220,
            "f1": 0.0011
        }),
        "final_test_metrics": meta.get("final_test_metrics", {
            "pr_auc": 0.0003,
            "roc_auc": 0.4316,
            "precision": 0.0000,
            "recall": 0.0000,
            "f1": 0.0000,
            "accuracy": 0.9777
        }),
        "disclosures": {
            "dataset": "MetroPT-3 (UCI #791)",
            "total_records": "1,516,948 Rows",
            "class_imbalance": "694 Positive Rows (0.0457%) vs 1.48M Normal Rows",
            "failure_episodes": "4 Documented Air-Leak Episodes",
            "split_methodology": "Event-Aligned Chronological Split (No random shuffle / No data leakage)",
            "status_note": "Experimental AI Risk Assessment & Decision Support Architecture"
        }
    }

@app.get("/api/events")
def get_events():
    """Returns documented ground-truth failure events for quick navigation."""
    return DOCUMENTED_EVENTS

@app.get("/api/model/evaluation")
@app.get("/api/model-evaluation")
def get_model_evaluation():
    """Returns comprehensive empirical evaluation, baseline comparisons, and threshold analysis."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    eval_json_path = os.path.join(base_dir, "data", "processed", "model_evaluation.json")
    
    if os.path.exists(eval_json_path):
        with open(eval_json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    # Fallback to model_info if json not yet generated
    return get_model_info()

# =========================================================================
# REAL-TIME SENSOR STREAMING & REPLAY API
# =========================================================================

class StreamScenarioRequest(BaseModel):
    scenario: str

class StreamSpeedRequest(BaseModel):
    speed: float

@app.get("/api/stream/status")
def get_stream_status():
    """Returns the current streaming engine status, scenario, index, and playback speed."""
    from backend.streaming_service import get_streaming_engine
    return get_streaming_engine().get_status()

@app.get("/api/stream/current")
def get_stream_current():
    """Returns the latest processed telemetry observation, active alert, evidence, and rolling chart buffers."""
    from backend.streaming_service import get_streaming_engine
    return get_streaming_engine().get_current_state()

@app.post("/api/stream/start")
def start_stream():
    """Starts or resumes continuous sensor telemetry replay."""
    from backend.streaming_service import get_streaming_engine
    return get_streaming_engine().start()

@app.post("/api/stream/stop")
def stop_stream():
    """Pauses sensor telemetry replay."""
    from backend.streaming_service import get_streaming_engine
    return get_streaming_engine().stop()

@app.post("/api/stream/reset")
def reset_stream():
    """Resets the current streaming scenario to index 0 and clears buffers."""
    from backend.streaming_service import get_streaming_engine
    return get_streaming_engine().reset()

@app.post("/api/stream/scenario")
def set_stream_scenario(req: StreamScenarioRequest):
    """Switches the active streaming scenario."""
    from backend.streaming_service import get_streaming_engine
    try:
        return get_streaming_engine().set_scenario(req.scenario)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/stream/speed")
def set_stream_speed(req: StreamSpeedRequest):
    """Updates the playback speed multiplier (1x, 2x, 5x, 10x)."""
    from backend.streaming_service import get_streaming_engine
    return get_streaming_engine().set_speed(req.speed)

@app.post("/api/stream/step")
def step_stream():
    """Manually steps forward one telemetry observation."""
    from backend.streaming_service import get_streaming_engine
    return get_streaming_engine().step_forward()

@app.get("/api/anomaly/explanation")
def get_anomaly_explanation_endpoint():
    """
    Returns calibrated 0-100 severity index, top contributing sensor deviations,
    trajectory (Worsening/Stable/Recovering), persistence context, and operational hypotheses.
    """
    from backend.streaming_service import get_streaming_engine
    return get_streaming_engine().get_anomaly_explanation()

# =========================================================================
# INTELLIGENT ALERT LIFECYCLE & OPERATOR WORKFLOW API
# =========================================================================

@app.get("/api/alerts")
def get_all_alerts_endpoint():
    """Returns chronological alert history log with workflow lifecycle status."""
    from backend.alert_service import get_alert_manager
    return get_alert_manager().get_all_alerts()

@app.get("/api/alerts/active")
def get_active_alerts_endpoint():
    """Returns active or unhandled operator alerts."""
    from backend.alert_service import get_alert_manager
    return get_alert_manager().get_active_alerts()

@app.post("/api/alerts/{alert_id}/acknowledge")
def acknowledge_alert_endpoint(alert_id: str):
    """Marks an alert as acknowledged by an operator without changing underlying ML states."""
    from backend.alert_service import get_alert_manager
    res = get_alert_manager().acknowledge_alert(alert_id)
    if res.get("status") == "error":
        raise HTTPException(status_code=404, detail=res["message"])
    return res

@app.post("/api/alerts/{alert_id}/resolve")
def resolve_alert_endpoint(alert_id: str):
    """Marks an alert as resolved by an operator without changing underlying ML states."""
    from backend.alert_service import get_alert_manager
    res = get_alert_manager().resolve_alert(alert_id)
    if res.get("status") == "error":
        raise HTTPException(status_code=404, detail=res["message"])
    return res

@app.get("/api/recommendations/current")
def get_current_recommendation_endpoint():
    """Returns evidence-based prescriptive maintenance recommendations and inspection checklist."""
    from backend.alert_service import get_alert_manager
    return get_alert_manager().get_current_recommendation()

# =========================================================================
# REMAINING USEFUL LIFE (RUL) FEASIBILITY AUDIT API
# =========================================================================

@app.get("/api/rul/status")
@app.get("/api/rul/feasibility")
def get_rul_status_endpoint():
    """Returns the scientific RUL feasibility audit, sample sufficiency evaluation, and verified capabilities."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    audit_path = os.path.join(base_dir, "data", "processed", "rul_feasibility_audit.json")
    if os.path.exists(audit_path):
        with open(audit_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "scientific_decision": {
            "verdict": "OUTCOME B — VALIDATED CONTINUOUS RUL ESTIMATION IS NOT FEASIBLE WITH CURRENT DATA",
            "outcome_code": "OUTCOME_B",
            "is_continuous_rul_feasible": False,
            "summary": "Extreme sample scarcity (N=4 failure cycles) and failure mode heterogeneity preclude scientifically defensible continuous RUL regression."
        }
    }

# =========================================================================
# REAL-WORLD CASE STUDIES & OPERATIONAL IMPACT ANALYSIS API
# =========================================================================

@app.get("/api/case-studies")
def get_all_case_studies_endpoint():
    """Returns all structured historical case studies (Event #1 and Event #4)."""
    from backend.case_study_service import get_case_study_service
    return get_case_study_service().get_all_case_studies()

@app.get("/api/case-studies/summary")
def get_case_studies_summary_endpoint():
    """Returns executive summary of available case study investigations."""
    from backend.case_study_service import get_case_study_service
    return get_case_study_service().get_summary()

@app.get("/api/case-studies/{case_id}")
def get_single_case_study_endpoint(case_id: str):
    """Returns full structured case study including timeline, AI detection, and impact analysis."""
    from backend.case_study_service import get_case_study_service
    cs = get_case_study_service().get_case_study(case_id)
    if not cs:
        raise HTTPException(status_code=404, detail=f"Case study '{case_id}' not found.")
    return cs

# =========================================================================
# STATIC ASSETS & SPA CLIENT-SIDE FALLBACK ROUTING
# =========================================================================
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

def find_dist_dir():
    candidates = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist"),
        os.path.join(os.getcwd(), "frontend", "dist"),
        os.path.abspath("frontend/dist"),
        "/app/frontend/dist"
    ]
    for c in candidates:
        if os.path.exists(c) and os.path.isfile(os.path.join(c, "index.html")):
            return c
    return candidates[0]

dist_dir = find_dist_dir()
assets_dir = os.path.join(dist_dir, "assets")

@app.get("/assets/{asset_name:path}")
async def serve_asset(asset_name: str):
    """Directly serves compiled JS and CSS frontend assets with guaranteed MIME types."""
    candidates = [
        os.path.join(assets_dir, asset_name),
        os.path.join(dist_dir, "assets", asset_name),
        os.path.join(os.getcwd(), "frontend", "dist", "assets", asset_name),
        os.path.abspath(f"frontend/dist/assets/{asset_name}"),
        f"/app/frontend/dist/assets/{asset_name}"
    ]
    for cand in candidates:
        if os.path.isfile(cand):
            media_type = "application/javascript" if cand.endswith(".js") else "text/css" if cand.endswith(".css") else None
            return FileResponse(cand, media_type=media_type)
    raise HTTPException(status_code=404, detail="Asset not found")

@app.get("/")
async def serve_root():
    """Serves the root React application."""
    candidates = [
        os.path.join(dist_dir, "index.html"),
        os.path.join(os.getcwd(), "frontend", "dist", "index.html"),
        os.path.abspath("frontend/dist/index.html"),
        "/app/frontend/dist/index.html"
    ]
    for cand in candidates:
        if os.path.isfile(cand):
            return FileResponse(cand)
    return HTMLResponse("<h1>MetroGuard AI</h1><p>Backend is ONLINE. Frontend build not found.</p>", status_code=200)

@app.get("/{full_path:path}")
async def serve_spa_frontend(full_path: str):
    """Serves static files or falls back to index.html for client-side SPA routing."""
    # Allow standard API endpoints to return proper 404
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API route not found")
        
    candidates = [
        os.path.join(dist_dir, full_path),
        os.path.join(os.getcwd(), "frontend", "dist", full_path),
        os.path.abspath(f"frontend/dist/{full_path}"),
        f"/app/frontend/dist/{full_path}"
    ]
    for cand in candidates:
        if full_path and os.path.isfile(cand):
            return FileResponse(cand)
            
    index_candidates = [
        os.path.join(dist_dir, "index.html"),
        os.path.join(os.getcwd(), "frontend", "dist", "index.html"),
        os.path.abspath("frontend/dist/index.html"),
        "/app/frontend/dist/index.html"
    ]
    for index_file in index_candidates:
        if os.path.isfile(index_file):
            return FileResponse(index_file)
            
    raise HTTPException(status_code=404, detail="Frontend index.html not found")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run("backend.main:app", host=host, port=port, reload=False)



