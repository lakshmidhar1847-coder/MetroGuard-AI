"""
MetroGuard AI - Leakage-Safe Feature Engineering Pipeline
Constructs backward-looking time-series features for metro train air compressor condition monitoring.

Feature Engineering Specification:
- 7 Continuous / Analogue Signals:
  * Current Raw Value
  * Rolling Mean (~1 min / 6 samples)
  * Rolling Std  (~1 min / 6 samples)
  * Rolling Mean (~5 min / 30 samples)
  * Rolling Std  (~5 min / 30 samples)
  * Lag Difference (~1 min / 6 samples: x[t] - x[t-6])
  * Lag Difference (~5 min / 30 samples: x[t] - x[t-30])

- 8 Digital / Control Signals:
  * Current State (Binary 0/1)
  * Rolling Transition / Cycling Count (~5 min / 30 samples)

- Ongoing Failure Exclusion:
  * Features are computed on the continuous chronological sequence.
  * Ongoing failure rows ('ongoing_failure') are excluded from the output training dataset.
  * No future information or target-derived signals are ever used.
"""

import os
import argparse
import time
import pandas as pd
import numpy as np

CONTINUOUS_SIGNALS = [
    'TP2', 'TP3', 'H1', 'DV_pressure', 'Reservoirs', 'Oil_temperature', 'Motor_current'
]

DIGITAL_SIGNALS = [
    'COMP', 'DV_eletric', 'Towers', 'MPG', 'LPS', 'Pressure_switch', 'Oil_level', 'Caudal_impulses'
]

