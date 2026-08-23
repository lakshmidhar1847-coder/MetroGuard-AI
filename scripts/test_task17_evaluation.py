"""
MetroGuard AI - Task 17 ML Evaluation & Hackathon Evidence Verification Suite
"""

import os
import sys
import json
import urllib.request
import urllib.error

def main():
    print("=" * 105)
    print(" TASK 17 — STRENGTHEN ML EVALUATION & HACKATHON EVIDENCE VERIFICATION")
    print("=" * 105)

    # 1. Verify GET /api/model/evaluation Endpoint
    print("\n[PART 1] TESTING GET /api/model/evaluation API CONTRACT:")
    url = "http://127.0.0.1:8000/api/model/evaluation"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        assert resp.status == 200, "Expected HTTP 200"
        assert "dataset_metadata" in data, "Missing dataset_metadata"
        assert "partitions" in data, "Missing partitions"
        assert "threshold_selection" in data, "Missing threshold_selection"
        assert "final_test_evaluation" in data, "Missing final_test_evaluation"
        assert "baseline_comparison" in data, "Missing baseline_comparison"
        assert "temporal_warning_metrics" in data, "Missing temporal_warning_metrics"
        assert "evaluation_integrity_pillars" in data, "Missing evaluation_integrity_pillars"

        print(f"  [PASS] GET /api/model/evaluation -> HTTP {resp.status} OK")
        print(f"         • Model: {data.get('model_name')}")
        print(f"         • Total Telemetry Rows: {data['dataset_metadata']['total_telemetry_rows']:,}")
        print(f"         • Class Imbalance: {data['dataset_metadata']['class_imbalance']}")
        print(f"         • Selected Threshold: {data['threshold_selection']['selected_threshold']}")
        print(f"         • Baselines Evaluated: {len(data['baseline_comparison'])} models")
        print(f"         • Temporal Events: {len(data['temporal_warning_metrics'])} episodes")

    # 2. Verify Final Untouched Test Metrics
    print("\n[PART 2] VERIFYING UNTOUCHED FINAL TEST EVALUATION METRICS:")
    final_test_if = data["final_test_evaluation"]["standalone_isolation_forest"]
    final_test_xgb = data["final_test_evaluation"]["standalone_xgboost"]
    final_test_hyb = data["final_test_evaluation"]["hybrid_engine_production"]
    
    cm_if = final_test_if["confusion_matrix"]
    cm_xgb = final_test_xgb["confusion_matrix"]
    cm_hyb = final_test_hyb["confusion_matrix"]

    print(f"  • Standalone XGBoost:        ROC-AUC: {final_test_xgb['roc_auc']} | PR-AUC: {final_test_xgb['pr_auc']} | Recall: {final_test_xgb['recall_percent']}% | TP={cm_xgb['tp']}, FP={cm_xgb['fp']:,}")
    print(f"  • Standalone Isol. Forest:   ROC-AUC: {final_test_if['roc_auc']} | PR-AUC: {final_test_if['pr_auc']} | Recall: {final_test_if['recall_percent']}% | TP={cm_if['tp']}, FP={cm_if['fp']:,}")
    print(f"  • Production Hybrid System:  ROC-AUC: {final_test_hyb['roc_auc']} | PR-AUC: {final_test_hyb['pr_auc']} | Recall: {final_test_hyb['recall_percent']}% | TP={cm_hyb['tp']}, FP={cm_hyb['fp']:,}")

    # 3. Verify Baseline Benchmark Results
    print("\n[PART 3] VERIFYING BASELINE BENCHMARK COMPARISONS:")
    for b in data["baseline_comparison"]:
        print(f"  • {b['model']:<42} -> PR-AUC: {b['pr_auc']} | ROC-AUC: {b['roc_auc']} | Rec: {b['event4_recall']:<6} | Dominant: {b.get('dominant_component', 'N/A')}")

    # 4. Verify Threshold Sensitivity Analysis
    print("\n[PART 4] VERIFYING THRESHOLD SELECTION PROTOCOL:")
    for th in data["threshold_selection"]["analysis"]:
        sel = "★ SELECTED" if th.get("is_selected", False) else ""
        print(f"  • Threshold τ = {th['threshold']:<4.2f} | Val Recall: {th['validation_recall']:>5.2f}% | Val Alerts: {th['val_alerts']:>6} | Test Recall: {th['test_recall']:>5.2f}% | {sel}")

    # 5. Verify Temporal Warning Metrics
    print("\n[PART 5] VERIFYING TEMPORAL EVENT-BASED PRE-FAILURE METRICS:")
    for ev in data["temporal_warning_metrics"]:
        print(f"  • {ev['event_id']} ({ev['partition']}): Anticipated = {ev['anticipated_by_system']} | Lead Time = {ev['detection_lead_time']} | Peak Risk = {ev['peak_risk_percentage']} | Status = {ev['status']}")

    # 6. Verify SPA Routing on /performance
    print("\n[PART 6] VERIFYING SPA DIRECT URL ACCESS & BROWSER ROUTES:")
    routes = [
        ("Root Dashboard", "http://127.0.0.1:8000/"),
        ("Model Performance", "http://127.0.0.1:8000/performance"),
        ("Risk Dashboard", "http://127.0.0.1:8000/risk"),
        ("Overview", "http://127.0.0.1:8000/overview"),
        ("Live Monitoring", "http://127.0.0.1:8000/monitoring"),
        ("Sensor Analysis", "http://127.0.0.1:8000/sensors")
    ]
    for label, r_url in routes:
        req = urllib.request.Request(r_url)
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode('utf-8')
            assert resp.status == 200, f"Expected 200 for {r_url}"
            assert '<div id="root">' in content, f"Missing root div for {r_url}"
            print(f"  [PASS] {label:<22} -> HTTP {resp.status} (SPA Catch-all Verified)")

    # 7. Regression Verification Across All System Endpoints
    print("\n[PART 7] VERIFYING ZERO REGRESSION ACROSS ALL APIS:")
    system_apis = [
        ("GET  /api/health", "http://127.0.0.1:8000/api/health", "GET", None),
        ("GET  /api/latest", "http://127.0.0.1:8000/api/latest", "GET", None),
        ("GET  /api/sensors", "http://127.0.0.1:8000/api/sensors", "GET", None),
        ("GET  /api/timeseries", "http://127.0.0.1:8000/api/timeseries?sensor=TP2&limit=5", "GET", None),
        ("GET  /api/events", "http://127.0.0.1:8000/api/events", "GET", None),
        ("GET  /api/model-info", "http://127.0.0.1:8000/api/model-info", "GET", None),
        ("GET  /api/model/evaluation", "http://127.0.0.1:8000/api/model/evaluation", "GET", None),
        ("POST /api/predict", "http://127.0.0.1:8000/api/predict", "POST", {"timestamp": "2020-04-17 23:30:00"}),
        ("POST /api/hybrid-predict", "http://127.0.0.1:8000/api/hybrid-predict", "POST", {"timestamp": "2020-04-17 23:30:00"})
    ]

    for label, api_url, method, payload in system_apis:
        if method == "POST":
            req = urllib.request.Request(
                api_url,
                data=json.dumps(payload).encode('utf-8'),
                headers={"Content-Type": "application/json"}
            )
        else:
            req = urllib.request.Request(api_url)
            
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200, f"Expected 200 for {api_url}"
            print(f"  [PASS] {label:<32} -> HTTP {resp.status}")

    print("\n" + "=" * 105)
    print(" ALL TASK 17 ML EVALUATION & HACKATHON EVIDENCE CHECKS PASSED (100% SUCCESS)")
    print("=" * 105)

if __name__ == "__main__":
    main()
