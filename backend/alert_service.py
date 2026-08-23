"""
MetroGuard AI - Intelligent Alert & Prescriptive Maintenance Workflow Engine
Manages alert lifecycle (ACTIVE, ACKNOWLEDGED, RESOLVED, ESCALATED),
smart deduplication, priority assignment, explainable trigger attribution,
and evidence-based prescriptive maintenance recommendations.
"""

import time
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime

class AlertManager:
    def __init__(self):
        self.lock = threading.RLock()
        self.alert_history: List[Dict[str, Any]] = []
        self.active_alert: Optional[Dict[str, Any]] = None
        self.seq_counter = 1

    def _generate_alert_id(self, scenario: str) -> str:
        sc_tag = scenario[:3].upper() if scenario else "SYS"
        self.seq_counter += 1
        return f"ALT-{sc_tag}-{self.seq_counter:04d}"

    def _determine_priority(self, alert_level: str, is_persistent: bool, severity: int) -> str:
        if alert_level == "HIGH RISK":
            return "CRITICAL"
        elif alert_level == "WARNING":
            return "HIGH" if (is_persistent or severity >= 60) else "MEDIUM"
        elif alert_level == "MONITOR":
            return "LOW"
        else:
            return "NOMINAL"

    def _determine_evidence_strength(self, max_abs_z: float, is_persistent: bool, severity: int, xgb_risk: float) -> str:
        if xgb_risk >= 70.0 or (max_abs_z >= 2.5 and is_persistent and severity >= 40):
            return "STRONG EVIDENCE"
        elif max_abs_z >= 1.5 or is_persistent or severity >= 30:
            return "MODERATE EVIDENCE"
        else:
            return "LOW EVIDENCE"

    def _build_prescriptive_recommendation(
        self,
        alert_level: str,
        hypothesis: Dict[str, Any],
        top_deviations: List[Dict[str, Any]],
        xgb_risk: float,
        evidence_strength: str
    ) -> Dict[str, Any]:
        """Builds evidence-backed maintenance recommendation with checklist and priority."""
        cond_type = hypothesis.get("condition_type", "NOMINAL")
        
        if alert_level == "HIGH RISK" or xgb_risk >= 70.0:
            return {
                "action": "Immediate depot pneumatic leak inspection and pressure decay verification.",
                "priority": "Immediate Attention",
                "reason": f"Supervised AI failure risk escalated to {xgb_risk:.1f}%, indicating impending pneumatic breakdown.",
                "inspection_checklist": [
                    "Perform 5-minute pneumatic line pressure-decay leak test",
                    "Inspect compressor delivery check-valve and solenoid seatings",
                    "Check cyclonic moisture separator auto-drain purge actuation",
                    "Verify drying tower desiccant regeneration cycle pressure"
                ],
                "evidence_strength": evidence_strength
            }
        elif cond_type == "THERMAL_ELEVATION":
            oil_val = next((d["current_value"] for d in top_deviations if d["sensor_id"] == "Oil_temperature"), "N/A")
            return {
                "action": "Inspect compressor oil radiator matrix and cooling ventilation circuit.",
                "priority": "Inspect Soon",
                "reason": f"Compressor oil temperature is deviating significantly at {oil_val}°C above nominal baseline.",
                "inspection_checklist": [
                    "Inspect oil heat exchanger matrix for external dust or debris clogging",
                    "Check lubrication oil reservoir level and sample for thermal degradation",
                    "Verify cooling fan operation and duct airflow velocity",
                    "Inspect oil temperature sensor RTD wiring and calibration"
                ],
                "evidence_strength": evidence_strength
            }
        elif cond_type == "FILTER_RESTRICTION":
            h1_val = next((d["current_value"] for d in top_deviations if d["sensor_id"] == "H1"), "N/A")
            return {
                "action": "Inspect cyclonic moisture separator element and automatic condensate purge.",
                "priority": "Schedule Inspection",
                "reason": f"Filter differential drop is elevated at {h1_val} bar, indicating possible particulate or moisture restriction.",
                "inspection_checklist": [
                    "Inspect cyclonic separator filter cartridge for particulate loading",
                    "Verify automatic condensate drain solenoid valve mechanical cycle",
                    "Check differential pressure transducer signal stability",
                    "Drain moisture bowl manually to check for oil emulsion"
                ],
                "evidence_strength": evidence_strength
            }
        elif cond_type == "PRESSURE_REGULATION":
            return {
                "action": "Calibrate pneumatic panel pressure regulator and inspect desiccant tower valves.",
                "priority": "Schedule Inspection",
                "reason": "Air delivery / reservoir pressures exhibiting out-of-tolerance oscillations.",
                "inspection_checklist": [
                    "Perform pneumatic distribution line pressure decay test",
                    "Inspect desiccant tower purge solenoid cycle timing",
                    "Calibrate pneumatic panel pressure relief valves",
                    "Check main reservoir non-return check valves"
                ],
                "evidence_strength": evidence_strength
            }
        else:
            return {
                "action": "Maintain routine preventive maintenance inspection cycle.",
                "priority": "Routine",
                "reason": "All monitored physical sensor channels conform to nominal baseline operating distributions.",
                "inspection_checklist": [
                    "Verify standard compressor visual indicators and oil sight glass",
                    "Log operating duty cycle and charging frequency",
                    "Ensure electrical motor current is balanced"
                ],
                "evidence_strength": evidence_strength
            }

    def process_telemetry_alert(
        self,
        timestamp: str,
        scenario: str,
        alert_info: Dict[str, Any],
        xgboost_info: Dict[str, Any],
        anomaly_info: Dict[str, Any],
        anomaly_intel: Dict[str, Any],
        evidence: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Processes instantaneous telemetry through the alert lifecycle,
        applying deduplication, escalation, and prescriptive recommendations.
        """
        with self.lock:
            alert_level = alert_info.get("level", "NORMAL")
            xgb_risk = float(xgboost_info.get("risk_percentage", 0.0))
            raw_anom_score = float(anomaly_info.get("score", 0.0))
            anom_sev = int(anomaly_intel.get("anomaly_severity", 0))
            is_persistent = anomaly_intel.get("persistence", {}).get("is_persistent", False)
            traj = anomaly_intel.get("trajectory", "STABLE")
            top_devs = anomaly_intel.get("top_sensor_deviations", [])
            hyp = anomaly_intel.get("operational_hypothesis", {})
            
            priority = self._determine_priority(alert_level, is_persistent, anom_sev)
            max_abs_z = max([d.get("abs_z", 0.0) for d in top_devs], default=0.0)
            evidence_strength = self._determine_evidence_strength(max_abs_z, is_persistent, anom_sev, xgb_risk)
            
            recommendation = self._build_prescriptive_recommendation(
                alert_level=alert_level,
                hypothesis=hyp,
                top_deviations=top_devs,
                xgb_risk=xgb_risk,
                evidence_strength=evidence_strength
            )
            
            # Determine primary trigger description
            if alert_level == "HIGH RISK":
                if xgb_risk >= 70.0:
                    primary_trigger = f"Supervised failure risk crossed critical threshold ({xgb_risk:.1f}% >= 70%)."
                else:
                    primary_trigger = "Concurrent multi-engine alert: Severe anomalous behavior confirmed by physical evidence."
            elif alert_level == "WARNING":
                if xgb_risk >= 10.0:
                    primary_trigger = f"Supervised failure warning ({xgb_risk:.1f}% >= 10%)."
                elif is_persistent:
                    primary_trigger = f"Persistent abnormal operating regime detected (Severity: {anom_sev}/100, ≥3 anomalies in 5m)."
                elif max_abs_z >= 2.5:
                    primary_trigger = f"Significant physical sensor deviation detected (|Z| = {max_abs_z:.2f}σ)."
                else:
                    primary_trigger = f"Unsupervised anomaly detector flagged elevated out-of-distribution state (Severity: {anom_sev}/100)."
            elif alert_level == "MONITOR":
                primary_trigger = f"Operational advisory: Transient sensor deviation flagged for persistence tracking (Severity: {anom_sev}/100)."
            else:
                primary_trigger = "Nominal operating baseline."
                
            # Build structured supporting evidence list
            supporting_evidence = []
            if top_devs:
                top1 = top_devs[0]
                sign = "+" if top1.get("deviation", 0) > 0 else ""
                supporting_evidence.append(f"{top1['name']}: {top1['current_value']} {top1['unit']} ({sign}{top1['deviation']} {top1['unit']}, Z = {top1['z_score']:+.2f}σ)")
                if len(top_devs) > 1:
                    top2 = top_devs[1]
                    s2 = "+" if top2.get("deviation", 0) > 0 else ""
                    supporting_evidence.append(f"{top2['name']}: {top2['current_value']} {top2['unit']} ({s2}{top2['deviation']} {top2['unit']}, Z = {top2['z_score']:+.2f}σ)")
            
            supporting_evidence.append(f"Calibrated Anomaly Severity: {anom_sev}/100 ({anomaly_intel.get('severity_label', 'NOMINAL')})")
            if is_persistent:
                supporting_evidence.append(f"Condition is SUSTAINED ({anomaly_intel.get('persistence', {}).get('abnormal_count', 0)}/30 obs in 5-min window)")
            else:
                supporting_evidence.append("Condition is currently TRANSIENT (Within nominal tolerance window)")
            supporting_evidence.append(f"Severity Trajectory: {traj}")
            
            # --- DEDUPLICATION & LIFECYCLE LOGIC ---
            priority_rank = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "NOMINAL": 0}
            cur_rank = priority_rank.get(priority, 0)
            
            if alert_level == "NORMAL":
                # Machine is operating nominally.
                if self.active_alert and self.active_alert["status"] in ["ACTIVE", "ACKNOWLEDGED"]:
                    self.active_alert["status"] = "RESOLVED"
                    self.active_alert["resolved_at"] = timestamp
                    self.active_alert["updated_at"] = timestamp
                    self.active_alert = None
            else:
                # Abnormal condition (MONITOR, WARNING, or HIGH RISK)
                if self.active_alert is None or self.active_alert["status"] == "RESOLVED":
                    # Brand new incident
                    new_alert_id = self._generate_alert_id(scenario)
                    new_alert = {
                        "alert_id": new_alert_id,
                        "created_at": timestamp,
                        "updated_at": timestamp,
                        "alert_level": alert_level,
                        "priority": priority,
                        "status": "ACTIVE",
                        "primary_trigger": primary_trigger,
                        "supporting_evidence": supporting_evidence,
                        "anomaly_severity": anom_sev,
                        "anomaly_score": raw_anom_score,
                        "xgboost_risk": xgb_risk,
                        "persistence_status": "PERSISTENT" if is_persistent else "TRANSIENT",
                        "trajectory": traj,
                        "scenario": scenario,
                        "recommendation": recommendation,
                        "acknowledged_at": None,
                        "resolved_at": None
                    }
                    self.active_alert = new_alert
                    self.alert_history.insert(0, new_alert)
                    if len(self.alert_history) > 30:
                        self.alert_history.pop()
                else:
                    # Active alert already exists
                    prev_rank = priority_rank.get(self.active_alert["priority"], 0)
                    if cur_rank > prev_rank:
                        # ESCALATION: Condition worsened (e.g. MONITOR -> WARNING, or WARNING -> HIGH RISK)
                        self.active_alert["status"] = "ESCALATED"
                        self.active_alert["updated_at"] = timestamp
                        
                        esc_alert_id = self._generate_alert_id(scenario)
                        esc_alert = {
                            "alert_id": esc_alert_id,
                            "created_at": timestamp,
                            "updated_at": timestamp,
                            "alert_level": alert_level,
                            "priority": priority,
                            "status": "ACTIVE",
                            "primary_trigger": f"ESCALATION: {primary_trigger}",
                            "supporting_evidence": supporting_evidence,
                            "anomaly_severity": anom_sev,
                            "anomaly_score": raw_anom_score,
                            "xgboost_risk": xgb_risk,
                            "persistence_status": "PERSISTENT" if is_persistent else "TRANSIENT",
                            "trajectory": traj,
                            "scenario": scenario,
                            "recommendation": recommendation,
                            "acknowledged_at": None,
                            "resolved_at": None
                        }
                        self.active_alert = esc_alert
                        self.alert_history.insert(0, esc_alert)
                        if len(self.alert_history) > 30:
                            self.alert_history.pop()
                    else:
                        # DEDUPLICATION: Update existing ongoing alert in-place
                        self.active_alert["updated_at"] = timestamp
                        self.active_alert["alert_level"] = alert_level
                        self.active_alert["anomaly_severity"] = anom_sev
                        self.active_alert["anomaly_score"] = raw_anom_score
                        self.active_alert["xgboost_risk"] = xgb_risk
                        self.active_alert["persistence_status"] = "PERSISTENT" if is_persistent else "TRANSIENT"
                        self.active_alert["trajectory"] = traj
                        self.active_alert["supporting_evidence"] = supporting_evidence
                        self.active_alert["recommendation"] = recommendation
                        
            return {
                "active_alert": self.active_alert,
                "current_recommendation": recommendation,
                "alert_history": list(self.alert_history)
            }

    def acknowledge_alert(self, alert_id: str) -> Dict[str, Any]:
        with self.lock:
            for al in self.alert_history:
                if al["alert_id"] == alert_id:
                    al["status"] = "ACKNOWLEDGED"
                    al["acknowledged_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    if self.active_alert and self.active_alert["alert_id"] == alert_id:
                        self.active_alert["status"] = "ACKNOWLEDGED"
                        self.active_alert["acknowledged_at"] = al["acknowledged_at"]
                    return {"status": "success", "message": f"Alert {alert_id} acknowledged by operator.", "alert": al}
            return {"status": "error", "message": f"Alert {alert_id} not found."}

    def resolve_alert(self, alert_id: str) -> Dict[str, Any]:
        with self.lock:
            for al in self.alert_history:
                if al["alert_id"] == alert_id:
                    al["status"] = "RESOLVED"
                    al["resolved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    if self.active_alert and self.active_alert["alert_id"] == alert_id:
                        self.active_alert = None
                    return {"status": "success", "message": f"Alert {alert_id} marked as resolved.", "alert": al}
            return {"status": "error", "message": f"Alert {alert_id} not found."}

    def get_all_alerts(self) -> List[Dict[str, Any]]:
        with self.lock:
            return list(self.alert_history)

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        with self.lock:
            return [a for a in self.alert_history if a["status"] in ["ACTIVE", "ACKNOWLEDGED"]]

    def get_current_recommendation(self) -> Dict[str, Any]:
        with self.lock:
            if self.active_alert and self.active_alert.get("recommendation"):
                return self.active_alert["recommendation"]
            return {
                "action": "Maintain routine preventive maintenance inspection cycle.",
                "priority": "Routine",
                "reason": "All monitored physical sensor channels conform to nominal baseline operating distributions.",
                "inspection_checklist": [
                    "Verify standard compressor visual indicators and oil sight glass",
                    "Log operating duty cycle and charging frequency",
                    "Ensure electrical motor current is balanced"
                ],
                "evidence_strength": "LOW EVIDENCE"
            }

    def reset(self):
        with self.lock:
            self.alert_history.clear()
            self.active_alert = None
            self.seq_counter = 1
            return {"status": "reset", "message": "Alert lifecycle reset to clean initial state."}

# Global singleton
_alert_manager_instance = None

def get_alert_manager() -> AlertManager:
    global _alert_manager_instance
    if _alert_manager_instance is None:
        _alert_manager_instance = AlertManager()
    return _alert_manager_instance
