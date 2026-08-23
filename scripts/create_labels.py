"""
MetroGuard AI - Ground-Truth Labeling & Target Definition
Defines predictive failure labels for metro train air compressor condition monitoring.

Ground-Truth Failure Events (from official MetroPT-3 maintenance logs):
- Event 1: 2020-04-18 00:00:00 to 2020-04-18 23:59:00 (Air Leak, High stress)
- Event 2: 2020-05-29 23:30:00 to 2020-05-30 06:00:00 (Air Leak, High stress)
- Event 3: 2020-06-05 10:00:00 to 2020-06-07 14:30:00 (Air Leak, High stress)
- Event 4: 2020-07-15 14:30:00 to 2020-07-15 19:00:00 (Air Leak, High stress)

Target Logic:
- failure_status = 'pre_failure'    & target = 1 : timestamp is within PREDICTION_HORIZON_MINUTES before event start
- failure_status = 'ongoing_failure'& target = 0 : timestamp is inside [start_time, end_time] of documented event
- failure_status = 'normal'         & target = 0 : normal operation outside pre-failure and event windows
"""

import os
import argparse
import pandas as pd
import numpy as np

# Verified Ground Truth Failure Episodes
FAILURE_EVENTS = [
    {
        "id": 1,
        "name": "Air Leak Event 1",
        "start": pd.Timestamp("2020-04-18 00:00:00"),
        "end": pd.Timestamp("2020-04-18 23:59:00"),
        "failure_type": "Air leak",
        "severity": "High stress"
    },
    {
        "id": 2,
        "name": "Air Leak Event 2",
        "start": pd.Timestamp("2020-05-29 23:30:00"),
        "end": pd.Timestamp("2020-05-30 06:00:00"),
        "failure_type": "Air leak",
        "severity": "High stress"
    },
    {
        "id": 3,
        "name": "Air Leak Event 3",
        "start": pd.Timestamp("2020-06-05 10:00:00"),
        "end": pd.Timestamp("2020-06-07 14:30:00"),
        "failure_type": "Air leak",
        "severity": "High stress"
    },
    {
        "id": 4,
        "name": "Air Leak Event 4",
        "start": pd.Timestamp("2020-07-15 14:30:00"),
        "end": pd.Timestamp("2020-07-15 19:00:00"),
        "failure_type": "Air leak",
        "severity": "High stress"
    },
]

def generate_labels(horizon_minutes=30):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_csv = os.path.join(base_dir, "data", "raw", "MetroPT3(AirCompressor).csv")
    processed_dir = os.path.join(base_dir, "data", "processed")
    os.makedirs(processed_dir, exist_ok=True)
    out_csv = os.path.join(processed_dir, "metropt3_labeled.csv")
    
    print("=" * 75)
    print(" METROGUARD AI - GROUND-TRUTH LABEL GENERATION")
    print("=" * 75)
    print(f"Prediction Horizon: {horizon_minutes} minutes")
    print(f"Loading raw telemetry from: {raw_csv}...")
    
    df = pd.read_csv(raw_csv)
    if 'Unnamed: 0' in df.columns:
        df = df.drop(columns=['Unnamed: 0'])
        
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Verify chronological ordering
    if not df['timestamp'].is_monotonic_increasing:
        print("Sorting records chronologically by timestamp...")
        df = df.sort_values('timestamp').reset_index(drop=True)
    else:
        print("Records are strictly sorted in chronological order.")
        
    # Check for duplicate timestamps
    num_dups = df['timestamp'].duplicated().sum()
    print(f"Duplicate timestamp count: {num_dups}")
    
    # Initialize failure_status and target
    df['failure_status'] = 'normal'
    df['target'] = 0
    
    horizon_delta = pd.Timedelta(minutes=horizon_minutes)
    
    print("\nApplying failure labels across documented events:")
    print("-" * 75)
    
    event_stats = []
    for ev in FAILURE_EVENTS:
        ev_id = ev["id"]
        ev_start = ev["start"]
        ev_end = ev["end"]
        pre_start = ev_start - horizon_delta
        
        # 1. Pre-failure window: [start - horizon, start)
        pre_mask = (df['timestamp'] >= pre_start) & (df['timestamp'] < ev_start)
        df.loc[pre_mask, 'failure_status'] = 'pre_failure'
        df.loc[pre_mask, 'target'] = 1
        
        # 2. Ongoing failure window: [start, end]
        event_mask = (df['timestamp'] >= ev_start) & (df['timestamp'] <= ev_end)
        df.loc[event_mask, 'failure_status'] = 'ongoing_failure'
        df.loc[event_mask, 'target'] = 0  # Marked as 0 but separated by failure_status
        
        pre_count = pre_mask.sum()
        event_count = event_mask.sum()
        
        pre_start_actual = df.loc[pre_mask, 'timestamp'].min() if pre_count > 0 else None
        pre_end_actual = df.loc[pre_mask, 'timestamp'].max() if pre_count > 0 else None
        
        event_stats.append({
            "Event": f"Event #{ev_id}",
            "Type": ev["failure_type"],
            "Pre-Failure Window": f"{pre_start} -> {ev_start}",
            "Pre-Failure Rows": pre_count,
            "Actual Pre Start": pre_start_actual,
            "Actual Pre End": pre_end_actual,
            "Event Window": f"{ev_start} -> {ev_end}",
            "Event Rows": event_count
        })
        
        print(f"  Event #{ev_id} ({ev['failure_type']}):")
        print(f"    - Pre-Failure Horizon ({pre_start} to {ev_start}): {pre_count} rows (target=1)")
        print(f"    - Ongoing Event Window ({ev_start} to {ev_end}): {event_count} rows (status='ongoing_failure')")

    # Global summary statistics
    total_rows = len(df)
    normal_rows = (df['failure_status'] == 'normal').sum()
    pre_failure_rows = (df['failure_status'] == 'pre_failure').sum()
    ongoing_rows = (df['failure_status'] == 'ongoing_failure').sum()
    target_pos_rows = (df['target'] == 1).sum()
    
    pos_pct = (target_pos_rows / total_rows) * 100
    
    print("\n" + "=" * 75)
    print(" LABELING SUMMARY & DISTRIBUTION")
    print("=" * 75)
    print(f"  Total Telemetry Rows       : {total_rows:,}")
    print(f"  Normal Operational Rows    : {normal_rows:,} ({normal_rows/total_rows*100:.2f}%)")
    print(f"  Pre-Failure (Target=1) Rows: {pre_failure_rows:,} ({pos_pct:.4f}%)")
    print(f"  Ongoing Failure Rows       : {ongoing_rows:,} ({ongoing_rows/total_rows*100:.2f}%)")
    print(f"  Target=1 / Target=0 Ratio  : 1 : {total_rows/target_pos_rows:.1f}")
    
    print(f"\nSaving labeled dataset to: {out_csv}...")
    df.to_csv(out_csv, index=False)
    file_size_mb = os.path.getsize(out_csv) / (1024 * 1024)
    print(f"Dataset successfully saved ({file_size_mb:.2f} MB).")
    
    return df, event_stats

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create ground-truth predictive failure labels for MetroPT-3")
    parser.add_argument("--horizon", type=int, default=30, help="Prediction horizon in minutes (default: 30)")
    args = parser.parse_args()
    
    generate_labels(horizon_minutes=args.horizon)
