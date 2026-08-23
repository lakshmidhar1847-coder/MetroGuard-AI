# MetroGuard AI — Final System Architecture & Technical Specification

## 1. Problem Statement
In urban rail transit networks (e.g., MetroPT-3 train fleet), the primary Auxiliary Power Unit (APU) air compressor supplies critical pressurized air for train braking, suspension leveling, and door actuation. Undetected pneumatic line air leaks and component failures lead to catastrophic in-service service withdrawals, schedule disruptions, and safety risks. Traditional threshold-based SCADA alarms only sound after pressure collapses, giving operators insufficient lead time to take preventive action.

## 2. Machine Selected
- **Equipment**: Main Train Air Compressor Unit (APU-TR-03).
- **Physical Subsystems**:
  - Electric induction motor & contactors.
  - Reciprocating compressor cylinder & crankcase.
  - Cyclonic moisture separator & filter assembly ($H_1$).
  - Twin-tower desiccant air drying system ($DV\_pressure$).
  - Main air storage reservoirs & train line distribution ($Reservoirs$, $TP3$).

## 3. Data Source
- **Dataset**: MetroPT-3 Benchmark (UCI Dataset #791).
- **Volume**: $1,516,948$ continuous 10-second telemetry observations spanning 7 months (Feb 1, 2020 – Sep 1, 2020).
- **Raw Channels (15)**: `TP2`, `TP3`, `H1`, `DV_pressure`, `Reservoirs`, `Motor_current`, `Oil_temperature`, `COMP`, `DV_eletric`, `TOWERS`, `MPG`, `LPS`, `Pressure_switch`, `Oil_level`, `Caudal_impulses`.
- **Target Definition**: Binary classification of impending failure within a forward-looking 30-minute operational window ($180$ seconds / $18$ rows pre-failure). Total pre-failure positives: $694$ rows ($0.0457\%$ extreme class imbalance).

## 4. Feature Engineering
65 engineered time-series features constructed strictly without future leakage:
1. **Raw Analog Telemetry (7)**: Instantaneous pressures, temperatures, and currents.
2. **Digital Control States (8)**: Compressor on/off, drain valves, dryer tower solenoids, pressure switches.
3. **Rolling Averages (14)**: 1-minute, 5-minute, and 15-minute moving baselines capturing gradual pressure/thermal drift.
4. **Rolling Standard Deviations (14)**: 1-minute, 5-minute, and 15-minute volatilities capturing aerodynamic turbulence and filter jitter.
5. **Moving Differences / Rates-of-Change (14)**: 1-minute and 5-minute gradient features measuring rapid pressure decay.
6. **Cross-Sensor Pressure Drops (4)**: $\Delta P_{\text{dryer}} = TP2 - TP3$, $\Delta P_{\text{filter}} = TP2 - H1$, $\Delta P_{\text{storage}} = TP3 - Reservoirs$.
7. **Pneumatic Instability Indexes (4)**: Combined thermal-pressure volatility ratios.

## 5. Supervised XGBoost (Tier 1: Known Failure Classification)
- **Role**: Detects known pre-failure signatures modeled on historical ground-truth events (Events #1 & #2).
- **Model**: `XGBClassifier` with scale positive weights ($\approx 2,185$), max depth 4, learning rate 0.05, 100 estimators.
- **Performance**:
  - Event #1 Recall: **`98.78%`** ($p = 0.9878$, High Risk).
  - Event #2 Recall: **`97.57%`** ($p = 0.9757$, High Risk).
  - Threshold: $\tau = 0.10$ ($p \ge 0.10 \rightarrow \text{Warning}$, $p \ge 0.70 \rightarrow \text{High Risk}$).

## 6. Unsupervised Isolation Forest (Tier 2: General Anomaly Detection)
- **Role**: Detects out-of-distribution operating regimes and unforeseen physical stresses (e.g., severe summer thermal load, discharge swings) without requiring failure labels.
- **Training**: Fitted exclusively on $140,914$ clean normal training samples (Feb 1 – May 31, 2020) with $0.00\%$ failure contamination.
- **Hyperparameters**: $N_{\text{trees}} = 150$, contamination = $0.01$, max samples = $1,024$.
- **Scoring**: Negative path length $S(x) = -\text{score\_samples}(x)$.
- **Thresholds**: $\tau_{\text{anom}} = 0.5040$ (99th percentile), $\tau_{\text{high}} = 0.5350$ (99.5th percentile).

## 7. Hybrid Risk Engine & Decision Matrix
Combines supervised probability with unsupervised anomaly scores:
- **`HIGH RISK`**: XGBoost $\ge 0.70$ OR (XGBoost $\ge 0.10$ AND Isolation Forest $\ge 0.5040$).
- **`FAILURE WARNING`**: XGBoost $\ge 0.10$.
- **`ANOMALY WARNING`**: Isolation Forest $\ge 0.5350$ OR Sustained Anomaly $\ge 0.5040$.
- **`MONITOR`**: Isolated Anomaly $\ge 0.5040$ OR single physical metric deviating $> 2.0\sigma$.
- **`NORMAL`**: All signals conform to baseline distributions.

## 8. Persistence Logic
- **Window**: 5-minute trailing chronological window ($[t - 5\text{m}, t]$).
- **Rule**: If $\ge 3$ observations within the 5-minute window exceed $\tau_{\text{anom}}$, `is_sustained_anomaly = True`.
- **Causality**: Zero future telemetry used. Transient sensor spikes are held at `MONITOR`.

## 9. Physical Evidence Attribution
Calculates baseline $Z$-scores relative to normal training operating distributions:
$$Z = \frac{x_i - \text{Median}_{\text{normal}}}{\sigma_{\text{normal}}}$$
- Signals with $|Z| \ge 2.0\sigma$ are dynamically formatted with actual values, units, and baseline medians.

## 10. Smart Operational Alerts
- **Level 1 (`NORMAL`)**: "Compressor System Operating Within Normal Envelope"
- **Level 2 (`MONITOR`)**: "Operational Advisory & Persistence Monitoring"
- **Level 3 (`WARNING`)**: "Pneumatic Failure Warning Alert" / "Abnormal Compressor Dynamics Warning"
- **Level 4 (`HIGH RISK`)**: "Critical Compressor Failure Risk Alert"

## 11. Prescriptive Maintenance Recommendations
Deterministic rule-based actions derived directly from active physical evidence:
- **Thermal Deviation ($Z \ge +2.0\sigma$)**: *"Inspect compressor cooling circuit, radiator airflow, lubricant condition, and temperature probe."*
- **Filter Volatility ($|Z| \ge 2.0\sigma$)**: *"Inspect cyclonic moisture separator filter assembly, differential pressure sensor, and automatic drain valve."*
- **Discharge Swing ($|Z| \ge 2.0\sigma$)**: *"Check compressor discharge non-return valve, pressure governor calibration, and manifold sealing."*
- **High Risk General Action**: *"Schedule technical pneumatic leak inspection and pressure-decay verification at next depot maintenance stop."*

## 12. API Architecture (FastAPI)
- `GET  /api/health`: Health status & version.
- `GET  /api/latest`: Real-time sensor stream.
- `GET  /api/sensors`: Sensor metadata catalog.
- `GET  /api/timeseries`: Historical sensor chart feeds.
- `GET  /api/events`: Ground-truth failure episodes.
- `GET  /api/model-info`: Dual-model scorecards & thresholds.
- `POST /api/predict`: Standalone XGBoost inference.
- `POST /api/hybrid-predict`: Full dual-engine + alerts + evidence + recommendations.

## 13. Frontend Architecture (React 18 + Vite + Tailwind CSS)
- Single-page application with dark industrial dashboard styling.
- **Pages**: Overview, Live Monitoring, AI Risk Assessment, Sensor Analysis, Model Performance.
- **Key Components**:
  - `RiskGauge`: Radial arc bound dynamically to XGBoost risk %.
  - `StatusBadge`: Industrial state badges with pulsating beacons.
  - `MachineHealthRibbon`: Top-level operational summary.
  - `"Why This Alert?" Panel`: Transparent physical signal attribution.
  - `PrescriptiveRecommendationsCard`: Maintenance action checklist.

## 14. End-to-End Data Flow
```
15 Raw Telemetry Channels ──> 65 Engineered Features
              │
    ┌─────────┴─────────┐
    ▼                   ▼
[XGBoost]       [Isolation Forest]
    │                   │
    └─────────┬─────────┘
              ▼
    [Hybrid Risk Engine]
              │
    [Persistence Filter]
              │
   [Physical Evidence Engine]
              │
    [Smart Alerts & Recs]
              │
    [FastAPI REST API]
              │
       [React Client]
              │
    [RiskGauge & Dashboard]
```

## 15. Limitations
1. **Extreme Class Imbalance**: With only $694$ failure rows ($0.0457\%$) in $1.51\text{M}$ records, unsupervised anomaly detection achieves high recall ($33.15\%$) at the cost of precision ($0.38\%$) on the untouched test partition.
2. **Decision Support**: Alerts guide human technicians rather than directly controlling train braking systems.

## 16. Future Improvements
1. **Edge Deployment**: Compiling the hybrid inference engine into ONNX Runtime or C++ for direct execution on train-borne embedded hardware.
2. **Multi-Train Fleet Aggregation**: Centralized cloud fleet dashboard monitoring hundreds of railcars simultaneously.
