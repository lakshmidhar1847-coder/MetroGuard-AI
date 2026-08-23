"""
MetroGuard AI - Dataset Inspection Script
Performs a comprehensive, programmatic inspection of the raw MetroPT-3 dataset.
"""

import os
import pandas as pd
import numpy as np

def inspect_metropt3():
    raw_dir = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
    csv_file = os.path.join(raw_dir, "MetroPT3(AirCompressor).csv")
    
    print("=" * 80)
    print(" METROGUARD AI - METROPT-3 DATASET INSPECTION REPORT")
    print("=" * 80)
    
    # 1. File names and sizes
    print("\n[1] RAW DATA DIRECTORY FILES & SIZES:")
    for fname in sorted(os.listdir(raw_dir)):
        fpath = os.path.join(raw_dir, fname)
        fsize_mb = os.path.getsize(fpath) / (1024 * 1024)
        print(f"  - {fname:<30} : {fsize_mb:>8.2f} MB ({os.path.getsize(fpath):,} bytes)")
    
    if not os.path.exists(csv_file):
        print(f"\nERROR: CSV file not found at {csv_file}")
        return

    print("\nLoading dataset (this may take a few seconds)...")
    df = pd.read_csv(csv_file)
    
    # 2 & 3. Rows and Columns
    num_rows, num_cols = df.shape
    print(f"\n[2 & 3] DATASET DIMENSIONS:")
    print(f"  - Total Rows    : {num_rows:,}")
    print(f"  - Total Columns : {num_cols}")
    
    # 4 & 5. Column Names and Data Types
    print(f"\n[4 & 5] COLUMN NAMES & DATA TYPES:")
    col_info = pd.DataFrame({
        'Data Type': df.dtypes,
        'Non-Null Count': df.notnull().sum(),
        'Null Count': df.isnull().sum(),
        'Null %': (df.isnull().sum() / len(df)) * 100,
        'Unique Values': df.nunique()
    })
    print(col_info.to_string())
    
    # 6. First 5 rows
    print("\n" + "-" * 80)
    print("[6] FIRST 5 ROWS:")
    print("-" * 80)
    print(df.head(5).to_string())
    
    # 7. Last 5 rows
    print("\n" + "-" * 80)
    print("[7] LAST 5 ROWS:")
    print("-" * 80)
    print(df.tail(5).to_string())
    
    # 8. Missing values per column
    print("\n" + "-" * 80)
    print("[8] MISSING VALUES ANALYSIS:")
    null_counts = df.isnull().sum()
    if null_counts.sum() == 0:
        print("  - Zero missing values detected across all columns (100% complete).")
    else:
        print(null_counts[null_counts > 0])
        
    # 9. Number of unique values
    print("\n[9] CARDINALITY / UNIQUE VALUES SUMMARY:")
    for col in df.columns:
        if col not in ['Unnamed: 0', 'timestamp']:
            uniques = df[col].unique()
            if len(uniques) <= 10:
                print(f"  - {col:<16} (Digital/Discrete, {len(uniques):>2} unique): {sorted(uniques.tolist())}")
            else:
                print(f"  - {col:<16} (Continuous,       {len(uniques):>7,} unique): Min={df[col].min():.3f}, Max={df[col].max():.3f}")

    # 10. Min and max timestamp
    print("\n[10] TIMESTAMP RANGE & SAMPLING:")
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    min_ts = df['timestamp'].min()
    max_ts = df['timestamp'].max()
    duration = max_ts - min_ts
    print(f"  - Minimum Timestamp : {min_ts}")
    print(f"  - Maximum Timestamp : {max_ts}")
    print(f"  - Total Timespan    : {duration.days} days, {duration.seconds // 3600} hours (approx {duration.days / 30.4:.1f} months)")
    
    # 11 & 12. Numeric vs Non-Numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    non_numeric_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
    print(f"\n[11] NUMERIC COLUMNS ({len(numeric_cols)}):")
    print("  ", numeric_cols)
    print(f"\n[12] NON-NUMERIC / CATEGORICAL / DATETIME COLUMNS ({len(non_numeric_cols)}):")
    print("  ", non_numeric_cols)
    
    # 13. Basic statistics for numeric columns
    sensor_cols = [c for c in numeric_cols if c != 'Unnamed: 0']
    print(f"\n[13] DESCRIPTIVE STATISTICS FOR SENSOR VARIABLES:")
    print("-" * 80)
    stats_df = df[sensor_cols].describe().T[['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']]
    print(stats_df.to_string())
    
    print("\n" + "=" * 80)
    print(" INSPECTION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    inspect_metropt3()
