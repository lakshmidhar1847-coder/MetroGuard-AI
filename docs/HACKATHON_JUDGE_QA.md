# MetroGuard AI — Hackathon Technical Judge Q&A Guide

> **Purpose**: Provides rigorous, scientifically honest, and technically verified answers to the most challenging questions from software, machine learning, and railway reliability judges.

---

## 1. Data & Feature Engineering Questions

### Q1: Where does this dataset come from, and what machine is being monitored?
**Answer**:
> "The dataset is the **MetroPT-3 Benchmark (UCI Dataset #791)**, published by researchers monitoring an urban electric passenger train operating in a commercial metropolitan transit network. 
>
> The monitored unit is **APU-TR-03**—the train's primary **Auxiliary Power Unit (APU) Main Air Compressor and Twin-Tower Desiccant Air Dryer System**. The dataset spans 7 continuous months (February 1 to September 1, 2020) and comprises $1,486,994$ observations recorded at a $0.1\text{ Hz}$ sampling rate (1 record every 10 seconds)."

---

### Q2: What are the 15 raw telemetry channels?
**Answer**:
> "The 15 raw channels comprise:
> - **7 Analogue Physical Signals**:
>   1. `TP2` (bar): Compressor cylinder delivery pressure.
>   2. `TP3` (bar): Pneumatic panel line distribution pressure.
>   3. `H1` (bar): Cyclonic moisture separator filter pressure drop.
>   4. `DV_pressure` (bar): Desiccant drying tower purge exhaust pressure.
>   5. `Reservoirs` (bar): Main air reservoir storage pressure.
>   6. `Oil_temperature` (°C): Compressor crankcase lubricating oil temperature.
>   7. `Motor_current` (A): Electric induction drive motor current draw.
> - **8 Digital Control & Interlock States**:
>   `COMP` (Contactor run state), `DV_eletric` (Drain purge solenoid), `Towers` (Desiccant tower switch), `MPG` (Main pressure governor), `LPS` (Low-pressure safety switch), `Pressure_switch` (Cut-off switch), `Oil_level` (Float switch), and `Caudal_impulses` (Delivery pulse rate)."

---

### Q3: Why did you engineer 65 features from 15 raw channels?
**Answer**:
> "In reciprocating compressors, component degradation manifests as dynamic instability rather than static threshold breaches. For example, a clogged moisture filter or leaking delivery check-valve causes high-frequency pressure oscillations, solenoid chatter, and elongated charging cycles while instantaneous pressure readings may temporarily appear normal.
>
> We engineer 65 domain features:
> - 15 raw instantaneous base signals.
> - 14 rolling means ($1\text{m}$ and $5\text{m}$) capturing gradual thermal and baseline pressure drift.
> - 14 rolling standard deviations ($1\text{m}$ and $5\text{m}$) capturing turbulence, valve jitter, and flow distortion.
> - 14 moving differentials ($\Delta 1\text{m}$ and $\Delta 5\text{m}$) capturing rapid pressure collapse gradients.
> - 8 state transition counters ($5\text{m}$) capturing solenoid hunting and duty cycle saturation.
>
> All features use backward-looking causal rolling windows ($[t - W, t]$) to ensure zero future data leakage."

---

## 2. Machine Learning & Anomaly Detection Questions

### Q4: Why did you use XGBoost for Tier 1? What does it predict?
**Answer**:
> "We selected **XGBoost (Histogram Gradient Boosted Trees)** because tabular time-series features exhibit complex non-linear threshold interactions across pressures, temperatures, and duty cycles.
>
> XGBoost is trained as a binary classifier to predict:
> $$P(y_t = 1 \mid \mathbf{x}_t) = P(\text{Failure occurs within the next 30 minutes} \mid \mathbf{x}_t)$$
> We configure a forward-looking prediction horizon of 30 minutes ($180$ rows pre-failure). XGBoost was trained with `scale_pos_weight = 2554.33` to handle the extreme class imbalance ($0.039\%$ failure positives in training)."

---

