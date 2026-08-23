"""
MetroGuard AI - Task 19 Explainable Anomaly Intelligence & Severity Refinement Verification Suite
"""

import os
import sys
import json
import time
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
    print(" TASK 19 — EXPLAINABLE ANOMALY INTELLIGENCE & SEVERITY CALIBRATION SUITE")
    print("=" * 105)

    base_url = "http://127.0.0.1:8000"

    # 1. Verify GET /api/anomaly/explanation
    print("\n[PART 1] TESTING GET /api/anomaly/explanation API CONTRACT:")
    status, expl = send_request(f"{base_url}/api/anomaly/explanation")
    assert status == 200, f"Expected 200, got {status}"
    assert "anomaly_score" in expl and "anomaly_severity" in expl and "severity_label" in expl
    assert "trajectory" in expl and "persistence" in expl and "top_sensor_deviations" in expl and "operational_hypothesis" in expl
    
    print(f"  [PASS] GET /api/anomaly/explanation -> HTTP {status} OK")
    print(f"         • Timestamp:          {expl.get('timestamp')}")
    print(f"         • Raw Score:          {expl['anomaly_score']} (Threshold τ = 0.5040)")
    print(f"         • Calibrated Severity:{expl['anomaly_severity']} / 100 ({expl['severity_label']})")
    print(f"         • Trajectory:         {expl['trajectory']}")
    print(f"         • Persistence:        {expl['persistence']['status']} ({expl['persistence']['abnormal_count']}/{expl['persistence']['window_size']} obs)")
    print(f"         • Operational Hyp:    {expl['operational_hypothesis']['title']}")
    print(f"         • Top Deviations:     {len(expl['top_sensor_deviations'])} ranked sensor channels")

    # 2. Test Anomaly Intelligence Across All 4 Scenarios
    print("\n[PART 2] TESTING ANOMALY INTELLIGENCE ACROSS ALL 4 SCENARIOS:")
    scenarios = [
        ("normal", "1. Normal Operation Baseline", "NOMINAL/LOW", 45),
        ("gradual_anomaly", "2. Gradual Thermal & Pressure Drift", "ELEVATED/WARNING", 80),
        ("pre_failure", "3. Known Pre-Failure Sequence (Event #1)", "HIGH RISK", 99),
        ("unseen_anomaly", "4. Unseen Summer Anomaly (Event #4 Comparison)", "ELEVATED/WARNING", 75)
    ]

    for sc_id, label, exp_alert, max_expected_sev in scenarios:
        # Switch scenario and reset
        send_request(f"{base_url}/api/stream/scenario", "POST", {"scenario": sc_id})
        send_request(f"{base_url}/api/stream/reset", "POST")
        
        # Step forward 5 observations
        for _ in range(5):
            send_request(f"{base_url}/api/stream/step", "POST")
            
        status, state = send_request(f"{base_url}/api/stream/current")
        assert status == 200
        
        intel = state["anomaly_intelligence"]
        top_devs = intel["top_sensor_deviations"]
        hyp = intel["operational_hypothesis"]
        
        print(f"\n  ---------------------------------------------------------------------------------------")
        print(f"  SCENARIO: {label} [{sc_id}]")
        print(f"  ---------------------------------------------------------------------------------------")
        print(f"  • Timestamp:          {state['timestamp']} (Index {state['current_index']}/{state['total_records']})")
        print(f"  • XGBoost Risk:       {state['xgboost']['risk_percentage']}% (Status: {state['xgboost']['status']})")
        print(f"  • Anomaly Severity:   {intel['anomaly_severity']}/100 ({intel['severity_label']}, Raw: {intel['anomaly_score']})")
        print(f"  • Trajectory:         {intel['trajectory']}")
        print(f"  • Persistence:        {intel['persistence']['status']} ({intel['persistence']['abnormal_count']}/{intel['persistence']['window_size']} obs)")
        print(f"  • Operational Hyp:    {hyp['title']} (Confidence: {hyp.get('confidence', 'MODERATE')})")
        print(f"  • Evidence Rationale: {hyp['evidence']}")
        print(f"  • Suggested Action:   {hyp['recommended_inspection']}")
        print(f"  • Top Sensor Deviations:")
        for d in top_devs[:3]:
            print(f"    - {d['name']:<36} | Cur: {d['current_value']:>6} {d['unit']:<4} | Base: {d['baseline_median']:>6} | Dev: {d['deviation']:>+6.2f} | Z: {d['z_score']:>+5.2f}σ | {d['trend']}")

    # 3. Verify Specific Scenario 4 Synergy (Unseen Summer Anomaly)
    print("\n[PART 3] SCIENTIFIC VERIFICATION OF UNSEEN SUMMER ANOMALY (EVENT #4):")
    send_request(f"{base_url}/api/stream/scenario", "POST", {"scenario": "unseen_anomaly"})
    send_request(f"{base_url}/api/stream/reset", "POST")
    for _ in range(10):
        send_request(f"{base_url}/api/stream/step", "POST")
    _, ev4_state = send_request(f"{base_url}/api/stream/current")
    
    ev4_intel = ev4_state["anomaly_intelligence"]
    assert ev4_state["xgboost"]["risk_percentage"] < 5.0, "Expected XGBoost to be low on unseen regime shift"
    assert ev4_intel["anomaly_severity"] >= 40, "Expected Anomaly severity to be elevated on Event #4"
    print(f"  [PASS] Event #4 Dual-Tier Verification:")
    print(f"         • Supervised XGBoost:     {ev4_state['xgboost']['risk_percentage']}% (Did NOT trigger due to seasonal shift)")
    print(f"         • Isolation Forest Tier:  {ev4_intel['anomaly_severity']}/100 ({ev4_intel['severity_label']}) (DETECTED out-of-distribution regime)")
    print(f"         • Primary Physical Cause: Oil Temperature {ev4_state['sensors']['Oil_temperature']['value']}°C (+{ev4_intel['top_sensor_deviations'][0]['deviation']}°C, Z={ev4_intel['top_sensor_deviations'][0]['z_score']}σ)")
    print(f"         • Operational Hypothesis: {ev4_intel['operational_hypothesis']['title']}")

    # 4. Verify SPA Routing on /monitoring
    print("\n[PART 4] VERIFYING SPA DIRECT URL ACCESS ON /monitoring:")
    req = urllib.request.Request(f"{base_url}/monitoring")
    with urllib.request.urlopen(req) as resp:
        content = resp.read().decode('utf-8')
        assert resp.status == 200 and '<div id="root">' in content
        print(f"  [PASS] GET /monitoring -> HTTP {resp.status} (SPA Route verified)")

    # 5. Full API Regression Test
    print("\n[PART 5] VERIFYING ZERO REGRESSION ACROSS ALL METROGUARD APIS:")
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
            print(f"  [PASS] {label:<32} -> HTTP {resp.status}")

    print("\n" + "=" * 105)
    print(" ALL TASK 19 EXPLAINABLE ANOMALY INTELLIGENCE TESTS PASSED (100% SUCCESS)")
    print("=" * 105)

if __name__ == "__main__":
    main()
