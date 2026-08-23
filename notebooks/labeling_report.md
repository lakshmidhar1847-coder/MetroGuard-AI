# MetroGuard AI — Ground-Truth Labeling & Target Formulation Report

## 1. Machine Learning Formulation & Objective
- **Problem Statement**: Predict whether an Air Production Unit (APU) air-leak failure episode will begin within the upcoming **30-minute operational window** (`PREDICTION_HORIZON_MINUTES = 30`) based strictly on historical and current sensor telemetry up to timestamp $T$.
- **Formal Target Definition**:
  $$\text{target}(T) = \begin{cases} 1 & \text{if a documented failure event starts in } (T, T + 30\text{ min}] \\ 0 & \text{otherwise} \end{cases}$$
- **Operational Meaning of `target = 1`**: 
  - Represents an **early-warning / imminent failure state**.
  - Provides operators with actionable lead time to take preventative maintenance actions before the compressor suffers critical failure or severe pressure collapse.
- **Handling of Ongoing Failure Periods (`failure_status = 'ongoing_failure'`)**:
  - Telemetry collected *during* an active failure (from failure onset until maintenance/resolution) is tagged with `failure_status = 'ongoing_failure'`.
  - These rows represent already-degraded compressor operating states and are **not** treated as normal negative examples. During binary classification training, they can be explicitly filtered out or evaluated in separate anomaly detection routines to prevent label contamination.

---

## 2. Documented Ground-Truth Failure Events

| Incident # | Start Time (UTC) | End Time (UTC) | Pre-Failure Window (30 min) | Failure Type | Severity |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Event #1** | `2020-04-18 00:00:00` | `2020-04-18 23:59:00` | `2020-04-17 23:30:00` → `2020-04-18 00:00:00` | Air Leak | High stress |
| **Event #2** | `2020-05-29 23:30:00` | `2020-05-30 06:00:00` | `2020-05-29 23:00:00` → `2020-05-29 23:30:00` | Air Leak | High stress |
| **Event #3** | `2020-06-05 10:00:00` | `2020-06-07 14:30:00` | `2020-06-05 09:30:00` → `2020-06-05 10:00:00` | Air Leak | High stress |
| **Event #4** | `2020-07-15 14:30:00` | `2020-07-15 19:00:00` | `2020-07-15 14:00:00` → `2020-07-15 14:30:00` | Air Leak | High stress |

---

## 3. Labeling Statistics & Class Distribution

```text
===========================================================================
 METROGUARD AI - LABEL DISTRIBUTION SUMMARY
===========================================================================
  Total Telemetry Rows       : 1,516,948  (100.00%)
  Normal Operational Rows    : 1,486,300  ( 97.98%)
  Pre-Failure (Target=1) Rows:       694  (  0.0457%)
  Ongoing Failure Rows       :    29,954  (  1.9746%)
===========================================================================
  Class Imbalance Ratio      : 1 Positive : 2,185.8 Total Observations
```

### Breakdown by Individual Failure Period:

| Period | Pre-Failure Rows (`target=1`) | Actual Pre-Failure Span | Ongoing Failure Rows (`ongoing_failure`) |
| :--- | :--- | :--- | :--- |
| **Event #1** | 149 | `2020-04-17 23:30:04` → `2020-04-17 23:59:49` | 8,657 |
| **Event #2** | 182 | `2020-05-29 23:00:04` → `2020-05-29 23:29:58` | 2,360 |
| **Event #3** | 182 | `2020-06-05 09:30:00` → `2020-06-05 09:59:54` | 17,315 |
| **Event #4** | 181 | `2020-07-15 14:00:07` → `2020-07-15 14:29:51` | 1,622 |
| **Total** | **694** | **4 Distinct Continuous Epochs** | **29,954** |

---

## 4. Boundary Continuity & Gaps Analysis
1. **Contiguity between Pre-Failure and Event Windows**:
   - For all 4 events, the transition from `pre_failure` (`target=1`) to `ongoing_failure` (`target=0`) is continuous with zero gap.
2. **Post-Event Depot Downtime Gaps**:
   - Following Event #3 (`2020-06-07 14:30:00`), logging temporarily paused as the metro train was removed from revenue service and towed to the maintenance depot. Telemetry cleanly resumed on `2020-06-08 11:48:04` following physical repair.
3. **Sampling Cadence Variations**:
   - In April 2020 (Event #1), sampling cadence varied slightly (~11–13 seconds, average ~12s), resulting in 149 rows in the 30-minute interval. In May–July 2020, sampling was precisely 10.0s (yielding 181–182 rows per 30 minutes). Timestamp-based arithmetic correctly handled all variations without row-count assumptions.

---

## 5. Data Leakage Prevention Verification
- **Forward-Only Target Assignment**: Labels are assigned purely via future failure start times without referencing future sensor measurements.
- **Zero In-Sample Feature Leakage**: No rolling statistics, transformations, or features have been derived from future timestamps or failure target columns.
- **Raw Integrity Preserved**: [data/raw/MetroPT3(AirCompressor).csv](file:///c:/Users/Lakshmidhar/OneDrive/Desktop/Hackathon/MetroGuard-AI/data/raw/MetroPT3(AirCompressor).csv) remains 100% pristine and unmodified. Processed outputs are saved independently to [data/processed/metropt3_labeled.csv](file:///c:/Users/Lakshmidhar/OneDrive/Desktop/Hackathon/MetroGuard-AI/data/processed/metropt3_labeled.csv).
