# MetroGuard AI — Enhanced Generalized Feature Engineering & Retraining Report

## 1. Motivation for Generalized Feature Formulation

The diagnostic in Task 14 revealed that initial baseline models learned rigid numerical cutoffs tied to specific operational regimes (such as nominal line pressure $TP3 \approx 8.2\text{ bar}$ in spring). When compressor baseline pressure shifted in summer ($TP3 > 9.3\text{ bar}$), tree splits failed to generalize.

To overcome this limitation without leaking future or test information, we designed **54 domain-specific, scale-invariant, and dimensionless features** grounded in physical compressor mechanics:

1. **Relative Differential Pressure Channels**:
   - $TP3 - Reservoirs$ and $|TP3 - Reservoirs|$: Pressure drop across downstream pneumatic panel.
   - $TP2 - H1$ and $|TP2 - H1|$: Pressure differential across cyclonic separator filter.
   - $TP3 - TP2$: Compressor-to-panel delivery gradient.
   - $DV\_pressure - TP2$: Drying tower discharge differential.
2. **Rolling Baseline Deviation & Standardized Residuals**:
   - $x_t - \text{roll\_mean\_5m}(x_t)$: Real-time deviation from the compressor's own historical 5-minute baseline.
   - $\frac{x_t - \text{roll\_mean\_5m}(x_t)}{\text{roll\_std\_5m}(x_t) + \epsilon}$: Standardized Z-score residual capturing sudden physical shocks independent of absolute pressure level.
3. **Multi-Scale Volatility Ratios**:
   - $\frac{\text{roll\_std\_1m}}{\text{roll\_std\_5m} + \epsilon}$ and $\frac{\text{roll\_std\_5m}}{\text{roll\_std\_1m} + \epsilon}$: Dimensionless ratios measuring the burstiness of high-frequency turbulence relative to medium-term variance.
4. **Coefficients of Variation**:
   - $\frac{\text{roll\_std\_5m}}{|\text{roll\_mean\_5m}| + \epsilon}$: Relative operational instability normalized by signal magnitude.
5. **Electro-Pneumatic Coupling**:
   - $\frac{TP3}{Motor\_current + \epsilon}$ and $\frac{TP2}{Motor\_current + \epsilon}$: Work efficiency proxy linking pneumatic output pressure to motor current draw.

---

## 2. Feature Safety & Zero-Leakage Audit

- **Original Input Features**: `65`
- **Newly Constructed Features**: `54`
- **Total Enhanced Model Features**: `119`
- **Temporal Causality**:
  - All rolling calculations use right-aligned causal windows $[t-W+1, t]$ with `min_periods=1`.
  - All differences use causal lags $x_t - x_{t-W}$.
- **Numerical Robustness**:
  - Protected with $\epsilon = 10^{-4}$ against zero division.
  - Zero NaNs, Infs, or numerical singularities exist across all 1.48M records.
- **Dataset Preservation**:
  - [data/processed/metropt3_features.csv](file:///c:/Users/Lakshmidhar/OneDrive/Desktop/Hackathon/MetroGuard-AI/data/processed/metropt3_features.csv) remains unmodified.
  - Feature catalog saved to [models/enhanced_feature_list.csv](file:///c:/Users/Lakshmidhar/OneDrive/Desktop/Hackathon/MetroGuard-AI/models/enhanced_feature_list.csv).

---

## 3. Validation Performance Comparison (Event #3 — June 2020)

Both enhanced models were fitted strictly on the **TRAIN** partition (`2020-02-01` to `2020-05-31`, Events #1 & #2) and evaluated exclusively on the **VALIDATION** partition (`2020-06-01` to `2020-06-30`, Event #3):

| Model Configuration | Feature Space | PR-AUC (Avg Prec) | ROC-AUC | Optimal Thresh | Precision | Recall | F1-Score |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Random Forest (Baseline)** | 65 | `0.001233` | `0.629840` | 0.007 | `0.002161` | `0.527473` (96 TP) | `0.004304` |
| **Random Forest (Enhanced)** | **119** | **`0.001248`** (+1.2%) | **`0.634171`** | 0.007 | **`0.002305`** | **`0.532967`** (97 TP) | **`0.004591`** (+6.7%) |
| **XGBoost (Baseline)** | 65 | `0.001751` | `0.662694` | 0.007 | `0.003167` | `0.225275` (41 TP) | `0.006246` |
| **XGBoost (Enhanced)** 🏆 | **119** | **`0.002400`** (**+37.1%**) | **`0.699196`** (**+5.5%**) | 0.007 | **`0.004847`** (**+53.0%**) | **`0.340659`** (**+51.2%**) | **`0.009558`** (**+53.0%**) |

---

## 4. Enhanced XGBoost Threshold Sweep Analysis

```text
Threshold | Precision | Recall   | F1-Score | TP / 182 | FP     | False Positive Rate (FPR)
----------+-----------+----------+----------+----------+--------+--------------------------
0.001     | 0.001991  | 0.637363 | 0.003970 | 116      | 58,135 | 29.21%
0.002     | 0.002360  | 0.554945 | 0.004701 | 101      | 42,690 | 21.45%
0.003     | 0.002308  | 0.472527 | 0.004593 | 86       | 37,177 | 18.68%
0.005     | 0.004380  | 0.390110 | 0.008662 | 71       | 16,140 |  8.11%
0.007 ⭐  | 0.004847  | 0.340659 | 0.009558 | 62       | 12,729 |  6.40% (Peak F1 & Specificity)
0.010     | 0.004776  | 0.291209 | 0.009397 | 53       | 11,045 |  5.55%
0.020     | 0.003168  | 0.153846 | 0.006209 | 28       |  8,809 |  4.43%
```

---

## 5. Candidate Selection & Untouched Test Set Principle

- **Selected Candidate Model**: **XGBoost Enhanced** ($119$ features, `tree_method="hist"`).
- **Selected Candidate Threshold**: **`0.007`** (delivers peak F1 of `0.009558`, with $34.07\%$ pre-failure recall and $93.6\%$ normal specificity on Validation Event #3).
- **Final Test Status**: **STRICTLY UNTOUCHED**. In adherence to proper ML protocol, the final test partition (`2020-07-01` to `2020-09-01`) was **not** evaluated or accessed during this iterative engineering cycle, preserving test integrity for final unbiased benchmarking.
