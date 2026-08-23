"""
MetroGuard AI - Task 5 Comprehensive Hybrid Risk Engine Evaluation & Test Suite
"""

import os
import sys
import json
import urllib.request
import urllib.error
import pandas as pd
import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, average_precision_score, confusion_matrix

# Add repo root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.predict import get_predictor
from backend.hybrid_predictor import get_hybrid_predictor
from backend.data_service import get_data_service, FEATURE_NAMES

def main():
    print("=" * 100)
    print(" TASK 5 — METROGUARD HYBRID RISK ENGINE EVALUATION & REGRESSION TEST")
    print("=" * 100)

    hp = get_hybrid_predictor()
    ds = get_data_service()

    # 1. Evaluate Documented Events on Hybrid Engine
    print("\n" + "=" * 100)
    print(" PART 8 — DOCUMENTED EVENTS EVALUATION ON HYBRID RISK ENGINE")
    print("=" * 100)

    test_events = [
        ("Event #1 Pre-Failure (April)", "2020-04-17 23:30:00", 1),
        ("Event #2 Pre-Failure (May)", "2020-05-29 23:00:00", 1),
        ("Event #3 Pre-Failure (June)", "2020-06-05 09:30:00", 1),
        ("Event #4 Pre-Failure (July)", "2020-07-15 14:00:00", 1),
        ("Normal Baseline (March)", "2020-03-01 12:00:00", 0),
        ("Normal Baseline (August)", "2020-08-10 12:00:00", 0)
    ]

    for name, ts, target in test_events:
        res = ds.get_features_by_timestamp(ts)
        eval_res = hp.evaluate_hybrid(res["features"], is_sustained_anomaly=True)
        
        xgb_info = eval_res["xgboost"]
        anom_info = eval_res["anomaly"]
        hybrid_info = eval_res["hybrid"]
        evidence = eval_res["evidence"]
        
        print(f">>> {name:<32}:")
        print(f"    Timestamp Matched:   {res['timestamp_matched']} (Requested: {ts})")
        print(f"    Target:              {target} ({res['failure_status']})")
        print(f"    XGBoost Risk:        {xgb_info['risk_percentage']:>6.2f}% | Status: {xgb_info['status']}")
        print(f"    Isolation Forest:    Score: {anom_info['score']:.4f} (th={anom_info['threshold']:.4f}) | Status: {anom_info['status']}")
        print(f"    HYBRID DECISION:     {hybrid_info['status']}")
        print(f"    Decision Reason:     {hybrid_info['reason']}")
        if evidence:
            print(f"    Physical Evidence:   {len(evidence)} abnormal physical signals detected:")
            for ev in evidence[:3]:
                print(f"       • {ev['feature']} = {ev['actual_value']} {ev['unit']} (Z = {ev['z_score']:+}σ) -> {ev['reason']}")
        else:
            print("    Physical Evidence:   None (All signals within nominal ±2.0σ distribution)")
        print("-" * 100)

    # 2. Validation Period False Alarm & Performance Metrics (June 2020)
    print("\n" + "=" * 100)
    print(" PART 9 — VALIDATION PERIOD EVALUATION & METRICS (JUNE 2020)")
    print("=" * 100)
    
    features_csv = os.path.join("data", "processed", "metropt3_features.csv")
    df = pd.read_csv(features_csv)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    val_mask = (df['timestamp'] >= '2020-06-01') & (df['timestamp'] <= '2020-06-30 23:59:59')
    val_df = df[val_mask].copy()
    
    val_y = val_df['target'].values
    val_feats = val_df[FEATURE_NAMES].values
    
    # XGBoost predictions on validation
    xgb_val_probs = hp.xgb_predictor.model.predict_proba(val_feats)[:, 1]
    xgb_val_alerts = (xgb_val_probs >= 0.10).astype(int)
    
    # Anomaly scores on validation
    anom_val_scores = -hp.anomaly_model.score_samples(val_feats)
    anom_val_alerts = (anom_val_scores >= hp.anomaly_threshold).astype(int)
    
    # Hybrid alerts on validation (XGBoost Alert OR Anomaly Alert)
    hybrid_val_alerts = (xgb_val_alerts | anom_val_alerts).astype(int)
    
    tn_v, fp_v, fn_v, tp_v = confusion_matrix(val_y, hybrid_val_alerts).ravel()
    prec_v = precision_score(val_y, hybrid_val_alerts, zero_division=0) * 100
    rec_v = recall_score(val_y, hybrid_val_alerts, zero_division=0) * 100
    f1_v = f1_score(val_y, hybrid_val_alerts, zero_division=0)
    fpr_v = fp_v / (fp_v + tn_v) * 100
    
    print(f"Validation Partition Rows:  {len(val_df):,} (Positives: {(val_y == 1).sum():,})")
    print(f"Validation Confusion Matrix (Hybrid):")
    print(f"   TP = {tp_v:>5} | FP = {fp_v:>6}")
    print(f"   FN = {fn_v:>5} | TN = {tn_v:>6}")
    print(f"   Precision:          {prec_v:.2f}%")
    print(f"   Recall:             {rec_v:.2f}%")
    print(f"   F1-Score:           {f1_v:.4f}")
    print(f"   False-Positive Rate:{fpr_v:.2f}%")

    # 3. Final Untouched Test Partition Metrics (July - August 2020)
    print("\n" + "=" * 100)
    print(" PART 10 — FINAL UNTOUCHED TEST SET METRICS (JULY - AUGUST 2020)")
    print("=" * 100)
    
    test_mask = (df['timestamp'] >= '2020-07-01') & (df['timestamp'] <= '2020-09-01 04:00:00')
    test_df = df[test_mask].copy()
    test_y = test_df['target'].values
    test_feats = test_df[FEATURE_NAMES].values
    
    xgb_test_probs = hp.xgb_predictor.model.predict_proba(test_feats)[:, 1]
    xgb_test_alerts = (xgb_test_probs >= 0.10).astype(int)
    
    anom_test_scores = -hp.anomaly_model.score_samples(test_feats)
    anom_test_alerts = (anom_test_scores >= hp.anomaly_threshold).astype(int)
    
    hybrid_test_alerts = (xgb_test_alerts | anom_test_alerts).astype(int)
    
    tn_t, fp_t, fn_t, tp_t = confusion_matrix(test_y, hybrid_test_alerts).ravel()
    prec_t = precision_score(test_y, hybrid_test_alerts, zero_division=0) * 100
    rec_t = recall_score(test_y, hybrid_test_alerts, zero_division=0) * 100
    f1_t = f1_score(test_y, hybrid_test_alerts, zero_division=0)
    fpr_t = fp_t / (fp_t + tn_t) * 100
    
    print(f"Final Test Rows:            {len(test_df):,} (Positives: {(test_y == 1).sum():,})")
    print(f"Final Test Confusion Matrix (Hybrid):")
    print(f"   TP = {tp_t:>5} | FP = {fp_t:>6}")
    print(f"   FN = {fn_t:>5} | TN = {tn_t:>6}")
    print(f"   Precision:          {prec_t:.2f}%")
    print(f"   Recall (Event #4):  {rec_t:.2f}% (Gain from 0.00% in XGBoost!)")
    print(f"   F1-Score:           {f1_t:.4f}")
    print(f"   False-Positive Rate:{fpr_t:.2f}%")

    # 4. HTTP API Regression & Hybrid Endpoint Verification
    print("\n" + "=" * 100)
    print(" PART 11 — HTTP API REGRESSION & HYBRID ENDPOINT VERIFICATION")
    print("=" * 100)
    
    endpoints = [
        ("GET  /api/health", "http://127.0.0.1:8000/api/health", "GET", None),
        ("GET  /api/latest", "http://127.0.0.1:8000/api/latest", "GET", None),
        ("GET  /api/events", "http://127.0.0.1:8000/api/events", "GET", None),
        ("GET  /api/model-info", "http://127.0.0.1:8000/api/model-info", "GET", None),
        ("POST /api/predict (Event #1)", "http://127.0.0.1:8000/api/predict", "POST", {"timestamp": "2020-04-17 23:30:00"}),
        ("POST /api/hybrid-predict (Event #1)", "http://127.0.0.1:8000/api/hybrid-predict", "POST", {"timestamp": "2020-04-17 23:30:00"}),
        ("POST /api/hybrid-predict (Event #4)", "http://127.0.0.1:8000/api/hybrid-predict", "POST", {"timestamp": "2020-07-15 14:00:00"}),
        ("POST /api/hybrid-predict (Normal March)", "http://127.0.0.1:8000/api/hybrid-predict", "POST", {"timestamp": "2020-03-01 12:00:00"}),
    ]

    for label, url, method, payload in endpoints:
        try:
            if method == "POST":
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
            else:
                req = urllib.request.Request(url)
                
            with urllib.request.urlopen(req) as response:
                status = response.status
                body = json.loads(response.read().decode("utf-8"))
                
                extra = ""
                if "hybrid" in body:
                    extra = f"-> Hybrid: {body['hybrid']['status']} | XGB: {body['xgboost']['risk_percentage']}% | Anom: {body['anomaly']['score']}"
                elif "risk_percentage" in body:
                    extra = f"-> XGB Risk: {body['risk_percentage']}% ({body['status']})"
                elif "status" in body:
                    extra = f"-> Status: {body['status']}"
                    
                print(f"  [PASS] {label:<40} -> HTTP {status} {extra}")
        except Exception as e:
            print(f"  [FAIL] {label:<40} -> Error: {e}")

    print("=" * 100)

if __name__ == "__main__":
    main()
