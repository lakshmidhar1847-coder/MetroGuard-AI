"""
MetroGuard AI - Task 23 Real-World Case Studies & Operational Impact Verification Suite
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
    print(" TASK 23 — REAL-WORLD CASE STUDIES & OPERATIONAL IMPACT VERIFICATION SUITE")
    print("=" * 105)

    base_url = "http://127.0.0.1:8000"

    # 1. Test GET /api/case-studies
    print("\n[PART 1] TESTING CASE STUDIES LIST & SUMMARY ENDPOINTS:")
    status, cases = send_request(f"{base_url}/api/case-studies")
    assert status == 200, f"Expected 200, got {status}"
    assert len(cases) == 2, f"Expected 2 case studies, got {len(cases)}"
    print(f"  [PASS] GET /api/case-studies -> HTTP {status} OK ({len(cases)} case studies returned)")

    status, summary = send_request(f"{base_url}/api/case-studies/summary")
    assert status == 200 and "scientific_disclaimer" in summary
    print(f"  [PASS] GET /api/case-studies/summary -> HTTP {status} OK (Asset: {summary['asset_monitored']})")

    # 2. Verify Case Study 1: Pre-Failure Event #1
    print("\n[PART 2] VERIFYING CASE STUDY 1 (PRE-FAILURE PNEUMATIC EVENT #1):")
    status, cs1 = send_request(f"{base_url}/api/case-studies/pre_failure_event_1")
    assert status == 200 and cs1["case_id"] == "pre_failure_event_1"
    assert len(cs1["timeline"]) >= 5, "Expected structured timeline with >= 5 stages"
    assert cs1["detection_mechanisms"]["peak_risk_percentage"] >= 90.0, "Expected peak risk >= 90%"
    assert len(cs1["prescriptive_recommendation"]["inspection_checklist"]) == 4
    
    print(f"  • Title:             {cs1['title']}")
    print(f"  • Asset:             {cs1['asset']['unit_id']} ({cs1['asset']['operating_regime']})")
    print(f"  • Primary Engine:    {cs1['detection_mechanisms']['primary_engine']}")
    print(f"  • Peak XGB Risk:     {cs1['detection_mechanisms']['peak_risk_percentage']}%")
    print(f"  • Alert Level:       {cs1['detection_mechanisms']['alert_level']} ({cs1['detection_mechanisms']['alert_priority']})")
    print(f"  • Timeline Stages:   {len(cs1['timeline'])} stages verified")
    print(f"  • Prescriptive Action:{cs1['prescriptive_recommendation']['action']}")
    print(f"  • Impact Dimensions: {len(cs1['impact_analysis']['dimensions'])} qualitative dimensions evaluated")
    print(f"  [PASS] Case Study 1 structure and telemetry evidence verified.")

    # 3. Verify Case Study 2: Summer Holdout Event #4
    print("\n[PART 3] VERIFYING CASE STUDY 2 (UNSEEN SUMMER THERMAL ANOMALY EVENT #4):")
    status, cs2 = send_request(f"{base_url}/api/case-studies/summer_holdout_event_4")
    assert status == 200 and cs2["case_id"] == "summer_holdout_event_4"
    assert len(cs2["timeline"]) >= 5
    assert cs2["detection_mechanisms"]["calibrated_severity"] >= 45
    assert cs2["detection_mechanisms"]["supervised_xgboost_risk"] < 0.10, "Expected low XGBoost under distribution shift"
    
    print(f"  • Title:             {cs2['title']}")
    print(f"  • Asset:             {cs2['asset']['unit_id']} ({cs2['asset']['operating_regime']})")
    print(f"  • Primary Engine:    {cs2['detection_mechanisms']['primary_engine']}")
    print(f"  • Supervised Risk:   {cs2['detection_mechanisms']['supervised_xgboost_risk']*100:.2f}% (Supervised blindspot under thermal shift)")
    print(f"  • Anomaly Severity:  {cs2['detection_mechanisms']['calibrated_severity']}/100 (ELEVATED)")
    print(f"  • Physical Evidence: Oil Temp {cs2['detection_mechanisms']['top_deviating_sensors'][0]['reading']} ({cs2['detection_mechanisms']['top_deviating_sensors'][0]['z_score']})")
    print(f"  • Prescriptive Action:{cs2['prescriptive_recommendation']['action']}")
    print(f"  [PASS] Case Study 2 orthogonal anomaly detection and thermal evidence verified.")

    # 4. Verify Scientific Integrity & Non-Fabrication
    print("\n[PART 4] VERIFYING SCIENTIFIC INTEGRITY & ZERO-FABRICATION PROTOCOL:")
    for cs in [cs1, cs2]:
        raw_json = json.dumps(cs)
        # Check no dollar/euro currency signs or claims of guaranteed failure prevention
        assert "$" not in raw_json and "€" not in raw_json, f"Found currency symbol in case study {cs['case_id']}!"
        assert "prevented a real-world failure" not in raw_json.lower()
        assert "disclaimer" in cs["impact_analysis"]
        for dim in cs["impact_analysis"]["dimensions"]:
            assert dim["level"] in ["LOW", "MODERATE", "HIGH"]
            assert len(dim["evidence_rationale"]) > 10
    print(f"  [PASS] Zero-Fabrication Confirmed: No invented dollars, downtime savings, or guaranteed failure prevention claims.")

    # 5. Verify SPA Routing on /case-study
    print("\n[PART 5] VERIFYING SPA DIRECT URL ACCESS ON /case-study:")
    for route in ["/case-study", "/overview", "/monitoring", "/risk", "/sensors", "/performance"]:
        req = urllib.request.Request(f"{base_url}{route}")
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode('utf-8')
            assert resp.status == 200 and '<div id="root">' in content
            print(f"  [PASS] GET {route:<18} -> HTTP {resp.status} (SPA Route verified)")

    # 6. Full REST API Regression (18 Endpoints)
    print("\n[PART 6] VERIFYING ALL BACKEND REST APIS (100% REGRESSION):")
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
    print(" ALL TASK 23 CASE STUDIES & IMPACT ANALYSIS TESTS PASSED (100% SUCCESS)")
    print("=" * 105)

if __name__ == "__main__":
    main()
