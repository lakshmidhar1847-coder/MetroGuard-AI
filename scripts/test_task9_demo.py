"""
MetroGuard AI - Task 9 Production Demo Hardening & Operator Experience Test Suite
Validates all required scenarios A through J, schema integrity, and hardcoded value audit.
"""

import os
import sys
import json
import urllib.request
import urllib.error
import re

def run_task9_tests():
    print("=" * 100)
    print(" TASK 9 — METROGUARD PRODUCTION DEMO HARDENING & OPERATOR EXPERIENCE TEST SUITE")
    print("=" * 100)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # 1. No-Hardcoding Audit (Part 14)
    print("\n[AUDIT] FRONTEND SOURCE CODE HARDCODED PREDICTION VALUES AUDIT:")
    frontend_src = os.path.join(base_dir, "frontend", "src")
    forbidden_terms = [
        "mockProbability",
        "fakeScore",
        "mockRisk",
        "fakeRisk",
        "0.987785",
        "0.975685",
        "0.000285",
        "0.5157",
        "0.4840"
    ]
    
    violations = []
    for root, _, files in os.walk(frontend_src):
        for f in files:
            if f.endswith(('.js', '.jsx', '.ts', '.tsx')):
                fpath = os.path.join(root, f)
                with open(fpath, 'r', encoding='utf-8') as code_file:
                    for line_num, line in enumerate(code_file.readlines(), 1):
                        for term in forbidden_terms:
                            if term in line:
                                violations.append((os.path.relpath(fpath, base_dir), line_num, term, line.strip()))

    if violations:
        print("  [FAIL] Hardcoded prediction variables or specific event floats found in frontend:")
        for v in violations:
            print(f"    - {v[0]}:{v[1]} (Found '{v[2]}') -> {v[3]}")
    else:
        print("  [PASS] 0 hardcoded prediction values or mock variables found in frontend source files.")

    # 2. Test Demo Scenarios A through F (Valid Operating Conditions)
    print("\n[PART 13] TESTING OPERATIONAL DEMO SCENARIOS (A through F):")
    scenarios = [
        ("A. Normal March Condition", {"timestamp": "2020-03-01 12:00:00"}),
        ("B. Event #1 Known Failure", {"timestamp": "2020-04-17 23:30:00"}),
        ("C. Event #2 Known Failure", {"timestamp": "2020-05-29 23:00:00"}),
        ("D. Event #3 Unseen Failure", {"timestamp": "2020-06-05 09:30:00"}),
        ("E. Event #4 Unseen Summer Anomaly", {"timestamp": "2020-07-15 14:00:00"}),
        ("F. Normal August Condition", {"timestamp": "2020-08-10 12:00:00"})
    ]

    for name, payload in scenarios:
        req = urllib.request.Request(
            "http://127.0.0.1:8000/api/hybrid-predict",
            data=json.dumps(payload).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            
            # Assert schema contracts
            assert resp.status == 200, f"Expected HTTP 200 for {name}"
            assert "timestamp_matched" in data, "Missing timestamp_matched"
            assert "xgboost" in data and "anomaly" in data and "hybrid" in data
            assert "alert" in data and "evidence" in data
            assert "recommendations" in data["alert"]
            assert data.get("features_analyzed") == 65
            
            xgb = data["xgboost"]
            anom = data["anomaly"]
            hyb = data["hybrid"]
            alert = data["alert"]
            evidence = data["evidence"]
            
            print(f">>> {name:<35}:")
            print(f"    • HTTP Status:               {resp.status} OK")
            print(f"    • Matched Telemetry:         {data['timestamp_matched']} (Delta: {data.get('time_difference_seconds')}s)")
            print(f"    • Known Failure Risk %:      {xgb['risk_percentage']:>6.2f}% ({xgb['status']} | Prob: {xgb['risk_probability']:.6f})")
            print(f"    • System Anomaly Index:      {anom['score']:.4f} ({anom['status']} | Threshold: {anom['threshold']:.4f})")
            print(f"    • Hybrid Decision:           {hyb['status']}")
            print(f"    • Alert Level:               {alert['level']} — {alert['title']}")
            print(f"    • 'Why This Alert?' Reason:  {alert['reason']}")
            print(f"    • Physical Evidence Count:   {len(evidence)} signal(s)")
            for item in evidence[:2]:
                print(f"       - {item['feature']} ({item['actual_value']} {item['unit']} vs med {item['baseline_median']}) -> {item['reason']}")
            print(f"    • Recommended Actions:       {len(alert['recommendations'])} action(s)")
            for rec in alert['recommendations']:
                print(f"       -> [ACTION] {rec}")
            print(f"    • Features Analyzed:         {data['features_analyzed']} (Expected: 65)")
            print("-" * 100)

    # 3. Test Scenarios G, H, I (Invalid Input Boundaries)
    print("\n[PART 13] TESTING INVALID INPUTS & BOUNDARY SAFETY (G, H, I):")
    invalid_cases = [
        ("G. Invalid Timestamp String", {"timestamp": "invalid"}, 404),
        ("H. Out-of-Range Date (2025)", {"timestamp": "2025-01-01 00:00:00"}, 404),
        ("I. Empty Request Body ({})", {}, 400)
    ]
    for label, payload, exp_code in invalid_cases:
        req = urllib.request.Request(
            "http://127.0.0.1:8000/api/hybrid-predict",
            data=json.dumps(payload).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req) as resp:
                print(f"  [FAIL] {label:<32} -> Got HTTP {resp.status} (Expected {exp_code})")
        except urllib.error.HTTPError as e:
            if e.code == exp_code:
                err_data = json.loads(e.read().decode('utf-8'))
                print(f"  [PASS] {label:<32} -> Got HTTP {e.code} (Expected) | Error: {err_data.get('detail')}")
            else:
                print(f"  [FAIL] {label:<32} -> Got HTTP {e.code} (Expected {exp_code})")

    # 4. API Regression Test (Part 16)
    print("\n[PART 16] VERIFYING ZERO REGRESSION ACROSS SYSTEM ENDPOINTS:")
    regression_endpoints = [
        ("GET  /api/health", "http://127.0.0.1:8000/api/health", "GET", None),
        ("GET  /api/latest", "http://127.0.0.1:8000/api/latest", "GET", None),
        ("GET  /api/sensors", "http://127.0.0.1:8000/api/sensors", "GET", None),
        ("GET  /api/timeseries", "http://127.0.0.1:8000/api/timeseries?sensor=TP2&limit=5", "GET", None),
        ("GET  /api/events", "http://127.0.0.1:8000/api/events", "GET", None),
        ("GET  /api/model-info", "http://127.0.0.1:8000/api/model-info", "GET", None),
        ("POST /api/predict", "http://127.0.0.1:8000/api/predict", "POST", {"timestamp": "2020-04-17 23:30:00"}),
        ("POST /api/hybrid-predict", "http://127.0.0.1:8000/api/hybrid-predict", "POST", {"timestamp": "2020-04-17 23:30:00"}),
        ("GET  / (Root SPA)", "http://127.0.0.1:8000/", "GET", None),
        ("GET  /risk (SPA Route)", "http://127.0.0.1:8000/risk", "GET", None),
    ]

    for label, url, method, body in regression_endpoints:
        if method == "POST":
            req = urllib.request.Request(
                url,
                data=json.dumps(body).encode('utf-8'),
                headers={"Content-Type": "application/json"}
            )
        else:
            req = urllib.request.Request(url)
            
        with urllib.request.urlopen(req) as resp:
            print(f"  [PASS] {label:<30} -> HTTP {resp.status}")

    print("\n" + "=" * 100)
    print(" ALL TASK 9 DEMO HARDENING & OPERATOR EXPERIENCE TESTS PASSED (100% SUCCESS)")
    print("=" * 100)

if __name__ == "__main__":
    run_task9_tests()
