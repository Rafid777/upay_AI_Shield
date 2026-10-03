"""
upay AI Shield V3 - Live Risk Simulator, What-If Analysis & Attack Scenario Simulator
Provides endpoints for:
- Live Hybrid Transaction Simulation
- Counterfactual What-If Parameter Tuning
- Attack Scenario Simulator Presets (Normal, ATO, Scam, High Velocity, New Device, Suspicious Network)
All simulations are explicitly labeled: 'SYNTHETIC SCENARIO / SIMULATION'.
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas import WhatIfRequest, WhatIfResponse
from backend.services.model_service import model_service
from backend.services.shap_service import shap_service
from backend.services.behavioral_service import behavioral_service
from backend.services.ato_service import ato_service
from backend.services.scam_service import scam_service
from backend.services.anomaly_service import anomaly_service
from backend.services.rule_engine import rule_engine
from backend.services.risk_fusion_service import risk_fusion
from backend.services.what_if_service import WhatIfSimulatorService
from src.data_pipeline import MODEL_FEATURES

router = APIRouter(tags=["Simulation & What-If Analysis"])
what_if_service = WhatIfSimulatorService()


class SimulateRequest(BaseModel):
    amount: float = Field(..., description="Transaction amount in BDT (numeric only)")
    transaction_type: Optional[str] = "SEND_MONEY"
    channel: Optional[str] = "APP"
    hour: int = Field(12, ge=0, le=23)
    day_of_week: Optional[int] = Field(4, ge=0, le=6)
    is_new_device: int = Field(0, ge=0, le=1)
    is_new_receiver: int = Field(0, ge=0, le=1)
    location_changed: int = Field(0, ge=0, le=1)
    transactions_last_1h: int = Field(1, ge=0)
    transactions_last_24h: int = Field(3, ge=0)
    failed_attempts: int = Field(0, ge=0)
    account_age_days: Optional[int] = Field(180, ge=1)
    receiver_transaction_count: Optional[int] = Field(12, ge=0)
    amount_deviation: Optional[float] = Field(1.0, ge=0.1)
    location: Optional[str] = "Dhaka"
    customer_id: Optional[str] = None


ATTACK_PRESETS: Dict[str, Dict[str, Any]] = {
    "NORMAL_CUSTOMER": {
        "name": "Normal Customer Baseline",
        "description": "Routine daytime payment to known merchant/contact from registered handset.",
        "payload": {
            "amount": 850.0,
            "hour": 14,
            "day_of_week": 2,
            "is_new_device": 0,
            "is_new_receiver": 0,
            "location_changed": 0,
            "transactions_last_1h": 1,
            "transactions_last_24h": 3,
            "failed_attempts": 0,
            "account_age_days": 420,
            "receiver_transaction_count": 25,
            "amount_deviation": 1.0,
            "channel": "APP",
            "transaction_type": "PAYMENT",
            "location": "Dhaka"
        }
    },
    "ACCOUNT_TAKEOVER": {
        "name": "Account Takeover (ATO) Burst",
        "description": "Unregistered device authentication at 02:30 AM with password guessing and sudden balance drain.",
        "payload": {
            "amount": 28500.0,
            "hour": 2,
            "day_of_week": 4,
            "is_new_device": 1,
            "is_new_receiver": 1,
            "location_changed": 1,
            "transactions_last_1h": 8,
            "transactions_last_24h": 14,
            "failed_attempts": 4,
            "account_age_days": 180,
            "receiver_transaction_count": 2,
            "amount_deviation": 14.5,
            "channel": "APP",
            "transaction_type": "SEND_MONEY",
            "location": "Chattogram"
        }
    },
    "SCAM_TRANSFER": {
        "name": "High-Value Social Engineering Scam",
        "description": "Victim coerced into transferring 18x normal baseline to a newly created recipient account.",
        "payload": {
            "amount": 48000.0,
            "hour": 11,
            "day_of_week": 3,
            "is_new_device": 0,
            "is_new_receiver": 1,
            "location_changed": 0,
            "transactions_last_1h": 2,
            "transactions_last_24h": 4,
            "failed_attempts": 0,
            "account_age_days": 730,
            "receiver_transaction_count": 1,
            "amount_deviation": 18.0,
            "channel": "APP",
            "transaction_type": "SEND_MONEY",
            "location": "Dhaka"
        }
    },
    "HIGH_VELOCITY_ATTACK": {
        "name": "High-Velocity Script / Smurfing",
        "description": "Rapid successive cash-out operations (11 tx/hour) testing account balance limits.",
        "payload": {
            "amount": 6500.0,
            "hour": 19,
            "day_of_week": 5,
            "is_new_device": 1,
            "is_new_receiver": 1,
            "location_changed": 0,
            "transactions_last_1h": 11,
            "transactions_last_24h": 25,
            "failed_attempts": 2,
            "account_age_days": 95,
            "receiver_transaction_count": 3,
            "amount_deviation": 3.5,
            "channel": "APP",
            "transaction_type": "CASH_OUT",
            "location": "Sylhet"
        }
    },
    "NEW_DEVICE_ATTACK": {
        "name": "Unregistered Device Cash-Out",
        "description": "Nocturnal login on previously unseen hardware device followed immediately by large transfer.",
        "payload": {
            "amount": 22000.0,
            "hour": 3,
            "day_of_week": 1,
            "is_new_device": 1,
            "is_new_receiver": 0,
            "location_changed": 1,
            "transactions_last_1h": 3,
            "transactions_last_24h": 5,
            "failed_attempts": 3,
            "account_age_days": 310,
            "receiver_transaction_count": 8,
            "amount_deviation": 8.5,
            "channel": "APP",
            "transaction_type": "CASH_OUT",
            "location": "Khulna"
        }
    },
    "SUSPICIOUS_NETWORK": {
        "name": "Mule Network Inflow Cluster",
        "description": "High-value transfer directed to a central receiver account linked to multiple customer sources.",
        "payload": {
            "amount": 35000.0,
            "hour": 16,
            "day_of_week": 0,
            "is_new_device": 1,
            "is_new_receiver": 1,
            "location_changed": 1,
            "transactions_last_1h": 5,
            "transactions_last_24h": 9,
            "failed_attempts": 1,
            "account_age_days": 210,
            "receiver_transaction_count": 1,
            "amount_deviation": 9.0,
            "channel": "WEB",
            "transaction_type": "SEND_MONEY",
            "location": "Rajshahi"
        }
    }
}


@router.post("/simulate")
def simulate_transaction(
    payload: SimulateRequest,
    db: Session = Depends(get_db)
):
    """
    Evaluates a simulated transaction through the full Hybrid Risk Intelligence Pipeline:
    Supervised XGBoost + Unsupervised Isolation Forest + Deterministic Rules +
    Customer Behavior Profile + ATO Signals + Scam Patterns + SHAP Local Attribution.
    """
    feat_dict = {
        "amount": float(payload.amount),
        "hour": int(payload.hour),
        "day_of_week": int(payload.day_of_week or 4),
        "is_new_receiver": int(payload.is_new_receiver),
        "is_new_device": int(payload.is_new_device),
        "location_changed": int(payload.location_changed),
        "transactions_last_1h": int(payload.transactions_last_1h),
        "transactions_last_24h": int(payload.transactions_last_24h),
        "failed_attempts": int(payload.failed_attempts),
        "account_age_days": int(payload.account_age_days or 180),
        "receiver_transaction_count": int(payload.receiver_transaction_count or 12),
        "amount_deviation": float(payload.amount_deviation or 1.0)
    }

    cust_id = payload.customer_id or "CUST_SIMULATED"
    baseline = behavioral_service.get_customer_baseline(db, cust_id)
    tx_dict = dict(feat_dict)
    tx_dict.update({
        "channel": payload.channel,
        "transaction_type": payload.transaction_type,
        "location": payload.location
    })

    # Run Hybrid Risk Fusion
    fusion_res = risk_fusion.fuse_risk_assessment(
        transaction_data=tx_dict,
        customer_baseline=baseline
    )

    # Detailed SHAP factors
    shap_detailed = shap_service.explain_detailed(feat_dict)

    # Behavioral deviations
    deviations = behavioral_service.compute_behavioral_deviation(baseline, tx_dict)

    # ATO signals
    ato_signals = ato_service.evaluate_ato_signals(tx_dict)

    # Scam pattern evaluation
    scam_res = scam_service.analyze_scam_patterns(tx_dict, baseline)

    return {
        "risk_score": fusion_res["risk_score"],
        "risk_level": fusion_res["risk_level"],
        "recommended_action": fusion_res["recommended_action"],
        "model_probability": fusion_res["model_probability"],
        "anomaly_score": fusion_res["anomaly_score"],
        "anomaly_level": fusion_res["anomaly_level"],
        "rule_score": fusion_res["rule_score"],
        "behavior_score": fusion_res["behavior_score"],
        "ato_score": fusion_res["ato_score"],
        "scam_score": fusion_res["scam_score"],
        "network_score": fusion_res["network_score"],
        "component_scores": fusion_res["component_scores"],
        "top_risk_factors": fusion_res["top_risk_factors"],
        "shap_explanation": shap_detailed["top_risk_increasing"][:5],
        "top_risk_increasing": shap_detailed["top_risk_increasing"][:5],
        "top_risk_reducing": shap_detailed["top_risk_reducing"][:3],
        "behavioral_deviations": deviations.get("deviations_list", []),
        "behavioral_comparison": deviations.get("comparison", {}),
        "ato_indicators": ato_signals,
        "potential_scam_patterns": scam_res,
        "disclaimer": "Simulation only — not a production transaction decision."
    }


@router.get("/simulate/presets")
def list_attack_presets():
    """
    Returns available attack and benign scenario simulation presets.
    """
    presets = []
    for key, data in ATTACK_PRESETS.items():
        presets.append({
            "preset_id": key,
            "name": data["name"],
            "description": data["description"],
            "sample_amount_bdt": data["payload"]["amount"],
            "sample_amount_display": f"৳{data['payload']['amount']:,.2f}",
            "channel": data["payload"]["channel"],
            "transaction_type": data["payload"]["transaction_type"]
        })
    return {"total_presets": len(presets), "presets": presets}


@router.post("/simulate/preset/{preset_id}")
def run_attack_preset(
    preset_id: str,
    db: Session = Depends(get_db)
):
    """
    Executes a predefined Attack Scenario Preset through the real Hybrid Risk Intelligence Pipeline.
    Clearly labeled: 'SYNTHETIC SCENARIO'.
    """
    preset_key = preset_id.upper()
    if preset_key not in ATTACK_PRESETS:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found. Available: {list(ATTACK_PRESETS.keys())}")

    preset_data = ATTACK_PRESETS[preset_key]
    payload_dict = preset_data["payload"]
    req = SimulateRequest(**payload_dict)

    result = simulate_transaction(payload=req, db=db)
    result["preset_id"] = preset_key
    result["preset_name"] = preset_data["name"]
    result["scenario_type"] = "SYNTHETIC SCENARIO"
    result["label"] = "SYNTHETIC SCENARIO — Evaluated through live hybrid ML, anomaly & rule pipeline."
    return result


@router.post("/what-if", response_model=WhatIfResponse)
def simulate_what_if(
    payload: WhatIfRequest,
    db: Session = Depends(get_db)
):
    """
    Performs counterfactual what-if analysis by re-running the live XGBoost model
    on modified features and computing the exact score delta and factor changes.
    """
    res = what_if_service.simulate_what_if(
        db=db,
        transaction_id=payload.transaction_id,
        base_features=payload.base_features,
        modified_features=payload.modified_features
    )
    return res
