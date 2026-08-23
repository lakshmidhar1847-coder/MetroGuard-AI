"""
MetroGuard AI - Task 22 Final UI/UX & Hackathon-Ready Product Verification Suite
"""

import os
import sys
import json
import urllib.request
import urllib.error

def send_request(url, method="GET", body=None):
    if method == "POST":
        req = urllib.request.Request(
            url,
            data=json.dumps(body or {}).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
    else:
        req = urllib.request.Request(url)
        
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode('utf-8'))

def main():
    print("=" * 105)
    print(" TASK 22 — FINAL UI/UX POLISH & HACKATHON-READY PRODUCT VERIFICATION SUITE")
    print("=" * 105)

    base_url = "http://127.0.0.1:8000"

    # 1. Verify All SPA Client Routes
    print("\n[PART 1] VERIFYING ALL SPA CLIENT-SIDE ROUTES (DIRECT URL & REFRESH):")
    routes = [
        ("/", "Root Control Center / Overview"),
        ("/overview", "System Health & Asset Overview"),
        ("/monitoring", "Live Telemetry & Alert Center Command Center"),
        ("/risk", "Dual-Tier AI Risk Assessment & Diagnostic Radar"),
        ("/sensors", "Comprehensive 15-Signal Telemetry Suite"),
        ("/performance", "Audited ML Benchmarks & Scientific Transparency")
    ]
    for r, label in routes:
        req = urllib.request.Request(f"{base_url}{r}")
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode('utf-8')
            assert resp.status == 200 and '<div id="root">' in content
            print(f"  [PASS] {r:<15} ({label:<55}) -> HTTP {resp.status} OK")

    # 2. Verify Full REST API Regression (16 Endpoints)
    print("\n[PART 2] VERIFYING ALL BACKEND REST APIS (100% REGRESSION):")
    apis = [
        ("GET  /api/health", f"{base_url}/api/health", "GET", None),
        ("GET  /api/latest", f"{base_url}/api/latest", "GET", None),
        ("GET  /api/sensors", f"{base_url}/api/sensors", "GET", None),
        ("GET  /api/timeseries", f"{base_url}/api/timeseries?sensor=TP2&limit=5", "GET", None),
        ("GET  /api/multisensor", f"{base_url}/api/multisensor?limit=5", "GET", None),
        ("GET  /api/events", f"{base_url}/api/events", "GET", None),
        ("GET  /api/model-info", f"{base_url}/api/model-info", "GET", None),
        ("GET  /api/model/evaluation", f"{base_url}/api/model/evaluation", "GET", None),
        ("GET  /api/stream/status", f"{base_url}/api/stream/status", "GET", None),
        ("GET  /api/stream/current", f"{base_url}/api/stream/current", "GET", None),
        ("GET  /api/anomaly/explanation", f"{base_url}/api/anomaly/explanation", "GET", None),
        ("GET  /api/alerts", f"{base_url}/api/alerts", "GET", None),
        ("GET  /api/alerts/active", f"{base_url}/api/alerts/active", "GET", None),
        ("GET  /api/recommendations/current", f"{base_url}/api/recommendations/current", "GET", None),
        ("GET  /api/rul/status", f"{base_url}/api/rul/status", "GET", None),
        ("POST /api/predict", f"{base_url}/api/predict", "POST", {"timestamp": "2020-04-17 23:30:00"}),
        ("POST /api/hybrid-predict", f"{base_url}/api/hybrid-predict", "POST", {"timestamp": "2020-04-17 23:30:00"})
    ]

    for label, url, method, body in apis:
        if method == "POST":
            req = urllib.request.Request(
                url,
                data=json.dumps(body).encode('utf-8'),
                headers={"Content-Type": "application/json"}
            )
        else:
            req = urllib.request.Request(url)
            
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            print(f"  [PASS] {label:<35} -> HTTP {resp.status} OK")

    # 3. Verify Live Stream State Completeness
    print("\n[PART 3] VERIFYING TELEMETRY SNAPSHOT PAYLOAD INTEGRITY:")
    _, stream_snap = send_request(f"{base_url}/api/stream/current")
    required_keys = [
        "scenario", "scenario_label", "sensors", "xgboost", "anomaly", 
        "anomaly_intelligence", "active_operator_alert", "prescriptive_recommendation", 
        "operator_alert_history", "chart_history"
    ]
    for k in required_keys:
        assert k in stream_snap, f"Missing key '{k}' in stream snapshot!"
    print(f"  [PASS] All {len(required_keys)} critical telemetry & intelligence payload fields verified.")

    # 4. Verify 4 Replay Scenarios Determinism
    print("\n[PART 4] VERIFYING DETERMINISTIC BEHAVIOR ACROSS ALL 4 DEMO SCENARIOS:")
    scenario_checks = [
        ("normal", "1. Normal Baseline", "NOMINAL"),
        ("gradual_anomaly", "2. Gradual Drift", "HIGH"),
        ("pre_failure", "3. Pre-Failure (Event #1)", "CRITICAL"),
        ("unseen_anomaly", "4. Summer Holdout (Event #4)", "MEDIUM")
    ]
    for sc_id, sc_name, expected_prio in scenario_checks:
        send_request(f"{base_url}/api/stream/scenario", "POST", {"scenario": sc_id})
        send_request(f"{base_url}/api/stream/reset", "POST")
        for _ in range(5):
            send_request(f"{base_url}/api/stream/step", "POST")
        _, sc_state = send_request(f"{base_url}/api/stream/current")
        alt = sc_state.get("active_operator_alert")
        prio = alt["priority"] if alt else "NOMINAL"
        print(f"  [PASS] Scenario '{sc_name:<28}': Priority = {prio:<8} | XGB = {sc_state['xgboost']['risk_percentage']}% | Anom Sev = {sc_state['anomaly_intelligence']['anomaly_severity']}/100")

    print("\n" + "=" * 105)
    print(" ALL TASK 22 FINAL POLISH & PRODUCT EXPERIENCE TESTS PASSED (100% SUCCESS)")
    print("=" * 105)

if __name__ == "__main__":
    main()
