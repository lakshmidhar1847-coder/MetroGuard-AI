"""
MetroGuard AI - Task 3 Comprehensive Model Diagnostic & Distribution Analysis
"""

import os
import sys
import json
import pandas as pd
import numpy as np

# Add repo root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.predict import get_predictor
from backend.data_service import get_data_service, FEATURE_NAMES

def main():
    predictor = get_predictor()
    ds = get_data_service()

    features_csv = os.path.join("data", "processed", "metropt3_features.csv")
    print("Loading metropt3_features.csv...")
    df = pd.read_csv(features_csv)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    train_mask = (df['timestamp'] >= '2020-02-01') & (df['timestamp'] <= '2020-05-31 23:59:59')
    val_mask = (df['timestamp'] >= '2020-06-01') & (df['timestamp'] <= '2020-06-30 23:59:59')
    test_mask = (df['timestamp'] >= '2020-07-01') & (df['timestamp'] <= '2020-09-01 04:00:00')

    train_pos = df[train_mask & (df['target'] == 1)]
    train_neg = df[train_mask & (df['target'] == 0)]
    val_pos = df[val_mask & (df['target'] == 1)]
    val_neg = df[val_mask & (df['target'] == 0)]
    test_pos = df[test_mask & (df['target'] == 1)]
    test_neg = df[test_mask & (df['target'] == 0)]

    print(f"Train Normal:     {len(train_neg):,} rows")
    print(f"Train Positives:  {len(train_pos):,} rows (Events #1 & #2)")
    print(f"Val Normal:       {len(val_neg):,} rows")
    print(f"Val Positives:    {len(val_pos):,} rows (Event #3)")
    print(f"Test Normal:      {len(test_neg):,} rows")
    print(f"Test Positives:   {len(test_pos):,} rows (Event #4)")

    top_feats = [
        "H1_roll_std_1m",
        "H1_roll_std_5m",
        "H1_diff_5m",
        "DV_pressure_roll_mean_5m",
        "TP3_roll_std_1m",
        "Reservoirs_roll_mean_1m",
        "DV_pressure_diff_5m",
        "DV_pressure",
        "Motor_current_roll_std_5m",
        "TP3",
        "TP2",
        "Oil_temperature"
    ]

    print("\n" + "=" * 110)
    print(" PART 4: FEATURE DISTRIBUTION MEAN & MEDIAN COMPARISON")
    print("=" * 110)
    print(f"{'Feature':<26} | {'Train Normal':<16} | {'Train Pos (E1/2)':<18} | {'Val Pos (E3)':<18} | {'Test Pos (E4)':<18}")
    print("-" * 110)
    for f in top_feats:
        tn_mean, tn_med = train_neg[f].mean(), train_neg[f].median()
        tp_mean, tp_med = train_pos[f].mean(), train_pos[f].median()
        vp_mean, vp_med = val_pos[f].mean(), val_pos[f].median()
        te_mean, te_med = test_pos[f].mean(), test_pos[f].median()
        print(f"{f:<26} | {tn_mean:>7.4f} (med {tn_med:>5.2f}) | {tp_mean:>8.4f} (med {tp_med:>5.2f}) | {vp_mean:>8.4f} (med {vp_med:>5.2f}) | {te_mean:>8.4f} (med {te_med:>5.2f})")
    print("=" * 110)

    # Probability sweeps on each event
    print("\n" + "=" * 110)
    print(" PREDICTED PROBABILITY DISTRIBUTION BY SUBSET")
    print("=" * 110)
    
    subsets = [
        ("Train Normal", train_neg.sample(min(5000, len(train_neg)), random_state=42)),
        ("Train Positives (Events #1 & #2)", train_pos),
        ("Validation Positives (Event #3)", val_pos),
        ("Final Test Positives (Event #4)", test_pos),
        ("Final Test Normal", test_neg.sample(min(5000, len(test_neg)), random_state=42))
    ]

    for name, subset in subsets:
        probs = []
        for _, row in subset.iterrows():
            f_dict = {f: float(row[f]) for f in predictor.feature_names}
            res = predictor.predict(f_dict)
            probs.append(res["risk_probability"])
        probs = np.array(probs)
        p_min = probs.min()
        p_max = probs.max()
        p_mean = probs.mean()
        p_med = np.median(probs)
        p_p90 = np.percentile(probs, 90)
        p_p95 = np.percentile(probs, 95)
        
        warn_count = (probs >= 0.10).sum()
        high_count = (probs >= 0.70).sum()
        
        print(f"{name:<34} (N={len(probs):>5}): min={p_min:.6f}, max={p_max:.6f}, mean={p_mean:.6f}, med={p_med:.6f}, p90={p_p90:.6f}, p95={p_p95:.6f}")
        print(f"   -> Triggered Warning (>=0.10): {warn_count:>4} ({warn_count/len(probs)*100:.2f}%) | Triggered High Risk (>=0.70): {high_count:>4} ({high_count/len(probs)*100:.2f}%)")

    print("=" * 110)

    # Threshold sweep for Event #3 and #4
    print("\n" + "=" * 110)
    print(" PART 6: THRESHOLD SENSITIVITY SWEEP (EVENT RECALL)")
    print("=" * 110)
    
    thresholds = [0.0005, 0.001, 0.002, 0.005, 0.007, 0.010, 0.020, 0.050, 0.100, 0.200, 0.500]
    
    # Pre-calculate probabilities for Val Pos and Test Pos
    val_probs = np.array([predictor.predict({f: float(r[f]) for f in predictor.feature_names})["risk_probability"] for _, r in val_pos.iterrows()])
    test_probs = np.array([predictor.predict({f: float(r[f]) for f in predictor.feature_names})["risk_probability"] for _, r in test_pos.iterrows()])
    
    print(f"{'Threshold':<12} | {'Event #3 Recall (Val)':<24} | {'Event #4 Recall (Test)':<24}")
    print("-" * 70)
    for th in thresholds:
        val_rec = (val_probs >= th).mean() * 100
        test_rec = (test_probs >= th).mean() * 100
        print(f"{th:<12.4f} | {val_rec:>20.2f}% | {test_rec:>20.2f}%")
    print("=" * 110)

if __name__ == "__main__":
    main()
