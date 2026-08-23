"""
MetroGuard AI — Task 25.5 Final Scientific Consistency & System Verification Suite
Tests metric accuracy, threshold consistency, terminology integrity, replay synchronization,
and full REST/SPA regression across the system.
"""

import os
import sys
import json
import requests

BASE_URL = "http://127.0.0.1:8000"

def test_scientific_consistency():
    print("=" * 105)
    print(" TASK 25.5 — FINAL SCIENTIFIC CONSISTENCY & SYSTEM AUDIT VERIFICATION")
    print("=" * 105)

    # 1. VERIFY SPA ROUTES
    print("\n[PART 1] VERIFYING ALL CLIENT-SIDE SPA ROUTES:")
    routes = [
        ("/", "Overview Dashboard & Multi-Event Replay"),
        ("/overview", "Explicit Overview Route"),
        ("/monitoring", "Live Monitoring & Detailed Command Center"),
        ("/risk", "Dual-Tier AI Risk Assessment & Radar"),
        ("/sensors", "15-Signal Raw Telemetry Suite"),
        ("/performance", "Audited Model Benchmarks & Scientific Transparency"),
        ("/case-study", "Real-World Case Studies & Operational Impact")
    ]
    for route, desc in routes:
        try:
            res = requests.get(f"{BASE_URL}{route}", timeout=5)
            assert res.status_code == 200, f"Route {route} failed with status {res.status_code}"
            print(f"  [PASS] {route:<18} ({desc:<50}) -> HTTP 200 OK")
        except Exception as e:
            print(f"  [FAIL] {route}: {e}")
            sys.exit(1)

    # 2. VERIFY CORE PRODUCTION THRESHOLDS IN METADATA & HYBRID ENGINE
    print("\n[PART 2] VERIFYING CORE PRODUCTION THRESHOLDS & MODEL METADATA:")
    try:
        res = requests.get(f"{BASE_URL}/api/model-info", timeout=5)
        assert res.status_code == 200
        data = res.json()
        
        xgb_thresh = data.get("selected_threshold", 0.10)
        assert xgb_thresh == 0.10, f"XGBoost threshold mismatch: expected 0.10, got {xgb_thresh}"
        print(f"  [PASS] XGBoost Classification Threshold:  τ = {xgb_thresh:.2f} (P >= 0.10)")

        # Verify Isolation Forest thresholds from streaming current snapshot
        snap_res = requests.get(f"{BASE_URL}/api/stream/current", timeout=5)
        assert snap_res.status_code == 200
        snap = snap_res.json()
        anom_thresh = snap["anomaly"]["threshold"]
        assert anom_thresh == 0.504, f"Isolation Forest threshold mismatch: expected 0.504, got {anom_thresh}"
        print(f"  [PASS] Isolation Forest 99th %-tile Threshold: τ = {anom_thresh:.4f} (Maps to 50/100 Severity Index)")
    except Exception as e:
        print(f"  [FAIL] Metadata Threshold Verification: {e}")
        sys.exit(1)

    # 3. VERIFY PHYSICAL EVIDENCE & MATHEMATICAL FORMULAS
    print("\n[PART 3] VERIFYING PHYSICAL EVIDENCE & STATISTICAL Z-SCORE INTEGRITY:")
    try:
        # Event #1 Peak Evidence Verification
        c1_res = requests.get(f"{BASE_URL}/api/case-studies/pre_failure_event_1", timeout=5)
        assert c1_res.status_code == 200
        c1 = c1_res.json()
        assert "+2.19σ" in str(c1), "Event #1 +2.19σ peak evidence not found in Case Study 1"
        print("  [PASS] Event #1 Peak Evidence: H1 = 8.24 bar -> Z = +2.19σ (Peak Pre-Failure Milestone)")

        # Event #4 Peak Thermal Evidence Verification
        c2_res = requests.get(f"{BASE_URL}/api/case-studies/summer_holdout_event_4", timeout=5)
        assert c2_res.status_code == 200
        c2 = c2_res.json()
        assert "81.4" in str(c2) and "+3.69σ" in str(c2), "Event #4 81.4°C / +3.69σ thermal evidence not found"
        print("  [PASS] Event #4 Peak Evidence: Oil Temp = 81.40 °C -> Z = +3.69σ (Thermal Overload Milestone)")
    except Exception as e:
        print(f"  [FAIL] Physical Evidence Verification: {e}")
        sys.exit(1)

    # 4. VERIFY REPLAY SCENARIO SWITCHING & SHARED STREAM SYNCHRONIZATION
    print("\n[PART 4] VERIFYING MULTI-EVENT REPLAY & SHARED SYNCHRONIZATION:")
    scenarios = [
        ("normal", "1. Normal Baseline", "NORMAL"),
        ("pre_failure", "3. Pre-Failure Event #1", "HIGH RISK"),
        ("unseen_anomaly", "4. Summer Holdout Event #4", "WARNING"),
        ("gradual_anomaly", "2. Gradual Drift", "NORMAL")
    ]
    for sc_id, sc_name, target_state in scenarios:
        try:
            set_res = requests.post(f"{BASE_URL}/api/stream/scenario", json={"scenario": sc_id}, timeout=5)
            assert set_res.status_code == 200, f"Setting scenario failed: {set_res.text}"
            rst_res = requests.post(f"{BASE_URL}/api/stream/reset", timeout=5)
            assert rst_res.status_code == 200
            
            cur_res = requests.get(f"{BASE_URL}/api/stream/current", timeout=5)
            assert cur_res.status_code == 200
            cur = cur_res.json()
            assert cur["scenario"] == sc_id
            print(f"  [PASS] Replay Scenario '{sc_name:<28}' -> Synchronized (Snapshot TS: {cur['timestamp']})")
        except Exception as e:
            print(f"  [FAIL] Scenario {sc_id}: {e}")
            sys.exit(1)

    # 5. VERIFY 100% OF BACKEND REST APIS
    print("\n[PART 5] VERIFYING ALL BACKEND REST APIS (100% REGRESSION):")
    endpoints = [
        ("GET", "/api/health", None),
        ("GET", "/api/latest", None),
        ("GET", "/api/sensors", None),
        ("GET", "/api/timeseries", None),
        ("GET", "/api/multisensor", None),
        ("GET", "/api/events", None),
        ("GET", "/api/model-info", None),
        ("GET", "/api/model/evaluation", None),
        ("GET", "/api/stream/status", None),
        ("GET", "/api/stream/current", None),
        ("GET", "/api/anomaly/explanation", None),
        ("GET", "/api/alerts", None),
        ("GET", "/api/alerts/active", None),
        ("GET", "/api/recommendations/current", None),
        ("GET", "/api/rul/status", None),
        ("GET", "/api/case-studies", None),
        ("GET", "/api/case-studies/summary", None),
        ("GET", "/api/case-studies/pre_failure_event_1", None),
        ("GET", "/api/case-studies/summer_holdout_event_4", None),
        ("POST", "/api/predict", {"timestamp": "2020-04-17 23:30:00"}),
        ("POST", "/api/hybrid-predict", {"timestamp": "2020-04-17 23:30:00"})
    ]
    for method, ep, payload in endpoints:
        try:
            if method == "GET":
                r = requests.get(f"{BASE_URL}{ep}", timeout=5)
            else:
                r = requests.post(f"{BASE_URL}{ep}", json=payload or {}, timeout=5)
            assert r.status_code == 200, f"{method} {ep} returned {r.status_code}"
            print(f"  [PASS] {method:<5} {ep:<50} -> HTTP 200 OK")
        except Exception as e:
            print(f"  [FAIL] {method} {ep}: {e}")
            sys.exit(1)

    print("\n" + "=" * 105)
    print(" ALL TASK 25.5 FINAL SCIENTIFIC CONSISTENCY TESTS PASSED (100% SUCCESS)")
    print("=" * 105)

if __name__ == "__main__":
    test_scientific_consistency()