### Q5: How was the XGBoost production threshold ($\tau = 0.10$) selected?
**Answer**:
> "We performed a threshold sensitivity sweep across $\tau \in [0.01, 0.90]$ on our independent validation partition (June 2020, Event #3). 
>
> In railway safety systems, false negatives (missed failures) are far more costly than false alarms (brief inspections). A threshold of $\tau = 0.10$ maximizes early pre-failure detection lead time while avoiding excessive false alarms during routine compressor cycling."

---

### Q6: Why did you add Isolation Forest? Why not just use XGBoost?
**Answer**:
> "Supervised learning inherently suffers from **distribution shift and unseen failure mode blindspots**. In industrial environments, machines can degrade in novel ways never captured in the training data.
>
> For instance, our XGBoost model was trained on spring pneumatic leaks (Events #1 & #2). When evaluated on the unseen **July Event #4 holdout**—which was an extreme summer thermal overload ($>81^\circ\text{C}$)—XGBoost output only $0.06\%$ risk because it had never seen thermal runaway failure labels.
>
> **Isolation Forest** provides an orthogonal, unsupervised defense layer. Trained on $140,914$ clean normal baseline samples, it isolates multidimensional outliers without requiring labels, achieving **$33.15\%$ recall on the unseen summer Event #4 holdout** and catching the $+3.69\sigma$ thermal elevation."

---

### Q7: How is the Isolation Forest score calibrated into a 0–100 Anomaly Severity Index?
**Answer**:
> "Raw Isolation Forest scores $S(\mathbf{x}) = -\text{score\_samples}(\mathbf{x})$ fall in the range $[0.30, 0.60]$, which is unintuitive for operators.
>
> We apply a piecewise linear calibration anchored to empirical percentiles of clean training data:
> - $S < 0.35 \rightarrow \mathbf{0\text{–}20}$ (`NOMINAL` background noise)
> - $S \in [0.35, 0.5040) \rightarrow \mathbf{20\text{–}50}$ (`LOW` operating range)
> - $S \in [0.5040, 0.5350) \rightarrow \mathbf{50\text{–}75}$ (`ELEVATED` anomaly, above 99th percentile $\tau_{\text{elevated}} = 0.5040$)
> - $S \ge 0.5350 \rightarrow \mathbf{75\text{–}100}$ (`SEVERE` anomaly, above 99.5th percentile $\tau_{\text{high}} = 0.5350$)"

---

## 3. Hybrid Decision Engine & Explainability Questions

### Q8: How does the Hybrid Decision Engine combine XGBoost, Isolation Forest, and Physical Evidence?
**Answer**:
> "The engine operates deterministically with clear industrial precedence rules:
> 1. **`HIGH RISK` (Critical Priority)**: Triggered if XGBoost $\ge 70\%$, OR if XGBoost $\ge 10\%$ simultaneously coincides with elevated Isolation Forest severity ($\ge 50/100$).
> 2. **`WARNING` (High / Medium Priority)**: Triggered if XGBoost $\ge 10\%$ (Pneumatic Warning), OR if Isolation Forest reaches severe levels ($\ge 75/100$) / sustained elevated anomaly with $|Z| \ge 2.0\sigma$ physical deviations (Thermal / Anomaly Warning).
> 3. **`MONITOR` (Low Priority)**: Triggered on isolated transient outliers, initiating a 5-minute persistence buffer.
> 4. **`NORMAL` (Nominal)**: Confirms all signals remain within baseline boundaries."

---

### Q9: What is Physical Evidence Attribution, and how does it prevent black-box decisions?
**Answer**:
> "Instead of providing an uninterpretable probability, MetroGuard decomposes active sensor features into statistical $Z$-scores relative to normal baseline medians:
> $$Z = \frac{x_i - \text{Median}_{\text{normal}}}{\sigma_{\text{normal}}}$$
> Signals exceeding $|Z| \ge 2.0\sigma$ are dynamically formatted into human-readable evidence cards (e.g., *'Cyclonic Separator Drop (H1) is elevated at 8.24 bar, +2.19σ above normal'*). This directly informs the technician which physical subsystem is degrading."

---

## 4. Scientific Evaluation & Anti-Leakage Questions

### Q10: How did you ensure zero data leakage in your ML pipeline?
**Answer**:
> "We enforced strict temporal, leak-free protocols:
> 1. **Chronological Splitting**: We strictly split data by time and failure events. Zero random shuffling or $K$-fold cross-validation was used.
>    - *Train*: Feb 1 – May 31, 2020 ($845,815$ rows, Events #1 & #2).
>    - *Validation*: June 1 – June 30, 2020 ($199,199$ rows, Event #3).
>    - *Untouched Final Test*: July 1 – September 1, 2020 ($441,980$ rows, Event #4 + August holdout).
> 2. **No Synthetic Balancing**: We strictly rejected SMOTE or generative oversampling, training directly on authentic imbalanced distributions ($0.039\%$ positives).
> 3. **Causal Feature Windows**: All rolling statistics use backward-looking horizons only."

---

### Q11: Why is raw accuracy a misleading metric for predictive maintenance?
**Answer**:
> "On our $441,980$-row final test partition, failure positives represent only $181$ rows ($0.041\%$). A trivial 'dumb' baseline that always outputs 'Normal' achieves **$99.96\%$ accuracy while missing $100\%$ of failures**.
>
> That is why we evaluate **Precision-Recall Area Under Curve (PR-AUC)**, **ROC-AUC ($0.9797$)**, and **Event Recall ($98.18\%$ on spring failures, $33.15\%$ on summer holdout)**."

---

### Q12: Why doesn't MetroGuard show a continuous Remaining Useful Life (RUL) countdown clock?
**Answer**:
> "We conducted a formal quantitative RUL audit (**Outcome B Protocol**). The dataset contains only $N=4$ recorded failure events across 7 months on a single train unit (`APU-TR-03`). Furthermore, the failure modes are heterogeneous (pneumatic leaks vs summer thermal stress).
>
> Attempting to train a continuous regression RUL model on $N=4$ cycles produces completely ungeneralizable, overfitted countdown numbers. MetroGuard adheres to scientific honesty: we provide validated **30-minute early warning classification and anomaly severity tracking**, transparently explaining why exact continuous RUL regression is unsupported by the data."

---

## 5. Industrial Deployment & Real-World Operations Questions

### Q13: Does MetroGuard directly actuate machine controls or train brakes?
**Answer**:
> "No. MetroGuard is architected strictly as an **Operator and Depot Decision Support System**. In railway operations, automated emergency braking is governed by SIL-4 certified hardware safety relays (e.g., trainline safety loops).
>
> MetroGuard assists human depot engineers and dispatchers by prioritizing staging queues, generating work orders, and providing targeted 4-point inspection checklists before trains enter revenue service."

---

### Q14: What happens if the model produces a false positive or false negative?
**Answer**:
> "- **False Positive Handling**: A transient alarm is held at `MONITOR` advisory status unless sustained across a 5-minute persistence window. If an alert is generated, the operator can click **Acknowledge** and **Resolve** in the UI, logging the event in the audit trail without disrupting train scheduling.
> - **False Negative Mitigation**: Because Tier 1 (XGBoost) and Tier 2 (Isolation Forest) operate orthogonally, a failure signature missed by supervised pattern matching is captured by the unsupervised anomaly detector."

---

### Q15: How would you deploy MetroGuard in an actual railway enterprise?
**Answer**:
> "Our architecture is production-ready for two deployment modes:
> 1. **On-Train Edge Processing**: The feature engineering and dual-tier inference pipeline can be compiled via ONNX Runtime to execute locally on an ARM64 embedded train-borne gateway, sending lightweight incident JSON packets via cellular / trackside Wi-Fi.
> 2. **Depot Fleet Cloud Service**: The existing FastAPI backend can ingest multi-train MQTT / Kafka telemetry streams, serving centralized command dashboards across hundreds of fleet units simultaneously."
