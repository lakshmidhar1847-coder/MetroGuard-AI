"""
MetroGuard AI - Task 15: Generalized Leakage-Free Feature Engineering & Model Retraining
Constructs dimensionless, relative, multi-scale volatility, and baseline deviation features
to improve generalization across compressor failure regimes without using Final Test data.
"""

import os
import json
import time
import joblib
import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
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

EPS = 1e-4

def run_enhanced_pipeline():
    start_time = time.time()
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    orig_features_csv = os.path.join(base_dir, "data", "processed", "metropt3_features.csv")
    out_enhanced_csv = os.path.join(base_dir, "data", "processed", "metropt3_enhanced_features.csv")
    models_dir = os.path.join(base_dir, "models")
    os.makedirs(models_dir, exist_ok=True)
    
    print("=" * 85)
    print(" METROGUARD AI - TASK 15: GENERALIZED FEATURE ENGINEERING & RETRAINING")
    print("=" * 85)
    
    # 1. Load original feature dataset (preserving original untouched)
    print("\n[Step 1/7] Loading existing feature dataset...")
    df = pd.read_csv(orig_features_csv)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    metadata_cols = ['timestamp', 'failure_status', 'target']
    original_feature_cols = [c for c in df.columns if c not in metadata_cols]
    print(f"Loaded {len(df):,} records with {len(original_feature_cols)} original features.")
    
    # 2. Construct generalized, leakage-free features
    print("\n[Step 2/7] Constructing generalized, dimensionless & relative features...")
    new_features_dict = {}
    new_feature_formulas = []
    
    # Category A: Relative Pressure Features
    new_features_dict["TP3_minus_Reservoirs"] = (df["TP3"] - df["Reservoirs"]).astype("float32")
    new_feature_formulas.append(("TP3_minus_Reservoirs", "Relative Pressure", "TP3 - Reservoirs"))
    
    new_features_dict["TP3_abs_diff_Reservoirs"] = (df["TP3"] - df["Reservoirs"]).abs().astype("float32")
    new_feature_formulas.append(("TP3_abs_diff_Reservoirs", "Relative Pressure", "|TP3 - Reservoirs|"))
    
    new_features_dict["TP3_ratio_Reservoirs"] = (df["TP3"] / (df["Reservoirs"] + EPS)).astype("float32")
    new_feature_formulas.append(("TP3_ratio_Reservoirs", "Relative Pressure", "TP3 / (Reservoirs + eps)"))
    
    new_features_dict["TP2_minus_H1"] = (df["TP2"] - df["H1"]).astype("float32")
    new_feature_formulas.append(("TP2_minus_H1", "Relative Pressure", "TP2 - H1 (Cyclonic Filter Drop)"))
    
    new_features_dict["TP2_abs_diff_H1"] = (df["TP2"] - df["H1"]).abs().astype("float32")
    new_feature_formulas.append(("TP2_abs_diff_H1", "Relative Pressure", "|TP2 - H1|"))
    
    new_features_dict["TP3_minus_TP2"] = (df["TP3"] - df["TP2"]).astype("float32")
    new_feature_formulas.append(("TP3_minus_TP2", "Relative Pressure", "TP3 - TP2 (Line Pressure Gradient)"))
    
    new_features_dict["DV_pressure_minus_TP2"] = (df["DV_pressure"] - df["TP2"]).astype("float32")
    new_feature_formulas.append(("DV_pressure_minus_TP2", "Relative Pressure", "DV_pressure - TP2"))
    
    # Category B: Rolling Baseline Deviation & Standardized Residuals
    continuous_channels = ['TP2', 'TP3', 'H1', 'Reservoirs', 'DV_pressure', 'Oil_temperature', 'Motor_current']
    for ch in continuous_channels:
        # Residual from 5m mean
        dev_5m_name = f"{ch}_dev_mean_5m"
        new_features_dict[dev_5m_name] = (df[ch] - df[f"{ch}_roll_mean_5m"]).astype("float32")
        new_feature_formulas.append((dev_5m_name, "Baseline Deviation", f"{ch} - {ch}_roll_mean_5m"))
        
        # Standardized Z-Score Residual from 5m baseline
        zscore_5m_name = f"{ch}_zscore_5m"
        new_features_dict[zscore_5m_name] = ((df[ch] - df[f"{ch}_roll_mean_5m"]) / (df[f"{ch}_roll_std_5m"] + EPS)).astype("float32")
        new_feature_formulas.append((zscore_5m_name, "Standardized Residual", f"({ch} - {ch}_roll_mean_5m) / ({ch}_roll_std_5m + eps)"))
        
        # Residual from 1m mean
        dev_1m_name = f"{ch}_dev_mean_1m"
        new_features_dict[dev_1m_name] = (df[ch] - df[f"{ch}_roll_mean_1m"]).astype("float32")
        new_feature_formulas.append((dev_1m_name, "Baseline Deviation", f"{ch} - {ch}_roll_mean_1m"))

    # Category C: Multi-Scale Volatility Ratios
    turbulent_channels = ['TP2', 'TP3', 'H1', 'Reservoirs', 'DV_pressure', 'Motor_current']
    for ch in turbulent_channels:
        vol_ratio_short_long = f"{ch}_vol_ratio_1m_to_5m"
        new_features_dict[vol_ratio_short_long] = (df[f"{ch}_roll_std_1m"] / (df[f"{ch}_roll_std_5m"] + EPS)).astype("float32")
        new_feature_formulas.append((vol_ratio_short_long, "Multi-Scale Volatility", f"{ch}_roll_std_1m / ({ch}_roll_std_5m + eps)"))
        
        vol_ratio_long_short = f"{ch}_vol_ratio_5m_to_1m"
        new_features_dict[vol_ratio_long_short] = (df[f"{ch}_roll_std_5m"] / (df[f"{ch}_roll_std_1m"] + EPS)).astype("float32")
        new_feature_formulas.append((vol_ratio_long_short, "Multi-Scale Volatility", f"{ch}_roll_std_5m / ({ch}_roll_std_1m + eps)"))

    # Category D: Coefficient of Variation (Relative Instability vs Magnitude)
    for ch in turbulent_channels:
        cv_5m_name = f"{ch}_cv_5m"
        new_features_dict[cv_5m_name] = (df[f"{ch}_roll_std_5m"] / (df[f"{ch}_roll_mean_5m"].abs() + EPS)).astype("float32")
        new_feature_formulas.append((cv_5m_name, "Coefficient of Variation", f"{ch}_roll_std_5m / (|{ch}_roll_mean_5m| + eps)"))
        
        cv_1m_name = f"{ch}_cv_1m"
        new_features_dict[cv_1m_name] = (df[f"{ch}_roll_std_1m"] / (df[f"{ch}_roll_mean_1m"].abs() + EPS)).astype("float32")
        new_feature_formulas.append((cv_1m_name, "Coefficient of Variation", f"{ch}_roll_std_1m / (|{ch}_roll_mean_1m| + eps)"))

    # Category E: Electrical-to-Pneumatic Coupling
    new_features_dict["TP3_per_Current"] = (df["TP3"] / (df["Motor_current"] + EPS)).astype("float32")
    new_feature_formulas.append(("TP3_per_Current", "Electro-Pneumatic Coupling", "TP3 / (Motor_current + eps)"))
    
    new_features_dict["TP2_per_Current"] = (df["TP2"] / (df["Motor_current"] + EPS)).astype("float32")
    new_feature_formulas.append(("TP2_per_Current", "Electro-Pneumatic Coupling", "TP2 / (Motor_current + eps)"))

    # Merge new features into DataFrame
    new_features_df = pd.DataFrame(new_features_dict)
    
    # 3. Feature safety audit (sanitize NaNs and infinite values)
    print("\n[Step 3/7] Performing feature safety & numerical stability audit...")
    # Replace inf and -inf, fillna with 0.0
    new_features_df = new_features_df.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    # Clip extreme numerical artifacts safely
    new_features_df = new_features_df.clip(lower=-1e4, upper=1e4)
    
    nan_count = new_features_df.isnull().sum().sum()
    print(f"  Total NaNs / Infs in new features after sanitization: {nan_count}")
    
    new_feature_names = list(new_features_dict.keys())
    all_feature_cols = original_feature_cols + new_feature_names
    
    print(f"  Original Features Count : {len(original_feature_cols)}")
    print(f"  Newly Created Features  : {len(new_feature_names)}")
    print(f"  Total Enhanced Features : {len(all_feature_cols)}")
    
    # Save enhanced feature catalog
    feat_catalog_df = pd.DataFrame(new_feature_formulas, columns=["Feature", "Category", "Formula"])
    feat_catalog_path = os.path.join(models_dir, "enhanced_feature_list.csv")
    feat_catalog_df.to_csv(feat_catalog_path, index=False)
    print(f"  Saved new feature catalog to: {feat_catalog_path}")

    # Combine into enhanced dataframe
    enhanced_df = pd.concat([df[['timestamp', 'failure_status', 'target'] + original_feature_cols], new_features_df], axis=1)

    # 4. Partition using strictly the same chronological boundaries
    print("\n[Step 4/7] Partitioning data using unchanged chronological boundaries...")
    t_val_start = pd.Timestamp('2020-06-01 00:00:00')
    t_test_start = pd.Timestamp('2020-07-01 00:00:00')
    
    train_mask = enhanced_df['timestamp'] < t_val_start
    val_mask = (enhanced_df['timestamp'] >= t_val_start) & (enhanced_df['timestamp'] < t_test_start)
    
    train_df = enhanced_df[train_mask]
    val_df = enhanced_df[val_mask]
    
    X_train = train_df[all_feature_cols].values
    y_train = train_df['target'].values
    
    X_val = val_df[all_feature_cols].values
    y_val = val_df['target'].values
    
    print(f"  Train partition records : {len(train_df):,} (Positives: {(y_train==1).sum():,})")
    print(f"  Val partition records   : {len(val_df):,} (Positives: {(y_val==1).sum():,})")

    # 5. Train Enhanced Random Forest & Enhanced XGBoost ONLY on TRAIN
    print("\n[Step 5/7] Training Enhanced Models on TRAIN partition ONLY...")
    
    # Random Forest Enhanced
    rf_start = time.time()
    print("  Training Enhanced Random Forest (n_estimators=150, max_depth=15, min_samples_leaf=5)...")
    rf_enh = RandomForestClassifier(
        n_estimators=150, max_depth=15, min_samples_leaf=5, class_weight="balanced_subsample", random_state=42, n_jobs=-1
    )
    rf_enh.fit(X_train, y_train)
    rf_time = time.time() - rf_start
    print(f"  Enhanced Random Forest trained in {rf_time:.2f}s.")
    
    # XGBoost Enhanced
    xgb_start = time.time()
    neg_pos_ratio = float((y_train == 0).sum() / (y_train == 1).sum())
    print(f"  Training Enhanced XGBoost (scale_pos_weight={neg_pos_ratio:.2f})...")
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
    xgb_time = time.time() - xgb_start
    print(f"  Enhanced XGBoost trained in {xgb_time:.2f}s.")

    # 6. Evaluate Enhanced Models on VALIDATION ONLY
    print("\n[Step 6/7] Evaluating Enhanced Models on VALIDATION partition (Event #3)...")
    p_rf_enh = rf_enh.predict_proba(X_val)[:, 1]
    p_xgb_enh = xgb_enh.predict_proba(X_val)[:, 1]
    
    rf_enh_pr_auc = float(average_precision_score(y_val, p_rf_enh))
    rf_enh_roc_auc = float(roc_auc_score(y_val, p_rf_enh))
    xgb_enh_pr_auc = float(average_precision_score(y_val, p_xgb_enh))
    xgb_enh_roc_auc = float(roc_auc_score(y_val, p_xgb_enh))
    
    print(f"  Enhanced Random Forest : PR-AUC = {rf_enh_pr_auc:.6f}, ROC-AUC = {rf_enh_roc_auc:.6f}")
    print(f"  Enhanced XGBoost       : PR-AUC = {xgb_enh_pr_auc:.6f}, ROC-AUC = {xgb_enh_roc_auc:.6f}")
    
    val_records = []
    for mname, probs, pr_auc, roc_auc in [("Random Forest Enhanced", p_rf_enh, rf_enh_pr_auc, rf_enh_roc_auc), ("XGBoost Enhanced", p_xgb_enh, xgb_enh_pr_auc, xgb_enh_roc_auc)]:
        for th in THRESHOLDS:
            preds = (probs >= th).astype(int)
            p = float(precision_score(y_val, preds, zero_division=0))
            r = float(recall_score(y_val, preds, zero_division=0))
            f = float(f1_score(y_val, preds, zero_division=0))
            cm = confusion_matrix(y_val, preds)
            tn, fp, fn, tp = cm.ravel()
            fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
            
            val_records.append({
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
            
    val_res_df = pd.DataFrame(val_records)
    val_csv_path = os.path.join(models_dir, "enhanced_validation_results.csv")
    val_res_df.to_csv(val_csv_path, index=False)
    print(f"  Saved validation threshold results to: {val_csv_path}")

    # Best thresholds by F1 & Recall
    rf_enh_best_row = val_res_df[val_res_df["Model"] == "Random Forest Enhanced"].sort_values("F1", ascending=False).iloc[0]
    xgb_enh_best_row = val_res_df[val_res_df["Model"] == "XGBoost Enhanced"].sort_values("F1", ascending=False).iloc[0]

    # Baseline comparison table
    baseline_comp = [
        {
            "Model": "Random Forest (Original Baseline)",
            "Features": 65,
            "PR_AUC": 0.001233,
            "ROC_AUC": 0.629840,
            "Best_Threshold": 0.007,
            "Precision": 0.002161,
            "Recall": 0.527473,
            "F1": 0.004304
        },
        {
            "Model": "Random Forest (Enhanced)",
            "Features": len(all_feature_cols),
            "PR_AUC": rf_enh_pr_auc,
            "ROC_AUC": rf_enh_roc_auc,
            "Best_Threshold": float(rf_enh_best_row["Threshold"]),
            "Precision": float(rf_enh_best_row["Precision"]),
            "Recall": float(rf_enh_best_row["Recall"]),
            "F1": float(rf_enh_best_row["F1"])
        },
        {
            "Model": "XGBoost (Original Baseline)",
            "Features": 65,
            "PR_AUC": 0.001751,
            "ROC_AUC": 0.662694,
            "Best_Threshold": 0.007,
            "Precision": 0.003167,
            "Recall": 0.225275,
            "F1": 0.006246
        },
        {
            "Model": "XGBoost (Enhanced)",
            "Features": len(all_feature_cols),
            "PR_AUC": xgb_enh_pr_auc,
            "ROC_AUC": xgb_enh_roc_auc,
            "Best_Threshold": float(xgb_enh_best_row["Threshold"]),
            "Precision": float(xgb_enh_best_row["Precision"]),
            "Recall": float(xgb_enh_best_row["Recall"]),
            "F1": float(xgb_enh_best_row["F1"])
        }
    ]
    comp_df = pd.DataFrame(baseline_comp)
    comp_csv_path = os.path.join(models_dir, "enhanced_model_comparison.csv")
    comp_df.to_csv(comp_csv_path, index=False)
    print(f"  Saved model comparison summary to: {comp_csv_path}")

    # 7. Print summary and selection
    print("\n" + "=" * 95)
    print(" ENHANCED MODEL VALIDATION PERFORMANCE COMPARISON")
    print("=" * 95)
    print(comp_df.to_string(index=False))
    print("=" * 95)
    
    # Save enhanced model artifact & metadata
    if xgb_enh_pr_auc >= rf_enh_pr_auc:
        candidate_model_name = "XGBoost Enhanced"
        candidate_model = xgb_enh
        candidate_th = float(xgb_enh_best_row["Threshold"])
    else:
        candidate_model_name = "Random Forest Enhanced"
        candidate_model = rf_enh
        candidate_th = float(rf_enh_best_row["Threshold"])
        
    print(f"\n>>> SELECTED CANDIDATE MODEL: {candidate_model_name} (Threshold = {candidate_th}) <<<")
    print(">>> FINAL TEST EVALUATED: NO (Test set strictly preserved untouched) <<<")
    
    elapsed = time.time() - start_time
    print(f"\nTask 15 pipeline finished successfully in {elapsed:.2f} seconds.")
    
    return comp_df, feat_catalog_df, val_res_df

if __name__ == "__main__":
    run_enhanced_pipeline()
