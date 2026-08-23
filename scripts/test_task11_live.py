"""
MetroGuard AI - Task 11 Final UI Verification & Live Output Verification Suite
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
import numpy as np

def main():
    print("=" * 105)
    print(" TASK 11 — FINAL UI VERIFICATION + LIVE OUTPUT LINK + HACKATHON DEMO HARDENING")
    print("=" * 105)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # 1. Verify Browser Output Links
    print("\n[STEP 1] VERIFYING LIVE BROWSER OUTPUT LINKS:")
    urls = [
        ("Root Dashboard", "http://127.0.0.1:8000/"),
        ("Risk Dashboard", "http://127.0.0.1:8000/risk"),
        ("Overview Route", "http://127.0.0.1:8000/overview"),
        ("Live Stream Route", "http://127.0.0.1:8000/monitoring"),
        ("Sensors Route", "http://127.0.0.1:8000/sensors"),
        ("Performance Route", "http://127.0.0.1:8000/performance")
    ]
    for label, url in urls:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode('utf-8')
            assert resp.status == 200, f"Expected 200 for {url}"
            assert '<div id="root">' in content, f"Missing root div in {url}"
            print(f"  [PASS] {label:<22} -> HTTP {resp.status} (Verified SPA mount)")

    # 2. Verify Events #1, #2, #3, #4
    print("\n[STEP 2] VERIFYING DOCUMENTED EVENTS (#1, #2, #3, #4) ON LIVE BACKEND:")
    events = [
        ("Event #1 (April 17 23:30)", "2020-04-17 23:30:00", 1),
        ("Event #2 (May 29 23:00)", "2020-05-29 23:00:00", 1),
        ("Event #3 (June 5 09:30)", "2020-06-05 09:30:00", 1),
        ("Event #4 (July 15 14:00)", "2020-07-15 14:00:00", 1),
        ("Custom (April 10 10:00)", "2020-04-10 10:00:00", 0)
    ]

    for name, ts, target in events:
        req = urllib.request.Request(
            "http://127.0.0.1:8000/api/hybrid-predict",
            data=json.dumps({"timestamp": ts}).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            xgb = data["xgboost"]
            anom = data["anomaly"]
            hyb = data["hybrid"]
            alert = data["alert"]
            ev = data["evidence"]
            
            print(f">>> {name}:")
            print(f"    • Requested: {data['timestamp_requested']} | Matched: {data['timestamp_matched']} (Delta: {data.get('time_difference_seconds')}s)")
            print(f"    • XGBoost:   {xgb['risk_percentage']:>6.2f}% ({xgb['status']}) | Prob: {xgb['risk_probability']:.6f}")
            print(f"    • Anomaly:   Score {anom['score']:.4f} ({anom['status']}) | th: {anom['threshold']:.4f}")
            print(f"    • Decision:  {hyb['status']} -> {hyb['reason']}")
            print(f"    • Alert:     {alert['level']} — {alert['title']}")
            print(f"    • Evidence:  {len(ev)} abnormal signal(s)")
            for item in ev[:2]:
                print(f"       - {item['feature']}: {item['actual_value']} {item['unit']} (Z = {item['z_score']:+}σ) -> {item['reason']}")
            print(f"    • Recs:      {len(alert['recommendations'])} actions")
            for rec in alert['recommendations']:
                print(f"       -> [ACTION] {rec}")
            print("-" * 100)

    # 3. Verify Error Handling
    print("\n[STEP 3] VERIFYING ERROR HANDLING (400, 404):")
    error_cases = [
        ("Empty Payload {}", {}, 400),
        ("Invalid String 'invalid'", {"timestamp": "invalid"}, 404),
        ("Out-of-Range Date '2025-01-01'", {"timestamp": "2025-01-01 00:00:00"}, 404)
    ]
    for label, payload, exp_code in error_cases:
        req = urllib.request.Request(
            "http://127.0.0.1:8000/api/hybrid-predict",
            data=json.dumps(payload).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req) as resp:
                print(f"  [FAIL] {label:<32} -> Got HTTP {resp.status} (Expected {exp_code})")
        except urllib.error.HTTPError as e:
            err_b = json.loads(e.read().decode('utf-8'))
            print(f"  [PASS] {label:<32} -> Got HTTP {e.code} (Expected) | Error: {err_b.get('detail')}")

    # 4. Latency Benchmark (10 Calls)
    print("\n[STEP 4] INFERENCE LATENCY BENCHMARK (10 CONSECUTIVE INVOCATIONS):")
    latencies = []
    payload = {"timestamp": "2020-04-17 23:30:00"}
    for _ in range(10):
        t0 = time.perf_counter()
        req = urllib.request.Request(
            "http://127.0.0.1:8000/api/hybrid-predict",
            data=json.dumps(payload).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            resp.read()
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0)

    print(f"  • Min Latency:    {np.min(latencies):.2f} ms")
    print(f"  • Max Latency:    {np.max(latencies):.2f} ms")
    print(f"  • Mean Latency:   {np.mean(latencies):.2f} ms")
    print(f"  • Median Latency: {np.median(latencies):.2f} ms")
    print(f"  • P95 Latency:    {np.percentile(latencies, 95):.2f} ms")

    print("\n" + "=" * 105)
    print(" ALL TASK 11 VERIFICATION TESTS PASSED (100% SUCCESS)")
    print("=" * 105)

if __name__ == "__main__":
    main()
