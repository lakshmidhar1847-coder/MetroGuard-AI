"""
MetroGuard AI - Task 4: Hybrid Anomaly Detection Layer (Experimental)
Trains and evaluates an unsupervised Isolation Forest on normal-only training telemetry.
Saves model artifact to models/metroguard_anomaly_model.pkl and metadata to models/anomaly_metadata.json.
"""

import os
import sys
import json
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler, StandardScaler
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, average_precision_score, confusion_matrix

# Add repo root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.predict import get_predictor
from backend.data_service import FEATURE_NAMES

def main():
    print("=" * 90)
    print(" TASK 4 — HYBRID ANOMALY DETECTION EXPERIMENT")
    print("=" * 90)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    features_csv = os.path.join(base_dir, "data", "processed", "metropt3_features.csv")
    models_dir = os.path.join(base_dir, "models")
    anomaly_model_path = os.path.join(models_dir, "metroguard_anomaly_model.pkl")
    anomaly_meta_path = os.path.join(models_dir, "anomaly_metadata.json")

    print(f"Loading features dataset from {features_csv}...")
    df = pd.read_csv(features_csv)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # 1. Partitions definition
    train_mask = (df['timestamp'] >= '2020-02-01') & (df['timestamp'] <= '2020-05-31 23:59:59')
    val_mask = (df['timestamp'] >= '2020-06-01') & (df['timestamp'] <= '2020-06-30 23:59:59')
    test_mask = (df['timestamp'] >= '2020-07-01') & (df['timestamp'] <= '2020-09-01 04:00:00')

    # 2. Normal-only training data (target == 0 and failure_status == 'normal')
    train_normal_df = df[train_mask & (df['target'] == 0) & (df['failure_status'] == 'normal')].copy()
    
    # Uniform 1-minute sampling for training stability & memory efficiency (every 6th row = 10s -> 60s)
    train_normal_sampled = train_normal_df.iloc[::6].copy().reset_index(drop=True)
    print(f"Training Period:       2020-02-01 through 2020-05-31")
    print(f"Total Normal Rows:     {len(train_normal_df):,}")
    print(f"Sampled Normal Rows:   {len(train_normal_sampled):,} (1-minute cadence)")
    print(f"Target Positives in Training: 0 (Strict Normal-Only)")

    # 3. Features selection
    # Using the exact 65 engineered features for seamless alignment with XGBoost
    features_to_use = [f for f in FEATURE_NAMES if f in df.columns]
    print(f"Features count:        {len(features_to_use)}")

    X_train = train_normal_sampled[features_to_use].values

    # Check for NaNs
    print(f"Missing/NaN values in training: {np.isnan(X_train).sum()}")

    # 4. Train Isolation Forest
    print("\nTraining Isolation Forest baseline...")
    # contamination set to small expected anomaly rate in clean data (0.01 = 1%)
    iso_forest = IsolationForest(
        n_estimators=150,
        max_samples=0.8,
        contamination=0.01,
        random_state=42,
        n_jobs=-1
    )
    iso_forest.fit(X_train)

    # In IsolationForest, score_samples() returns the opposite of the anomaly score (lower = more abnormal).
    # Normalizing anomaly score: S(x) = -score_samples(x). Higher S(x) means MORE ANOMALOUS.
    
    # Compute baseline score statistics on training normal data
    train_scores = -iso_forest.score_samples(X_train)
    score_min = float(train_scores.min())
    score_max = float(train_scores.max())
    score_mean = float(train_scores.mean())
    score_std = float(train_scores.std())
    print(f"Train Normal Anomaly Scores: min={score_min:.4f}, max={score_max:.4f}, mean={score_mean:.4f}, std={score_std:.4f}")

    # 5. Validation-based Threshold Calibration (June partition)
    print("\nEvaluating on Validation Partition (June 2020)...")
    val_df = df[val_mask].copy()
    X_val = val_df[features_to_use].values
    y_val = val_df['target'].values
    
    val_scores = -iso_forest.score_samples(X_val)
    val_pos_scores = val_scores[y_val == 1]
    val_neg_scores = val_scores[y_val == 0]
    
    val_roc_auc = roc_auc_score(y_val, val_scores)
    val_pr_auc = average_precision_score(y_val, val_scores)
    print(f"Validation ROC-AUC: {val_roc_auc:.4f}")
    print(f"Validation PR-AUC:  {val_pr_auc:.4f}")
    print(f"Val Normal Score Mean:   {val_neg_scores.mean():.4f} (med {np.median(val_neg_scores):.4f})")
    print(f"Val Positive Score Mean: {val_pos_scores.mean():.4f} (med {np.median(val_pos_scores):.4f})")

    # Select candidate threshold on validation: e.g. 99th percentile of normal training scores
    threshold_val_99 = float(np.percentile(train_scores, 99))
    threshold_val_995 = float(np.percentile(train_scores, 99.5))
    selected_threshold = threshold_val_99
    print(f"Selected Validation-Calibrated Anomaly Threshold (99th pct): {selected_threshold:.4f}")

    # 6. Save Model Artifact & Metadata
    anomaly_bundle = {
        "model": iso_forest,
        "features": features_to_use,
        "train_score_stats": {
            "min": score_min,
            "max": score_max,
            "mean": score_mean,
            "std": score_std
        },
        "selected_threshold": selected_threshold
    }
    joblib.dump(anomaly_bundle, anomaly_model_path, compress=3)
    print(f"Saved anomaly model artifact to {anomaly_model_path}")

    meta = {
        "model_name": "MetroGuard Isolation Forest Anomaly Detector",
        "model_type": "IsolationForest",
        "n_estimators": 150,
        "contamination": 0.01,
        "random_state": 42,
        "feature_count": len(features_to_use),
        "features": features_to_use,
        "training_period": {
            "start": "2020-02-01 00:00:00",
            "end": "2020-05-31 23:59:59",
            "total_normal_samples": len(train_normal_df),
            "sampled_training_rows": len(train_normal_sampled)
        },
        "thresholds": {
            "train_99th_percentile": threshold_val_99,
            "train_99_5th_percentile": threshold_val_995,
            "selected_threshold": selected_threshold
        },
        "validation_metrics": {
            "roc_auc": float(val_roc_auc),
            "pr_auc": float(val_pr_auc)
        }
    }
    with open(anomaly_meta_path, 'w') as f:
        json.dump(meta, f, indent=2)
    print(f"Saved anomaly metadata to {anomaly_meta_path}")

    # 7. Evaluate on Specific Documented Events & Partitions
    print("\n" + "=" * 90)
    print(" PART 4 & 5 — EVENT-BY-EVENT ANOMALY SCORE EVALUATION")
    print("=" * 90)

    predictor = get_predictor()

    events = [
        ("Event #1 Pre-Failure (April)", "2020-04-17 23:30:00", 1),
        ("Event #2 Pre-Failure (May)", "2020-05-29 23:00:00", 1),
        ("Event #3 Pre-Failure (June)", "2020-06-05 09:30:00", 1),
        ("Event #4 Pre-Failure (July)", "2020-07-15 14:00:00", 1),
        ("Normal Baseline (March)", "2020-03-01 12:00:00", 0),
        ("Normal Baseline (August)", "2020-08-10 12:00:00", 0)
    ]

    event_results = []
    for name, ts, true_target in events:
        target_dt = pd.to_datetime(ts)
        deltas = (df['timestamp'] - target_dt).abs()
        idx = deltas.idxmin()
        row = df.loc[idx]
        
        # XGBoost inference
        f_dict = {f: float(row[f]) for f in FEATURE_NAMES}
        xgb_res = predictor.predict(f_dict)
        
        # Anomaly score
        row_feat_vec = np.array([[float(row[f]) for f in features_to_use]])
        raw_anomaly_score = float(-iso_forest.score_samples(row_feat_vec)[0])
        is_anom = raw_anomaly_score >= selected_threshold
        
        event_results.append({
            "name": name,
            "timestamp": str(row['timestamp']),
            "target": true_target,
            "xgb_prob": xgb_res['risk_probability'],
            "xgb_risk_pct": xgb_res['risk_percentage'],
            "xgb_status": xgb_res['status'],
            "anomaly_score": round(raw_anomaly_score, 4),
            "anomaly_detected": is_anom,
            "anomaly_threshold": round(selected_threshold, 4)
        })
        
        print(f">>> {name:<32}:")
        print(f"    Timestamp:            {row['timestamp']}")
        print(f"    Target:               {true_target} ({row['failure_status']})")
        print(f"    XGBoost Risk:         {xgb_res['risk_percentage']:>6.2f}% (Prob: {xgb_res['risk_probability']:.6f} | {xgb_res['status']})")
        print(f"    Anomaly Score:        {raw_anomaly_score:.4f} (Threshold: {selected_threshold:.4f} -> {'ANOMALY DETECTED' if is_anom else 'NORMAL'})")
        print("-" * 90)

    # 8. Full Untouched Final Test Set Evaluation
    print("\n" + "=" * 90)
    print(" FULL UNTOUCHED FINAL TEST SET EVALUATION (JULY - AUGUST 2020)")
    print("=" * 90)
    
    test_df = df[test_mask].copy()
    X_test = test_df[features_to_use].values
    y_test = test_df['target'].values
    
    test_scores = -iso_forest.score_samples(X_test)
    test_roc_auc = roc_auc_score(y_test, test_scores)
    test_pr_auc = average_precision_score(y_test, test_scores)
    
    test_pos_scores = test_scores[y_test == 1]
    test_neg_scores = test_scores[y_test == 0]
    
    print(f"Final Test Rows:          {len(test_df):,} (Positives: {(y_test == 1).sum():,})")
    print(f"Final Test ROC-AUC:       {test_roc_auc:.4f}")
    print(f"Final Test PR-AUC:        {test_pr_auc:.4f}")
    print(f"Final Test Pos Score Mean: {test_pos_scores.mean():.4f} (med {np.median(test_pos_scores):.4f})")
    print(f"Final Test Neg Score Mean: {test_neg_scores.mean():.4f} (med {np.median(test_neg_scores):.4f})")

    # Classification metrics at selected threshold
    y_pred_anom = (test_scores >= selected_threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred_anom).ravel()
    prec = precision_score(y_test, y_pred_anom, zero_division=0)
    rec = recall_score(y_test, y_pred_anom, zero_division=0)
    f1 = f1_score(y_test, y_pred_anom, zero_division=0)
    
    print(f"\nIsolation Forest Confusion Matrix on Final Test (th={selected_threshold:.4f}):")
    print(f"   TP = {tp:>5} | FP = {fp:>6}")
    print(f"   FN = {fn:>5} | TN = {tn:>6}")
    print(f"   Precision: {prec * 100:.2f}%")
    print(f"   Recall:    {rec * 100:.2f}% (Event #4 pre-failure detection rate)")
    print(f"   F1-Score:  {f1:.4f}")

    # 9. Hybrid Strategy Simulation
    print("\n" + "=" * 90)
    print(" PART 6 — HYBRID STRATEGY SIMULATION ON FINAL TEST")
    print("=" * 90)
    
    # Calculate XGBoost probabilities on full final test (sample for speed or vector batch)
    print("Computing XGBoost probabilities on Final Test...")
    xgb_test_probs = predictor.model.predict_proba(X_test)[:, 1]
    
    xgb_th = 0.10
    anom_th = selected_threshold
    
    # Strategy 1: XGBoost Only (Baseline)
    y_pred_xgb = (xgb_test_probs >= xgb_th).astype(int)
    tn1, fp1, fn1, tp1 = confusion_matrix(y_test, y_pred_xgb).ravel()
    
    # Strategy 2: Anomaly Only
    y_pred_anom_only = (test_scores >= anom_th).astype(int)
    tn2, fp2, fn2, tp2 = confusion_matrix(y_test, y_pred_anom_only).ravel()
    
    # Strategy 3: Hybrid OR (XGBoost >= 0.10 OR Anomaly >= threshold)
    y_pred_hybrid_or = ((xgb_test_probs >= xgb_th) | (test_scores >= anom_th)).astype(int)
    tn3, fp3, fn3, tp3 = confusion_matrix(y_test, y_pred_hybrid_or).ravel()
    
    # Strategy 4: High Confidence Hybrid (XGBoost >= 0.10 OR Anomaly >= 99.5th pct)
    y_pred_hybrid_high = ((xgb_test_probs >= xgb_th) | (test_scores >= threshold_val_995)).astype(int)
    tn4, fp4, fn4, tp4 = confusion_matrix(y_test, y_pred_hybrid_high).ravel()

    strategies = [
        ("1. XGBoost Only (Baseline th=0.10)", tp1, fp1, tn1, fn1, y_test, y_pred_xgb),
        ("2. Anomaly Only (Isolation Forest)", tp2, fp2, tn2, fn2, y_test, y_pred_anom_only),
        ("3. Hybrid OR (XGBoost OR Anomaly)", tp3, fp3, tn3, fn3, y_test, y_pred_hybrid_or),
        ("4. Hybrid Conservative (XGB OR Anom_99.5%)", tp4, fp4, tn4, fn4, y_test, y_pred_hybrid_high),
    ]

    print(f"{'Strategy':<42} | {'TP':<5} | {'FP':<7} | {'FN':<5} | {'Recall':<8} | {'Precision':<10} | {'F1':<8}")
    print("-" * 96)
    for s_name, s_tp, s_fp, s_tn, s_fn, y_t, y_p in strategies:
        s_rec = recall_score(y_t, y_p, zero_division=0) * 100
        s_prec = precision_score(y_t, y_p, zero_division=0) * 100
        s_f1 = f1_score(y_t, y_p, zero_division=0)
        print(f"{s_name:<42} | {s_tp:>5} | {s_fp:>7} | {s_fn:>5} | {s_rec:>7.2f}% | {s_prec:>9.2f}% | {s_f1:>8.4f}")
    print("=" * 90)

    # 10. Physical Feature Interpretation for Event #4
    print("\n" + "=" * 90)
    print(" PART 7 — PHYSICAL FEATURE ATTRIBUTION FOR EVENT #4")
    print("=" * 90)
    ev4_df = df[test_mask & (df['target'] == 1)]
    ev4_row = ev4_df.iloc[len(ev4_df)//2]
    
    # Compare against normal training median
    train_normal_medians = train_normal_df[features_to_use].median()
    train_normal_stds = train_normal_df[features_to_use].std()
    
    z_scores = {}
    for f in features_to_use:
        std_val = train_normal_stds[f] if train_normal_stds[f] > 1e-6 else 1.0
        z_scores[f] = (ev4_row[f] - train_normal_medians[f]) / std_val
        
    sorted_anom_feats = sorted(z_scores.items(), key=lambda x: abs(x[1]), reverse=True)
    print(f"Event #4 Peak Observation ({ev4_row['timestamp']}) vs Normal Baseline Z-Scores (Top 10):")
    for f, z in sorted_anom_feats[:10]:
        val_act = ev4_row[f]
        val_norm = train_normal_medians[f]
        print(f"  - {f:<30}: Actual = {val_act:>8.4f} | Normal Median = {val_norm:>8.4f} | Z-Score = {z:>+6.2f} std devs")
    print("=" * 90)

if __name__ == "__main__":
    main()
