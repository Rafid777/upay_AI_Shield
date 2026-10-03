"""
upay AI Shield V3 - Hybrid Risk Fusion Engine
Combines Supervised ML (XGBoost), Unsupervised Anomaly Detection (Isolation Forest),
Deterministic Rules, Customer Behavioral DNA, ATO Signals, Scam Intelligence,
and Network Topology into a unified, mathematically calibrated Risk Intelligence output.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import logging

from backend.services.model_service import model_service
from backend.services.anomaly_service import anomaly_service
from backend.services.rule_engine import rule_engine
from backend.services.behavioral_service import behavioral_service
from backend.services.ato_service import ato_service
from backend.services.scam_service import scam_service
from backend.services.shap_service import shap_service

logger = logging.getLogger("upay_shield.risk_fusion")


@dataclass
class RiskFusionWeights:
    """Documented, configurable component weights summing to 1.0."""
    w_xgb: float = 0.35        # Supervised XGBoost predictive probability (x100)
    w_anomaly: float = 0.15    # Unsupervised Isolation Forest anomaly score (x100)
    w_rule: float = 0.15       # Deterministic business & policy rules (0-100)
    w_behavior: float = 0.15   # Customer personal baseline deviation (0-100)
    w_ato: float = 0.10        # Account takeover multi-signal detector (0-100)
    w_scam: float = 0.05       # Scam typologies pattern engine (0-100)
    w_network: float = 0.05    # Entity topology & mule fan-in risk (0-100)


class RiskFusionEngine:
    def __init__(self, weights: Optional[RiskFusionWeights] = None):
        self.weights = weights or RiskFusionWeights()

    def fuse_risk_assessment(
        self,
        transaction_data: Dict[str, Any],
        customer_baseline: Optional[Dict[str, Any]] = None,
        network_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes complete multi-engine risk evaluation and fuses signals
        into a unified, explainable 0–100 risk score and operational tier.
        """
        # 1. Supervised XGBoost Prediction
        xgb_res = model_service.predict(transaction_data)
        model_prob = float(xgb_res.get("probability", 0.0))
        xgb_score = float(xgb_res.get("risk_score", model_prob * 100.0))

        # 2. Unsupervised Isolation Forest Anomaly Detection
        anomaly_res = anomaly_service.score_transaction(transaction_data, customer_baseline)
        anomaly_score = float(anomaly_res.get("anomaly_score", 0.0))
        anomaly_score_100 = anomaly_score * 100.0

        # 3. Deterministic Rule Engine
        rule_res = rule_engine.evaluate_rules(transaction_data)
        rule_score = float(rule_res.get("rule_score", 0.0))

        # 4. Customer Behavioral Deviation
        cust_base = customer_baseline or {
            "average_amount": float(transaction_data.get("avg_transaction_amount", 1000.0) or 1000.0),
            "typical_hours": "08:00–22:00"
        }
        behavior_res = behavioral_service.compute_behavioral_deviation(cust_base, transaction_data)
        behavior_score = float(behavior_res.get("behavior_score", 10.0))

        # 5. Account Takeover (ATO) Signals
        ato_res = ato_service.evaluate_ato_signals(transaction_data)
        ato_score = float(ato_res.get("ato_score", 0.0))

        # 6. Scam Typology Patterns
        scam_res = scam_service.analyze_scam_patterns(transaction_data, cust_base)
        scam_score = float(scam_res.get("scam_score", 5.0))

        # 7. Network Intelligence Risk Score
        net_info = network_data or {}
        network_score = float(net_info.get("network_score", 10.0))

        # --- MATHEMATICAL RISK FUSION ---
        # Weighted linear combination
        w = self.weights
        fused_raw = (
            w.w_xgb * xgb_score +
            w.w_anomaly * anomaly_score_100 +
            w.w_rule * rule_score +
            w.w_behavior * behavior_score +
            w.w_ato * ato_score +
            w.w_scam * scam_score +
            w.w_network * network_score
        )

        # Safety Non-Linear Override:
        # If supervised ML detects critical risk (>= 90) or ATO/Rule detects severe emergency (>= 75),
        # ensure the fused score guarantees a HIGH tier (>= 80)
        if xgb_score >= 90.0 or rule_score >= 75.0 or ato_score >= 75.0:
            fused_score = max(fused_raw, 82.0)
        elif xgb_score <= 10.0 and rule_score <= 15.0 and ato_score <= 10.0:
            fused_score = min(fused_raw, 30.0)
        else:
            fused_score = fused_raw

        unified_risk_score = float(min(max(round(fused_score, 1), 0.0), 100.0))

        # Determine Tier & Action
        if unified_risk_score >= 80.0:
            risk_level = "HIGH"
            recommended_action = "HUMAN_REVIEW"
        elif unified_risk_score >= 50.0:
            risk_level = "MEDIUM"
            recommended_action = "ADDITIONAL_REVIEW"
        else:
            risk_level = "LOW"
            recommended_action = "CONTINUE"

        # Generate Top Risk Factors from SHAP and Detectors
        top_factors = self._collate_top_risk_factors(
            transaction_data=transaction_data,
            xgb_factors=xgb_res.get("top_factors", []),
            rules=rule_res.get("triggered_rules", []),
            ato_signals=ato_res.get("detected_signals", []),
            scam_patterns=scam_res.get("patterns_detected", []),
            anomalous_features=anomaly_res.get("anomalous_features", [])
        )

        return {
            "risk_score": unified_risk_score,
            "risk_level": risk_level,
            "recommended_action": recommended_action,
            "model_probability": round(model_prob, 4),
            "anomaly_score": round(anomaly_score, 4),
            "anomaly_level": anomaly_res.get("anomaly_level", "LOW"),
            "rule_score": rule_score,
            "behavior_score": behavior_score,
            "ato_score": ato_score,
            "scam_score": scam_score,
            "network_score": network_score,
            "top_risk_factors": top_factors,
            "component_scores": {
                "model_risk": round(xgb_score, 1),
                "behavior_anomaly": round(behavior_score, 1),
                "ato_indicators": round(ato_score, 1),
                "scam_signals": round(scam_score, 1),
                "network_risk": round(network_score, 1),
                "rule_risk": round(rule_score, 1),
                "anomaly_model": round(anomaly_score_100, 1),
            },
            "fusion_weights": {
                "w_xgb": w.w_xgb,
                "w_anomaly": w.w_anomaly,
                "w_rule": w.w_rule,
                "w_behavior": w.w_behavior,
                "w_ato": w.w_ato,
                "w_scam": w.w_scam,
                "w_network": w.w_network,
            },
            "governance_note": "Risk scores guide human analyst triage queues. Autonomous fund freezing or account blocking is prohibited."
        }

    def _collate_top_risk_factors(
        self,
        transaction_data: Dict[str, Any],
        xgb_factors: List[Dict[str, Any]],
        rules: List[Dict[str, Any]],
        ato_signals: List[Dict[str, Any]],
        scam_patterns: List[Dict[str, Any]],
        anomalous_features: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        factors = []

        # Include SHAP factors
        for f in xgb_factors[:4]:
            factors.append({
                "factor": f.get("feature", "model_signal"),
                "description": f.get("description", ""),
                "impact": f.get("impact", "+0.0"),
                "source": "SHAP_XAI"
            })

        # Include prominent rules
        for r in rules[:3]:
            factors.append({
                "factor": r.get("rule_id", "RULE"),
                "description": r.get("name", "") + " — " + r.get("description", ""),
                "impact": f"+{r.get('weight', 10):.0f} pts",
                "source": "RULE_ENGINE"
            })

        # Include ATO or Scam signatures
        for a in ato_signals[:2]:
            factors.append({
                "factor": a.get("code", "ATO"),
                "description": a.get("label", "") + ": " + a.get("description", ""),
                "impact": f"+{a.get('weight', 15):.0f} pts",
                "source": "ATO_ENGINE"
            })

        for s in scam_patterns[:2]:
            factors.append({
                "factor": s.get("pattern_code", "SCAM"),
                "description": s.get("pattern_name", "") + ": " + s.get("description", ""),
                "impact": s.get("severity", "MEDIUM"),
                "source": "SCAM_ENGINE"
            })

        return factors[:6]


risk_fusion = RiskFusionEngine()