def engineer_features(short_minutes=1, long_minutes=5, sample_interval_sec=10):
    start_time = time.time()
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    labeled_csv = os.path.join(base_dir, "data", "processed", "metropt3_labeled.csv")
    out_csv = os.path.join(base_dir, "data", "processed", "metropt3_features.csv")
    
    print("=" * 80)
    print(" METROGUARD AI - TIME-SERIES FEATURE ENGINEERING PIPELINE")
    print("=" * 80)
    print(f"Short Rolling Window : {short_minutes} minute(s) (~{int(short_minutes * 60 / sample_interval_sec)} samples)")
    print(f"Long Rolling Window  : {long_minutes} minute(s) (~{int(long_minutes * 60 / sample_interval_sec)} samples)")
    print(f"Input Dataset        : {labeled_csv}")
    
    # 1. Load labeled dataset
    print("\n[Step 1/5] Loading labeled dataset...")
    df = pd.read_csv(labeled_csv)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Verify strict chronological order
    if not df['timestamp'].is_monotonic_increasing:
        print("Sorting chronologically by timestamp...")
        df = df.sort_values('timestamp').reset_index(drop=True)
    else:
        print("Chronological order verified (strictly increasing).")
        
    initial_total_rows = len(df)
    w_short = max(1, int(round((short_minutes * 60) / sample_interval_sec)))
    w_long = max(1, int(round((long_minutes * 60) / sample_interval_sec)))
    
    # 2. Continuous signal feature generation (strictly backward-looking)
    print("\n[Step 2/5] Generating backward-looking features for continuous signals...")
    engineered_feature_names = []
    
    for col in CONTINUOUS_SIGNALS:
        raw_series = df[col].astype('float32')
        df[col] = raw_series
        engineered_feature_names.append(col)
        
        # Rolling stats (backward-looking, min_periods=1 ensures no NaNs from warm-up)
        col_mean_short = f"{col}_roll_mean_{short_minutes}m"
        col_std_short  = f"{col}_roll_std_{short_minutes}m"
        col_mean_long  = f"{col}_roll_mean_{long_minutes}m"
        col_std_long   = f"{col}_roll_std_{long_minutes}m"
        col_diff_short = f"{col}_diff_{short_minutes}m"
        col_diff_long  = f"{col}_diff_{long_minutes}m"
        
        df[col_mean_short] = raw_series.rolling(window=w_short, min_periods=1).mean().astype('float32')
        df[col_std_short]  = raw_series.rolling(window=w_short, min_periods=1).std().fillna(0.0).astype('float32')
        df[col_mean_long]  = raw_series.rolling(window=w_long, min_periods=1).mean().astype('float32')
        df[col_std_long]   = raw_series.rolling(window=w_long, min_periods=1).std().fillna(0.0).astype('float32')
        
        # Lag differences (backward looking: x[t] - x[t - lag])
        df[col_diff_short] = (raw_series - raw_series.shift(w_short)).fillna(0.0).astype('float32')
        df[col_diff_long]  = (raw_series - raw_series.shift(w_long)).fillna(0.0).astype('float32')
        
        engineered_feature_names.extend([
            col_mean_short, col_std_short, col_mean_long, col_std_long, col_diff_short, col_diff_long
        ])
        
    print(f"  Generated {len(CONTINUOUS_SIGNALS) * 7} continuous feature columns.")

    # 3. Digital signal feature generation
    print("\n[Step 3/5] Generating state and transition features for digital signals...")
    for col in DIGITAL_SIGNALS:
        raw_series = df[col].astype('float32')
        df[col] = raw_series
        engineered_feature_names.append(col)
        
        # Transition / cycle count over long window
        col_changes = f"{col}_changes_{long_minutes}m"
        transitions = (raw_series.diff().abs() > 0).astype('float32')
        df[col_changes] = transitions.rolling(window=w_long, min_periods=1).sum().fillna(0.0).astype('float32')
        engineered_feature_names.append(col_changes)
        
    print(f"  Generated {len(DIGITAL_SIGNALS) * 2} digital feature columns.")
    print(f"  Total Model Input Features: {len(engineered_feature_names)}")

    # 4. Filter out ongoing failure rows for clean predictive training
    print("\n[Step 4/5] Filtering out ongoing failure episodes...")
    ongoing_mask = (df['failure_status'] == 'ongoing_failure')
    ongoing_count = ongoing_mask.sum()
    
    clean_df = df[~ongoing_mask].copy().reset_index(drop=True)
    
    total_training_rows = len(clean_df)
    positive_rows = (clean_df['target'] == 1).sum()
    negative_rows = (clean_df['target'] == 0).sum()
    pos_pct = (positive_rows / total_training_rows) * 100
    
    print(f"  Original Labeled Rows    : {initial_total_rows:,}")
    print(f"  Ongoing Failure Excluded : {ongoing_count:,}")
    print(f"  Remaining Training Rows  : {total_training_rows:,}")
    print(f"  - Positive (Target=1)    : {positive_rows:,} ({pos_pct:.4f}%)")
    print(f"  - Negative (Target=0)    : {negative_rows:,} ({100-pos_pct:.4f}%)")

    # 5. Save engineered training dataset to CSV
    print("\n[Step 5/5] Exporting processed feature dataset to CSV...")
    # Select columns: timestamp + failure_status + target + all feature columns
    export_cols = ['timestamp', 'failure_status', 'target'] + engineered_feature_names
    clean_df = clean_df[export_cols]
    
    # Missing values audit
    nan_count = clean_df[engineered_feature_names].isnull().sum().sum()
    print(f"  Missing values audit on clean dataset: {nan_count} NaNs.")
    
    print(f"  Writing CSV to: {out_csv}...")
    clean_df.to_csv(out_csv, index=False)
    csv_size_mb = os.path.getsize(out_csv) / (1024 * 1024)
    print(f"  CSV saved successfully: {csv_size_mb:.2f} MB")
    
    elapsed = time.time() - start_time
    print(f"\nFeature pipeline completed in {elapsed:.2f} seconds.")
    
    return clean_df, engineered_feature_names

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create leakage-safe time-series features for MetroGuard AI")
    parser.add_argument("--short_min", type=int, default=1, help="Short rolling window in minutes (default: 1)")
    parser.add_argument("--long_min", type=int, default=5, help="Long rolling window in minutes (default: 5)")
    args = parser.parse_args()
    
    engineer_features(short_minutes=args.short_min, long_minutes=args.long_min)
