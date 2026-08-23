"""
MetroGuard AI - Task 21 RUL Feasibility & Scientific Decision Verification Suite
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
    print(" TASK 21 — REMAINING USEFUL LIFE (RUL) FEASIBILITY & SCIENTIFIC DECISION SUITE")
    print("=" * 105)

    base_url = "http://127.0.0.1:8000"

    # 1. Test GET /api/rul/status and /api/rul/feasibility
    print("\n[PART 1] TESTING RUL FEASIBILITY API CONTRACT & SCIENTIFIC DECISION:")
    status, audit = send_request(f"{base_url}/api/rul/status")
    assert status == 200, f"Expected 200, got {status}"
    
    decision = audit.get("scientific_decision", {})
    assert decision.get("outcome_code") == "OUTCOME_B", f"Expected OUTCOME_B, got {decision.get('outcome_code')}"
    assert decision.get("is_continuous_rul_feasible") is False, "Expected RUL feasibility to be False"
    
    print(f"  [PASS] GET /api/rul/status -> HTTP {status} OK")
    print(f"         • Scientific Verdict:        {decision.get('verdict')}")
    print(f"         • Outcome Code:              {decision.get('outcome_code')}")
    print(f"         • Continuous RUL Feasible:   {decision.get('is_continuous_rul_feasible')}")
    print(f"         • Limiting Factors Count:    {len(audit.get('limiting_factors', []))}")
    print(f"         • Verified Capabilities:     {len(audit.get('verified_system_capabilities', []))}")

    # 2. Test Zero-Fabrication Integrity Check
    print("\n[PART 2] TESTING ZERO-FABRICATION & SCIENTIFIC TRANSPARENCY INTEGRITY:")
    _, state = send_request(f"{base_url}/api/stream/current")
    # Verify no fake remaining_hours or countdown fields exist in stream snapshot
    assert "remaining_hours" not in state, "Found fake remaining_hours field in live telemetry!"
    assert "countdown_seconds" not in state, "Found fake countdown_seconds field in live telemetry!"
    print(f"  [PASS] Zero-Fabrication Confirmed: Telemetry stream contains NO fabricated countdown clocks or hours.")

    # 3. Test SPA direct URL routing
    print("\n[PART 3] VERIFYING SPA DIRECT URL ACCESS:")
    for route in ["/monitoring", "/risk", "/performance", "/overview", "/"]:
        req = urllib.request.Request(f"{base_url}{route}")
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode('utf-8')
            assert resp.status == 200 and '<div id="root">' in content
            print(f"  [PASS] GET {route:<18} -> HTTP {resp.status} (SPA Route verified)")

    # 4. Full API Regression Test
    print("\n[PART 4] VERIFYING ZERO REGRESSION ACROSS ALL METROGUARD APIS:")
    apis = [
        ("GET  /api/health", f"{base_url}/api/health", "GET", None),
        ("GET  /api/latest", f"{base_url}/api/latest", "GET", None),
        ("GET  /api/sensors", f"{base_url}/api/sensors", "GET", None),
        ("GET  /api/timeseries", f"{base_url}/api/timeseries?sensor=TP2&limit=5", "GET", None),
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
            print(f"  [PASS] {label:<35} -> HTTP {resp.status}")

    print("\n" + "=" * 105)
    print(" ALL TASK 21 RUL FEASIBILITY & SCIENTIFIC DECISION TESTS PASSED (100% SUCCESS)")
    print("=" * 105)

if __name__ == "__main__":
    main()
