"""
upay AI Shield - Prediction API Route
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Transaction, RiskPrediction
from backend.schemas import PredictRequest, PredictResponse, SHAPFactor
from backend.services.model_service import model_service
from backend.services.shap_service import shap_service
from src.data_pipeline import MODEL_FEATURES

router = APIRouter(prefix="/predict", tags=["Prediction & Risk Scoring"])


@router.post("", response_model=PredictResponse)
def predict_transaction_risk(
    payload: PredictRequest,
    db: Session = Depends(get_db)
):
    """
    Evaluates transaction risk using the trained XGBoost model and calculates SHAP explainability factors.
    Supports either an existing transaction_id or manual feature payload.
    """
    tx_id = payload.transaction_id or "TX_CUSTOM"
    feature_dict = {}

    if payload.transaction_id:
        tx = db.query(Transaction).filter(Transaction.transaction_id == payload.transaction_id).first()
        if not tx:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transaction with ID '{payload.transaction_id}' not found."
            )
        feature_dict = {f: getattr(tx, f, 0.0) for f in MODEL_FEATURES}
    elif payload.features:
        feature_dict = payload.features.model_dump()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'transaction_id' or 'features' must be provided."
        )

    # Run inference
    pred_res = model_service.predict(feature_dict)
    
    # Calculate SHAP factors
    shap_factors_raw = shap_service.explain(pred_res["features_df"], top_k=6)
    shap_factors = [SHAPFactor(**sf) for sf in shap_factors_raw]

    # Save prediction record if transaction_id exists in database
    if payload.transaction_id:
        existing = db.query(RiskPrediction).filter(RiskPrediction.transaction_id == payload.transaction_id).first()
        if existing:
            existing.risk_probability = pred_res["risk_probability"]
            existing.risk_score = pred_res["risk_score"]
            existing.risk_level = pred_res["risk_level"]
            existing.recommended_action = pred_res["recommended_action"]
            existing.shap_factors = [sf.model_dump() for sf in shap_factors]
        else:
            new_pred = RiskPrediction(
                transaction_id=payload.transaction_id,
                model_version=pred_res["model_version"],
                risk_probability=pred_res["risk_probability"],
                risk_score=pred_res["risk_score"],
                risk_level=pred_res["risk_level"],
                recommended_action=pred_res["recommended_action"],
                shap_factors=[sf.model_dump() for sf in shap_factors]
            )
            db.add(new_pred)
        db.commit()

    return PredictResponse(
        transaction_id=tx_id,
        risk_probability=pred_res["risk_probability"],
        risk_score=pred_res["risk_score"],
        risk_level=pred_res["risk_level"],
        recommended_action=pred_res["recommended_action"],
        model_version=pred_res["model_version"],
        shap_factors=shap_factors
    )
