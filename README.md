# MetroGuard AI

**An Explainable Predictive Maintenance & Prescriptive Decision-Support System for Urban Rail Air Compressor Telemetry**

[![Architecture](https://img.shields.io/badge/Architecture-Dual--Tier%20Hybrid%20AI-blue.svg)](docs/SYSTEM_ARCHITECTURE.md)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%20REST%20(18%20APIs)-emerald.svg)](backend/main.py)
[![React](https://img.shields.io/badge/Frontend-React%2018%20%2B%20Vite%20%2B%20Tailwind-cyan.svg)](frontend/)
[![Dataset](https://img.shields.io/badge/Dataset-MetroPT--3%20(UCI%20%23791)-amber.svg)](https://archive.ics.uci.edu/dataset/791/metropt+3+dataset)
[![ROC-AUC](https://img.shields.io/badge/Final%20Test%20ROC--AUC-0.9797-purple.svg)](docs/FINAL_SCIENTIFIC_AUDIT.md)

---

## 🚆 Overview & Problem Statement

In urban passenger rail transit, the main air compressor (**APU-TR-03**) is the critical heartbeat of the train. It supplies pressurized air to friction brakes, secondary air suspension leveling, and passenger door actuators.

Traditional SCADA systems rely on static low-pressure threshold switches that only trigger alarms **after** reservoir pressure collapses—leaving trains stranded in tunnels and causing cascading depot bottlenecks.

**MetroGuard AI** transforms raw multi-channel machine telemetry into an explainable, early-warning decision support system. It provides maintenance engineers with a **30-minute lead time** and actionable, evidence-based inspection checklists before in-service breakdown occurs.

---

## 🔄 Core Data & Decision Pipeline

```text
15 Raw Telemetry Channels (7 Analogue Sensors + 8 Digital Control States)
        ↓
65 Engineered Time-Series Features (Rolling Means, Stds, Differentials, State Counters)
        ↓
Dual-Tier AI Architecture:
  ├── Tier 1: Supervised XGBoost (Learned pre-failure leak pattern recognition)
  └── Tier 2: Unsupervised Isolation Forest (Out-of-distribution safety net for seasonal drift)
        ↓
Physical Evidence Engine: Statistical Z-Score Deviations (|Z| >= 2.0σ vs Normal Medians)
        ↓
Deterministic Hybrid Decision Engine (NORMAL → MONITOR → WARNING → HIGH RISK)
        ↓
Smart Alert Center (Priority ranking, deduplication, operator acknowledge/resolve workflow)
        ↓
Prescriptive Maintenance Action (Evidence-based 4-point depot inspection checklists)
        ↓
Operator Dashboard (Overview Storytelling & Detailed Command Center)
```

---

## 🔬 Key Technical Distinction: 15 Raw Channels → 65 Features

> **Scientific Clarity**: MetroGuard AI strictly distinguishes between physical hardware telemetry and engineered model inputs:
> - **15 Raw Telemetry Channels**:
>   - **7 Analogue Physical Sensors**: Compressor delivery pressure (`TP2`), Pneumatic panel pressure (`TP3`), Cyclonic separator pressure drop (`H1`), Desiccant drying tower pressure (`DV_pressure`), Main air reservoirs (`Reservoirs`), Compressor oil temperature (`Oil_temperature`), Motor electrical current (`Motor_current`).
>   - **8 Digital Control / Interlock States**: Compressor contactor (`COMP`), Dryer purge valve (`DV_eletric`), Drying tower alternator (`Towers`), Pressure governor (`MPG`), Low pressure switch (`LPS`), Pressure switch state (`Pressure_switch`), Oil level sensor (`Oil_level`), Air flow caudal impulses (`Caudal_impulses`).
> - **65 Engineered Time-Series Features**: Causal rolling means ($1\text{m}, 5\text{m}$), rolling standard deviations ($1\text{m}, 5\text{m}$), 5-minute pressure gradients/differentials, and electrical duty-cycle counters computed over backward-looking windows.

---

## 🎯 Verified Capabilities & Model Benchmarks

| Metric / Evaluation Dimension | Verified Benchmark Value | Operational Context |
| :--- | :---: | :--- |
| **Event #1 Pre-Failure Recall (XGBoost)** | **`98.78%`** | Known Spring Pneumatic Leak ($30\text{m}$ warning horizon) |
| **Event #2 Pre-Failure Recall (XGBoost)** | **`97.57%`** | Known Spring Pneumatic Leak ($30\text{m}$ warning horizon) |
| **Event #4 Anomaly Recall (Isolation Forest)** | **`33.15%`** | Unseen Summer Thermal Outlier Holdout ($0$ training labels required) |
| **Event #4 Supervised Recall (XGBoost)** | **`6.00%`** | Demonstrates supervised blindspot under seasonal distribution shift |
| **Final Test ROC-AUC** | **`0.9797`** | Untouched 62-Day Final Test Partition ($441,980$ chronological rows) |
| **Final Test PR-AUC** | **`0.1607`** | Evaluated under severe $0.041\%$ positive class imbalance |
| **False Positive Rate** | **`2.19%`** | Nominal background operation |
| **Benchmark Dataset Duration** | **151.7 Days** | February 2020 to September 2020 ($1,516,948$ continuous rows) |

---

## ⚠️ Scientific Limitations & Outcome B Protocol

1. **Failure Scarcity & No Continuous Countdown ($N=4$)**:
   - The 7-month MetroPT-3 dataset contains exactly 4 maintenance interventions.
   - Continuous remaining useful life (RUL) regression requires dozens of run-to-failure cycles (e.g. NASA C-MAPSS). Fitting continuous curves on $N=4$ cycles produces statistical overfitting.
   - **MetroGuard's Decision**: MetroGuard honestly provides a validated **30-minute early warning classification** ($\tau = 0.10$) and **$0\text{–}100$ Anomaly Severity Indexing** rather than an unsupported countdown clock.
2. **Decision Support Framing**:
   - MetroGuard AI is designed as a depot decision support system for maintenance dispatchers. It does not autonomously actuate physical train brake lines.

---

## 📁 Repository Structure

```text
MetroGuard-AI/
├── backend/                  # FastAPI REST API & decision services
│   ├── alert_service.py      # Alert lifecycle, deduplication & prescriptive checklists
│   ├── anomaly_explainer.py  # 0-100 severity calibration & Z-score evidence ranker
│   ├── case_study_service.py # Historical incident investigations & impact analysis
│   ├── data_service.py       # Telemetry ingestion, metadata & sensor catalog
│   ├── hybrid_predictor.py   # Dual-tier XGBoost + Isolation Forest synthesis
│   ├── main.py               # 18 REST endpoints & SPA static mount
│   ├── predict.py            # Supervised XGBoost inference engine
│   └── streaming_service.py  # 4-scenario real-time telemetry replay engine
├── frontend/                 # React 18 / Vite / Tailwind CSS Command Center
│   ├── src/pages/            # 6 Dedicated Command Views (Overview, Monitoring, Risk, Sensors, Performance, Case Studies)
│   ├── src/components/       # Replay toolbar, Risk gauges, Waveforms, Status badges
│   └── dist/                 # Pre-compiled production bundle (served by FastAPI)
├── docs/                     # Technical specifications, audits & demo guides
│   ├── SYSTEM_ARCHITECTURE.md# Master technical architecture specification
│   ├── FINAL_SCIENTIFIC_AUDIT.md # Verified technical truth, metrics & threshold audit
│   ├── HACKATHON_DEMO_SCRIPT.md  # 8-10 min presentation script + 3-min lightning pitch
│   ├── HACKATHON_CHEAT_SHEET.md  # 1-page judge reference cheat sheet
│   ├── HACKATHON_JUDGE_QA.md     # 15 deep technical judge questions & answers
│   ├── HACKATHON_FINAL_CHECKLIST.md # Stage-ready demo checklist & recovery protocol
│   └── assets/               # Architecture diagrams (SVG)
├── models/                   # Frozen model artifacts, metadata & evaluation plots
├── data/                     # Data processing scripts & pre-computed scenario caches
└── scripts/                  # Automated verification & regression test suites
```

---

## 🚀 Quickstart & Local Setup

### 1. Prerequisites
- **Python 3.10+** (Tested on Python 3.14)
- **Node.js 18+** (Optional, only needed if rebuilding the frontend bundle)

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Start the MetroGuard Application
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

### 4. (Optional) Rebuild Frontend
The repository includes a pre-compiled `frontend/dist/` bundle. If you modify UI code:
```bash
cd frontend
npm install
npm run build
cd ..
```

---

## 🖥️ Available Application Routes

Once started, open your browser to:

| Route | Page Name | Primary Function |
| :--- | :--- | :--- |
| **`http://127.0.0.1:8000/`** | **Overview Dashboard** | Real-time machine health, Multi-event replay bar, "Why This Alert?" explainability chain, 5-stage timeline, and quick demo launchers. |
| **`http://127.0.0.1:8000/monitoring`** | **Live Monitoring** | Detailed multi-scale rolling waveforms, live 15-channel signals, and interactive 4-point prescriptive checklist. |
| **`http://127.0.0.1:8000/risk`** | **AI Risk Diagnostics** | Dual-tier radar, feature importance Gini gains, and probability distribution curves. |
| **`http://127.0.0.1:8000/sensors`** | **Sensors Suite** | 15 raw telemetry signals catalog and multi-scale moving window charts. |
| **`http://127.0.0.1:8000/performance`** | **Model Performance** | Audited 62-day summer holdout benchmarks, confusion matrices, and PR-AUC curves. |
| **`http://127.0.0.1:8000/case-study`** | **Case Studies** | In-depth 6-stage chronological investigations of Event #1 and Event #4. |

---

## 📚 Master Documentation Index

- 📖 [docs/SYSTEM_ARCHITECTURE.md](docs/SYSTEM_ARCHITECTURE.md) — Master System Architecture & Engineering Flow
- 📊 [docs/FINAL_SCIENTIFIC_AUDIT.md](docs/FINAL_SCIENTIFIC_AUDIT.md) — Verified Metrics, Thresholds & Scientific Consistency
- 🎤 [docs/HACKATHON_DEMO_SCRIPT.md](docs/HACKATHON_DEMO_SCRIPT.md) — 8–10 Minute Master Pitch & Live Demo Walkthrough
- 📝 [docs/HACKATHON_CHEAT_SHEET.md](docs/HACKATHON_CHEAT_SHEET.md) — 1-Page Quick Presenter Reference Card
- 💡 [docs/HACKATHON_JUDGE_QA.md](docs/HACKATHON_JUDGE_QA.md) — 15 Deep Technical Judge Questions & Answers
- ✅ [docs/HACKATHON_FINAL_CHECKLIST.md](docs/HACKATHON_FINAL_CHECKLIST.md) — Presentation Day Checklist & Emergency Recovery

---

## ⚖️ License & Acknowledgments

- **Dataset**: MetroPT-3 Benchmark provided by UCI Machine Learning Repository (Dataset #791) / FEUP.
- **License**: MIT License.
