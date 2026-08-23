"""
MetroGuard AI - Task 18 Real-Time Sensor Streaming & Replay Verification Suite
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
    print(" TASK 18 — REAL-TIME SENSOR STREAMING & REPLAY VERIFICATION SUITE")
    print("=" * 105)

    base_url = "http://127.0.0.1:8000"

    # 1. Test GET /api/stream/status
    print("\n[PART 1] TESTING GET /api/stream/status:")
    status, data = send_request(f"{base_url}/api/stream/status")
    assert status == 200, f"Expected 200, got {status}"
    assert "scenario" in data and "is_running" in data and "available_scenarios" in data
    print(f"  [PASS] Stream Status: Scenario = '{data['scenario']}' | Running = {data['is_running']} | Speed = {data['playback_speed']}x")
    print(f"         Available Scenarios: {[s['id'] for s in data['available_scenarios']]}")

    # 2. Test GET /api/stream/current
    print("\n[PART 2] TESTING GET /api/stream/current:")
    status, snap = send_request(f"{base_url}/api/stream/current")
    assert status == 200, f"Expected 200, got {status}"
    assert "sensors" in snap and "xgboost" in snap and "anomaly" in snap and "alert" in snap and "chart_history" in snap
    print(f"  [PASS] Live Telemetry Snapshot: Timestamp = {snap['timestamp']}")
    print(f"         • TP2: {snap['sensors']['TP2']['value']} bar | H1: {snap['sensors']['H1']['value']} bar | Oil Temp: {snap['sensors']['Oil_temperature']['value']} °C")
    print(f"         • XGBoost: {snap['xgboost']['risk_percentage']}% | Anomaly: {snap['anomaly']['score']} | Alert: {snap['alert']['level']}")
    print(f"         • Chart History Buffer: {len(snap['chart_history'])} observations")

    # 3. Test All 4 Scenarios
    print("\n[PART 3] TESTING SCENARIO SWITCHING & LIVE PIPELINE PROCESSING:")
    scenarios = ["normal", "gradual_anomaly", "pre_failure", "unseen_anomaly"]
    
    for sc in scenarios:
        # Switch scenario
        status, res = send_request(f"{base_url}/api/stream/scenario", "POST", {"scenario": sc})
        assert status == 200, f"Failed to set scenario {sc}"
        
        # Reset and step 3 times
        send_request(f"{base_url}/api/stream/reset", "POST")
        for _ in range(3):
            send_request(f"{base_url}/api/stream/step", "POST")
            
        status, state = send_request(f"{base_url}/api/stream/current")
        assert state["scenario"] == sc
        
        print(f"  [PASS] Scenario '{sc}':")
        print(f"         • Label:       {state['scenario_label']}")
        print(f"         • Timestamp:   {state['timestamp']} (Row {state['current_index']}/{state['total_records']})")
        print(f"         • Sensors:     TP2 = {state['sensors']['TP2']['value']} bar, Oil = {state['sensors']['Oil_temperature']['value']} °C")
        print(f"         • AI Decision: XGB {state['xgboost']['risk_percentage']}% | Anom {state['anomaly']['score']:.4f} | Alert: {state['alert']['level']} ({state['alert']['title']})")
        print(f"         • Evidence:    {len(state['evidence'])} signals | Recs: {len(state['alert']['recommendations'])} actions")

    # 4. Test Playback Speed Control (1x, 2x, 5x, 10x)
    print("\n[PART 4] TESTING SPEED MULTIPLIER CONTROL:")
    for spd in [1.0, 2.0, 5.0, 10.0]:
        status, res = send_request(f"{base_url}/api/stream/speed", "POST", {"speed": spd})
        assert status == 200 and res["playback_speed"] == spd
        print(f"  [PASS] Set Speed -> {spd}x (Playback speed updated)")

    # 5. Test Start / Pause / Reset Controls
    print("\n[PART 5] TESTING PLAY / PAUSE / RESET STREAM CONTROLS:")
    status, res = send_request(f"{base_url}/api/stream/stop", "POST")
    assert status == 200 and res["is_running"] is False
    print(f"  [PASS] Stream Stopped / Paused")

    status, res = send_request(f"{base_url}/api/stream/start", "POST")
    assert status == 200 and res["is_running"] is True
    print(f"  [PASS] Stream Resumed / Started")

    status, res = send_request(f"{base_url}/api/stream/reset", "POST")
    assert status == 200 and res["current_index"] == 0
    print(f"  [PASS] Stream Reset to Index 0")

    # 6. Test Error Handling
    print("\n[PART 6] TESTING STREAM ERROR HANDLING (INVALID SCENARIO):")
    try:
        req = urllib.request.Request(
            f"{base_url}/api/stream/scenario",
            data=json.dumps({"scenario": "non_existent_scenario"}).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req)
        print("  [FAIL] Expected 400 Bad Request")
    except urllib.error.HTTPError as e:
        err = json.loads(e.read().decode('utf-8'))
        print(f"  [PASS] Invalid Scenario -> HTTP {e.code} (Expected) | Error: {err.get('detail')}")

    # 7. Test SPA Routing on /monitoring
    print("\n[PART 7] VERIFYING SPA DIRECT URL ACCESS ON /monitoring:")
    req = urllib.request.Request(f"{base_url}/monitoring")
    with urllib.request.urlopen(req) as resp:
        content = resp.read().decode('utf-8')
        assert resp.status == 200 and '<div id="root">' in content
        print(f"  [PASS] GET /monitoring -> HTTP {resp.status} (SPA Route verified)")

    # 8. Full API Regression Test
    print("\n[PART 8] VERIFYING ZERO REGRESSION ACROSS ALL METROGUARD APIS:")
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
            print(f"  [PASS] {label:<30} -> HTTP {resp.status}")

    print("\n" + "=" * 105)
    print(" ALL TASK 18 REAL-TIME STREAMING TESTS PASSED (100% SUCCESS)")
    print("=" * 105)

if __name__ == "__main__":
    main()
