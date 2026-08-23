# MetroGuard AI — Final Hackathon Demo Checklist

Use this checklist during live presentation to verify full end-to-end functionality:

- [x] **Backend Server Running**: `python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000` (HTTP 200 on `/api/health`).
- [x] **Production Frontend Accessible**: `http://127.0.0.1:8000/` loads the unified control center dashboard.
- [x] **Direct SPA Route Support**: `http://127.0.0.1:8000/risk` directly loads the Risk Assessment page on browser refresh.
- [x] **Top-Level Machine Health Summary**: Header ribbon displays Compressor Unit name, Overall Status, Known Risk %, Anomaly Index, Active Alert, and Matched Observation.
- [x] **Normal Scenario Verification**:
  - Select *Normal March Baseline* (`2020-03-01 12:00:00`).
  - XGBoost displays `0.04%` (Normal).
  - Anomaly Score displays `0.3480` (Normal).
  - Decision displays `NORMAL` / `MONITOR`.
- [x] **Event #1 Known Failure Demo**:
  - Click *Event #1 (April 17 23:30)* quick-jump pill.
  - RiskGauge animates to **`98.78%`** (Red / High Risk).
  - Alert displays **`HIGH RISK` — Critical Compressor Failure Risk Alert**.
  - Physical Evidence displays $H_1 = 8.24\text{ bar}$ ($+2.19\sigma$).
  - Recommendations display cyclonic separator drain valve inspection.
- [x] **Event #2 Known Failure Demo**:
  - Click *Event #2 (May 29 23:00)* quick-jump pill.
  - RiskGauge animates to **`97.57%`** (Red / High Risk).
  - Alert displays **`HIGH RISK`**.
- [x] **Event #4 Unseen Summer Anomaly Demo**:
  - Click *Event #4 (July 15 14:00)* quick-jump pill.
  - XGBoost displays `0.03%` (Normal).
  - Isolation Forest & Physical Evidence detect multi-signal deviation ($\text{Oil\_temp} = 81.4^\circ\text{C}$ at $+3.69\sigma$, $TP2 = 10.3\text{ bar}$ at $+2.75\sigma$).
  - Alert elevates to **`WARNING` — Abnormal Compressor Dynamics Warning**.
  - Recommendations display cooling radiator inspection & discharge valve check.
- [x] **Custom Timestamp Testing**:
  - Enter `2020-04-10 10:00:00` into custom input.
  - Returns matched observation `2020-04-10 09:59:57` ($\Delta 3\text{s}$) with live inference metrics.
- [x] **Error Handling Demonstration**:
  - Enter `invalid` or `2025-01-01` into custom input.
  - Clean operator error notification displays (*"Telemetry observation not found"*), zero page crash.
- [x] **Zero Hardcoded Values Verified**: All numerical outputs originate dynamically from backend dual-model inference.
- [x] **Sub-35ms Inference Latency**: XGBoost mean latency $\approx 10.5\text{ms}$, Hybrid mean latency $\approx 31.0\text{ms}$.
- [x] **Zero Browser Console Errors**: 0 JavaScript runtime errors, 0 unhandled promise rejections.
