"""
MetroGuard AI - Task 16: Final Untouched Test Evaluation of Enhanced XGBoost
Evaluates the frozen Enhanced XGBoost model on the untouched Final Test partition (Event #4 + August 2020 holdout).
"""

import os
import json
import time
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from xgboost import XGBClassifier
from sklearn.metrics import (
    average_precision_score,
    roc_auc_score,
    precision_score,
    recall_score,
    f1_score,
    accuracy_score,
    confusion_matrix
)

EPS = 1e-4
FROZEN_THRESHOLD = 0.007

def run_final_test_evaluation():
    start_time = time.time()
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    orig_features_csv = os.path.join(base_dir, "data", "processed", "metropt3_features.csv")
    models_dir = os.path.join(base_dir, "models")
    
    print("=" * 85)
    print(" METROGUARD AI - TASK 16: FINAL UNTOUCHED TEST EVALUATION")
    print("=" * 85)
    print(f"Frozen Model     : Enhanced XGBoost (119 Features, hist tree method)")
    print(f"Frozen Threshold : {FROZEN_THRESHOLD} (Selected strictly via Validation)")
    
    # 1. Load dataset
    print("\n[Step 1/6] Loading feature dataset...")
    df = pd.read_csv(orig_features_csv)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    metadata_cols = ['timestamp', 'failure_status', 'target']
    original_feature_cols = [c for c in df.columns if c not in metadata_cols]
    
    # 2. Build exact 54 generalized features
    print("[Step 2/6] Constructing exact 54 generalized features...")
    new_features_dict = {}
    
    # Category A: Relative Pressure Features
    new_features_dict["TP3_minus_Reservoirs"] = (df["TP3"] - df["Reservoirs"]).astype("float32")
    new_features_dict["TP3_abs_diff_Reservoirs"] = (df["TP3"] - df["Reservoirs"]).abs().astype("float32")
    new_features_dict["TP3_ratio_Reservoirs"] = (df["TP3"] / (df["Reservoirs"] + EPS)).astype("float32")
    new_features_dict["TP2_minus_H1"] = (df["TP2"] - df["H1"]).astype("float32")
    new_features_dict["TP2_abs_diff_H1"] = (df["TP2"] - df["H1"]).abs().astype("float32")
    new_features_dict["TP3_minus_TP2"] = (df["TP3"] - df["TP2"]).astype("float32")
    new_features_dict["DV_pressure_minus_TP2"] = (df["DV_pressure"] - df["TP2"]).astype("float32")
    
    # Category B: Rolling Baseline Deviation & Standardized Residuals
    continuous_channels = ['TP2', 'TP3', 'H1', 'Reservoirs', 'DV_pressure', 'Oil_temperature', 'Motor_current']
    for ch in continuous_channels:
        new_features_dict[f"{ch}_dev_mean_5m"] = (df[ch] - df[f"{ch}_roll_mean_5m"]).astype("float32")
        new_features_dict[f"{ch}_zscore_5m"] = ((df[ch] - df[f"{ch}_roll_mean_5m"]) / (df[f"{ch}_roll_std_5m"] + EPS)).astype("float32")
        new_features_dict[f"{ch}_dev_mean_1m"] = (df[ch] - df[f"{ch}_roll_mean_1m"]).astype("float32")

    # Category C: Multi-Scale Volatility Ratios
    turbulent_channels = ['TP2', 'TP3', 'H1', 'Reservoirs', 'DV_pressure', 'Motor_current']
    for ch in turbulent_channels:
        new_features_dict[f"{ch}_vol_ratio_1m_to_5m"] = (df[f"{ch}_roll_std_1m"] / (df[f"{ch}_roll_std_5m"] + EPS)).astype("float32")
        new_features_dict[f"{ch}_vol_ratio_5m_to_1m"] = (df[f"{ch}_roll_std_5m"] / (df[f"{ch}_roll_std_1m"] + EPS)).astype("float32")

    # Category D: Coefficient of Variation
    for ch in turbulent_channels:
        new_features_dict[f"{ch}_cv_5m"] = (df[f"{ch}_roll_std_5m"] / (df[f"{ch}_roll_mean_5m"].abs() + EPS)).astype("float32")
        new_features_dict[f"{ch}_cv_1m"] = (df[f"{ch}_roll_std_1m"] / (df[f"{ch}_roll_mean_1m"].abs() + EPS)).astype("float32")

    # Category E: Electro-Pneumatic Coupling
    new_features_dict["TP3_per_Current"] = (df["TP3"] / (df["Motor_current"] + EPS)).astype("float32")
    new_features_dict["TP2_per_Current"] = (df["TP2"] / (df["Motor_current"] + EPS)).astype("float32")

    new_features_df = pd.DataFrame(new_features_dict).replace([np.inf, -np.inf], np.nan).fillna(0.0).clip(lower=-1e4, upper=1e4)
    all_feature_cols = original_feature_cols + list(new_features_dict.keys())
    
    enhanced_df = pd.concat([df[['timestamp', 'failure_status', 'target'] + original_feature_cols], new_features_df], axis=1)

    # 3. Partition chronological splits
    t_val_start = pd.Timestamp('2020-06-01 00:00:00')
    t_test_start = pd.Timestamp('2020-07-01 00:00:00')
    
    train_mask = enhanced_df['timestamp'] < t_val_start
    test_mask = enhanced_df['timestamp'] >= t_test_start
    
    train_df = enhanced_df[train_mask]
    test_df = enhanced_df[test_mask]
    
    X_train = train_df[all_feature_cols].values
    y_train = train_df['target'].values
    
    X_test = test_df[all_feature_cols].values
    y_test = test_df['target'].values
    
    # Verify Final Test Partition
    test_start_ts = test_df['timestamp'].min()
    test_end_ts = test_df['timestamp'].max()
    test_total_rows = len(test_df)
    test_pos_rows = int((y_test == 1).sum())
    test_neg_rows = int((y_test == 0).sum())
    test_pos_pct = (test_pos_rows / test_total_rows) * 100
    
    print("\n--- FINAL TEST PARTITION VERIFICATION ---")
    print(f"  Start Timestamp   : {test_start_ts}")
    print(f"  End Timestamp     : {test_end_ts}")
    print(f"  Total Rows        : {test_total_rows:,}")
    print(f"  Positive Rows     : {test_pos_rows:,} (Event #4)")
    print(f"  Negative Rows     : {test_neg_rows:,}")
    print(f"  Positive Rate     : {test_pos_pct:.4f}%")
    print(f"  Events Included   : Event #4 + July/August 2020 holdout")
    
    if test_pos_rows == 0:
        raise ValueError("Final test partition contains 0 positive samples! Aborting.")

    # 4. Train Frozen Enhanced XGBoost on TRAIN ONLY
    print("\n[Step 3/6] Training Frozen Enhanced XGBoost model on TRAIN partition ONLY...")
    neg_pos_ratio = float((y_train == 0).sum() / (y_train == 1).sum())
    xgb_enh = XGBClassifier(
        tree_method="hist",
        n_estimators=150,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=neg_pos_ratio,
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1
    )
    xgb_enh.fit(X_train, y_train)
    print("Model training on TRAIN complete.")

    # 5. Evaluate on FINAL TEST
    print("\n[Step 4/6] Generating predictions on UNTOUCHED FINAL TEST SET...")
    test_probs = xgb_enh.predict_proba(X_test)[:, 1]
    test_preds = (test_probs >= FROZEN_THRESHOLD).astype(int)
    
    pr_auc = float(average_precision_score(y_test, test_probs))
    roc_auc = float(roc_auc_score(y_test, test_probs))
    precision = float(precision_score(y_test, test_preds, zero_division=0))
    recall = float(recall_score(y_test, test_preds, zero_division=0))
    f1 = float(f1_score(y_test, test_preds, zero_division=0))
    acc = float(accuracy_score(y_test, test_preds))
    
    cm = confusion_matrix(y_test, test_preds)
    tn, fp, fn, tp = cm.ravel()
    
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
    specificity = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
    
    # Event #4 specific probability stats
    event4_pos_mask = (y_test == 1)
    ev4_probs = test_probs[event4_pos_mask]
    
    ev4_total = int(event4_pos_mask.sum())
    ev4_detected = int(tp)
    ev4_missed = int(fn)
    ev4_recall = float(tp / ev4_total)
    
    ev4_max_p = float(np.max(ev4_probs))
    ev4_med_p = float(np.median(ev4_probs))
    ev4_mean_p = float(np.mean(ev4_probs))
    ev4_p95_p = float(np.percentile(ev4_probs, 95))
    
    print("\n" + "=" * 85)
    print(" FINAL UNTOUCHED TEST RESULTS: ENHANCED XGBOOST")
    print("=" * 85)
    print(f"  PR-AUC (Average Precision) : {pr_auc:.6f}")
    print(f"  ROC-AUC                    : {roc_auc:.6f}")
    print(f"  Precision                  : {precision:.6f}")
    print(f"  Recall                     : {recall:.6f} ({tp} / {ev4_total})")
    print(f"  F1-Score                   : {f1:.6f}")
    print(f"  Accuracy                   : {acc:.6f}")
    print(f"  False Positive Rate (FPR)  : {fpr:.6f} ({fpr*100:.2f}%)")
    print(f"  Specificity                : {specificity:.6f} ({specificity*100:.2f}%)")
    print("-" * 85)
    print(f"  Confusion Matrix: TN={tn:,} | FP={fp:,} | FN={fn:,} | TP={tp:,}")
    print("-" * 85)
    print("  Event #4 Breakdown:")
    print(f"    Positive Rows  : {ev4_total}")
    print(f"    Detected (TP)  : {ev4_detected}")
    print(f"    Missed (FN)    : {ev4_missed}")
    print(f"    Recall Rate    : {ev4_recall:.4f} ({ev4_recall*100:.2f}%)")
    print(f"    Max Predicted P: {ev4_max_p:.6f}")
    print(f"    Median Pred P  : {ev4_med_p:.6f}")
    print(f"    Mean Pred P    : {ev4_mean_p:.6f}")
    print(f"    95th Pct Pred P: {ev4_p95_p:.6f}")
    print("=" * 85)

    # 6. Compare with Baseline XGBoost
    print("\n[Step 5/6] Building Baseline vs Enhanced Final Test Comparison Table...")
    comparison_data = [
        {
            "Model": "Baseline XGBoost (65 Features)",
            "PR_AUC": 0.000300,
            "ROC_AUC": 0.431600,
            "Precision": 0.000000,
            "Recall": 0.000000,
            "F1": 0.000000,
            "Accuracy": 0.977669,
            "TP": 0,
            "FP": 9689,
            "TN": 432110,
            "FN": 181,
            "FPR": 0.021931
        },
        {
            "Model": "Enhanced XGBoost (119 Features)",
            "PR_AUC": pr_auc,
            "ROC_AUC": roc_auc,
            "Precision": precision,
            "Recall": recall,
            "F1": f1,
            "Accuracy": acc,
            "TP": int(tp),
            "FP": int(fp),
            "TN": int(tn),
            "FN": int(fn),
            "FPR": fpr
        }
    ]
    comp_df = pd.DataFrame(comparison_data)
    comp_csv_path = os.path.join(models_dir, "final_test_model_comparison.csv")
    comp_df.to_csv(comp_csv_path, index=False)
    print(f"  Saved comparison to: {comp_csv_path}")

    # 7. Save Final Test Predictions CSV
    print("\n[Step 6/6] Saving Final Test Artifacts...")
    preds_df = pd.DataFrame({
        "timestamp": test_df["timestamp"],
        "actual_target": y_test,
        "predicted_probability": test_probs.round(6),
        "predicted_class": test_preds
    })
    preds_csv_path = os.path.join(models_dir, "final_test_predictions.csv")
    preds_df.to_csv(preds_csv_path, index=False)
    print(f"  Saved final test predictions to: {preds_csv_path} ({os.path.getsize(preds_csv_path)/(1024*1024):.2f} MB)")

    # Save Confusion Matrix Plot
    cm_plot_path = os.path.join(models_dir, "enhanced_confusion_matrix.png")
    plt.figure(figsize=(6, 5))
    sns.heatmap(
        cm, annot=True, fmt=',d', cmap='Blues',
        xticklabels=['Predicted Normal (0)', 'Predicted Failure (1)'],
        yticklabels=['Actual Normal (0)', 'Actual Failure (1)']
    )
    plt.title(f"Enhanced XGBoost Final Test Confusion Matrix\n(Threshold = {FROZEN_THRESHOLD})")
    plt.tight_layout()
    plt.savefig(cm_plot_path, dpi=150)
    plt.close()
    print(f"  Saved confusion matrix plot to: {cm_plot_path}")

    # Update saved model artifact and metadata to Enhanced XGBoost
    model_pkl_path = os.path.join(models_dir, "metroguard_model.pkl")
    joblib.dump(xgb_enh, model_pkl_path)
    print(f"  Updated model artifact: {model_pkl_path}")
    
    # Feature importances for enhanced model
    importances = xgb_enh.feature_importances_
    feat_imp_df = pd.DataFrame({
        'feature': all_feature_cols,
        'importance': importances
    }).sort_values('importance', ascending=False).reset_index(drop=True)
    feat_imp_path = os.path.join(models_dir, "feature_importance.csv")
    feat_imp_df.to_csv(feat_imp_path, index=False)

    metadata_path = os.path.join(models_dir, "model_metadata.json")
    with open(metadata_path, 'r') as f:
        meta = json.load(f)
        
    meta["model_name"] = "Enhanced XGBoost Classifier"
    meta["feature_names"] = all_feature_cols
    meta["selected_threshold"] = FROZEN_THRESHOLD
    meta["final_test_metrics"] = {
        "pr_auc": pr_auc,
        "roc_auc": roc_auc,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": acc,
        "tp": int(tp),
        "fp": int(fp),
        "tn": int(tn),
        "fn": int(fn),
        "fpr": fpr,
        "specificity": specificity,
        "event4_max_probability": ev4_max_p,
        "event4_median_probability": ev4_med_p,
        "event4_mean_probability": ev4_mean_p,
        "event4_p95_probability": ev4_p95_p
    }
    meta["top_15_features"] = feat_imp_df.head(15).to_dict(orient='records')
    
    with open(metadata_path, 'w') as f:
        json.dump(meta, f, indent=2)
    print(f"  Updated metadata to: {metadata_path}")

    total_time = time.time() - start_time
    print(f"\nFinal test evaluation completed in {total_time:.2f} seconds.")
    
    return {
        "test_metrics": {
            "pr_auc": pr_auc,
            "roc_auc": roc_auc,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "accuracy": acc,
            "tp": int(tp),
            "fp": int(fp),
            "tn": int(tn),
            "fn": int(fn)
        },
        "event4_stats": {
            "total": ev4_total,
            "detected": ev4_detected,
            "missed": ev4_missed,
            "recall": ev4_recall,
            "max_p": ev4_max_p,
            "median_p": ev4_med_p,
            "mean_p": ev4_mean_p
        },
        "comparison": comparison_data
    }

if __name__ == "__main__":
    run_final_test_evaluation()
