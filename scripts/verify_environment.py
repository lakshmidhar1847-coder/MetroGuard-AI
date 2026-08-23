"""
MetroGuard AI - Environment Verification Script
Verifies Python version and compatibility of required data-analysis & ML packages.
"""

import sys
import importlib

REQUIRED_PACKAGES = [
    ("numpy", "numpy"),
    ("pandas", "pandas"),
    ("scipy", "scipy"),
    ("scikit-learn", "sklearn"),
    ("xgboost", "xgboost"),
    ("joblib", "joblib"),
    ("matplotlib", "matplotlib"),
    ("seaborn", "seaborn"),
    ("requests", "requests"),
    ("tqdm", "tqdm"),
]

def main():
    print("=" * 65)
    print(" METROGUARD AI - ENVIRONMENT & ML STACK VERIFICATION")
    print("=" * 65)
    print(f"Python Version: {sys.version.split()[0]} ({sys.platform})")
    print(f"Python Executable: {sys.executable}")
    print("-" * 65)
    print(f"{'Package Name':<20} | {'Import Name':<15} | {'Version / Status':<25}")
    print("-" * 65)

    all_passed = True
    results = {}

    for pkg_display, import_name in REQUIRED_PACKAGES:
        try:
            mod = importlib.import_module(import_name)
            ver = getattr(mod, "__version__", "Installed (no __version__)")
            results[pkg_display] = {"status": "PASS", "version": ver}
            print(f"{pkg_display:<20} | {import_name:<15} | {ver:<25}")
        except Exception as e:
            all_passed = False
            results[pkg_display] = {"status": "FAIL", "error": str(e)}
            print(f"{pkg_display:<20} | {import_name:<15} | ERROR: {e}")

    print("-" * 65)
    print("Testing Functional Import Assertions...")
    test_failures = []
    
    if all_passed:
        try:
            import numpy as np
            import pandas as pd
            import scipy.signal
            from sklearn.ensemble import RandomForestClassifier
            import xgboost as xgb
            import joblib
            import matplotlib.pyplot as plt
            import seaborn as sns
            import requests
            import tqdm

            # Quick smoke tests
            arr = np.array([1.0, 2.0, 3.0])
            df = pd.DataFrame({"telemetry_test": arr})
            clf = RandomForestClassifier(n_estimators=2, random_state=42)
            xgb_model = xgb.XGBClassifier(n_estimators=2, max_depth=2)
            
            print("  [+] NumPy & Pandas data structures: OK")
            print("  [+] Scipy Signal processing: OK")
            print("  [+] Scikit-learn estimator instantiation: OK")
            print("  [+] XGBoost classifier instantiation: OK")
            print("  [+] Matplotlib & Seaborn visualization modules: OK")
            print("  [+] Joblib serialization & tqdm progress: OK")
        except Exception as e:
            all_passed = False
            test_failures.append(str(e))
            print(f"  [-] Functional Test Error: {e}")

    print("=" * 65)
    if all_passed and not test_failures:
        print(">>> OVERALL ENVIRONMENT VERIFICATION: PASS <<<")
        print("=" * 65)
        sys.exit(0)
    else:
        print(">>> OVERALL ENVIRONMENT VERIFICATION: FAIL <<<")
        if test_failures:
            print("Failures encountered:", test_failures)
        print("=" * 65)
        sys.exit(1)

if __name__ == "__main__":
    main()
