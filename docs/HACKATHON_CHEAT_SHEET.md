# MetroGuard AI — 1-Page Hackathon Presenter Cheat Sheet

> **Keep this open or printed right before presenting to judges.**

---

## ⚡ 30-Second Elevator Pitch
> *"MetroGuard AI is a predictive maintenance command center for urban rail air compressors. Today, traditional alarms only trigger after pressure collapses, stranding trains in tunnels. MetroGuard ingests 15 raw telemetry channels, engineers 65 time-series features, runs dual-tier supervised and unsupervised AI, and attributes physical Z-score evidence. This gives maintenance teams a 30-minute early warning and actionable 4-point inspection checklists before in-service breakdown occurs."*

---

## ⏱️ 2-Minute Rapid Walkthrough
1. **The Machine**: Compressor `APU-TR-03` (MetroPT-3 benchmark, 1.48M records, 7 months).
2. **Telemetry to Features**: 15 raw channels (7 analogue + 8 digital) $\rightarrow$ 65 rolling statistics & decay rates (zero leakage).
3. **Dual AI Tier**:
   - **XGBoost (Supervised)**: $98.78\%$ recall on known pneumatic leaks ($\tau = 0.10$).
   - **Isolation Forest (Unsupervised)**: $0\text{–}100$ severity index catching unseen summer thermal anomalies ($+3.69\sigma$ oil temp).
4. **Physical Evidence**: $Z$-score deviations ($|Z| \ge 2.0\sigma$) explain exactly *why* the machine is abnormal.
5. **Deterministic Hybrid Decision**: `NORMAL` $\rightarrow$ `MONITOR` $\rightarrow$ `WARNING` $\rightarrow$ `HIGH RISK`.
6. **Prescriptive Action**: Actionable depot checklists (pressure decay test, valve inspection).
7. **Scientific Honesty**: Validated on an untouched 62-day summer test holdout; rejects fake RUL countdowns (Outcome B).

---

## 🎯 Core Model Roles & Key Thresholds

| Component | Model / Method | Role | Key Threshold | Top Verified Metric |
| :--- | :--- | :--- | :---: | :--- |
| **Tier 1** | XGBoost Classifier (150 trees) | Known Failure Prediction | $\tau = 0.10$ | **98.78% Recall** on Event #1 |
| **Tier 2** | Isolation Forest (150 trees) | Unsupervised Outliers | $\tau = 0.5040$ (99th %-tile) | **33.15% Recall** on Summer Event #4 |
| **Evidence** | $Z$-Score Baseline Medians | Physical Attribution | $\|Z\| \ge 2.0\sigma$ | Oil Temp $+3.69\sigma$ ($81.4^\circ\text{C}$) |
| **Hybrid** | Deterministic Precedence Rules | Operational State | Precedence Matrix | **0.9797 ROC-AUC** on Final Test |

---

## 🌟 Recommended Live Demo Progression (Start from Overview `/`)

1. **Step 1 — Overview Storytelling (`/`)**: Select **Scenario 3: Pre-Failure Event #1** $\rightarrow$ Click **▶ Start Replay** ($5\text{x}$). Let judges watch telemetry update live, XGBoost surge to **$98.78\%$**, trigger **`CRITICAL`** incident, and generate **Prescriptive Maintenance Action**.
2. **Step 2 — Open Detailed Monitoring (`/monitoring`)**: Click *"Detailed Monitoring & Alerts →"* to show seamless synchronization on the same live stream, showing the interactive 4-point checklist and live multi-scale waveforms.
3. **Step 3 — Summer Holdout Event #4**: Switch to **Scenario 4** on Overview or Monitoring to show how Isolation Forest catches the **$+3.69\sigma$ thermal overload** with **`WARNING / HIGH Priority`** when supervised ML suffered seasonal distribution shift.

---

## 🔍 Hackathon Judge Core Concepts

### "Why Two Models?" (Dual-Tier AI)
- **Tier 1 (Supervised XGBoost)**: Pattern matcher trained on known historical pneumatic leaks ($98.78\%$ recall on Event #1).
- **Tier 2 (Unsupervised Isolation Forest)**: Safety net measuring multi-dimensional outlier distance ($0\text{–}100$ severity) to catch unseen seasonal regimes and thermal drift ($+3.69\sigma$ on Event #4) where supervised models face distribution shift.
- **Hybrid Engine**: Deterministically synthesizes both signals with physical $Z$-scores.

### "Why This Alert?" (4-Step Causal Chain)
1. **Physical**: Sensor deviating beyond normal median ($|Z| \ge 2.0\sigma$).
2. **AI Signal**: Supervised leak pattern ($P \ge 0.10$) OR unsupervised outlier ($S \ge 0.5040$).
3. **Threshold**: Production risk/severity threshold crossed.
4. **Decision**: Deterministic hybrid escalation into actionable depot priority (`CRITICAL` / `HIGH` / `MEDIUM` / `LOW`).

---

## 🧠 Top 5 Must-Remember Judge Answers

1. **Terminology**: Always say *"15 raw telemetry channels producing 65 engineered time-series features"*. Never say "65 sensors".
2. **Why Two Models?**: Supervised XGBoost detects known failure signatures; Unsupervised Isolation Forest catches out-of-distribution seasonal regimes that single-tier ML misses.
3. **Why Not Accuracy?**: With $0.041\%$ class imbalance, guessing "Normal" gives $99.96\%$ accuracy but misses every failure. We evaluate PR-AUC, ROC-AUC ($0.9797$), and Event Recall.
4. **Where Is Continuous RUL?**: Honestly explain **Outcome B**—with $N=4$ failure cycles across 7 months, continuous countdown regression is statistically invalid. We provide validated 30-minute classification instead.
5. **Safety Control**: MetroGuard is a depot decision support system, not an autonomous brake actuator.

---

## 🔗 Live Application URLs (Keep Tabs Open)

- **Overview Dashboard**: `http://127.0.0.1:8000/`
- **Live Monitoring & Alert Command Center**: `http://127.0.0.1:8000/monitoring`
- **AI Risk Diagnostics & Radar**: `http://127.0.0.1:8000/risk`
- **Sensors Suite**: `http://127.0.0.1:8000/sensors`
- **Audited Model Performance**: `http://127.0.0.1:8000/performance`
- **Case Studies & Operational Impact**: `http://127.0.0.1:8000/case-study`
