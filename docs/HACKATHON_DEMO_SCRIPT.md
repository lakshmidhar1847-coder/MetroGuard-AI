# MetroGuard AI — Master Hackathon Demonstration Script & Presentation Guide

> **Target Presentation Duration**: 8–10 Minutes (Standard Hackathon Judging Session)  
> **Emergency Pitch Duration**: 3 Minutes (Rapid Stage / Lightning Demo)  
> **Target Audience**: Mixed Judging Panel (Non-technical executives, AI/ML researchers, and Railway / Industrial Reliability engineers)  
> **Monitored Asset**: APU-TR-03 (MetroPT-3 Urban Rail Auxiliary Power Air Compressor)  
> **Core Pipeline**: 15 Raw Telemetry Channels $\rightarrow$ 65 Engineered Features $\rightarrow$ Dual-Tier AI (XGBoost + Isolation Forest) $\rightarrow$ Physical Evidence ($Z$-scores) $\rightarrow$ Hybrid Decision Engine $\rightarrow$ Smart Alert Center $\rightarrow$ Prescriptive Maintenance Checklist $\rightarrow$ Operator Command Center

---

## 1. Screen-by-Screen Recommended Demonstration Flow

| Step | Time | Page / Screen Route | Live Feature to Demonstrate | Key Spoken Message |
| :---: | :---: | :--- | :--- | :--- |
| **1** | $0:00 - 1:00$ | **`/`** (Overview) | Hero Banner, Asset `APU-TR-03`, 6-Step Pipeline Flow, **Interactive Multi-Event Replay Bar** | Real-world problem: undetected compressor leaks lead to train cancellations. MetroGuard provides actionable decision support. Select Event #1, hit **Start Replay**, and watch machine telemetry and AI risk evolve directly on the overview storytelling view! |
| **2** | $1:00 - 1:45$ | **`/sensors`** (Sensors Suite) | 15 Signals Catalog, Multi-Scale Waveform (`TP2`), 8 Digital States | 15 raw channels (7 analogue + 8 digital states) at 10s intervals transformed into 65 engineered time-series features. |
| **3** | $1:45 - 2:45$ | **`/risk`** (AI Risk Diagnostics) | Risk Gauge dial, Dual-Tier Diagnostic cards, Top Gini Gain Features | Tier 1 Supervised XGBoost (Known Failures) + Tier 2 Unsupervised Isolation Forest (Outliers) + Physical $Z$-score Evidence. |
| **4** | $2:45 - 4:45$ | **`/monitoring`** (Detailed Command Center) | Replay Synchronized Stream, Active Incident Card, Acknowledge/Resolve, Prescriptive Checklist, Anomaly Scorecard | Seamless synchronization: Monitoring shows the detailed technical telemetry and interactive 4-point checklist of the SAME active replay stream. |
| **5** | $4:45 - 6:00$ | **`/case-study`** (Case Studies) | Case 01 (Event #1) & Case 02 (Event #4) 6-stage timelines & qualitative impact cards | Why hybrid AI is mandatory: Supervised ML recognizes pneumatic leaks; Unsupervised Anomaly catches seasonal thermal drift under distribution shift. |
| **6** | $6:00 - 7:00$ | **`/performance`** (Model Performance) | 62-day Summer Holdout Headline ($441,980$ rows), PR-AUC, Confusion Matrix | Scientific integrity: Why accuracy ($97.77\%$) is misleading on $0.04\%$ class imbalance; anti-leakage temporal split methodology. |
| **7** | $7:00 - 8:00$ | **`/`** (Overview) | 4-KPI Scorecard, Capabilities vs Boundaries Matrix | Closing summary: MetroGuard turns raw sensor streams into explainable, evidence-backed prescriptive maintenance actions. |

---

## 2. Complete 8–10 Minute Master Presenter Script

### PART 1 — THE HOOK, STORYTELLING & LIVE OVERVIEW REPLAY ($0:00 - 1:15$)
- **URL**: `http://127.0.0.1:8000/`
- **SHOW**: 
  1. The Overview Dashboard hero header (`APU-TR-03`) and 6-step pipeline banner.
  2. The **Multi-Event Live Telemetry Replay Bar** and **Hackathon Quick Launchers**.
  3. The **Current Machine Status & Primary Operational Concern** card.
  4. The **Event Progression Timeline** (5 dynamic stages).
  5. The **Why This Alert? Explainability Chain** & **AI Signal Comparison ("Why Two Models?")**.
- **ACTION**: Select **Scenario 3: Pre-Failure (Event #1)** and click **▶ Start Replay** (set speed to `5x`).
- **SAY**:
  > "Good morning, judges. In urban passenger rail transit, the main air compressor is the heartbeat of the train. It powers the friction brakes, the suspension leveling, and passenger door actuation.
  >
  > Today, when a pneumatic solenoid valve leaks or a cooling matrix clogs, traditional SCADA systems only sound an alarm after reservoir pressure has completely collapsed. By then, the train is stranded in a tunnel, passengers are delayed, and depot operations are bottlenecked.
  >
  > MetroGuard AI turns machine telemetry into an intelligent, early-warning decision support system. Right here on our Overview Dashboard, we are replaying **historical pre-failure Event #1** from the MetroPT-3 benchmark:
  > - Notice how the **Current Machine Status** dynamically updates: Supervised XGBoost risk surges to **98.8%**, triggering a **CRITICAL Priority Smart Alert**.
  > - Look at our **Event Progression Timeline**: the marker advances from *Normal Baseline* $\rightarrow$ *Anomaly Onset* $\rightarrow$ *Warning State* $\rightarrow$ *High Risk Escalation*.
  > - In our **Why This Alert? Explainability Chain**, technicians see the exact 4-step reason: physical $H1$ separator drop deviation ($+2.44\sigma$), XGBoost pre-failure pattern detection, threshold crossing ($\tau = 0.10$), and deterministic hybrid escalation.
  > - And our **Prescriptive Action** provides the depot team with a targeted pneumatic leak directive before in-service breakdown occurs."
- **JUDGE TAKEAWAY**: The judges immediately see the complete multi-signal reasoning story—from raw sensor shifts to explainable AI detection and prescriptive maintenance actions—directly on the main dashboard.

---

### PART 2 — WHAT METROGUARD ACTUALLY OBSERVES ($0:45 - 1:15$)
- **URL**: `http://127.0.0.1:8000/sensors`
- **SHOW**: The Sensor Analysis page, selecting `TP2` (Compressor Output Pressure), and highlighting the 8 Digital Control Signals at the bottom.
- **SAY**:
  > "Let's look at what the system actually observes from the physical machine. MetroGuard ingests **15 raw telemetry channels** sampled every 10 seconds:
  > - 7 analog physical sensors—including compressor delivery pressure, panel distribution lines, moisture separator drop, and crankcase oil temperature.
  > - 8 discrete digital control states—including compressor contactors, drying tower solenoids, and pressure governor switches."
- **JUDGE TAKEAWAY**: The system runs on real industrial multi-sensor data (15 physical channels), not simulated mock variables.

---

### PART 3 — FEATURE ENGINEERING & ROLLING BEHAVIOR ($1:15 - 1:45$)
- **URL**: `http://127.0.0.1:8000/sensors`
- **SHOW**: The multi-scale rolling line chart showing Raw Reading vs 1-Minute Mean vs 5-Minute Baseline.
- **SAY**:
  > "In industrial machinery, a raw instantaneous reading rarely tells the whole story. A pressure of 8 bar might look normal on its own, but if its 1-minute rolling volatility spikes while the 5-minute decay rate accelerates, that reveals a developing leak.
  >
  > MetroGuard transforms those **15 raw telemetry channels into 65 engineered time-series features**:
  > - 1-minute and 5-minute rolling averages capturing gradual thermal drift.
  > - Rolling standard deviations capturing aerodynamic turbulence and filter jitter.
  > - Differential rates-of-change capturing pressure decay gradients.
  > - And 5-minute digital state transition counts capturing solenoid chatter.
  >
  > Crucially, all 65 features are computed strictly using backward-looking causal windows with zero future data leakage."
- **JUDGE TAKEAWAY**: Feature engineering transforms 15 raw channels into 65 rich time-series features that reveal degradation before pressure thresholds trip.

---

### PART 4 — THE DUAL-TIER AI ARCHITECTURE ($1:45 - 2:45$)
- **URL**: `http://127.0.0.1:8000/risk`
- **SHOW**: The Risk Assessment page, highlighting Tier 1 (XGBoost) vs Tier 2 (Isolation Forest) side-by-side diagnostic cards, and the radial Risk Gauge dial.
- **SAY**:
  > "To evaluate failure risk, MetroGuard deploys a **Dual-Tier AI Architecture**:
  >
  > **Tier 1 is a Supervised XGBoost Classifier**. It is trained on historical pre-failure episodes to predict the exact probability that the compressor will experience a breakdown within the next 30 minutes: $P(\text{Failure within 30m} \mid \mathbf{x})$. On verified historical spring pneumatic leaks, it achieves **98.78% recall**.
  >
  > But supervised learning has a well-known vulnerability in production: *distribution shift*. If an unprecedented failure mode occurs—like extreme summer thermal overload—supervised models trained only on spring leaks can miss it.
  >
  > That's why we built **Tier 2: an Unsupervised Isolation Forest Anomaly Detector**. It doesn't look for known failure labels. Instead, it measures multi-dimensional outlier distance across all 65 features compared against 140,000 clean baseline observations, mapping this to a calibrated 0-to-100 Anomaly Severity Index."
- **JUDGE TAKEAWAY**: The dual-tier architecture combines supervised pattern precision with unsupervised anomaly protection against unforeseen distribution shifts.

---

### PART 5 — PHYSICAL EVIDENCE ATTRIBUTION ($2:45 - 3:30$)
- **URL**: `http://127.0.0.1:8000/risk`
- **SHOW**: The "Why This Alert?" Diagnostic Panel, showing $Z$-scores ($>2.0\sigma$) and the Gini Gain feature importance ranking.
- **SAY**:
  > "Railway technicians will never trust a black-box percentage. If the AI simply outputs '85% risk', the engineer cannot act on it.
  >
  > MetroGuard bridges machine learning and mechanical engineering through **Physical Evidence Attribution**. For every observation, the system computes statistical $Z$-scores relative to normal baseline medians:
  > $$Z = \frac{x_i - \text{Median}_{\text{normal}}}{\sigma_{\text{normal}}}$$
  >
  > When an anomaly occurs, the system highlights the exact physical signals deviating beyond $\pm 2.0\sigma$—such as a $+2.19\sigma$ differential drop across the cyclonic moisture separator ($H1$), or a $+3.69\sigma$ elevation in oil temperature. The operator sees the physical cause immediately."
- **JUDGE TAKEAWAY**: $Z$-score physical evidence transforms black-box ML into transparent, explainable engineering diagnostics.

---

### PART 6 — DETERMINISTIC HYBRID DECISION SYNTHESIS ($3:30 - 4:15$)
- **URL**: `http://127.0.0.1:8000/monitoring`
- **SHOW**: The Machine Health Banner showing Operational State (`NORMAL`, `MONITOR`, `WARNING`, `HIGH RISK`).
- **SAY**:
  > "MetroGuard does not leave decision synthesis to chance. Our **Deterministic Hybrid Decision Engine** applies rigorous industrial precedence:
  > 1. **HIGH RISK (Critical)**: Triggers when supervised XGBoost risk reaches $\ge 70\%$, or when $\ge 10\%$ risk coincides with elevated unsupervised anomaly scores.
  > 2. **WARNING (High/Medium)**: Triggers on known failure warnings ($\ge 10\%$) or sustained out-of-distribution anomaly severity ($\ge 50/100$).
  > 3. **MONITOR (Advisory)**: Triggers on isolated transient deviations, flagging them for persistence window tracking.
  > 4. **NORMAL**: Confirms all 15 physical channels and 65 features remain within calibrated baseline envelopes."
- **JUDGE TAKEAWAY**: A deterministic decision engine synthesizes orthogonal AI outputs into predictable, safety-aligned operational states.

---

### PART 7 — LIVE DEMONSTRATION: REPLAY & PRESCRIPTIVE ACTION ($4:15 - 5:45$)
- **URL**: `http://127.0.0.1:8000/monitoring`
- **SHOW**:
  1. Click **Scenario 1 (Normal Baseline)** $\rightarrow$ Show `NORMAL` state, Risk $0.03\%$, Anomaly $19/100$, 0 critical alerts.
  2. Click **Scenario 3 (Pre-Failure Event #1)** $\rightarrow$ Watch live step progression:
     - XGBoost risk surges to **$98.78\%$**.
     - Incident Card triggers **`CRITICAL Priority (ALT-PRE-0002)`**.
     - Show the **Prescriptive Maintenance Action**: *"Immediate depot pneumatic leak inspection & pressure decay test"*.
     - Demonstrate clicking the interactive 4-point checklist (Pressure decay test, check delivery valve, inspect moisture drain valve).
     - Click **Acknowledge Alert** and **Mark Resolved** to show operator workflow lifecycle tracking.
  3. Click **Scenario 4 (Summer Holdout Event #4)** $\rightarrow$ Show the distribution shift defense:
     - Supervised XGBoost shows only $0.06\%$ (blindspot under thermal shift).
     - Isolation Forest catches it with Anomaly Severity **$52/100$ (`ELEVATED`)** and Oil Temp **$81.4^\circ\text{C}$ ($+3.69\sigma$)**.
     - Incident updates to **`WARNING / HIGH Priority`** with prescriptive radiator cooling checklist.
- **SAY**:
  > "Let's see this in action using our real-time telemetry replay engine.
  >
  > Under **Normal Baseline**, the compressor charges smoothly. Risk is $0.03\%$, anomaly index is nominal ($19/100$).
  >
  > Now, let's load **Pre-Failure Event #1**—a real historical pneumatic leak. Notice the rapid escalation: XGBoost identifies the leak pattern, surging to **98.8% risk**. A **CRITICAL Smart Alert** is dispatched with primary evidence ($H1$ separator drop at $+2.19\sigma$). The prescriptive engine provides the depot technician with a targeted 4-point inspection checklist. The operator acknowledges the alert, stages the repair, and resolves the incident.
  >
  > Next, look at **Summer Holdout Event #4**. Because this was an extreme thermal overload in July, the supervised XGBoost model output only $0.06\%$. But MetroGuard's unsupervised Isolation Forest immediately catches the thermal runaway ($+3.69\sigma$ oil temp), triggering an Anomaly Warning and directing technicians to inspect the radiator cooling circuit."
- **JUDGE TAKEAWAY**: The live demo proves the complete chain: raw signal shift $\rightarrow$ dual-tier detection $\rightarrow$ physical evidence $\rightarrow$ prescriptive 4-point checklist $\rightarrow$ operator workflow.

---

### PART 8 — REAL-WORLD CASE STUDIES ($5:45 - 6:45$)
- **URL**: `http://127.0.0.1:8000/case-study`
- **SHOW**: Case 01 vs Case 02 tabs, 6-stage chronological incident timeline, and qualitative impact cards.
- **SAY**:
  > "On our Case Studies page, we document these historical episodes from the MetroPT-3 benchmark:
  > - **Case 01** demonstrates how Supervised AI delivered a **30-minute early warning** prior to catastrophic pneumatic breakdown on Event #1.
  > - **Case 02** proves why our Hybrid Architecture is essential—catching summer thermal drift that single-model classifiers missed.
  >
  > Notice our **Scientific Integrity Protocol**: we explicitly present qualitative, evidence-aligned operational impacts (Early Warning Lead Time: HIGH, Maintenance Prioritization: HIGH) rather than inventing fabricated dollar savings or guaranteed failure prevention claims."
- **JUDGE TAKEAWAY**: Grounded in verified historical episodes with strict scientific transparency.

---

### PART 9 — AUDITED MODEL EVALUATION & ANTI-LEAKAGE AUDIT ($6:45 - 7:30$)
- **URL**: `http://127.0.0.1:8000/performance`
- **SHOW**: The 62-day Summer Holdout Headline ($441,980$ rows), PR-AUC and Recall table, and Threshold Sensitivity sweep.
- **SAY**:
  > "Let's examine the rigorous scientific evaluation. MetroGuard was tested on an **untouched 62-day summer holdout partition (July–September 2020) containing 441,980 continuous observations**.
  >
  > In predictive maintenance, failure rows represent only $0.041\%$ of the dataset. Therefore, raw accuracy ($97.77\%$) is completely deceptive because a naive model predicting 'Normal' would achieve $99.96\%$ accuracy while catching zero failures.
  >
  > We evaluate PR-AUC, ROC-AUC ($0.9797$), and Event Recall ($33.15\%$ on unseen holdout Event #4 and $98.18\%$ on spring events). Our data splits are strictly chronological with zero random shuffling and zero synthetic data fabrication."
- **JUDGE TAKEAWAY**: The team understands industrial class imbalance and evaluates models with strict leak-free methodology.

---

### PART 10 & 11 — SCIENTIFIC HONESTY & CLOSING ($7:30 - 8:30$)
- **URL**: `http://127.0.0.1:8000/`
- **SHOW**: Overview page, highlighting the Validated Capabilities vs Boundaries matrix.
- **SAY**:
  > "Finally, let's address Remaining Useful Life. Many predictive maintenance projects display an invented countdown clock saying '4 hours remaining'. We conducted a formal mathematical audit and established **Outcome B**: with only $N=4$ recorded failure cycles across 7 months of single-unit data, claiming a continuous regression RUL is scientifically unsupportable. MetroGuard chooses honesty over fake precision.
  >
  > In conclusion: MetroGuard is not just predicting a number. It ingests 15 raw telemetry channels, extracts 65 engineered time-series features, runs dual-tier supervised and unsupervised AI, attributes physical $Z$-score evidence, and delivers actionable prescriptive checklists to keep urban rail fleets running safely.
  >
  > Thank you. We are ready for your questions."
- **JUDGE TAKEAWAY**: MetroGuard combines technical excellence, explainable multi-signal intelligence, and uncompromising scientific credibility.

---

## 3. The 3-Minute Emergency Lightning Demo Script

Use this ultra-concise script when judges have limited time:

| Time | Action & Screen | Spoken Script |
| :---: | :--- | :--- |
| **0:00 - 0:20** | **Overview (`/`)** | "MetroGuard AI solves a critical railway problem: undetected compressor leaks lead to train service cancellations. MetroGuard provides 30-minute early warning and prescriptive repair checklists before pressure collapses." |
| **0:20 - 0:40** | **Sensors (`/sensors`)** | "We ingest **15 raw telemetry channels** (7 analogue + 8 digital states) at 10-second intervals, extracting **65 engineered time-series features** including rolling volatilities and pressure decay rates with zero future data leakage." |
| **0:40 - 1:10** | **Risk (`/risk`)** | "Our Dual-Tier AI combines **Supervised XGBoost** (98.8% recall on known pneumatic leaks) with **Unsupervised Isolation Forest** (catching unseen summer thermal outliers), backed by statistical $Z$-score physical evidence." |
| **1:10 - 2:10** | **Live Monitoring (`/monitoring`)** | "Here is our live replay: Under **Pre-Failure Event #1**, XGBoost surges to **98.8% risk**, generating a **CRITICAL Smart Alert** and a directed **4-point pneumatic inspection checklist**. Under **Summer Event #4**, unsupervised anomaly detection catches a $+3.69\sigma$ thermal overload where single-tier models failed." |
| **2:10 - 2:40** | **Case Study / Performance (`/case-study`)** | "We validated this on an untouched 62-day summer holdout ($441,980$ rows) with $0.9797$ ROC-AUC. We transparently disclose our boundaries—rejecting fake countdown clocks in favor of validated early warning classification." |
| **2:40 - 3:00** | **Overview (`/`)** | "MetroGuard transforms complex machine telemetry into explainable, evidence-backed operator action. Thank you!" |

---

## 4. "Why is MetroGuard Different?" Judge Comparison Matrix

| Capability / Dimension | Traditional SCADA Alarms | Single Supervised ML Model | MetroGuard AI Hybrid Command Center |
| :--- | :---: | :---: | :---: |
| **Telemetry Ingestion** | Raw static thresholds ($P < 7.0\text{ bar}$) | Flat instantaneous features | **15 Raw Channels $\rightarrow$ 65 Rolling Time-Series Features** |
| **Known Failure Detection** | ❌ None (Post-failure only) | ✅ Yes (High precision on training data) | ✅ **Tier 1 XGBoost (98.78% recall on Event #1)** |
| **Unseen Out-of-Distribution Regimes**| ❌ Blind | ❌ Blind (Distribution shift failure) | ✅ **Tier 2 Isolation Forest (33.15% recall on Summer Holdout)** |
| **Explainable Physical Evidence** | ❌ Raw values only | ❌ Black-box probabilities | ✅ **Statistical $Z$-Scores relative to normal baseline medians** |
| **Operational Decision Logic** | Hardcoded alarm thresholds | Single probability threshold | ✅ **Deterministic Hybrid Engine (Normal / Monitor / Warning / High Risk)** |
| **Prescriptive Action Guidance** | ❌ None | ❌ None | ✅ **Targeted mechanical remediation & 4-point inspection checklists** |
| **Operator Lifecycle Tracking** | ❌ Unmanaged alarms | ❌ Static score | ✅ **Active / Acknowledged / Resolved / Escalated workflow audit** |
| **Scientific Honesty on RUL** | ❌ N/A | ⚠️ Often invents fake countdowns | ✅ **Outcome B: Transparent sample scarcity ($N=4$) disclosure** |

---

## 5. Live Demonstration Failure & Fallback Protocol

If an unexpected technical glitch occurs during judging, follow this graceful protocol:

1. **If Backend Server Disconnects**:
   - *Action*: Open terminal and re-run `python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000`.
   - *Presenter pivot*: *"Let me refresh the live Uvicorn service connection—our static React frontend serves cached telemetry seamlessly while the API reconnects."*
2. **If Replay Stream Pauses or Lags**:
   - *Action*: Navigate to `/case-study` and show **Case 01** and **Case 02**.
   - *Presenter pivot*: *"We have pre-computed full 6-stage chronological timelines for all documented UCI #791 episodes on our Case Study page, showing the exact signal progression at every milestone stage."*
3. **If Browser Tab Hangs**:
   - *Action*: Hard refresh (`Ctrl + F5`) on `http://127.0.0.1:8000/`.
   - *Presenter pivot*: *"The single-page application mounts instantaneously with all 6 command views synchronized."*
4. **General Golden Rule**:
   - **NEVER fabricate live data or pretend a static chart is live**. State honestly: *"This demonstrates the verified replay of the historical MetroPT-3 holdout episode."*

---

## 6. Pre-Demo Environment Checklist (5 Minutes Before Stage)

- [ ] **Backend Running**: Uvicorn server active on `http://127.0.0.1:8000/` (verify via `curl http://127.0.0.1:8000/api/health` $\rightarrow$ `{"status":"ONLINE"}`).
- [ ] **Frontend Build Current**: `npm run build` executed cleanly in `frontend/dist/`.
- [ ] **Browser Tabs Prepared**:
  - Tab 1: `http://127.0.0.1:8000/` (Overview)
  - Tab 2: `http://127.0.0.1:8000/monitoring` (Live Monitoring)
  - Tab 3: `http://127.0.0.1:8000/risk` (Risk Diagnostics)
  - Tab 4: `http://127.0.0.1:8000/case-study` (Case Studies)
  - Tab 5: `http://127.0.0.1:8000/performance` (Model Performance)
- [ ] **Replay Scenario Reset**: Stream paused and reset to `Normal Baseline` on Live Monitoring.
- [ ] **Display Resolution**: Browser zoom set to $100\%$ or $90\%$ for optimal 1080p projector clarity.
- [ ] **Zero Console Errors**: Open DevTools console to confirm clean $0$-error execution.
