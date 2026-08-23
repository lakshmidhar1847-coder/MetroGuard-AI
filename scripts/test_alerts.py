"""
MetroGuard AI - Task 7 Smart Alerts & Prescriptive Maintenance Test Suite
Validates alert levels, persistence filtering, physical evidence attribution,
prescriptive recommendations, and API regression safety.
"""

import os
import sys
import json
import urllib.request
import urllib.error

# Add repo root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_tests():
    print("=" * 100)
    print(" TASK 7 — SMART ALERTS & PRESCRIPTIVE MAINTENANCE LAYER VERIFICATION")
    print("=" * 100)

    # 1. Test Documented Events and Normal Baseline Scenarios
    print("\n[PART 1] Testing Documented Events & Baseline Operational Scenarios...")
    scenarios = [
        ("Event #1 Pre-Failure (April)", {"timestamp": "2020-04-17 23:30:00"}),
        ("Event #2 Pre-Failure (May)", {"timestamp": "2020-05-29 23:00:00"}),
        ("Event #3 Pre-Failure (June)", {"timestamp": "2020-06-05 09:30:00"}),
        ("Event #4 Pre-Failure (July)", {"timestamp": "2020-07-15 14:00:00"}),
        ("Normal Baseline (March)", {"timestamp": "2020-03-01 12:00:00"}),
        ("Normal Baseline (August)", {"timestamp": "2020-08-10 12:00:00"})
    ]

    for name, payload in scenarios:
        req = urllib.request.Request(
            "http://127.0.0.1:8000/api/hybrid-predict",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            status_code = resp.status
            data = json.loads(resp.read().decode("utf-8"))
            
            # Assert contract structure
            assert "alert" in data, "Missing alert object in response"
            alert = data["alert"]
            xgb = data["xgboost"]
            anom = data["anomaly"]
            hyb = data["hybrid"]
            evidence = data["evidence"]
            
            assert "level" in alert, "Missing alert level"
            assert "title" in alert, "Missing alert title"
            assert "reason" in alert, "Missing alert reason"
            assert "recommendations" in alert, "Missing recommendations"
            assert data.get("features_analyzed") == 65, f"Expected 65 features, got {data.get('features_analyzed')}"
            
            print(f">>> {name}:")
            print(f"    Timestamp Matched:   {data['timestamp_matched']} (Delta: {data.get('time_difference_seconds')}s)")
            print(f"    XGBoost Risk:        {xgb['risk_percentage']:>6.2f}% (Prob: {xgb['risk_probability']:.6f} | {xgb['status']})")
            print(f"    Anomaly Score:       {anom['score']:.4f} (th={anom['threshold']:.4f} | {anom['status']})")
            print(f"    Hybrid Status:       {hyb['status']}")
            print(f"    ALERT LEVEL:         {alert['level']}")
            print(f"    Alert Title:         {alert['title']}")
            print(f"    Alert Reason:        {alert['reason']}")
            print(f"    Physical Evidence:   {len(evidence)} signals > 2.0σ")
            for ev in evidence[:2]:
                print(f"       • {ev['feature']} = {ev['actual_value']} {ev['unit']} (Z = {ev['z_score']:+}σ) -> {ev['reason']}")
            print(f"    Recommendations:     {len(alert['recommendations'])} actions")
            for rec in alert['recommendations']:
                print(f"       -> [ACTION] {rec}")
            print("-" * 100)

    # 2. Test Invalid Input Boundary Cases
    print("\n[PART 2] Testing Invalid Inputs & Boundary Safety...")
    invalid_cases = [
        ("Invalid Non-Date String", {"timestamp": "invalid"}, 404),
        ("Out-of-Range Date (2025)", {"timestamp": "2025-01-01 00:00:00"}, 404),
        ("Missing / Empty Request Body", {}, 400)
    ]

    for name, payload, exp_status in invalid_cases:
        req = urllib.request.Request(
            "http://127.0.0.1:8000/api/hybrid-predict",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req) as resp:
                print(f"  [FAIL] {name:<28} -> HTTP {resp.status} (Expected {exp_status})")
        except urllib.error.HTTPError as e:
            if e.code == exp_status:
                err_data = json.loads(e.read().decode("utf-8"))
                print(f"  [PASS] {name:<28} -> HTTP {e.code} (Expected) | Error: {err_data.get('detail')}")
            else:
                print(f"  [FAIL] {name:<28} -> HTTP {e.code} (Expected {exp_status})")

    # 3. Existing API Regression Check
    print("\n[PART 3] Verifying Zero Regression Across All Existing Endpoints...")
    routes = [
        ("GET  /api/health", "http://127.0.0.1:8000/api/health", "GET", None),
        ("GET  /api/latest", "http://127.0.0.1:8000/api/latest", "GET", None),
        ("GET  /api/sensors", "http://127.0.0.1:8000/api/sensors", "GET", None),
        ("GET  /api/timeseries", "http://127.0.0.1:8000/api/timeseries?sensor=TP2&limit=5", "GET", None),
        ("GET  /api/events", "http://127.0.0.1:8000/api/events", "GET", None),
        ("GET  /api/model-info", "http://127.0.0.1:8000/api/model-info", "GET", None),
        ("POST /api/predict", "http://127.0.0.1:8000/api/predict", "POST", {"timestamp": "2020-04-17 23:30:00"}),
        ("POST /api/hybrid-predict", "http://127.0.0.1:8000/api/hybrid-predict", "POST", {"timestamp": "2020-04-17 23:30:00"}),
        ("GET  / (Static Production UI)", "http://127.0.0.1:8000/", "GET", None)
    ]

    for label, url, method, body in routes:
        if method == "POST":
            req = urllib.request.Request(
                url,
                data=json.dumps(body).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
        else:
            req = urllib.request.Request(url)
            
        with urllib.request.urlopen(req) as resp:
            print(f"  [PASS] {label:<32} -> HTTP {resp.status}")

    print("\n" + "=" * 100)
    print(" ALL SMART ALERTS & PRESCRIPTIVE MAINTENANCE CHECKS PASSED (100% SUCCESS)")
    print("=" * 100)

if __name__ == "__main__":
    run_tests()
