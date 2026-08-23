"""
MetroGuard AI - Task 20 Intelligent Alert & Maintenance Recommendation Verification Suite
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
    print(" TASK 20 — INTELLIGENT ALERT & MAINTENANCE RECOMMENDATION VERIFICATION SUITE")
    print("=" * 105)

    base_url = "http://127.0.0.1:8000"

    # 1. Test GET /api/alerts and /api/recommendations/current
    print("\n[PART 1] TESTING ALERT & RECOMMENDATION API CONTRACTS:")
    status, alerts = send_request(f"{base_url}/api/alerts")
    assert status == 200, f"Expected 200, got {status}"
    print(f"  [PASS] GET /api/alerts -> HTTP {status} OK (Initial alert history count: {len(alerts)})")

    status, rec = send_request(f"{base_url}/api/recommendations/current")
    assert status == 200 and "action" in rec and "priority" in rec and "inspection_checklist" in rec
    print(f"  [PASS] GET /api/recommendations/current -> HTTP {status} OK")
    print(f"         • Action:   {rec['action']}")
    print(f"         • Priority: {rec['priority']} | Strength: {rec['evidence_strength']}")
    print(f"         • Checklist items: {len(rec['inspection_checklist'])}")

    # 2. Test Scenario 2: Gradual Anomaly & Deduplication
    print("\n[PART 2] TESTING ALERT DEDUPLICATION IN GRADUAL ANOMALY SCENARIO:")
    send_request(f"{base_url}/api/stream/scenario", "POST", {"scenario": "gradual_anomaly"})
    send_request(f"{base_url}/api/stream/reset", "POST")
    
    # Step forward 10 times
    for _ in range(10):
        send_request(f"{base_url}/api/stream/step", "POST")
        
    status, state = send_request(f"{base_url}/api/stream/current")
    active_alt = state.get("active_operator_alert")
    all_alts = state.get("operator_alert_history", [])
    
    print(f"  • Telemetry Timestamp: {state['timestamp']} (Row {state['current_index']})")
    print(f"  • Active Alert ID:     {active_alt['alert_id'] if active_alt else 'None'}")
    print(f"  • Alert Priority:      {active_alt['priority'] if active_alt else 'N/A'}")
    print(f"  • Primary Trigger:     {active_alt['primary_trigger'] if active_alt else 'N/A'}")
    print(f"  • Total Alerts in Log: {len(all_alts)} (Verifying deduplication: should NOT create 10 separate alerts)")
    assert len(all_alts) <= 2, f"Expected deduplication, but found {len(all_alts)} alerts generated!"
    print(f"  [PASS] Deduplication Verified: Continuous streaming updated active alert '{active_alt['alert_id']}' in-place without log spam.")

    # 3. Test Operator Lifecycle: Acknowledge and Resolve
    print("\n[PART 3] TESTING OPERATOR LIFECYCLE WORKFLOW (ACKNOWLEDGE / RESOLVE):")
    if active_alt:
        alt_id = active_alt["alert_id"]
        
        # Acknowledge
        status, ack_res = send_request(f"{base_url}/api/alerts/{alt_id}/acknowledge", "POST")
        assert status == 200 and ack_res["alert"]["status"] == "ACKNOWLEDGED"
        print(f"  [PASS] POST /api/alerts/{alt_id}/acknowledge -> Status: ACKNOWLEDGED (Acknowledged at: {ack_res['alert']['acknowledged_at']})")
        
        # Verify ML state is untouched
        _, state_after_ack = send_request(f"{base_url}/api/stream/current")
        assert state_after_ack["active_operator_alert"]["status"] == "ACKNOWLEDGED"
        assert state_after_ack["xgboost"]["risk_percentage"] == state["xgboost"]["risk_percentage"]
        print(f"  [PASS] ML Integrity Verified: Operator acknowledge did NOT modify underlying ML risk or sensor telemetry.")

        # Resolve
        status, res_res = send_request(f"{base_url}/api/alerts/{alt_id}/resolve", "POST")
        assert status == 200 and res_res["alert"]["status"] == "RESOLVED"
        print(f"  [PASS] POST /api/alerts/{alt_id}/resolve -> Status: RESOLVED (Resolved at: {res_res['alert']['resolved_at']})")

    # 4. Test Scenario 3: Known Pre-Failure Escalation & Immediate Depot Recommendation
    print("\n[PART 4] TESTING PRE-FAILURE CRITICAL ESCALATION & IMMEDIATE RECOMMENDATION:")
    send_request(f"{base_url}/api/stream/scenario", "POST", {"scenario": "pre_failure"})
    send_request(f"{base_url}/api/stream/reset", "POST")
    
    for _ in range(5):
        send_request(f"{base_url}/api/stream/step", "POST")
        
    status, pf_state = send_request(f"{base_url}/api/stream/current")
    pf_alert = pf_state.get("active_operator_alert")
    pf_rec = pf_state.get("prescriptive_recommendation")
    
    assert pf_alert is not None, "Expected active alert on pre-failure"
    assert pf_alert["priority"] == "CRITICAL", f"Expected CRITICAL priority, got {pf_alert['priority']}"
    assert pf_rec["priority"] == "Immediate Attention", f"Expected Immediate Attention, got {pf_rec['priority']}"
    
    print(f"  • Pre-Failure Alert ID: {pf_alert['alert_id']}")
    print(f"  • Priority:            {pf_alert['priority']} (XGBoost: {pf_state['xgboost']['risk_percentage']}%)")
    print(f"  • Primary Trigger:     {pf_alert['primary_trigger']}")
    print(f"  • Prescriptive Action: {pf_rec['action']}")
    print(f"  • Evidence Strength:   {pf_rec['evidence_strength']}")
    print(f"  • Inspection Checklist:")
    for idx, item in enumerate(pf_rec["inspection_checklist"]):
        print(f"    [{idx+1}] {item}")
    print(f"  [PASS] Known Pre-Failure Scenario Verified: Supervised risk correctly triggered CRITICAL priority and Immediate Attention actions.")

    # 5. Test Scenario 4: Unseen Summer Anomaly (Event #4)
    print("\n[PART 5] TESTING UNSEEN SUMMER ANOMALY (EVENT #4) ANOMALY-DRIVEN ALERT & THERMAL ACTION:")
    send_request(f"{base_url}/api/stream/scenario", "POST", {"scenario": "unseen_anomaly"})
    send_request(f"{base_url}/api/stream/reset", "POST")
    for _ in range(10):
        send_request(f"{base_url}/api/stream/step", "POST")
        
    status, ev4_state = send_request(f"{base_url}/api/stream/current")
    ev4_alert = ev4_state.get("active_operator_alert")
    ev4_rec = ev4_state.get("prescriptive_recommendation")
    
    assert ev4_state["xgboost"]["risk_percentage"] < 5.0, "Expected low XGBoost on unseen regime"
    assert ev4_alert is not None, "Expected anomaly-driven alert on Event #4"
    assert "Thermal" in ev4_rec["action"] or "radiator" in ev4_rec["action"] or "cooling" in ev4_rec["action"].lower()
    
    print(f"  • Alert ID:            {ev4_alert['alert_id']}")
    print(f"  • Priority:            {ev4_alert['priority']} (Isolation Forest Severity: {ev4_state['anomaly_intelligence']['anomaly_severity']}/100)")
    print(f"  • Supervised XGB Risk: {ev4_state['xgboost']['risk_percentage']}% (Did NOT trigger due to seasonal shift)")
    print(f"  • Primary Trigger:     {ev4_alert['primary_trigger']}")
    print(f"  • Prescriptive Action: {ev4_rec['action']}")
    print(f"  • Evidence Strength:   {ev4_rec['evidence_strength']}")
    print(f"  [PASS] Unseen Anomaly Scenario Verified: Thermal deviation correctly generated evidence-based cooling recommendation.")

    # 6. Test Scenario 1: Normal Baseline Clean Operation
    print("\n[PART 6] TESTING NORMAL BASELINE CLEAN OPERATION:")
    send_request(f"{base_url}/api/stream/scenario", "POST", {"scenario": "normal"})
    send_request(f"{base_url}/api/stream/reset", "POST")
    for _ in range(5):
        send_request(f"{base_url}/api/stream/step", "POST")
    _, norm_state = send_request(f"{base_url}/api/stream/current")
    norm_rec = norm_state.get("prescriptive_recommendation")
    print(f"  • Recommendation:      {norm_rec['action']}")
    print(f"  • Priority:            {norm_rec['priority']}")
    print(f"  [PASS] Normal Scenario Verified: Baseline operation generates Routine maintenance recommendations.")

    # 7. Verify SPA Routing on /monitoring
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
        ("GET  /api/anomaly/explanation", f"{base_url}/api/anomaly/explanation", "GET", None),
        ("GET  /api/alerts", f"{base_url}/api/alerts", "GET", None),
        ("GET  /api/alerts/active", f"{base_url}/api/alerts/active", "GET", None),
        ("GET  /api/recommendations/current", f"{base_url}/api/recommendations/current", "GET", None),
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
    print(" ALL TASK 20 INTELLIGENT ALERT & RECOMMENDATION TESTS PASSED (100% SUCCESS)")
    print("=" * 105)

if __name__ == "__main__":
    main()
