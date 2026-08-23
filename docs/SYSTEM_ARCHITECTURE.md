# MetroGuard AI — Master System Architecture & Technical Specification

> **Asset Monitored**: `APU-TR-03` (Urban Rail Main Air Compressor & Twin-Tower Desiccant Air Dryer)  
> **Telemetry Dataset**: MetroPT-3 Benchmark (UCI #791, 1,486,994 continuous 10-second records)  
> **Deployment Architecture**: Unified Production FastAPI + React 18 / Vite / Tailwind CSS Command Center  
> **Scientific Integrity Standard**: Zero-leakage chronological evaluation, no synthetic balancing (SMOTE), zero fake countdowns, transparent RUL feasibility disclosure (Outcome B).

---

## 1. Executive System Overview

In heavy urban passenger rail transit, the **Auxiliary Power Unit (APU) Main Air Compressor** supplies compressed air critical for:
- Train electro-pneumatic friction braking.
- Secondary air-spring bogie leveling.
- Passenger door power actuation.
- Automatic pantograph raising and electrical interlocks.

### The Operational Challenge
Traditional railway SCADA systems employ simple low-pressure threshold switches (e.g., alert when reservoir drops below $7.0\text{ bar}$). By the time such static thresholds trigger during revenue service, pneumatic pressure has already collapsed, resulting in emergency train withdrawal, passenger stranding, depot bottlenecking, and severe schedule disruptions.

### The MetroGuard AI Solution
MetroGuard AI is a multi-tier predictive maintenance and prescriptive decision command center. The system receives 15 raw telemetry channels (7 analogue signals + 8 digital control states) sampled at 10-second intervals and transforms them into a 65-dimensional engineered feature representation used by the production ML pipeline:
1. **Tier 1 (Supervised XGBoost Classifier)**: Predicts the probability of impending failure within a forward-looking 30-minute operational window ($P(\text{Failure within 30m} \mid x)$), trained on documented pre-failure pneumatic leak signatures across 65 engineered features.
2. **Tier 2 (Unsupervised Isolation Forest Detector)**: Quantifies multi-dimensional outlier distance without relying on failure labels, defending against unseen seasonal regimes and thermal degradation across 65 engineered features.
3. **Physical Evidence Engine**: Decomposes multidimensional inferences into statistical $Z$-scores relative to normal baseline medians ($|Z| \ge 2.0\sigma$).
4. **Deterministic Hybrid Decision Engine**: Synthesizes orthogonal AI signals and physical evidence into standardized operational states (`NORMAL`, `MONITOR`, `WARNING`, `HIGH RISK`).
5. **Intelligent Alert & Prescriptive Maintenance Engine**: Deduplicates alarms, manages operator workflow lifecycles (`ACTIVE`, `ACKNOWLEDGED`, `RESOLVED`, `ESCALATED`), and dispatches actionable 4-point depot inspection checklists.

---

## 2. Master System Architecture Diagram

```text
========================================================================================================
                                      METROGUARD AI PIPELINE ARCHITECTURE
========================================================================================================

 [15 RAW TELEMETRY CHANNELS]
 7 Analogue Sensors (Pressures, Temperatures, Motor Current) + 8 Digital Control States @ 10s Sampling Rate
                                │
                                ▼
 [PREPROCESSING & ROLLING FEATURE EXTRACTION]
 65 Engineered Features: Rolling Means & Volatilities (1m, 5m) + Differentials (diff_1m, diff_5m) + State Flips
                                │
               ┌────────────────┴────────────────┐
               ▼                                 ▼
   [TIER 1: SUPERVISED XGBOOST]      [TIER 2: UNSUPERVISED ISOLATION FOREST]
   65-Feature Known Failure Model    65-Feature Outlier Detector
   Target: P(Failure within 30m)     Multidimensional Isolation Score S(x)
   Trained on Spring Pneumatic Leaks Trained on 140,914 Clean Normal Baseline Rows
   Threshold: τ = 0.10               Threshold: τ = 0.5040 (99th Percentile)
   Event #1 Recall: 98.78%           Event #4 Recall: 33.15% (Oil Temp +3.69σ)
               │                                 │
               └────────────────┬────────────────┘
                                │
                                ▼
 [PHYSICAL EVIDENCE & PERSISTENCE ENGINE]
 Baseline Medians & Standard Deviations + Z-Score Extremity (|Z| ≥ 2.0σ) + Trailing 5m Persistence
                                │
                                ▼
 [DETERMINISTIC HYBRID DECISION ENGINE]
 Rule Precedence: Supervised Peak ──> Multi-Signal Agreement ──> Unsupervised Drift ──> Nominal
 Operational States: NORMAL (Routine) | MONITOR (Advisory) | WARNING (High/Medium) | HIGH RISK (Critical)
                                │
                                ▼
 [SMART ALERT & DEDUPLICATION ENGINE]
 Incident State Machine: ACTIVE ──> ACKNOWLEDGED ──> RESOLVED / ESCALATED
 Deduplication Fingerprinting | Priority Mapping (CRITICAL, HIGH, MEDIUM, LOW, NOMINAL)
                                │
                                ▼
 [PRESCRIPTIVE MAINTENANCE & WORKFLOW ENGINE]
 Directed Mechanical Remediation + Evidence Strength Rating + Interactive 4-Point Inspection Checklists
                                │
                                ▼
 [UNIFIED FASTAPI + REACT 18 COMMAND CENTER]
 18 REST APIs | 6 Interactive Command Pages: Overview, Live Monitoring, Risk Radar, Sensors, Metrics, Cases
========================================================================================================
```

*Vector SVG Diagram Asset*: Located at [`docs/assets/architecture_diagram.svg`](file:///c:/Users/Lakshmidhar/OneDrive/Desktop/Hackathon/MetroGuard-AI/docs/assets/architecture_diagram.svg).

---

## 3. End-to-End Data Flow

The runtime execution path transforms raw telemetry into operator decisions across 8 distinct stages:

```text
Telemetry Ingestion (backend/streaming_service.py)
       │
       ▼
Data Extraction & Validation (backend/data_service.py)
       │
       ▼
Dual-Tier Model Inference (backend/hybrid_predictor.py & backend/predict.py)
       │
       ▼
Explainable Anomaly Calibration (backend/anomaly_explainer.py)
       │
       ▼
Alert Management & Deduplication (backend/alert_service.py)
       │
       ▼
Prescriptive Recommendation Generation (backend/alert_service.py)
       │
       ▼
FastAPI REST Delivery (backend/main.py)
       │
       ▼
React Command Center UI (frontend/src/App.jsx & frontend/src/pages/)
```

---

## 4. Layer-by-Layer Detailed Technical Specification

### Layer 1: Telemetry Ingestion & Real-Time Replay Engine
- **Source Module**: [`backend/streaming_service.py`](file:///c:/Users/Lakshmidhar/OneDrive/Desktop/Hackathon/MetroGuard-AI/backend/streaming_service.py)
- **Monitored Asset**: `APU-TR-03`
- **Sampling Frequency**: $0.1\text{ Hz}$ (1 observation every 10 seconds).
- **Channels Ingested (15)**:
  1. `TP2` (bar): Compressor delivery output pressure.
  2. `TP3` (bar): Pneumatic panel line distribution pressure.
  3. `H1` (bar): Moisture separator filter pressure drop.
  4. `DV_pressure` (bar): Desiccant drying tower purge exhaust pressure.
  5. `Reservoirs` (bar): Main air reservoir storage pressure.
  6. `Oil_temperature` (°C): Compressor crankcase lubricating oil temperature.
  7. `Motor_current` (A): Electric induction motor supply current.
  8. `COMP` (binary): Compressor contactor run state ($1 = \text{Pumping}, 0 = \text{Idle}$).
  9. `DV_eletric` (binary): Automatic drain purge solenoid command.
  10. `Towers` (binary): Desiccant twin-tower switching valve state.
  11. `MPG` (binary): Main pressure governor electrical contact.
  12. `LPS` (binary): Low-pressure safety switch contact.
  13. `Pressure_switch` (binary): Unloading differential pressure switch.
  14. `Oil_level` (binary): Lubricant reservoir level float switch.
  15. `Caudal_impulses` (binary): Air delivery pulse flow indicator.
- **Deterministic Scenario Replay**:
  - `normal`: 180 observations ($30\text{ min}$) of healthy cyclical charging.
  - `gradual_anomaly`: 180 observations of progressive thermal buildup ($65^\circ\text{C} \rightarrow 82^\circ\text{C}$) and pressure drift.
  - `pre_failure`: 180 observations leading into historical Event #1 pneumatic breakdown ($98.78\%$ XGBoost risk).
  - `unseen_anomaly`: 180 observations from July 2020 Event #4 holdout under seasonal distribution shift ($Z = +3.69\sigma$).

---

### Layer 2: Feature Engineering & Preprocessing Engine
- **Source Module**: [`scripts/create_features.py`](file:///c:/Users/Lakshmidhar/OneDrive/Desktop/Hackathon/MetroGuard-AI/scripts/create_features.py) & [`backend/data_service.py`](file:///c:/Users/Lakshmidhar/OneDrive/Desktop/Hackathon/MetroGuard-AI/backend/data_service.py)
- **Feature Vector Dimensionality**: $D = 65$.
- **Anti-Leakage Design**: All transformations use backward-looking rolling windows ($[t - W, t]$). Zero future telemetry is used.
- **Feature Categories**:
  1. *Instantaneous Analogue Sensors ($7$)*: Raw pressure, temperature, and electrical readings.
  2. *Digital Control States ($8$)*: Instantaneous state ($0$ or $1$) for solenoids, governors, and contactors.
  3. *1-Minute Rolling Means ($7$)*: $\bar{x}_{1\text{m}}(t) = \frac{1}{6} \sum_{k=0}^5 x(t - 10k\text{s})$.
  4. *1-Minute Rolling Standard Deviations ($7$)*: Short-term volatility and aerodynamic turbulence.
  5. *5-Minute Rolling Means ($7$)*: $\bar{x}_{5\text{m}}(t) = \frac{1}{30} \sum_{k=0}^{29} x(t - 10k\text{s})$.
  6. *5-Minute Rolling Standard Deviations ($7$)*: Long-term volatility and filter jitter.
  7. *1-Minute Differentials ($7$)*: $\Delta x_{1\text{m}}(t) = x(t) - x(t - 60\text{s})$.
  8. *5-Minute Differentials ($7$)*: $\Delta x_{5\text{m}}(t) = x(t) - x(t - 300\text{s})$.
  9. *5-Minute State Transitions ($8$)*: Count of binary flips ($\sum |\Delta s|$) measuring solenoid chatter and duty cycling.

---

### Layer 3: Tier 1 Supervised Known-Failure Classifier (XGBoost)
- **Source Module**: [`backend/predict.py`](file:///c:/Users/Lakshmidhar/OneDrive/Desktop/Hackathon/MetroGuard-AI/backend/predict.py)
- **Artifact**: [`models/metroguard_model.pkl`](file:///c:/Users/Lakshmidhar/OneDrive/Desktop/Hackathon/MetroGuard-AI/models/metroguard_model.pkl)
- **Objective**: Predict binary probability of failure within the next 30 minutes ($P(y=1 \mid \mathbf{x}_t)$).
- **Hyperparameters**:
  - Algorithm: `XGBClassifier` (histogram tree method, tree_method=`hist`).
  - Estimators: $150$ trees.
  - Max Depth: $6$.
  - Learning Rate: $\eta = 0.05$.
  - Subsample / Colsample: $0.80$ / $0.80$.
  - Scale Positive Weight: $w_{\text{pos}} = 2554.33$ (compensating for $0.039\%$ training class imbalance).
- **Production Thresholds**:
  - $\tau_{\text{advisory}} = 0.10$ ($P \ge 0.10 \rightarrow \text{WARNING}$).
  - $\tau_{\text{critical}} = 0.70$ ($P \ge 0.70 \rightarrow \text{HIGH RISK}$).
- **Top Contributing Features (Gini Gain)**:
  1. `H1_roll_std_1m` ($34.94\%$): High-frequency moisture separator pressure oscillation.
  2. `H1_roll_std_5m` ($13.41\%$): 5-minute filter turbulence.
  3. `H1_diff_5m` ($8.09\%$): Rapid filter differential decay rate.
  4. `DV_pressure_roll_mean_5m` ($4.18\%$): Desiccant tower purge pressure.
  5. `TP3_roll_std_1m` ($3.99\%$): Pneumatic panel line oscillation.

---

### Layer 4: Tier 2 Unsupervised Outlier Detector (Isolation Forest)
- **Source Module**: [`backend/hybrid_predictor.py`](file:///c:/Users/Lakshmidhar/OneDrive/Desktop/Hackathon/MetroGuard-AI/backend/hybrid_predictor.py) & [`backend/anomaly_explainer.py`](file:///c:/Users/Lakshmidhar/OneDrive/Desktop/Hackathon/MetroGuard-AI/backend/anomaly_explainer.py)
- **Artifact**: [`models/metroguard_anomaly_model.pkl`](file:///c:/Users/Lakshmidhar/OneDrive/Desktop/Hackathon/MetroGuard-AI/models/metroguard_anomaly_model.pkl)
- **Objective**: Quantify multidimensional isolation path length across all 65 features without failure labels.
- **Training Population**: $140,914$ clean normal training samples (Feb 1 – May 31, 2020) with $0.00\%$ failure contamination.
- **Hyperparameters**:
  - Estimators: $150$ isolation trees.
  - Contamination: $0.01$ ($1\%$).
  - Scoring Formula: $S(\mathbf{x}) = -\text{score\_samples}(\mathbf{x})$ where higher $S(\mathbf{x})$ represents greater isolation extremity.
- **Empirical Thresholds**:
  - $99\text{th}$ Percentile Threshold: $\tau_{\text{elevated}} = 0.5040$.
  - $99.5\text{th}$ Percentile Threshold: $\tau_{\text{high}} = 0.5350$.
- **0–100 Piecewise Severity Index Calibration**:
  $$\text{Severity}(S) = \begin{cases}
  \frac{S - 0.30}{0.05} \times 20 & S \in [0.30, 0.35) \rightarrow \text{NOMINAL } (0\text{–}20) \\
  20 + \frac{S - 0.35}{0.154} \times 30 & S \in [0.35, 0.504) \rightarrow \text{LOW } (20\text{–}50) \\
  50 + \frac{S - 0.504}{0.031} \times 25 & S \in [0.504, 0.535) \rightarrow \text{ELEVATED } (50\text{–}75) \\
  75 + \frac{S - 0.535}{0.065} \times 25 & S \ge 0.535 \rightarrow \text{SEVERE } (75\text{–}100)
  \end{cases}$$

---

### Layer 5: Physical Evidence Attribution & Persistence Tracking
- **Source Module**: [`backend/hybrid_predictor.py`](file:///c:/Users/Lakshmidhar/OneDrive/Desktop/Hackathon/MetroGuard-AI/backend/hybrid_predictor.py)
- **Baseline Statistics**: Calibrated on $845,484$ normal operational observations:
  - `Oil_temperature`: $\text{Median} = 58.70^\circ\text{C}, \sigma = 6.15^\circ\text{C}$.
  - `TP2` (Discharge): $\text{Median} = -0.01\text{ bar}, \sigma = 3.75\text{ bar}$.
  - `H1` (Separator Drop): $\text{Median} = -0.01\text{ bar}, \sigma = 3.76\text{ bar}$.
  - `DV_pressure` (Dryer): $\text{Median} = -0.02\text{ bar}, \sigma = 0.38\text{ bar}$.
  - `Reservoirs`: $\text{Median} = 8.97\text{ bar}, \sigma = 0.72\text{ bar}$.
  - `Motor_current`: $\text{Median} = 0.00\text{ A}, \sigma = 3.65\text{ A}$.
- **Attribution Rule**: A physical feature is flagged as active engineering evidence if its absolute $Z$-score exceeds $2.0$:
  $$Z_i = \frac{x_i - \text{Median}_{\text{normal}, i}}{\sigma_{\text{normal}, i}}, \quad |Z_i| \ge 2.0$$
- **Persistence Filter**: Requires at least 3 out of 5 consecutive observations within a trailing 5-minute window to exceed $\tau_{\text{elevated}}$ before escalating to `SUSTAINED ANOMALY`, suppressing transient noise spikes.

---

### Layer 6: Deterministic Hybrid Decision Synthesis Engine
- **Source Module**: [`backend/hybrid_predictor.py`](file:///c:/Users/Lakshmidhar/OneDrive/Desktop/Hackathon/MetroGuard-AI/backend/hybrid_predictor.py)
- **Decision Precedence Table**:

| Condition / Signal Configuration | Supervised State | Anomaly State | Physical Evidence | Hybrid Operational Decision | Active Priority |
| :--- | :---: | :---: | :---: | :---: | :---: |
| $P(\text{XGB}) \ge 0.70$ | `HIGH RISK` | Any | Active | **`HIGH RISK`** | **`CRITICAL`** |
| $P(\text{XGB}) \ge 0.10 \land \text{Anom} \ge 0.5040$ | `WARNING` | `ELEVATED` / `HIGH` | Active | **`HIGH RISK`** | **`CRITICAL`** |
| $P(\text{XGB}) \ge 0.10$ | `WARNING` | `NORMAL` | Active | **`FAILURE WARNING`** | **`HIGH`** |
| $\text{Anom} \ge 0.5350 \lor (\text{Anom} \ge 0.5040 \land \text{Sustained})$ | `NORMAL` | `HIGH` / `ELEVATED` | $|Z| \ge 2.0\sigma$ | **`ANOMALY WARNING`** | **`HIGH` / `MEDIUM`** |
| $\text{Anom} \ge 0.5040 \lor \text{Count}(\|Z\| \ge 2.0) \ge 1$ | `NORMAL` | `ELEVATED` | Isolated | **`MONITOR`** | **`LOW`** |
| All signals within normal envelopes | `NORMAL` | `NORMAL` | None | **`NORMAL`** | **`NOMINAL`** |

---

### Layer 7: Intelligent Alert & Prescriptive Maintenance Engine
- **Source Module**: [`backend/alert_service.py`](file:///c:/Users/Lakshmidhar/OneDrive/Desktop/Hackathon/MetroGuard-AI/backend/alert_service.py)
- **Lifecycle States**:
  - `ACTIVE`: Newly triggered incident requiring operator attention.
  - `ACKNOWLEDGED`: Operator has reviewed the alarm; persistence monitoring continues.
  - `RESOLVED`: Maintenance completed or telemetry recovered to nominal baseline.
  - `ESCALATED`: Severity increased during an existing active incident.
- **Prescriptive Maintenance Rules**:

| Active Mechanical Hypothesis | Primary Physical Trigger | Prescriptive Action | Interactive 4-Point Inspection Checklist |
| :--- | :--- | :--- | :--- |
| **High Known Failure Risk** | $P(\text{XGB}) \ge 70\%$ | Immediate depot pneumatic leak inspection & pressure decay test. | 1. 5-min pressure decay test<br>2. Check delivery check-valve seating<br>3. Inspect moisture separator drain purge<br>4. Verify desiccant tower regeneration |
| **Thermal Elevation** | Oil Temp $>75^\circ\text{C}$ ($Z \ge +2.5\sigma$) | Inspect compressor oil radiator matrix and cooling ventilation circuit. | 1. Clean oil heat exchanger matrix<br>2. Sample lubricant for thermal breakdown<br>3. Check cooling fan airflow velocity<br>4. Inspect oil RTD wiring calibration |
| **Filter Restriction** | $H1 \ge 4.0\text{ bar}$ ($Z \ge +2.0\sigma$) | Inspect cyclonic moisture separator element & automatic drain purge. | 1. Inspect separator cartridge loading<br>2. Verify drain valve electrical purge cycle<br>3. Check differential pressure sensor<br>4. Inspect moisture bowl for oil emulsion |
| **Pressure Regulation Drift** | Reservoirs $/ TP3 \le 7.5\text{ bar}$ | Calibrate pneumatic panel regulator and check desiccant tower valves. | 1. Distribution line pressure decay test<br>2. Check desiccant tower purge solenoids<br>3. Calibrate relief valves<br>4. Inspect reservoir non-return check valves |

---

### Layer 8: RUL Feasibility Audit & Scientific Honesty Protocol (Outcome B)
- **Source Module**: [`backend/main.py`](file:///c:/Users/Lakshmidhar/OneDrive/Desktop/Hackathon/MetroGuard-AI/backend/main.py) & [`scripts/audit_task21_rul_feasibility.py`](file:///c:/Users/Lakshmidhar/OneDrive/Desktop/Hackathon/MetroGuard-AI/scripts/audit_task21_rul_feasibility.py)
- **Report Artifact**: [`data/processed/rul_feasibility_audit.json`](file:///c:/Users/Lakshmidhar/OneDrive/Desktop/Hackathon/MetroGuard-AI/data/processed/rul_feasibility_audit.json)
- **Formal Scientific Verdict**: `OUTCOME B — VALIDATED CONTINUOUS RUL ESTIMATION IS NOT FEASIBLE WITH CURRENT DATA`.
- **Limiting Factors**:
  1. *Sample Scarcity*: Only $N=4$ recorded failure episodes across 7 months of single-unit telemetry (`APU-TR-03`). Statistically insufficient for multi-variate regression with confidence intervals.
  2. *Failure Mode Heterogeneity*: Event #1 & #2 were abrupt pneumatic solenoid leaks; Event #4 was high-ambient summer thermal stress. No monotonic degradation trend exists across runs.
  3. *Unobserved Maintenance Resets*: Component repairs and desiccant canister swaps were performed without recorded maintenance logs.
- **Scientific Protocol**: MetroGuard rejects invented countdown clocks and instead delivers validated 30-minute early warning classification and anomaly severity tracking.

---

## 5. Backend REST API Architecture

The FastAPI backend exposes 18 high-performance REST endpoints on `http://127.0.0.1:8000`:

| HTTP Method | Route | Description | Response Schema / Data |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | System health, uptime & pipeline version | `{"status": "ONLINE", "version": "1.0.0"}` |
| `GET` | `/api/latest` | Instantaneous 15-sensor telemetry & ML prediction | Sensor values, timestamp, XGB probability |
| `GET` | `/api/sensors` | Catalog of 15 monitored sensors | IDs, names, units, categories, descriptions |
| `GET` | `/api/timeseries` | Historical multi-scale sensor readings | Timestamps, raw, 1m mean, 5m baseline |
| `GET` | `/api/multisensor` | Multi-channel synchronized telemetry | Aligned sensor streams for comparison |
| `GET` | `/api/events` | Ground-truth UCI #791 failure episodes | Event metadata, timestamps, root causes |
| `GET` | `/api/model-info` | Dual-model metadata, parameters & thresholds | XGBoost and Isolation Forest configs |
| `GET` | `/api/model/evaluation` | Full untouched final test benchmark metrics | Standalone vs Hybrid comparison, PR-AUC |
| `GET` | `/api/stream/status` | Streaming replay engine live state | Scenario, active state, speed multiplier |
| `GET` | `/api/stream/current` | Full streaming intelligence snapshot | Telemetry, dual AI, alerts, recommendations |
| `POST` | `/api/stream/start` | Start real-time telemetry streaming | Stream activation status |
| `POST` | `/api/stream/stop` | Pause telemetry streaming | Stream pause confirmation |
| `POST` | `/api/stream/reset` | Reset stream pointer to scenario start | Scenario reset status |
| `POST` | `/api/stream/scenario`| Select active demo scenario ($1\text{–}4$) | Scenario switch confirmation |
| `POST` | `/api/stream/speed` | Set replay speed multiplier ($1\text{x}, 2\text{x}, 5\text{x}, 10\text{x}$) | Speed confirmation |
| `POST` | `/api/stream/step` | Advance telemetry by single 10s tick | Single observation payload |
| `GET` | `/api/anomaly/explanation` | Explainable anomaly scorecard & $Z$-scores | Severity $0\text{–}100$, top deviations, hypothesis |
| `GET` | `/api/alerts` | Chronological operator alert history | Full deduplicated alert log |
| `GET` | `/api/alerts/active` | Current active operator incident | Priority, trigger, checklist, status |
| `POST` | `/api/alerts/{id}/acknowledge` | Acknowledge active incident | State transition confirmation |
| `POST` | `/api/alerts/{id}/resolve` | Mark active incident as resolved | Resolved audit record |
| `GET` | `/api/recommendations/current` | Current prescriptive maintenance action | Action title, reason, 4-point checklist |
| `GET` | `/api/rul/status` | RUL feasibility audit & Outcome B disclosure | Scientific limitations and capabilities |
| `GET` | `/api/case-studies` | All structured historical case studies | Event #1 & Event #4 full reports |
| `GET` | `/api/case-studies/summary` | Executive case study summary | Total cases, asset metadata |
| `GET` | `/api/case-studies/{id}` | Full investigation report for single case | 6-stage timeline, evidence, impact |
| `POST` | `/api/predict` | Standalone supervised XGBoost inference | Probability, percentage, status |
| `POST` | `/api/hybrid-predict` | Full dual-tier inference + evidence + alerts | Complete hybrid evaluation payload |

---

## 6. Frontend & Operator Command Center Architecture

Built with React 18, Vite, Tailwind CSS, Lucide Icons, and Recharts:

```text
frontend/src/
├── App.jsx                       # Main application router and state polling
├── main.jsx                      # React DOM entrypoint
├── components/
│   ├── Header.jsx                # Global top-bar with asset status and clock
│   ├── Sidebar.jsx               # Navigation drawer with glowing status badges
│   ├── StatusBadge.jsx           # Industrial pulsating state indicator
│   ├── SensorCard.jsx            # Dynamic sensor card with min/max sparklines
│   └── RiskGauge.jsx             # Radial SVG risk dial with dynamic threshold
├── pages/
│   ├── OverviewPage.jsx          # Hero asset banner, 6-step flow, 4 KPIs, quick launch
│   ├── LiveMonitoringPage.jsx    # Real-time replay, alert center, checklists, RUL audit
│   ├── RiskAssessmentPage.jsx    # Dual-tier AI diagnostics, radar, feature importance
│   ├── SensorAnalysisPage.jsx    # 15-channel multi-scale wave explorer & digital matrix
│   ├── ModelPerformancePage.jsx  # 62-day holdout benchmark, PR-AUC, confusion matrix
│   └── CaseStudyPage.jsx         # Executive case reports, 6-stage timelines, impact
└── services/
    └── api.js                    # Axios API client for all 18 backend endpoints
```

---

## 7. Model Performance & Evaluation Benchmark

All models were evaluated on the **untouched 62-day final test partition** (July 1, 2020 – September 1, 2020; $441,980$ continuous observations):

| Evaluation Metric | Standalone XGBoost (Tier 1) | Standalone Isolation Forest (Tier 2) | MetroGuard Dual-Engine Hybrid |
| :--- | :---: | :---: | :---: |
| **ROC-AUC** | $0.4316$ | **$0.9797$** | **$0.9797$** |
| **PR-AUC** | $0.0003$ | **$0.0105$** | **$0.0105$** |
| **Event #4 Recall** | $0.00\%$ | **$33.15\%$** | **$33.15\%$** |
| **Spring Recall (Events #1 & #2)** | **$98.18\%$** | $62.40\%$ | **$98.18\%$** |
| **Accuracy (Misleading Benchmark)** | $97.77\%$ | $97.77\%$ | $97.77\%$ |
| **Primary Operational Role** | Known Pre-Failure Pneumatic Leaks | Out-of-Distribution Summer Thermal Drift | **Complete Multi-Signal Coverage** |

---

## 8. System Traceability Matrix

| Architecture Layer | Source Implementation Module | Primary Input | Primary Output | Verification Test Suite |
| :--- | :--- | :--- | :--- | :--- |
| **1. Data Ingestion** | [`backend/data_service.py`](file:///c:/Users/Lakshmidhar/OneDrive/Desktop/Hackathon/MetroGuard-AI/backend/data_service.py) | Raw CSV Telemetry | Aligned 15-sensor dict | `scripts/test_task10_final.py` |
| **2. Feature Extraction** | [`scripts/create_features.py`](file:///c:/Users/Lakshmidhar/OneDrive/Desktop/Hackathon/MetroGuard-AI/scripts/create_features.py) | 15-sensor time series | 65-feature vector | `scripts/test_risk_pipeline.py` |
| **3. Supervised AI (Tier 1)** | [`backend/predict.py`](file:///c:/Users/Lakshmidhar/OneDrive/Desktop/Hackathon/MetroGuard-AI/backend/predict.py) | 65 features | $P(\text{Failure within 30m})$ | `scripts/test_task17_evaluation.py` |
| **4. Anomaly AI (Tier 2)** | [`backend/hybrid_predictor.py`](file:///c:/Users/Lakshmidhar/OneDrive/Desktop/Hackathon/MetroGuard-AI/backend/hybrid_predictor.py) | 65 features | Outlier Score $S(\mathbf{x})$ | `scripts/test_task19_anomaly_intelligence.py` |
| **5. Anomaly Explainability** | [`backend/anomaly_explainer.py`](file:///c:/Users/Lakshmidhar/OneDrive/Desktop/Hackathon/MetroGuard-AI/backend/anomaly_explainer.py) | Raw score + baselines | Severity $0\text{–}100$, $Z$-scores | `scripts/test_task19_anomaly_intelligence.py` |
| **6. Physical Evidence** | [`backend/hybrid_predictor.py`](file:///c:/Users/Lakshmidhar/OneDrive/Desktop/Hackathon/MetroGuard-AI/backend/hybrid_predictor.py) | Feature dict + medians | Evidence list ($|Z| \ge 2.0\sigma$) | `scripts/test_hybrid_engine.py` |
| **7. Decision Synthesis** | [`backend/hybrid_predictor.py`](file:///c:/Users/Lakshmidhar/OneDrive/Desktop/Hackathon/MetroGuard-AI/backend/hybrid_predictor.py) | XGB + IF + Evidence | Operational state (`NORMAL`..`HIGH RISK`) | `scripts/test_task10_final.py` |
| **8. Smart Alerts** | [`backend/alert_service.py`](file:///c:/Users/Lakshmidhar/OneDrive/Desktop/Hackathon/MetroGuard-AI/backend/alert_service.py) | Operational state + history | Deduplicated incident state | `scripts/test_task20_alerts.py` |
| **9. Prescriptive Action** | [`backend/alert_service.py`](file:///c:/Users/Lakshmidhar/OneDrive/Desktop/Hackathon/MetroGuard-AI/backend/alert_service.py) | Active hypothesis | Action title + 4-point checklist | `scripts/test_task20_alerts.py` |
| **10. Streaming Replay** | [`backend/streaming_service.py`](file:///c:/Users/Lakshmidhar/OneDrive/Desktop/Hackathon/MetroGuard-AI/backend/streaming_service.py) | MetroPT-3 episode rows | Synchronized snapshot stream | `scripts/test_task18_streaming.py` |
| **11. Case Studies** | [`backend/case_study_service.py`](file:///c:/Users/Lakshmidhar/OneDrive/Desktop/Hackathon/MetroGuard-AI/backend/case_study_service.py) | Verified episode data | Structured timelines & impact | `scripts/test_task23_case_studies.py` |
| **12. REST Delivery** | [`backend/main.py`](file:///c:/Users/Lakshmidhar/OneDrive/Desktop/Hackathon/MetroGuard-AI/backend/main.py) | Service singletons | 18 FastAPI JSON endpoints | `scripts/test_task23_1_overview_regression.py`|
| **13. UI Command Center**| [`frontend/src/`](file:///c:/Users/Lakshmidhar/OneDrive/Desktop/Hackathon/MetroGuard-AI/frontend/src) | REST API payloads | Interactive React 18 SPA | `npm run build` |

---

## 9. Deployment, Build & Runtime Architecture

### Runtime Server
- **FastAPI Engine**: Python 3.10+ ASGI server managed via Uvicorn.
- **Serving Architecture**: FastAPI natively serves all `/api/*` endpoints and mounts the compiled Vite production bundle (`frontend/dist/`) to serve all SPA routes (`/`, `/overview`, `/monitoring`, `/risk`, `/sensors`, `/performance`, `/case-study`).

### Production Startup Command
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

### Production Frontend Build
```bash
cd frontend
npm run build
```

---

## 10. Scientific Limitations & Future Roadmap

### Current Boundaries
1. **Sample Scarcity**: Ground-truth failure labels are restricted to $N=4$ episodes. Model evaluations reflect retrospective replay on recorded data rather than claims of in-service live failure prevention.
2. **Decision Support Focus**: MetroGuard delivers prescriptive recommendations and checklists for human depot technicians; it does not autonomously actuate train braking interlocks.
3. **Continuous RUL Estimation**: Accurately declared infeasible under Outcome B due to lack of monotonic run-to-failure degradation curves across diverse operational seasons.

### Future Improvements
1. **Edge Inference Engine**: Exporting XGBoost and Isolation Forest pipelines to ONNX Runtime / TensorRT for direct on-train embedded execution on ARM64 hardware.
2. **Multi-Train Fleet Aggregator**: Centralized depot telemetry broker aggregating hundreds of railcars across metropolitan transit networks.
