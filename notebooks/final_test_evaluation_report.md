# MetroGuard AI — Final Untouched Test Evaluation Report (Enhanced XGBoost)

## 1. Experimental Integrity & Protocol Governance

In accordance with strict machine learning methodology:
1. **Frozen Model Artifact**: The **Enhanced XGBoost Classifier** ($119$ features) was trained strictly on the **TRAIN** partition (`2020-02-01` to `2020-05-31`, Events #1 & #2) and frozen prior to final testing.
2. **Frozen Decision Threshold**: The decision threshold **`0.007`** was selected exclusively on the **VALIDATION** partition (Event #3) and remained completely unaltered.
3. **No Test Set Snooping / Post-Test Tuning**: Event #4 and the August 2020 holdout data were never used for feature selection, hyperparameter tuning, threshold calibration, or iterative refinement.
4. **Single-Pass Evaluation**: Final test results were computed in a single pass without subsequent optimization.

---

## 2. Final Test Partition Demographics

| Metric | Value | Description |
| :--- | :--- | :--- |
| **Partition Span** | `2020-07-01 00:00:08` $\rightarrow$ `2020-09-01 03:59:50` | Full summer holdout (~2 months) |
| **Total Test Observations** | `441,980` | 100.00% |
| **Negative Class (`target=0`)** | `441,799` | 99.9590% |
| **Positive Class (`target=1`)** | `181` | 0.0410% |
| **Failure Episodes Included** | **Event #4 (Air Leak, July 15, 2020)** | Complete ground-truth episode |

---

## 3. Final Test Metrics & Confusion Matrix

```text
=====================================================================================
 FINAL UNTOUCHED TEST RESULTS: ENHANCED XGBOOST (Threshold = 0.007)
=====================================================================================
  PR-AUC (Average Precision) : 0.000330
  ROC-AUC                    : 0.430179
  Precision                  : 0.000000
  Recall                     : 0.000000 (0 / 181 failure intervals detected)
  F1-Score                   : 0.000000
  Accuracy                   : 0.938051
  False Positive Rate (FPR)  : 0.061564 (6.16%)
  Specificity                : 0.938436 (93.84%)
-------------------------------------------------------------------------------------
  Confusion Matrix:
    True Negatives  (TN):    414,600
    False Positives (FP):     27,199
    False Negatives (FN):        181
    True Positives  (TP):          0
=====================================================================================
```

---

## 4. Event #4 Detailed Detection Breakdown

- **Total Event #4 Positive Rows**: `181`
- **Detected (True Positives)**: `0`
- **Missed (False Negatives)**: `181`
- **Event #4 Recall Rate**: **`0.00%`**
- **Predicted Probability Distribution on Event #4 Positives**:
  - Maximum Predicted Probability: `0.002642` (0.26%)
  - 95th Percentile Probability: `0.000760`
  - Mean Predicted Probability: `0.000477`
  - Median Predicted Probability: `0.000395`

*Observation*: All 181 Event #4 failure observations received predicted probabilities below `0.002642`, falling beneath the frozen operating threshold of `0.007`.

---

## 5. Baseline vs. Enhanced Final Test Comparison

| Metric | Baseline XGBoost (65 Features, Thresh = 0.10) | Enhanced XGBoost (119 Features, Thresh = 0.007) | Difference / Delta |
| :--- | :--- | :--- | :--- |
| **PR-AUC** | `0.000300` | **`0.000330`** | +10.0% |
| **ROC-AUC** | `0.431600` | `0.430179` | -0.3% |
| **Precision** | `0.000000` | `0.000000` | Unchanged |
| **Recall** | `0.000000` | `0.000000` | Unchanged |
| **F1-Score** | `0.000000` | `0.000000` | Unchanged |
| **Accuracy** | `0.977669` | `0.938051` | -3.9% (reflects lower threshold) |
| **True Positives (TP)** | `0` | `0` | Unchanged |
| **False Positives (FP)** | `9,689` | `27,199` | +17,510 |
| **True Negatives (TN)** | `432,110` | `414,600` | -17,510 |
| **False Negatives (FN)** | `181` | `181` | Unchanged |

---

## 6. Scientific Interpretation & Answers to Key Evaluation Questions

1. **Did generalized features improve final-test performance?**
   - *Marginally in PR-AUC* (`0.000300` $\rightarrow$ `0.000330`), but not sufficiently to elevate Event #4 probabilities above the validation-selected decision threshold.
2. **Did Event #4 detection improve compared with the baseline?**
   - *No*. True Positives remained $0 / 181$.
3. **How many of the 181 Event #4 positive intervals were detected?**
   - Exactly **$0$** out of $181$ intervals were detected at the frozen threshold of $0.007$.
4. **Did PR-AUC improve?**
   - Yes, slightly from `0.000300` to `0.000330`.
5. **Did ROC-AUC improve?**
   - No, remained effectively unchanged at `0.4302` vs `0.4316`.
6. **Did the false-positive burden increase or decrease?**
   - Increased from $9,689$ to $27,199$ ($6.16\%$ FPR) because the validation operating point was calibrated at a lower threshold ($0.007$ vs baseline $0.10$).
7. **Is the model sufficiently reliable for deployment?**
   - **NO**. A purely supervised gradient boosted decision tree trained on spring baseline conditions cannot reliably detect summer high-pressure sudden failure events without producing excessive false alarms.
8. **What is the scientifically justified next modeling direction?**
   - **Hybrid Semi-Supervised Anomaly Architecture**: Train an **Unsupervised Autoencoder / Isolation Forest / Mahalanobis Distance Network** on purely normal compressor telemetry. An unsupervised reconstruction model measures how far any telemetry point deviates from the multi-sensor physical correlation manifold, bypassing the limitation of supervised tree cutoffs on unseen failure regimes.
