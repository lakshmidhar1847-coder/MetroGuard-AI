# MetroGuard AI — Machine Learning Model Training & Temporal Evaluation Report

## 1. Executive Summary & Experimental Design

This report documents the rigorous training, validation, and untouched chronological test evaluation of the initial machine learning models for **MetroGuard AI**. 

### Key Design Principles:
1. **Event-Aligned Chronological Partitioning**: Standard 80/20 naive splits failed because all 4 failure events occurred between April and July, leaving the final test set with zero failures. We structured an **event-aligned chronological split** where each partition contains authentic, verified air-leak episodes:
   - **Training Set (Feb 1 – May 31, 2020)**: 845,815 rows, 331 positive failure intervals (Events #1 & #2).
   - **Validation Set (Jun 1 – Jun 30, 2020)**: 199,199 rows, 182 positive failure intervals (Event #3).
   - **Final Test Set (Jul 1 – Sep 1, 2020)**: 441,980 rows, 181 positive failure intervals (Event #4 + August holdout).
2. **Extreme Class Imbalance Adaptation**:
   - Positive class frequency: ~0.04% across partitions.
   - Models evaluated primarily on **PR-AUC (Precision-Recall AUC)**, **Recall**, **Precision**, and **F1-Score** rather than raw Accuracy.
   - Decision threshold tuned empirically on the Validation set rather than arbitrarily setting 0.50.

---

## 2. Partition Verification & Data Balance

| Partition | Temporal Span | Total Instances | Negative Samples (`target=0`) | Positive Samples (`target=1`) | Positive Rate (%) | Events Included |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TRAIN** | `2020-02-01` → `2020-05-31` | `845,815` | `845,484` | **331** | **0.0391%** | **Event #1 & Event #2** |
| **VALIDATION** | `2020-06-01` → `2020-06-30` | `199,199` | `199,017` | **182** | **0.0914%** | **Event #3** |
| **FINAL TEST** | `2020-07-01` → `2020-09-01` | `441,980` | `441,799` | **181** | **0.0410%** | **Event #4 + Aug Holdout** |

---

## 3. Model Architecture & Hyperparameters

### Model A: Random Forest Classifier
- `n_estimators`: `150`
- `max_depth`: `15`
- `min_samples_leaf`: `5`
- `class_weight`: `"balanced_subsample"`
- `random_state`: `42`
- `n_jobs`: `-1`
- Training Time: `123.04s`

### Model B: XGBoost Classifier (Histogram-Based)
- `tree_method`: `"hist"`
- `n_estimators`: `150`
- `max_depth`: `6`
- `learning_rate`: `0.05`
- `subsample`: `0.80`
- `colsample_bytree`: `0.80`
- `scale_pos_weight`: `2554.33` (computed strictly from training class distribution)
- `eval_metric`: `"logloss"`
- `random_state`: `42`
- `n_jobs`: `-1`
- Training Time: `26.48s`

---

## 4. Validation Threshold Tuning & Model Comparison (Event #3)

### Validation Metric Comparison Table

| Model | PR-AUC | ROC-AUC | Optimal Thresh | Precision | Recall | F1-Score |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Random Forest** | 0.0012 | 0.6298 | 0.10 | 0.0011 | 0.1703 | 0.0022 |
| **XGBoost (Selected)** | **0.0018** | **0.6627** | **0.10** | 0.0006 | 0.0220 | 0.0011 |

### Threshold Sweep Detail on Validation Set

```text
Threshold  | RF Precision | RF Recall | RF F1  || XGB Precision | XGB Recall | XGB F1
-------------------------------------------------------------------------------------
0.10       | 0.0011       | 0.1703    | 0.0022 || 0.0006        | 0.0220     | 0.0011
0.20       | 0.0010       | 0.1429    | 0.0020 || 0.0003        | 0.0110     | 0.0006
0.30       | 0.0003       | 0.0110    | 0.0006 || 0.0004        | 0.0110     | 0.0007
0.40       | 0.0000       | 0.0000    | 0.0000 || 0.0002        | 0.0055     | 0.0004
0.50       | 0.0000       | 0.0000    | 0.0000 || 0.0000        | 0.0000     | 0.0000
```

> **Model Selection Rationale**:
> **XGBoost** was selected as the champion model because it delivered superior ranking power on the validation dataset (**PR-AUC = 0.0018** vs 0.0012; **ROC-AUC = 0.6627** vs 0.6298) and trained in ~26 seconds (over 4.6x faster than Random Forest). A baseline operational decision threshold of **0.10** was frozen for downstream evaluation.

---

## 5. Untouched Final Test Performance (Event #4 + Holdout)

The selected **XGBoost** model was evaluated **once** on the untouched final test set (`2020-07-01` to `2020-09-01`):

```text
=================================================================
 FINAL UNTOUCHED TEST EVALUATION RESULTS
=================================================================
  Model Evaluated  : XGBoost (Tree Method: hist)
  Decision Thresh  : 0.10
  PR-AUC (Avg Prec): 0.0003
  ROC-AUC          : 0.4316
  Precision        : 0.0000
  Recall           : 0.0000 (0 / 181 failure intervals triggered)
  F1-Score         : 0.0000
  Accuracy         : 0.977669
-----------------------------------------------------------------
  Confusion Matrix:
    True Negatives  (TN):    432,110
    False Positives (FP):      9,689
    False Negatives (FN):        181
    True Positives  (TP):          0
=================================================================
```

---

## 6. Top 15 Feature Importances & Physical Interpretation

```text
Rank | Feature Name                 | Importance Score | Physical Interpretation
-----+------------------------------+------------------+---------------------------------------------------
 1   | H1_roll_std_1m               | 0.3494           | Short-term turbulence across cyclonic separator filter
 2   | H1_roll_std_5m               | 0.1341           | Sustained pressure volatility across cyclonic filter
 3   | H1_diff_5m                   | 0.0809           | Filter differential pressure rate-of-change
 4   | DV_pressure_roll_mean_5m     | 0.0418           | Air-drying tower discharge pressure baseline
 5   | TP3_roll_std_1m              | 0.0399           | Pneumatic panel line pressure jitter
 6   | Reservoirs_roll_mean_1m      | 0.0358           | Reservoir air storage pressure level
 7   | DV_pressure_diff_5m          | 0.0321           | Dryer discharge valve pressure transitions
 8   | DV_pressure                  | 0.0282           | Instantaneous drying tower discharge reading
 9   | Motor_current_roll_std_5m    | 0.0242           | Motor electrical current fluctuations under load
 10  | TP3                          | 0.0232           | Pneumatic panel pressure instantaneous reading
 11  | TP3_roll_mean_1m             | 0.0185           | Short-term panel pressure trend
 12  | Motor_current_roll_std_1m    | 0.0159           | Motor phase current short-term oscillation
 13  | Reservoirs_roll_std_5m       | 0.0159           | Downstream reservoir pressure volatility
 14  | DV_pressure_roll_mean_1m     | 0.0156           | Short-term dryer discharge pressure
 15  | Reservoirs_diff_5m           | 0.0152           | Reservoir pressure drop rate-of-change
```

---

## 7. Engineering Discussion & Real-World Machine Learning Findings

1. **Failure Heterogeneity Across Railway Episodes**:
   - In **Events #1, #2, and #3**, air leaks were preceded by severe pressure oscillations across filter `H1` and drop in panel pressure `TP3`, which tree models could detect during validation.
   - In **Event #4** (July 15, 2020), the train compressor was operating continuously pinned at maximum pressure (`~9.9 bar`) and continuous motor load (`~5.9A`) immediately before the rapid failure onset. Because the failure exhibited an abrupt onset rather than gradual cycling turbulence, the single static threshold trained on Events 1 & 2 did not trigger prior to failure time $T_0$.
2. **Significance of Real-World Telemetry**:
   - Because we strictly avoided synthetic data or fabricated labels, these results reflect genuine industrial machine learning challenges on real railway assets.
3. **Next Improvement Steps**:
   - Multi-scale windowing (e.g. 15m, 60m, 120m degradation windows).
   - Semi-supervised Reconstruction / Anomaly Detection (e.g., Autoencoder / Isolation Forest reconstruction error) paired with tree-based gradient boosting.
   - Temperature & environmental normalization (July/August summer ambient temperatures vs February/April winter/spring baseline).
