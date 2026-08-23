# MetroGuard AI — Feature Engineering & Leakage Audit Report

## 1. Feature Engineering Architecture & Strategy

To predict whether an Air Production Unit (APU) failure will occur within the next 30 minutes, we construct **domain-specific, backward-looking time-series features** from 15 physical sensors and valve control signals.

### Core Mathematical Constraints for Temporal Integrity:
1. **Strictly Backward-Looking**: For any feature $f(T)$ evaluated at timestamp $T$, $f(T) = g(\{X_t \mid t \le T\})$. No future information $t > T$ is ever accessed.
2. **Causal Rolling Aggregates**:
   - `rolling(window, min_periods=1)` defaults to right-aligned causal windows $[T - \Delta t, T]$.
   - No centered windows (`center=False`) or forward window operations.
3. **Continuous-Time Computation Before Filtering**:
   - Rolling statistics and lag differences are computed over the unbroken chronological time-series before excluding active breakdown periods. This avoids artificial boundary distortions at operational transitions.
4. **Clean Training Target Isolation**:
   - Active breakdown periods (`failure_status = 'ongoing_failure'`) are removed from the training dataset to ensure the model does not learn active failure physics as "normal" negative behavior.

---

## 2. Feature Catalog (65 Total Model Input Features)

### A. Continuous Analogue Signals (49 Features)
Computed for each of the 7 analogue channels: `TP2`, `TP3`, `H1`, `DV_pressure`, `Reservoirs`, `Oil_temperature`, `Motor_current`.

| Feature Template | Description | Mathematical Formulation | Physical Interpretation |
| :--- | :--- | :--- | :--- |
| `{signal}` | Current Instantaneous Value | $x_t$ | Real-time sensor state |
| `{signal}_roll_mean_1m` | 1-minute Rolling Mean | $\frac{1}{K}\sum_{i=0}^{K-1} x_{t-i}$ ($K \approx 6$) | Short-term smoothed baseline |
| `{signal}_roll_std_1m` | 1-minute Rolling Std Dev | $\sqrt{\frac{1}{K-1}\sum_{i=0}^{K-1} (x_{t-i} - \bar{x})^2}$ | Rapid short-term signal volatility / chatter |
| `{signal}_roll_mean_5m` | 5-minute Rolling Mean | $\frac{1}{N}\sum_{i=0}^{N-1} x_{t-i}$ ($N \approx 30$) | Medium-term operational trend |
| `{signal}_roll_std_5m` | 5-minute Rolling Std Dev | $\sqrt{\frac{1}{N-1}\sum_{i=0}^{N-1} (x_{t-i} - \bar{x})^2}$ | Sustained system turbulence |
| `{signal}_diff_1m` | 1-minute Lag Difference | $x_t - x_{t-6}$ | Rate-of-change over 1 minute |
| `{signal}_diff_5m` | 5-minute Lag Difference | $x_t - x_{t-30}$ | Rate-of-change over 5 minutes |

### B. Digital & Control Valve Signals (16 Features)
Computed for the 8 digital control signals: `COMP`, `DV_eletric`, `Towers`, `MPG`, `LPS`, `Pressure_switch`, `Oil_level`, `Caudal_impulses`.

| Feature Template | Description | Physical Interpretation |
| :--- | :--- | :--- |
| `{signal}` | Current Binary State ($0 \text{ or } 1$) | Active switch/valve position |
| `{signal}_changes_5m` | Rolling 5-minute Transition Count | Valve cycling frequency (e.g. rapid valve cycling before an air leak) |

---

## 3. Dataset Summary & Class Distribution

```text
================================================================================
 METROGUARD AI - FEATURE DATASET SUMMARY
================================================================================
  Original Labeled Telemetry Rows  : 1,516,948
  Ongoing Failure Rows Excluded    :    29,954
  Clean Model Training Rows        : 1,486,994 (100.00%)
  ------------------------------------------------------------------------------
  Negative Class (Target=0, Normal): 1,486,300 ( 99.9533%)
  Positive Class (Target=1, Pre-Fail):     694 (  0.0467%)
  Total Model Input Features       :        65
  Metadata Columns (Not for model) :         3 ('timestamp', 'failure_status', 'target')
  Total Dataset Columns            :        68
  Missing / NaN Values             :         0 (100% complete)
  Storage Size (CSV)               :    798.63 MB
================================================================================
```

---

## 4. Pre-Failure Telemetry Sanity Check

Below is empirical proof of feature responsiveness in the final 5 minutes preceding documented air-leak failure events:

```text
================ Event 2 PRE-FAILURE TELEMETRY (Last 5 min before onset) ================
          timestamp  target   TP2  TP2_roll_mean_1m  TP2_roll_std_1m  TP2_diff_5m   TP3  TP3_roll_mean_1m  TP3_diff_1m  Motor_current  Motor_current_roll_mean_5m  COMP  COMP_changes_5m
2020-05-29 23:29:38       1 8.724          8.215667         0.931926       -0.030 8.570          8.571667    -0.006001         5.8450                     5.63775   0.0              0.0
2020-05-29 23:29:48       1 8.726          8.209000         0.927333       -0.036 8.576          8.570000    -0.010000         5.7725                     5.63675   0.0              0.0
2020-05-29 23:29:58       1 6.646          8.247666         0.838058        0.734 8.576          8.568334    -0.010000         5.2275                     5.63700   0.0              0.0

================ Event 3 PRE-FAILURE TELEMETRY (Last 5 min before onset) ================
          timestamp  target   TP2  TP2_roll_mean_1m  TP2_roll_std_1m  TP2_diff_5m   TP3  TP3_roll_mean_1m  TP3_diff_1m  Motor_current  Motor_current_roll_mean_5m  COMP  COMP_changes_5m
2020-06-05 09:59:34       1 6.016          7.960000         1.039806       -2.894 8.454          8.487333    -0.080000         5.1775                    5.611167   0.0              0.0
2020-06-05 09:59:44       1 7.828          8.005333         1.024486        0.374 8.442          8.476666    -0.063999         5.6000                    5.617500   0.0              0.0
2020-06-05 09:59:54       1 8.488          8.037666         1.038386        0.274 8.426          8.465000    -0.070001         5.6450                    5.622083   0.0              0.0
```

---

## 5. Comprehensive Leakage Audit Checklist

| Audit Item | Verification Method | Status | Details |
| :--- | :--- | :--- | :--- |
| **No Target as Feature** | Schema Inspection | **PASSED** | `target` is isolated solely as the prediction label column. |
| **No Status as Feature** | Schema Inspection | **PASSED** | `failure_status` is isolated solely as metadata. |
| **No Future Rolling Windows** | Code Review | **PASSED** | All rolling windows are purely backward-looking ($t-w \dots t$). |
| **No Centered Windows** | Code Review | **PASSED** | `center=False` (default) used across all pandas rolling calculations. |
| **No Future Timestamps** | Temporal Verification | **PASSED** | Data is strictly monotonically sorted; features only index prior rows. |
| **No Random Train/Test Split** | Architecture | **PASSED** | No shuffling or non-chronological transformations applied. |
| **No Event Info Leaked** | Feature List Audit | **PASSED** | Features use only raw physical telemetry signals ($15$ channels). |
| **NaN Warm-up Handling** | Missing Value Audit | **PASSED** | Initial rolling window warm-up handled cleanly with backward padding (`min_periods=1`, `fillna(0)`). Zero NaNs exist. |
