"""
MetroGuard AI - Task 23.1 Overview Page Regression & Safe Fix Verification Suite
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
    print(" TASK 23.1 — OVERVIEW PAGE REGRESSION DIAGNOSIS & SAFE FIX VERIFICATION SUITE")
    print("=" * 105)

    base_url = "http://127.0.0.1:8000"

    # 1. Test All SPA Routes (Direct Access & Refresh)
    print("\n[PART 1] VERIFYING ALL SPA CLIENT-SIDE ROUTES:")
    spa_routes = [
        ("/", "Root Route -> Overview Dashboard"),
        ("/overview", "Explicit Route -> Overview Dashboard"),
        ("/monitoring", "Live Monitoring & Alert Center Command Center"),
        ("/risk", "Dual-Tier AI Risk Assessment & Diagnostic Radar"),
        ("/sensors", "Comprehensive 15-Signal Telemetry Suite"),
        ("/performance", "Audited ML Benchmarks & Scientific Transparency"),
        ("/case-study", "Real-World Case Studies & Operational Impact"),
        ("/case-studies", "Alternative Plural Route -> Case Studies")
    ]

    for route, desc in spa_routes:
        req = urllib.request.Request(f"{base_url}{route}")
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode('utf-8')
            assert resp.status == 200 and '<div id="root">' in content, f"Route {route} failed to load SPA index.html!"
            print(f"  [PASS] {route:<18} ({desc:<55}) -> HTTP {resp.status} OK")

    # 2. Verify Overview Page API Dependencies
    print("\n[PART 2] VERIFYING OVERVIEW PAGE API DEPENDENCIES:")
    overview_apis = [
        ("GET  /api/health", f"{base_url}/api/health"),
        ("GET  /api/latest", f"{base_url}/api/latest"),
        ("GET  /api/sensors", f"{base_url}/api/sensors"),
        ("GET  /api/model-info", f"{base_url}/api/model-info"),
        ("GET  /api/case-studies", f"{base_url}/api/case-studies")
    ]

    for label, url in overview_apis:
        status, data = send_request(url)
        assert status == 200, f"Overview dependency {label} returned {status}"
        print(f"  [PASS] {label:<35} -> HTTP {status} OK")

    # 3. Verify Latest Reading Telemetry Payload for Overview
    print("\n[PART 3] VERIFYING REAL-TIME SENSOR TELEMETRY ON OVERVIEW:")
    status, latest = send_request(f"{base_url}/api/latest")
    assert "sensors" in latest and "prediction" in latest and "timestamp" in latest
    sensors = latest["sensors"]
    primary_keys = ['TP2', 'TP3', 'Reservoirs', 'Oil_temperature', 'Motor_current', 'DV_pressure']
    for pk in primary_keys:
        assert pk in sensors, f"Missing primary sensor '{pk}' in latest telemetry!"
    print(f"  [PASS] All 6 primary sensor cards populated ({', '.join(primary_keys)})")
    print(f"         • Timestamp: {latest['timestamp']}")
    print(f"         • Risk Estimate: {latest['prediction']['risk_percentage']}% ({latest['prediction']['status']})")

    # 4. Verify Case Studies Functionality Preserved
    print("\n[PART 4] VERIFYING CASE STUDY FUNCTIONALITY PRESERVED (TASK 23 COMPATIBILITY):")
    status, cases = send_request(f"{base_url}/api/case-studies")
    assert status == 200 and len(cases) == 2
    status, cs1 = send_request(f"{base_url}/api/case-studies/pre_failure_event_1")
    assert status == 200 and cs1["case_id"] == "pre_failure_event_1"
    status, cs2 = send_request(f"{base_url}/api/case-studies/summer_holdout_event_4")
    assert status == 200 and cs2["case_id"] == "summer_holdout_event_4"
    print(f"  [PASS] Case Study 1 (Event #1 Pneumatic) & Case Study 2 (Event #4 Summer Anomaly) fully operational.")

    # 5. Full REST API Regression (18 Endpoints)
    print("\n[PART 5] VERIFYING ALL BACKEND REST APIS (100% REGRESSION):")
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
        ("GET  /api/case-studies", f"{base_url}/api/case-studies", "GET", None),
        ("GET  /api/case-studies/summary", f"{base_url}/api/case-studies/summary", "GET", None),
        ("GET  /api/case-studies/pre_failure_event_1", f"{base_url}/api/case-studies/pre_failure_event_1", "GET", None),
        ("GET  /api/case-studies/summer_holdout_event_4", f"{base_url}/api/case-studies/summer_holdout_event_4", "GET", None),
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
            print(f"  [PASS] {label:<45} -> HTTP {resp.status} OK")

    print("\n" + "=" * 105)
    print(" ALL TASK 23.1 OVERVIEW PAGE REGRESSION TESTS PASSED (100% SUCCESS)")
    print("=" * 105)

if __name__ == "__main__":
    main()
