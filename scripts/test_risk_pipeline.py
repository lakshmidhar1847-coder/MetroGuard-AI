import os
import sys
import urllib.request
import urllib.error
import json
import pandas as pd

# Add repo root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.predict import get_predictor
from backend.data_service import get_data_service, FEATURE_NAMES

def run_tests():
    predictor = get_predictor()
    ds = get_data_service()

    print("=" * 80)
    print(" PART 4: FEATURE VALIDATION AUDIT")
    print("=" * 80)
    expected_features = set(predictor.feature_names)
    cached_features = set(FEATURE_NAMES)

    print(f"Expected Model Feature Count: {len(expected_features)}")
    print(f"Cached Feature Count:         {len(cached_features)}")
    print(f"Missing Features:             {list(expected_features - cached_features)}")
    print(f"Unexpected Features:          {list(cached_features - expected_features)}")

    sample_res = ds.get_features_by_timestamp("2020-04-17 23:30:00")
    sample_feats = sample_res["features"]
    nan_count = sum(1 for v in sample_feats.values() if v is None or pd.isna(v))
    print(f"Null / NaN Count in Sample:   {nan_count}")
    print("=" * 80)

    print("\n" + "=" * 80)
    print(" PART 5: EVENT PREDICTION & INFERENCE VERIFICATION")
    print("=" * 80)

    events_to_test = [
        ("Event #1 Pre-Failure (April)", "2020-04-17 23:30:00"),
        ("Event #2 Pre-Failure (May)", "2020-05-29 23:00:00"),
        ("Event #3 Pre-Failure (June)", "2020-06-05 09:30:00"),
        ("Event #4 Pre-Failure (July)", "2020-07-15 14:00:00"),
        ("Normal Baseline (March)", "2020-03-01 12:00:00"),
        ("Normal Baseline (August)", "2020-08-10 12:00:00")
    ]

    for name, ts in events_to_test:
        res = ds.get_features_by_timestamp(ts)
        pred = predictor.predict(res["features"])
        print(f">>> {name}:")
        print(f"    Query Timestamp     : {ts}")
        print(f"    Matched Timestamp   : {res['timestamp_matched']} (delta = {res['time_difference_seconds']}s)")
        print(f"    Ground Truth Target : {res['target']} (status = {res['failure_status']})")
        print(f"    Features Evaluated  : {len(res['features'])} complete channels")
        print(f"    Risk Probability    : {pred['risk_probability']:.6f}")
        print(f"    Risk Percentage     : {pred['risk_percentage']:>6.2f}%")
        print(f"    Model Classification: {pred['status']}")
        print("-" * 80)

    print("\n" + "=" * 80)
    print(" PART 6: HTTP ENDPOINT & ERROR HANDLING VERIFICATION")
    print("=" * 80)

    http_tests = [
        ("Valid Event #1 Timestamp", {"timestamp": "2020-04-17 23:30:00"}, 200),
        ("Valid Normal Timestamp", {"timestamp": "2020-03-01 12:00:00"}, 200),
        ("Invalid Non-Date String", {"timestamp": "invalid-date-string"}, 404),
        ("Out-of-Range Timestamp", {"timestamp": "2025-01-01 00:00:00"}, 404),
        ("Empty Payload (Missing timestamp & features)", {}, 400),
    ]

    for test_name, payload, expected_status in http_tests:
        url = "http://127.0.0.1:8000/api/predict"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req) as response:
                status_code = response.status
                body = json.loads(response.read().decode("utf-8"))
                print(f"  [PASS] {test_name:<42} -> HTTP {status_code} | Risk: {body.get('risk_percentage')}% | Status: {body.get('status')}")
        except urllib.error.HTTPError as e:
            status_code = e.code
            err_body = json.loads(e.read().decode("utf-8"))
            if status_code == expected_status:
                print(f"  [PASS] {test_name:<42} -> HTTP {status_code} (Expected) | Error: {err_body.get('detail')}")
            else:
                print(f"  [FAIL] {test_name:<42} -> HTTP {status_code} (Expected {expected_status}) | Error: {err_body.get('detail')}")
        except Exception as e:
            print(f"  [FAIL] {test_name:<42} -> Exception: {e}")

    print("=" * 80)

if __name__ == "__main__":
    run_tests()
