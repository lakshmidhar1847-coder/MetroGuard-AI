"""
MetroGuard AI - Model Training & Validation Pipeline
Trains and validates real machine learning models (Random Forest & XGBoost)
on the Event-Aligned Chronological Split of the MetroPT-3 compressor telemetry.
"""

import os
import json
import time
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.ensemble import RandomForestClassifier
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

def run_training_pipeline():
    start_time = time.time()
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    features_csv = os.path.join(base_dir, "data", "processed", "metropt3_features.csv")
    models_dir = os.path.join(base_dir, "models")
    os.makedirs(models_dir, exist_ok=True)
    
    print("=" * 80)
    print(" METROGUARD AI - MODEL TRAINING & TEMPORAL VALIDATION")
    print("=" * 80)
    
    # 1. Load feature dataset
    print("\n[Step 1/8] Loading features dataset...")
    df = pd.read_csv(features_csv)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    metadata_cols = ['timestamp', 'failure_status', 'target']
    feature_cols = [c for c in df.columns if c not in metadata_cols]
    print(f"Total rows: {len(df):,}")
    print(f"Feature count: {len(feature_cols)}")
    
    # 2. Event-aligned chronological partition
    print("\n[Step 2/8] Partitioning data using Event-Aligned Chronological Split...")
    t_val_start = pd.Timestamp('2020-06-01 00:00:00')
    t_test_start = pd.Timestamp('2020-07-01 00:00:00')
    
    train_mask = df['timestamp'] < t_val_start
    val_mask = (df['timestamp'] >= t_val_start) & (df['timestamp'] < t_test_start)
    test_mask = df['timestamp'] >= t_test_start
    
    train_df = df[train_mask].copy()
    val_df = df[val_mask].copy()
    test_df = df[test_mask].copy()
    
    partitions = [
        ("TRAIN", train_df, "Events #1 & #2"),
        ("VALIDATION", val_df, "Event #3"),
        ("FINAL TEST", test_df, "Event #4 + August holdout")
    ]
    
    split_info = {}
    print("-" * 80)
    print(f"{'Partition':<12} | {'Start Time':<19} | {'End Time':<19} | {'Total':<10} | {'Positives':<9} | {'Pos %':<8} | {'Events':<20}")
    print("-" * 80)
    
    for name, p_df, ev_name in partitions:
        p_start = p_df['timestamp'].min()
        p_end = p_df['timestamp'].max()
        p_total = len(p_df)
        p_pos = int((p_df['target'] == 1).sum())
        p_neg = int((p_df['target'] == 0).sum())
        p_pct = (p_pos / p_total) * 100 if p_total > 0 else 0.0
        
        split_info[name] = {
            "start": str(p_start),
            "end": str(p_end),
            "total": p_total,
            "positives": p_pos,
            "negatives": p_neg,
            "positive_pct": p_pct,
            "events": ev_name
        }
        
        print(f"{name:<12} | {str(p_start):<19} | {str(p_end):<19} | {p_total:<10,} | {p_pos:<9,} | {p_pct:<7.4f}% | {ev_name:<20}")
        
        if p_pos == 0:
            raise ValueError(f"Partition {name} unexpectedly contains 0 positive samples! Aborting.")
            
    print("-" * 80)
    
    X_train = train_df[feature_cols].values
    y_train = train_df['target'].values
    
    X_val = val_df[feature_cols].values
    y_val = val_df['target'].values
    
    X_test = test_df[feature_cols].values
    y_test = test_df['target'].values
    
    # 3. Train Random Forest
    print("\n[Step 3/8] Training RandomForestClassifier (n_estimators=150, max_depth=15, min_samples_leaf=5)...")
    rf_start = time.time()
    rf_model = RandomForestClassifier(
        n_estimators=150,
        max_depth=15,
        min_samples_leaf=5,
        class_weight="balanced_subsample",
        random_state=42,
        n_jobs=-1
    )
    rf_model.fit(X_train, y_train)
    rf_time = time.time() - rf_start
    print(f"Random Forest trained in {rf_time:.2f} seconds.")
    
    # 4. Train XGBoost
    print("\n[Step 4/8] Training XGBClassifier (tree_method='hist', n_estimators=150, max_depth=6)...")
    xgb_start = time.time()
    neg_pos_ratio = float((y_train == 0).sum() / (y_train == 1).sum())
    print(f"Calculated scale_pos_weight for XGBoost: {neg_pos_ratio:.2f}")
    
    xgb_model = XGBClassifier(
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
    xgb_model.fit(X_train, y_train)
    xgb_time = time.time() - xgb_start
    print(f"XGBoost trained in {xgb_time:.2f} seconds.")
    
    # 5. Evaluate on Validation Set
    print("\n[Step 5/8] Evaluating Models on VALIDATION SET (Event #3)...")
    rf_val_proba = rf_model.predict_proba(X_val)[:, 1]
    xgb_val_proba = xgb_model.predict_proba(X_val)[:, 1]
    
    rf_pr_auc = float(average_precision_score(y_val, rf_val_proba))
    rf_roc_auc = float(roc_auc_score(y_val, rf_val_proba))
    
    xgb_pr_auc = float(average_precision_score(y_val, xgb_val_proba))
    xgb_roc_auc = float(roc_auc_score(y_val, xgb_val_proba))
    
    thresholds = [0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70]
    
    print("\n--- Validation Threshold Evaluation: Random Forest ---")
    print(f"{'Threshold':<10} | {'Precision':<12} | {'Recall':<12} | {'F1-Score':<12}")
    print("-" * 55)
    rf_thresh_results = {}
    for th in thresholds:
        preds = (rf_val_proba >= th).astype(int)
        p = float(precision_score(y_val, preds, zero_division=0))
        r = float(recall_score(y_val, preds, zero_division=0))
        f = float(f1_score(y_val, preds, zero_division=0))
        rf_thresh_results[th] = {"precision": p, "recall": r, "f1": f}
        print(f"{th:<10.2f} | {p:<12.4f} | {r:<12.4f} | {f:<12.4f}")
        
    print("\n--- Validation Threshold Evaluation: XGBoost ---")
    print(f"{'Threshold':<10} | {'Precision':<12} | {'Recall':<12} | {'F1-Score':<12}")
    print("-" * 55)
    xgb_thresh_results = {}
    for th in thresholds:
        preds = (xgb_val_proba >= th).astype(int)
        p = float(precision_score(y_val, preds, zero_division=0))
        r = float(recall_score(y_val, preds, zero_division=0))
        f = float(f1_score(y_val, preds, zero_division=0))
        xgb_thresh_results[th] = {"precision": p, "recall": r, "f1": f}
        print(f"{th:<10.2f} | {p:<12.4f} | {r:<12.4f} | {f:<12.4f}")
        
    # Best threshold selection for each
    rf_best_th = max(rf_thresh_results, key=lambda t: rf_thresh_results[t]['f1'])
    xgb_best_th = max(xgb_thresh_results, key=lambda t: xgb_thresh_results[t]['f1'])
    
    # 6. Model Comparison & Selection
    print("\n[Step 6/8] MODEL COMPARISON ON VALIDATION SET:")
    print("=" * 80)
    print(f"{'Model':<16} | {'PR-AUC':<10} | {'ROC-AUC':<10} | {'Best Thresh':<12} | {'Precision':<10} | {'Recall':<10} | {'F1':<10}")
    print("-" * 80)
    print(f"{'Random Forest':<16} | {rf_pr_auc:<10.4f} | {rf_roc_auc:<10.4f} | {rf_best_th:<12.2f} | {rf_thresh_results[rf_best_th]['precision']:<10.4f} | {rf_thresh_results[rf_best_th]['recall']:<10.4f} | {rf_thresh_results[rf_best_th]['f1']:<10.4f}")
    print(f"{'XGBoost':<16} | {xgb_pr_auc:<10.4f} | {xgb_roc_auc:<10.4f} | {xgb_best_th:<12.2f} | {xgb_thresh_results[xgb_best_th]['precision']:<10.4f} | {xgb_thresh_results[xgb_best_th]['recall']:<10.4f} | {xgb_thresh_results[xgb_best_th]['f1']:<10.4f}")
    print("=" * 80)
    
    # Select winner based primarily on PR-AUC and F1
    if xgb_pr_auc >= rf_pr_auc:
        selected_model_name = "XGBoost"
        selected_model = xgb_model
        selected_threshold = xgb_best_th
        val_metrics = {
            "pr_auc": xgb_pr_auc,
            "roc_auc": xgb_roc_auc,
            "threshold": xgb_best_th,
            "precision": xgb_thresh_results[xgb_best_th]['precision'],
            "recall": xgb_thresh_results[xgb_best_th]['recall'],
            "f1": xgb_thresh_results[xgb_best_th]['f1']
        }
    else:
        selected_model_name = "Random Forest"
        selected_model = rf_model
        selected_threshold = rf_best_th
        val_metrics = {
            "pr_auc": rf_pr_auc,
            "roc_auc": rf_roc_auc,
            "threshold": rf_best_th,
            "precision": rf_thresh_results[rf_best_th]['precision'],
            "recall": rf_thresh_results[rf_best_th]['recall'],
            "f1": rf_thresh_results[rf_best_th]['f1']
        }
        
    print(f"\n>>> SELECTED BEST MODEL: {selected_model_name} (Threshold = {selected_threshold:.2f}) <<<")
    
    # 7. Final Test Evaluation (Untouched Test Set)
    print("\n[Step 7/8] Evaluating Selected Model on UNTOUCHED FINAL TEST SET (Event #4)...")
    test_proba = selected_model.predict_proba(X_test)[:, 1]
    test_preds = (test_proba >= selected_threshold).astype(int)
    
    test_pr_auc = float(average_precision_score(y_test, test_proba))
    test_roc_auc = float(roc_auc_score(y_test, test_proba))
    test_prec = float(precision_score(y_test, test_preds, zero_division=0))
    test_rec = float(recall_score(y_test, test_preds, zero_division=0))
    test_f1 = float(f1_score(y_test, test_preds, zero_division=0))
    test_acc = float(accuracy_score(y_test, test_preds))
    
    cm = confusion_matrix(y_test, test_preds)
    tn, fp, fn, tp = cm.ravel()
    
    print("\n" + "=" * 65)
    print(" FINAL UNTOUCHED TEST EVALUATION RESULTS")
    print("=" * 65)
    print(f"  Model Evaluated  : {selected_model_name}")
    print(f"  Decision Thresh  : {selected_threshold:.2f}")
    print(f"  PR-AUC (Avg Prec): {test_pr_auc:.4f}")
    print(f"  ROC-AUC          : {test_roc_auc:.4f}")
    print(f"  Precision        : {test_prec:.4f}")
    print(f"  Recall           : {test_rec:.4f} ({tp}/{tp+fn} failure intervals caught)")
    print(f"  F1-Score         : {test_f1:.4f}")
    print(f"  Accuracy         : {test_acc:.6f}")
    print("-" * 65)
    print("  Confusion Matrix:")
    print(f"    True Negatives  (TN): {tn:>10,}")
    print(f"    False Positives (FP): {fp:>10,}")
    print(f"    False Negatives (FN): {fn:>10,}")
    print(f"    True Positives  (TP): {tp:>10,}")
    print("=" * 65)

    test_metrics = {
        "pr_auc": test_pr_auc,
        "roc_auc": test_roc_auc,
        "precision": test_prec,
        "recall": test_rec,
        "f1": test_f1,
        "accuracy": test_acc,
        "confusion_matrix": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp)
        },
        "test_positives": int((y_test == 1).sum()),
        "test_negatives": int((y_test == 0).sum())
    }

    # 8. Feature Importance & Artifact Saving
    print("\n[Step 8/8] Generating Feature Importance, Artifacts, and Saving Models...")
    
    # Feature importances
    importances = selected_model.feature_importances_
    feat_imp_df = pd.DataFrame({
        'feature': feature_cols,
        'importance': importances
    }).sort_values('importance', ascending=False).reset_index(drop=True)
    
    feat_imp_path = os.path.join(models_dir, "feature_importance.csv")
    feat_imp_df.to_csv(feat_imp_path, index=False)
    print(f"  Feature importance saved: {feat_imp_path}")
    
    print("\n--- TOP 15 MOST IMPORTANT FEATURES ---")
    for idx, row in feat_imp_df.head(15).iterrows():
        print(f"  {idx+1:>2}. {row['feature']:<30} : {row['importance']:.4f}")

    # Plot confusion matrix
    cm_plot_path = os.path.join(models_dir, "confusion_matrix.png")
    plt.figure(figsize=(6, 5))
    sns.heatmap(
        cm, annot=True, fmt=',d', cmap='Blues',
        xticklabels=['Predicted Normal (0)', 'Predicted Failure (1)'],
        yticklabels=['Actual Normal (0)', 'Actual Failure (1)']
    )
    plt.title(f"{selected_model_name} Final Test Confusion Matrix\n(Threshold = {selected_threshold:.2f})")
    plt.tight_layout()
    plt.savefig(cm_plot_path, dpi=150)
    plt.close()
    print(f"  Confusion matrix plot saved: {cm_plot_path}")

    # Save model
    model_pkl_path = os.path.join(models_dir, "metroguard_model.pkl")
    joblib.dump(selected_model, model_pkl_path)
    print(f"  Trained model artifact saved: {model_pkl_path} ({os.path.getsize(model_pkl_path)/(1024*1024):.2f} MB)")

    # Save metadata JSON
    model_params = selected_model.get_params()
    # Convert any non-serializable objects to str
    serializable_params = {k: (str(v) if not isinstance(v, (int, float, bool, str, list, dict, type(None))) else v) for k, v in model_params.items()}
    
    metadata = {
        "model_name": selected_model_name,
        "feature_names": feature_cols,
        "prediction_horizon_minutes": 30,
        "selected_threshold": selected_threshold,
        "risk_thresholds": {
            "normal_below": selected_threshold,
            "warning_range": [selected_threshold, 0.70],
            "high_risk_above": 0.70
        },
        "train_period": split_info["TRAIN"],
        "validation_period": split_info["VALIDATION"],
        "final_test_period": split_info["FINAL TEST"],
        "validation_metrics": val_metrics,
        "final_test_metrics": test_metrics,
        "model_parameters": serializable_params,
        "top_15_features": feat_imp_df.head(15).to_dict(orient='records')
    }
    
    metadata_json_path = os.path.join(models_dir, "model_metadata.json")
    with open(metadata_json_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"  Model metadata saved: {metadata_json_path}")
    
    total_time = time.time() - start_time
    print(f"\nPipeline finished successfully in {total_time:.2f} seconds.")
    
    return {
        "rf_metrics": {"pr_auc": rf_pr_auc, "roc_auc": rf_roc_auc, "best_th": rf_best_th, **rf_thresh_results[rf_best_th]},
        "xgb_metrics": {"pr_auc": xgb_pr_auc, "roc_auc": xgb_roc_auc, "best_th": xgb_best_th, **xgb_thresh_results[xgb_best_th]},
        "selected_model": selected_model_name,
        "selected_threshold": selected_threshold,
        "test_metrics": test_metrics,
        "top_15_features": feat_imp_df.head(15).to_dict(orient='records'),
        "split_info": split_info
    }

if __name__ == "__main__":
    run_training_pipeline()
