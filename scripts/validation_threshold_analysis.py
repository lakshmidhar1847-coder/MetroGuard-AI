"""
MetroGuard AI - Task 13: Validation-Only Threshold Analysis
Evaluates Random Forest and XGBoost across a fine-grained grid of decision thresholds
exclusively on the VALIDATION partition (Event #3, June 2020) without touching the test set.
"""

import os
import joblib
import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    average_precision_score,
    roc_auc_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)

THRESHOLDS = [
    0.001, 0.002, 0.003, 0.005, 0.007,
    0.010, 0.020, 0.030, 0.050, 0.070,
    0.100, 0.150, 0.200, 0.300, 0.500
]

def run_validation_threshold_analysis():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    features_csv = os.path.join(base_dir, "data", "processed", "metropt3_features.csv")
    models_dir = os.path.join(base_dir, "models")
    xgb_path = os.path.join(models_dir, "metroguard_model.pkl")
    out_csv = os.path.join(models_dir, "validation_threshold_analysis.csv")
    
    print("=" * 85)
    print(" METROGUARD AI - TASK 13: VALIDATION-ONLY THRESHOLD ANALYSIS")
    print("=" * 85)
    
    # 1. Load feature dataset & filter to VALIDATION partition only
    print("Loading dataset and extracting VALIDATION set (June 2020, Event #3)...")
    df = pd.read_csv(features_csv)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    t_val_start = pd.Timestamp('2020-06-01 00:00:00')
    t_test_start = pd.Timestamp('2020-07-01 00:00:00')
    
    train_mask = df['timestamp'] < t_val_start
    val_mask = (df['timestamp'] >= t_val_start) & (df['timestamp'] < t_test_start)
    
    train_df = df[train_mask]
    val_df = df[val_mask]
    
    metadata_cols = ['timestamp', 'failure_status', 'target']
    feature_cols = [c for c in df.columns if c not in metadata_cols]
    
    X_train = train_df[feature_cols].values
    y_train = train_df['target'].values
    
    X_val = val_df[feature_cols].values
    y_val = val_df['target'].values
    
    print(f"Validation Records : {len(val_df):,}")
    print(f"Validation Positives: {(y_val == 1).sum():,}")
    print(f"Validation Negatives: {(y_val == 0).sum():,}")
    
    # 2. Load XGBoost and fit identical Random Forest on TRAIN
    print("\nLoading XGBoost model artifact...")
    xgb_model = joblib.load(xgb_path)
    
    print("Fitting Random Forest on TRAIN partition (random_state=42)...")
    rf_model = RandomForestClassifier(
        n_estimators=150, max_depth=15, min_samples_leaf=5, class_weight='balanced_subsample', random_state=42, n_jobs=-1
    )
    rf_model.fit(X_train, y_train)
    
    # 3. Compute predicted probabilities on VALIDATION ONLY
    print("Computing predicted probabilities on validation partition...")
    p_rf = rf_model.predict_proba(X_val)[:, 1]
    p_xgb = xgb_model.predict_proba(X_val)[:, 1]
    
    # Threshold-independent metrics
    rf_pr_auc = float(average_precision_score(y_val, p_rf))
    rf_roc_auc = float(roc_auc_score(y_val, p_rf))
    xgb_pr_auc = float(average_precision_score(y_val, p_xgb))
    xgb_roc_auc = float(roc_auc_score(y_val, p_xgb))
    
    print("\n--- THRESHOLD-INDEPENDENT VALIDATION METRICS ---")
    print(f"Random Forest : PR-AUC = {rf_pr_auc:.6f}, ROC-AUC = {rf_roc_auc:.6f}")
    print(f"XGBoost       : PR-AUC = {xgb_pr_auc:.6f}, ROC-AUC = {xgb_roc_auc:.6f}")
    
    # 4. Sweep thresholds for both models
    results = []
    
    for mname, probs, pr_auc, roc_auc in [("Random Forest", p_rf, rf_pr_auc, rf_roc_auc), ("XGBoost", p_xgb, xgb_pr_auc, xgb_roc_auc)]:
        for th in THRESHOLDS:
            preds = (probs >= th).astype(int)
            
            p = float(precision_score(y_val, preds, zero_division=0))
            r = float(recall_score(y_val, preds, zero_division=0))
            f = float(f1_score(y_val, preds, zero_division=0))
            
            cm = confusion_matrix(y_val, preds)
            tn, fp, fn, tp = cm.ravel()
            
            fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
            
            results.append({
                "Model": mname,
                "Threshold": th,
                "PR_AUC": pr_auc,
                "ROC_AUC": roc_auc,
                "Precision": p,
                "Recall": r,
                "F1": f,
                "TP": int(tp),
                "FP": int(fp),
                "TN": int(tn),
                "FN": int(fn),
                "FPR": fpr
            })
            
    res_df = pd.DataFrame(results)
    res_df.to_csv(out_csv, index=False)
    print(f"\nFull validation threshold analysis saved to: {out_csv}")
    
    # Print formatted comparison tables
    print("\n" + "=" * 90)
    print(" RANDOM FOREST VALIDATION THRESHOLD ANALYSIS")
    print("=" * 90)
    rf_table = res_df[res_df["Model"] == "Random Forest"][["Threshold", "Precision", "Recall", "F1", "TP", "FP", "FN", "FPR"]]
    print(rf_table.to_string(index=False))
    
    print("\n" + "=" * 90)
    print(" XGBOOST VALIDATION THRESHOLD ANALYSIS")
    print("=" * 90)
    xgb_table = res_df[res_df["Model"] == "XGBoost"][["Threshold", "Precision", "Recall", "F1", "TP", "FP", "FN", "FPR"]]
    print(xgb_table.to_string(index=False))
    print("=" * 90)
    
    return res_df

if __name__ == "__main__":
    run_validation_threshold_analysis()
