"""
MetroGuard AI - Task 12: Probability Distribution Diagnostic
Calculates empirical probability distributions across validation and test partitions
for Random Forest and XGBoost to diagnose model behavior and temporal distribution shift.
"""

import os
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestClassifier

def run_diagnostic():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    features_csv = os.path.join(base_dir, "data", "processed", "metropt3_features.csv")
    models_dir = os.path.join(base_dir, "models")
    xgb_model_path = os.path.join(models_dir, "metroguard_model.pkl")
    
    print("Loading feature dataset...")
    df = pd.read_csv(features_csv)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    t_val_start = pd.Timestamp('2020-06-01 00:00:00')
    t_test_start = pd.Timestamp('2020-07-01 00:00:00')
    
    train_mask = df['timestamp'] < t_val_start
    val_mask = (df['timestamp'] >= t_val_start) & (df['timestamp'] < t_test_start)
    test_mask = df['timestamp'] >= t_test_start
    
    train_df = df[train_mask]
    val_df = df[val_mask]
    test_df = df[test_mask]
    
    metadata_cols = ['timestamp', 'failure_status', 'target']
    feature_cols = [c for c in df.columns if c not in metadata_cols]
    
    print(f"Train rows: {len(train_df):,}, Val rows: {len(val_df):,}, Test rows: {len(test_df):,}")
    
    # 1. Load XGBoost and fit identical Random Forest
    print("Loading XGBoost model artifact...")
    xgb_model = joblib.load(xgb_model_path)
    
    print("Fitting Random Forest on TRAIN partition...")
    rf_model = RandomForestClassifier(
        n_estimators=150, max_depth=15, min_samples_leaf=5, class_weight='balanced_subsample', random_state=42, n_jobs=-1
    )
    rf_model.fit(train_df[feature_cols].values, train_df['target'].values)
    
    # 2. Partition groups
    groups = {
        "val_normal": val_df[val_df['target'] == 0],
        "val_positive": val_df[val_df['target'] == 1],
        "test_normal": test_df[test_df['target'] == 0],
        "test_positive": test_df[test_df['target'] == 1]
    }
    
    # 3. Compute probabilities and statistics
    stats_records = []
    prob_dict = {"RF": {}, "XGB": {}}
    
    for gname, gdf in groups.items():
        X_g = gdf[feature_cols].values
        p_rf = rf_model.predict_proba(X_g)[:, 1]
        p_xgb = xgb_model.predict_proba(X_g)[:, 1]
        
        prob_dict["RF"][gname] = p_rf
        prob_dict["XGB"][gname] = p_xgb
        
        for mname, probs in [("Random Forest", p_rf), ("XGBoost", p_xgb)]:
            stats_records.append({
                "Model": mname,
                "Group": gname,
                "Rows": len(probs),
                "Min": float(np.min(probs)),
                "Max": float(np.max(probs)),
                "Mean": float(np.mean(probs)),
                "Median": float(np.median(probs)),
                "P90": float(np.percentile(probs, 90)),
                "P95": float(np.percentile(probs, 95)),
                "P99": float(np.percentile(probs, 99))
            })
            
    stats_df = pd.DataFrame(stats_records)
    csv_out_path = os.path.join(models_dir, "probability_distribution.csv")
    stats_df.to_csv(csv_out_path, index=False)
    print(f"\nSaved summary statistics to: {csv_out_path}")
    
    # Print formatted stats table
    print("\n" + "=" * 95)
    print(" EMPIRICAL PREDICTED PROBABILITY DISTRIBUTIONS")
    print("=" * 95)
    print(stats_df.to_string(index=False))
    print("=" * 95)
    
    # 4. Final Test Positives threshold breakdown
    eval_thresholds = [0.01, 0.02, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50]
    
    test_pos_rf = prob_dict["RF"]["test_positive"]
    test_pos_xgb = prob_dict["XGB"]["test_positive"]
    
    print("\n" + "=" * 80)
    print(" FINAL TEST POSITIVE ROWS (Event #4, n=181) THRESHOLD COUNT BREAKDOWN")
    print("=" * 80)
    print(f"{'Threshold':<12} | {'Random Forest (Count >= Thresh)':<32} | {'XGBoost (Count >= Thresh)':<30}")
    print("-" * 80)
    
    for th in eval_thresholds:
        rf_cnt = int((test_pos_rf >= th).sum())
        xgb_cnt = int((test_pos_xgb >= th).sum())
        rf_pct = (rf_cnt / 181) * 100
        xgb_pct = (xgb_cnt / 181) * 100
        print(f"{th:<12.2f} | {rf_cnt:>4} / 181 ({rf_pct:>5.1f}%)                 | {xgb_cnt:>4} / 181 ({xgb_pct:>5.1f}%)")
        
    print("-" * 80)
    print(f"Max Probability among 181 Event #4 Positives (Random Forest): {np.max(test_pos_rf):.6f}")
    print(f"Max Probability among 181 Event #4 Positives (XGBoost)      : {np.max(test_pos_xgb):.6f}")
    print("=" * 80)
    
    # 5. Plot distribution comparison
    plot_path = os.path.join(models_dir, "probability_distribution_plot.png")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Subplot 1: Validation Probs (Log scale)
    axes[0, 0].hist(np.log10(prob_dict["XGB"]["val_normal"] + 1e-6), bins=50, alpha=0.5, density=True, label="Val Normal (Target=0)", color='blue')
    axes[0, 0].hist(np.log10(prob_dict["XGB"]["val_positive"] + 1e-6), bins=30, alpha=0.7, density=True, label="Val Positive (Event #3, Target=1)", color='red')
    axes[0, 0].set_title("XGBoost: Validation Set Probabilities (log10 scale)")
    axes[0, 0].set_xlabel("log10(Predicted Risk Probability)")
    axes[0, 0].set_ylabel("Density")
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # Subplot 2: Final Test Probs (Log scale)
    axes[0, 1].hist(np.log10(prob_dict["XGB"]["test_normal"] + 1e-6), bins=50, alpha=0.5, density=True, label="Test Normal (Target=0)", color='blue')
    axes[0, 1].hist(np.log10(prob_dict["XGB"]["test_positive"] + 1e-6), bins=30, alpha=0.7, density=True, label="Test Positive (Event #4, Target=1)", color='red')
    axes[0, 1].set_title("XGBoost: Final Test Set Probabilities (log10 scale)")
    axes[0, 1].set_xlabel("log10(Predicted Risk Probability)")
    axes[0, 1].set_ylabel("Density")
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)

    # Subplot 3: Random Forest Validation
    axes[1, 0].hist(prob_dict["RF"]["val_normal"], bins=50, alpha=0.5, density=True, label="Val Normal (Target=0)", color='blue')
    axes[1, 0].hist(prob_dict["RF"]["val_positive"], bins=30, alpha=0.7, density=True, label="Val Positive (Event #3, Target=1)", color='red')
    axes[1, 0].set_title("Random Forest: Validation Set Probabilities")
    axes[1, 0].set_xlabel("Predicted Risk Probability")
    axes[1, 0].set_ylabel("Density")
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)

    # Subplot 4: Random Forest Final Test
    axes[1, 1].hist(prob_dict["RF"]["test_normal"], bins=50, alpha=0.5, density=True, label="Test Normal (Target=0)", color='blue')
    axes[1, 1].hist(prob_dict["RF"]["test_positive"], bins=30, alpha=0.7, density=True, label="Test Positive (Event #4, Target=1)", color='red')
    axes[1, 1].set_title("Random Forest: Final Test Set Probabilities")
    axes[1, 1].set_xlabel("Predicted Risk Probability")
    axes[1, 1].set_ylabel("Density")
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(plot_path, dpi=150)
    plt.close()
    print(f"Saved diagnostic probability plot to: {plot_path}")
    
if __name__ == "__main__":
    run_diagnostic()
