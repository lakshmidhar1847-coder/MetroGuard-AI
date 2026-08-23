"""
MetroGuard AI - Task 14: Event #4 Feature Distribution Diagnostic
Examines and compares the statistical distributions of the Top 15 XGBoost features
across Train Normal, Train Positives (Events #1 & #2), Validation Positives (Event #3),
and Final Test Positives (Event #4) to isolate physical and temporal distribution shifts.
"""

import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def run_event4_diagnostic():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    features_csv = os.path.join(base_dir, "data", "processed", "metropt3_features.csv")
    models_dir = os.path.join(base_dir, "models")
    meta_json_path = os.path.join(models_dir, "model_metadata.json")
    out_csv = os.path.join(models_dir, "event4_feature_diagnostic.csv")
    out_plot = os.path.join(models_dir, "event4_feature_distributions.png")
    
    print("Loading model metadata and Top 15 features...")
    with open(meta_json_path, 'r') as f:
        meta = json.load(f)
    top_15_features = [item['feature'] for item in meta['top_15_features']]
    print(f"Top 15 Features: {top_15_features}")
    
    print("\nLoading feature dataset...")
    df = pd.read_csv(features_csv)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    t_val_start = pd.Timestamp('2020-06-01 00:00:00')
    t_test_start = pd.Timestamp('2020-07-01 00:00:00')
    
    train_mask = df['timestamp'] < t_val_start
    val_mask = (df['timestamp'] >= t_val_start) & (df['timestamp'] < t_test_start)
    test_mask = df['timestamp'] >= t_test_start
    
    # 4 Groups
    groups = {
        "train_normal": df[train_mask & (df['target'] == 0)],
        "train_positive": df[train_mask & (df['target'] == 1)],  # Events #1 & #2
        "val_positive": df[val_mask & (df['target'] == 1)],      # Event #3
        "test_positive": df[test_mask & (df['target'] == 1)]     # Event #4
    }
    
    print(f"Train Normal Rows    : {len(groups['train_normal']):,}")
    print(f"Train Positive Rows  : {len(groups['train_positive']):,} (Events #1 & #2)")
    print(f"Val Positive Rows    : {len(groups['val_positive']):,} (Event #3)")
    print(f"Test Positive Rows   : {len(groups['test_positive']):,} (Event #4)")
    
    # Calculate summary statistics per group and feature
    records = []
    
    # Also calculate historical positive baseline (Train + Val Positives) for shift metrics
    hist_pos_df = df[(train_mask | val_mask) & (df['target'] == 1)]
    
    shift_scores = {}
    
    for feat in top_15_features:
        feat_stats = {"Feature": feat}
        
        # Calculate stats for all 4 groups
        for gname, gdf in groups.items():
            vals = gdf[feat].values
            mean_val = float(np.mean(vals))
            med_val = float(np.median(vals))
            std_val = float(np.std(vals))
            min_val = float(np.min(vals))
            max_val = float(np.max(vals))
            p5_val = float(np.percentile(vals, 5))
            p95_val = float(np.percentile(vals, 95))
            
            records.append({
                "Feature": feat,
                "Group": gname,
                "Count": len(vals),
                "Mean": mean_val,
                "Median": med_val,
                "Std": std_val,
                "Min": min_val,
                "Max": max_val,
                "P5": p5_val,
                "P95": p95_val
            })
            
        # Distribution shift indicator: Standardized mean shift relative to Train Positives
        train_pos_vals = groups["train_positive"][feat].values
        test_pos_vals = groups["test_positive"][feat].values
        
        mu_train = np.mean(train_pos_vals)
        sigma_train = np.std(train_pos_vals)
        mu_test = np.mean(test_pos_vals)
        
        # Shift index (Cohen's d style distance)
        shift_idx = abs(mu_test - mu_train) / (sigma_train + 1e-6)
        shift_scores[feat] = shift_idx

    stats_df = pd.DataFrame(records)
    stats_df.to_csv(out_csv, index=False)
    print(f"\nSaved feature distribution statistics to: {out_csv}")
    
    # Add shift index to ranking
    shift_ranking = pd.DataFrame([
        {"Feature": f, "Shift_Index_vs_TrainPos": s} for f, s in shift_scores.items()
    ]).sort_values("Shift_Index_vs_TrainPos", ascending=False).reset_index(drop=True)
    
    print("\n" + "=" * 80)
    print(" TOP 15 FEATURES RANKED BY DISTRIBUTION SHIFT IN EVENT #4")
    print("=" * 80)
    for i, row in shift_ranking.iterrows():
        print(f"  {i+1:>2}. {row['Feature']:<30} | Shift Index: {row['Shift_Index_vs_TrainPos']:>8.4f}")
    print("=" * 80)
    
    # Print comparative table for Top 5 largest shifted features
    top_5_shifted = shift_ranking["Feature"].head(5).tolist()
    print("\n" + "=" * 105)
    print(" COMPARATIVE SUMMARY FOR TOP 5 LARGEST SHIFTED FEATURES")
    print("=" * 105)
    for feat in top_5_shifted:
        print(f"\n>>> FEATURE: {feat} (Shift Index: {shift_scores[feat]:.2f})")
        feat_sub = stats_df[stats_df["Feature"] == feat][["Group", "Mean", "Median", "Std", "Min", "Max", "P5", "P95"]]
        print(feat_sub.to_string(index=False))

    # Generate comparative boxplots / violinplots
    plt.figure(figsize=(16, 12))
    for i, feat in enumerate(top_5_shifted, 1):
        plt.subplot(3, 2, i)
        
        data_to_plot = [
            groups["train_normal"][feat].sample(min(5000, len(groups["train_normal"])), random_state=42).values,
            groups["train_positive"][feat].values,
            groups["val_positive"][feat].values,
            groups["test_positive"][feat].values
        ]
        
        plt.boxplot(data_to_plot, tick_labels=["Train Normal", "Train Pos (Ev 1&2)", "Val Pos (Ev 3)", "Test Pos (Ev 4)"])
        plt.title(f"Shift Rank #{i}: {feat} (Shift={shift_scores[feat]:.2f})")
        plt.ylabel("Feature Value")
        plt.grid(True, alpha=0.3)
        
    plt.tight_layout()
    plt.savefig(out_plot, dpi=150)
    plt.close()
    print(f"\nDiagnostic distribution plot saved to: {out_plot}")
    
    return stats_df, shift_ranking

if __name__ == "__main__":
    run_event4_diagnostic()
