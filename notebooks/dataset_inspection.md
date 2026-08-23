# MetroPT-3 Dataset Inspection & Ground Truth Report

## 1. Dataset Overview & Provenance
- **Dataset Name**: MetroPT-3 Dataset (Air Production Unit of Metro Trains)
- **Official Source**: UCI Machine Learning Repository (Dataset ID: [791](https://archive.ics.uci.edu/dataset/791/metropt+3+dataset))
- **Donation Date**: March 21, 2023
- **Primary References**:
  - Davari, N., Veloso, B., Ribeiro, R.P., Pereira, P.M., Gama, J. (2021). *Predictive maintenance based on anomaly detection using deep learning for air production unit in the railway industry*. IEEE DSAA 2021. DOI: [10.1109/DSAA53316.2021.9564181](https://doi.org/10.1109/DSAA53316.2021.9564181)
  - Veloso, B., Ribeiro, R.P., Pereira, P.M., Gama, J. (2022). *The MetroPT dataset for predictive maintenance*. Nature Scientific Data 9, 764. DOI: [10.1038/s41597-022-01877-3](https://doi.org/10.1038/s41597-022-01877-3)
- **Context & Application**: Real-world multivariate telemetry collected from the Air Production Unit (APU) / compressor subsystem of metro trains operated by Metro do Porto, Portugal. Used for condition monitoring, predictive maintenance, and remaining useful life (RUL) estimation.

---

## 2. Raw Dataset Files & Footprint in `data/raw/`

| File Name | File Size (MB) | Exact Bytes | Description |
| :--- | :--- | :--- | :--- |
| `MetroPT3(AirCompressor).csv` | 208.19 MB | 218,300,507 | Full raw telemetry records (CSV format) |
| `Data Description_Metro.pdf` | 0.08 MB | 81,208 | Official dataset documentation & failure event table |
| `metropt_3_dataset.zip` | 208.27 MB | 218,381,995 | Original pristine zip archive from UCI repository |

---

## 3. Dataset Dimensions & Temporal Scope
- **Total Records / Instances**: `1,516,948` rows
- **Total Columns**: `17` columns (`1` index + `1` timestamp + `15` sensor/valve signals)
- **Temporal Range**: 
  - **Start Timestamp**: `2020-02-01 00:00:00`
  - **End Timestamp**: `2020-09-01 03:59:50`
  - **Span**: 213 days, 3 hours (~7 calendar months)
  - **Sampling Resolution**: 10-second intervals (0.1 Hz telemetry logging)

---

## 4. Signal Dictionary & Schema

| # | Column Name | Type | Physical Unit | Unique Values | Description & Operational Function |
| :- | :--- | :--- | :--- | :- | :--- |
| 1 | `Unnamed: 0` | `int64` | Index | 1,516,948 | Original recording row index |
| 2 | `timestamp` | `datetime64[ns]` | Timestamp | 1,516,948 | Date and time of sensor logging (UTC format) |
| 3 | `TP2` | `float64` | bar | 5,257 | Compressor discharge pressure |
| 4 | `TP3` | `float64` | bar | 3,683 | Pressure generated at the pneumatic panel |
| 5 | `H1` | `float64` | bar | 2,665 | Pressure generated from pressure drop during discharge of cyclonic separator filter |
| 6 | `DV_pressure` | `float64` | bar | 2,257 | Pressure drop when drying towers discharge air dryers (0 when working under load) |
| 7 | `Reservoirs` | `float64` | bar | 3,682 | Downstream reservoir pressure (tracks TP3) |
| 8 | `Oil_temperature` | `float64` | °C | 2,462 | Compressor lubricating oil temperature |
| 9 | `Motor_current` | `float64` | A | 1,809 | Electric current of 3-phase motor (~0A off, ~4A offload, ~7A loaded, ~9A start) |
| 10 | `COMP` | `float64` | Binary (0/1) | 2 | Air intake valve electrical signal (1 = active/closed, no air intake; 0 = open) |
| 11 | `DV_eletric` | `float64` | Binary (0/1) | 2 | Compressor outlet valve control (1 = compressor under load; 0 = off/offload) |
| 12 | `Towers` | `float64` | Binary (0/1) | 2 | Active drying tower indicator (0 = Tower 1 active; 1 = Tower 2 active) |
| 13 | `MPG` | `float64` | Binary (0/1) | 2 | Intake valve control signal to start compressor under load when pressure < 8.2 bar |
| 14 | `LPS` | `float64` | Binary (0/1) | 2 | Low Pressure Signal (1 = alarm trigger when pressure drops below 7.0 bar) |
| 15 | `Pressure_switch` | `float64` | Binary (0/1) | 2 | Detection of discharge in air-drying towers |
| 16 | `Oil_level` | `float64` | Binary (0/1) | 2 | Low oil level alarm sensor (1 = oil level normal; 0/active alert when below threshold) |
| 17 | `Caudal_impulses` | `float64` | Binary (0/1) | 2 | Pulse counter outputs from air volume flow from APU into reservoirs |

---

## 5. Missing Values & Data Quality Audit
- **Null / Missing Value Count**: **0** across all 17 columns (100% complete).
- **Data Integrity**: Timestamps are strictly sequential; all sensor values fall within valid physical operational envelopes.

---

## 6. Descriptive Statistics for Sensor Features

```text
                     count       mean       std     min     25%     50%      75%     max
TP2              1516948.0   1.367826  3.250930  -0.032  -0.014  -0.012  -0.0100  10.676
TP3              1516948.0   8.984611  0.639095   0.730   8.492   8.960   9.4920  10.302
H1               1516948.0   7.568155  3.333200  -0.036   8.254   8.784   9.3740  10.288
DV_pressure      1516948.0   0.055956  0.382402  -0.032  -0.022  -0.020  -0.0180   9.844
Reservoirs       1516948.0   8.985233  0.638307   0.712   8.494   8.960   9.4920  10.300
Oil_temperature  1516948.0  62.644182  6.516261  15.400  57.775  62.700  67.2500  89.050
Motor_current    1516948.0   2.050171  2.302053   0.020   0.040   0.045   3.8075   9.295
COMP             1516948.0   0.836957  0.369405   0.000   1.000   1.000   1.0000   1.000
DV_eletric       1516948.0   0.160611  0.367172   0.000   0.000   0.000   0.0000   1.000
Towers           1516948.0   0.919848  0.271528   0.000   1.000   1.000   1.0000   1.000
MPG              1516948.0   0.832664  0.373276   0.000   1.000   1.000   1.0000   1.000
LPS              1516948.0   0.003420  0.058381   0.000   0.000   0.000   0.0000   1.000
Pressure_switch  1516948.0   0.991437  0.092141   0.000   1.000   1.000   1.0000   1.000
Oil_level        1516948.0   0.904156  0.294378   0.000   1.000   1.000   1.0000   1.000
Caudal_impulses  1516948.0   0.937107  0.242771   0.000   1.000   1.000   1.0000   1.000
```

---

## 7. Official Ground-Truth Failure & Maintenance Documentation

### Are failure labels included directly in the CSV?
**NO**. The raw telemetry CSV file contains purely unlabeled continuous and discrete sensor readings.

### Failure Information Source:
Provided in the official companion maintenance logs documented in `Data Description_Metro.pdf` and published research papers (Davari et al., 2021; Veloso et al., 2022).

### Documented Ground-Truth Failure Events:

| Incident # | Start Time (UTC) | End Time (UTC) | Failure Type | Severity | Operator Maintenance Action & Log |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **#1** | `2020-04-18 00:00:00` | `2020-04-18 23:59:00` | **Air Leak** | High stress | Compressor high-stress cycling event due to air leakage. |
| **#2** | `2020-05-29 23:30:00` | `2020-05-30 06:00:00` | **Air Leak** | High stress | Maintenance intervention logged on 30-May at 12:00. |
| **#3** | `2020-06-05 10:00:00` | `2020-06-07 14:30:00` | **Air Leak** | High stress | Extended degradation leak; Maintenance performed on 08-Jun at 16:00. |
| **#4** | `2020-07-15 14:30:00` | `2020-07-15 19:00:00` | **Air Leak** | High stress | Severe air leakage episode; Maintenance performed on 16-Jul at 00:00. |

---

## 8. Summary of Findings for Next Steps
1. The dataset contains genuine high-fidelity telemetry with zero synthetic or fabricated values.
2. The operational data exhibits clear physical relationships (e.g. pressure correlations between `TP3` and `Reservoirs`, motor load transitions between ~0A, ~4A, and ~7A, valve cycling between `DV_eletric` and `COMP`).
3. Ground-truth failure events are precisely dated, enabling objective anomaly detection evaluation and predictive lead-time validation in upcoming phases.
