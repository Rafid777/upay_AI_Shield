"""
upay AI Shield - Gemini AI Investigation Service
Integrates Gemini as an AI Investigation Assistant to interpret XGBoost predictions,
SHAP evidence, behavioral baselines, and Account Takeover (ATO) indicators.

CRITICAL CONSTRAINTS:
- Gemini is NOT the fraud classifier.
- Gemini only analyzes provided evidence.
- Gemini MUST NEVER independently confirm fraud or invent facts.
- Gemini MUST NEVER recommend autonomous blocking or make financial decisions.
- If Gemini fails or times out, the service returns a safe deterministic fallback.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from backend.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a financial risk investigation assistant for a financial risk analyst in upay AI Shield.
Analyze ONLY the evidence provided to you.
Do not invent facts or evidence.
Do not independently declare fraud or scam as confirmed.
Do not make autonomous financial decisions.
Distinguish model prediction from analyst judgment.
Explain why the transaction is unusual and identify what the human analyst should investigate next.
CURRENCY CONTEXT: All monetary amounts represent Bangladesh Taka (BDT / ৳). Express all monetary values with the ৳ symbol (e.g., ৳18,500) or BDT. Never refer to USD or dollars.

Output MUST be valid, clean JSON with this exact structure:
{
  "summary": "Concise 2-3 sentence executive case summary analyzing model score and observed evidence",
  "key_findings": [
    "Identified empirical finding 1",
    "Identified empirical finding 2"
  ],
  "behavioral_deviations": [
    "Observed deviation from customer historical baseline 1",
    "Observed deviation from customer historical baseline 2"
  ],
  "ato_indicators": [
    "Potential account takeover indicator 1"
  ],
  "scam_patterns": [
    "Potential scam pattern indicator 1"
  ],
  "network_observations": [
    "Entity relationship or counterparty observation 1"
  ],
  "investigation_questions": [
    "Specific verification question for analyst 1",
    "Specific verification question for analyst 2"
  ],
  "recommended_action": "CONTINUE" | "ADDITIONAL_REVIEW" | "HUMAN_REVIEW",
  "confidence_note": "Evidence-grounded confidence evaluation note",
  "human_review_required": true
}
"""


class GeminiInvestigationService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.client = None
        self.model_name = "gemini-2.5-flash"
        self._init_client()

    def _init_client(self):
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not configured. Fallback mode will be active.")
            return

        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            logger.info(f"Gemini client initialized with model '{self.model_name}'")
        except Exception as e:
            logger.warning(f"Failed to initialize google-genai client: {e}. Fallback mode active.")
            self.client = None

    def generate_investigation(
        self,
        transaction_data: Dict[str, Any],
        prediction_result: Dict[str, Any],
        shap_factors: List[Dict[str, Any]],
        customer_baseline: Optional[Dict[str, Any]] = None,
        behavioral_deviations: Optional[Dict[str, Any]] = None,
        ato_signals: Optional[Dict[str, Any]] = None,
        scam_patterns: Optional[Dict[str, Any]] = None,
        risk_story: Optional[Dict[str, Any]] = None,
        network_graph: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Synthesizes transaction facts, XGBoost probability, SHAP factors, customer baseline,
        ATO indicators, scam patterns, and network intelligence into an AI investigation report.
        """
        tx_id = transaction_data.get("transaction_id", "UNKNOWN")
        risk_score = float(prediction_result.get("risk_score", 0.0))
        risk_level = prediction_result.get("risk_level", "LOW")
        action = prediction_result.get("recommended_action", "HUMAN_REVIEW" if risk_score >= 80 else ("ADDITIONAL_REVIEW" if risk_score >= 50 else "CONTINUE"))

        evidence_payload = {
            "transaction_facts": {
                "transaction_id": tx_id,
                "amount": transaction_data.get("amount"),
                "timestamp": transaction_data.get("timestamp"),
                "channel": transaction_data.get("channel"),
                "transaction_type": transaction_data.get("transaction_type"),
                "hour": transaction_data.get("hour"),
                "location": transaction_data.get("location"),
                "is_new_receiver": bool(transaction_data.get("is_new_receiver")),
                "is_new_device": bool(transaction_data.get("is_new_device")),
                "location_changed": bool(transaction_data.get("location_changed")),
                "transactions_last_1h": transaction_data.get("transactions_last_1h"),
                "transactions_last_24h": transaction_data.get("transactions_last_24h"),
                "failed_attempts": transaction_data.get("failed_attempts"),
                "amount_deviation": transaction_data.get("amount_deviation")
            },
            "model_prediction": {
                "risk_probability": prediction_result.get("risk_probability"),
                "risk_score": risk_score,
                "risk_level": risk_level,
                "recommended_action": action
            },
            "shap_top_contributors": shap_factors,
            "customer_behavioral_baseline": customer_baseline or {},
            "current_transaction_deviations": behavioral_deviations or {},
            "account_takeover_indicators": ato_signals or {},
            "scam_pattern_intelligence": scam_patterns or {},
            "network_intelligence": (network_graph or {}).get("insights", []),
            "risk_story_timeline": (risk_story or {}).get("timeline_events", [])
        }

        # Attempt Gemini call if client available
        if self.client:
            try:
                prompt_content = f"{SYSTEM_PROMPT}\n\nTRANSACTION EVIDENCE PACKAGE:\n{json.dumps(evidence_payload, indent=2)}\n\nGenerate structured JSON investigation report:"
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt_content
                )
                
                raw_text = response.text.strip()
                if "```json" in raw_text:
                    raw_text = raw_text.split("```json")[1].split("```")[0].strip()
                elif "```" in raw_text:
                    raw_text = raw_text.split("```")[1].split("```")[0].strip()

                parsed = json.loads(raw_text)

                # Ensure consistent contract
                parsed["transaction_id"] = tx_id
                parsed["risk_context"] = {"risk_score": risk_score, "risk_level": risk_level}
                parsed["key_findings"] = parsed.get("key_findings") or parsed.get("risk_signals") or []
                parsed["risk_signals"] = parsed["key_findings"]
                parsed["behavioral_deviations"] = parsed.get("behavioral_deviations") or (behavioral_deviations or {}).get("deviations_list", [])
                parsed["ato_indicators"] = parsed.get("ato_indicators") or [s["label"] for s in (ato_signals or {}).get("detected_signals", [])]
                parsed["scam_patterns"] = parsed.get("scam_patterns") or [p["pattern_name"] for p in (scam_patterns or {}).get("patterns_detected", [])]
                parsed["network_observations"] = parsed.get("network_observations") or [i["pattern"] for i in (network_graph or {}).get("insights", [])]
                parsed["investigation_questions"] = parsed.get("investigation_questions") or parsed.get("evidence_to_review") or []
                parsed["evidence_to_review"] = parsed["investigation_questions"]
                parsed["recommended_action"] = action
                parsed["human_review_required"] = risk_score >= 50.0
                parsed["is_ai_generated"] = True
                parsed["notice"] = "Generated by AI Investigation Assistant. Final determination rests with human analyst."
                logger.info(f"Gemini investigation report successfully generated for {tx_id}")
                return parsed

            except Exception as e:
                logger.error(f"Gemini API call failed for {tx_id}: {e}. Activating deterministic fallback.")

        # Deterministic Safe Fallback
        return self._generate_safe_fallback(
            tx_id=tx_id,
            risk_score=risk_score,
            risk_level=risk_level,
            action=action,
            shap_factors=shap_factors,
            tx_data=transaction_data,
            deviations=behavioral_deviations,
            ato_signals=ato_signals,
            scam_patterns=scam_patterns,
            network_graph=network_graph
        )

    def answer_chat_query(
        self,
        transaction_id: str,
        user_query: str,
        investigation_data: Dict[str, Any],
        transaction_data: Dict[str, Any],
        shap_factors: List[Dict[str, Any]],
        baseline_data: Optional[Dict[str, Any]] = None,
        ato_signals: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Interactive conversational Q&A grounded strictly in actual transaction evidence,
        customer baseline deviations, and ATO indicators.
        """
        risk_score = investigation_data.get("risk_context", {}).get("risk_score", 0.0)
        risk_level = investigation_data.get("risk_context", {}).get("risk_level", "LOW")

        context = {
            "transaction_id": transaction_id,
            "transaction_facts": transaction_data,
            "shap_factors": shap_factors,
            "customer_baseline": baseline_data or {},
            "ato_indicators": ato_signals or {},
            "investigation_summary": investigation_data.get("summary")
        }

        if self.client:
            try:
                chat_prompt = f"""You are the upay AI Shield Investigation Assistant for a certified fraud analyst.
Analyst Question: "{user_query}"

Transaction & Behavioral Context for {transaction_id}:
{json.dumps(context, indent=2)}

STRICT RULES:
1. Answer clearly, factually, and concisely based strictly on the provided evidence.
2. If asked about normal behavior or baseline, cite specific figures from customer baseline.
3. If asked about account takeover, refer to the detected ATO indicators.
4. Do NOT independently confirm fraud; suggest what the analyst should manually verify.
5. Remind that final decisions rest with the human analyst.
6. All currency values are in Bangladesh Taka (BDT / ৳). Express amounts with the ৳ symbol (e.g., ৳18,500). Never refer to USD or dollars.
"""
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=chat_prompt
                )
                return {
                    "transaction_id": transaction_id,
                    "reply": response.text.strip(),
                    "risk_context": {"risk_score": risk_score, "risk_level": risk_level},
                    "evidence_sources": ["XGBoost Risk Probability", "SHAP TreeExplainer Attribution", "Customer Empirical Baseline", "ATO Engine"]
                }
            except Exception as e:
                logger.error(f"Gemini chat error for {transaction_id}: {e}. Returning safe fallback answer.")

        # Fallback chat handler
        reply = self._generate_fallback_chat_reply(
            query=user_query,
            tx_data=transaction_data,
            shap_factors=shap_factors,
            risk_score=risk_score,
            risk_level=risk_level,
            baseline=baseline_data,
            ato_signals=ato_signals
        )
        return {
            "transaction_id": transaction_id,
            "reply": reply,
            "risk_context": {"risk_score": risk_score, "risk_level": risk_level},
            "evidence_sources": ["Deterministic Rule Engine", "SHAP Attributions", "Customer Baseline"]
        }

    def _generate_safe_fallback(
        self,
        tx_id: str,
        risk_score: float,
        risk_level: str,
        action: str,
        shap_factors: List[Dict[str, Any]],
        tx_data: Dict[str, Any],
        deviations: Optional[Dict[str, Any]] = None,
        ato_signals: Optional[Dict[str, Any]] = None,
        scam_patterns: Optional[Dict[str, Any]] = None,
        network_graph: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Compliant structured fallback constructed from actual model + SHAP + baseline + scam/network evidence."""
        top_risks = [f for f in shap_factors if f.get("impact") == "RISK_INCREASING"][:4]

        risk_signals = [f"{f['feature'].replace('_', ' ').title()}: {f['explanation']}" for f in top_risks]
        if not risk_signals:
            risk_signals = ["All monitored behavioral metrics are within expected tolerances."]

        dev_list = (deviations or {}).get("deviations_list", [])
        if not dev_list:
            dev_list = ["Transaction values conform to customer's historical operating profile."]

        ato_list = [s["label"] for s in (ato_signals or {}).get("detected_signals", [])]
        scam_list = [p["pattern_name"] for p in (scam_patterns or {}).get("patterns_detected", [])]
        net_list = [i.get("description", i.get("pattern", "Connected entity interaction")) for i in (network_graph or {}).get("insights", [])]

        investigation_questions = [
            f"Verify customer authorization for transaction amount of ৳{tx_data.get('amount', 0):,.2f}.",
            "Confirm if the session originated from an authorized customer device hardware ID.",
            "Verify beneficiary account relationship and transaction justification."
        ]

        if (ato_signals or {}).get("severity") in ["HIGH", "CRITICAL"]:
            investigation_questions.insert(0, "Initiate out-of-band customer verification due to potential account takeover signals.")
        if scam_list:
            investigation_questions.append(f"Investigate potential scam pattern indicators: {', '.join(scam_list[:2])}.")

        summary = (
            f"Transaction {tx_id} evaluated with an XGBoost risk score of {risk_score:.1f}/100 ({risk_level}). "
            f"Primary risk drivers identified via SHAP include {', '.join([f['feature'].replace('_', ' ') for f in top_risks]) or 'none'}. "
            f"In accordance with responsible AI governance, human analyst review is recommended prior to taking consequential action."
        )

        return {
            "transaction_id": tx_id,
            "summary": summary,
            "risk_context": {
                "risk_score": risk_score,
                "risk_level": risk_level
            },
            "risk_signals": risk_signals,
            "key_findings": risk_signals,
            "behavioral_deviations": dev_list,
            "ato_indicators": ato_list,
            "scam_patterns": scam_list,
            "network_observations": net_list,
            "investigation_questions": investigation_questions,
            "evidence_to_review": investigation_questions,
            "recommended_action": action,
            "confidence_note": "Deterministic assessment derived from calibrated XGBoost model, SHAP TreeExplainer attributions, and behavioral telemetry.",
            "human_review_required": risk_score >= 50.0,
            "is_ai_generated": False,
            "notice": "Generated via deterministic fallback based on actual XGBoost, SHAP, behavioral telemetry, and scam/network engines."
        }

    def _generate_fallback_chat_reply(
        self,
        query: str,
        tx_data: Dict[str, Any],
        shap_factors: List[Dict[str, Any]],
        risk_score: float,
        risk_level: str,
        baseline: Optional[Dict[str, Any]] = None,
        ato_signals: Optional[Dict[str, Any]] = None
    ) -> str:
        q = query.lower()
        top_risks = [f for f in shap_factors if f.get("impact") == "RISK_INCREASING"]

        if "why" in q or "flagged" in q:
            reasons = "\n- ".join([f"{f['feature'].replace('_', ' ').title()}: {f['explanation']}" for f in top_risks[:3]])
            return f"Transaction {tx_data.get('transaction_id')} was evaluated at {risk_score:.1f}/100 ({risk_level} Risk) primarily driven by:\n- {reasons}\n\nPlease verify whether the customer initiated this payment."

        elif "normal" in q or "baseline" in q or "compare" in q or "changed" in q:
            avg_amt = (baseline or {}).get("average_amount", 1250.0)
            cur_amt = tx_data.get("amount", 0.0)
            dev = tx_data.get("amount_deviation", cur_amt / max(avg_amt, 1))
            return (
                f"**Behavioral Baseline Comparison:**\n"
                f"- Customer Historical Average: ৳{avg_amt:,.2f}\n"
                f"- Current Transaction: ৳{cur_amt:,.2f} ({dev:.1f}x deviation)\n"
                f"- Device Status: {'NEW / UNREGISTERED' if tx_data.get('is_new_device') else 'Known Device'}\n"
                f"- Beneficiary Status: {'FIRST-TIME RECIPIENT' if tx_data.get('is_new_receiver') else 'Known Recipient'}\n"
                f"- Location: {'GEOGRAPHIC SHIFT' if tx_data.get('location_changed') else 'Standard Location'}\n"
                f"- Velocity: {tx_data.get('transactions_last_1h', 0)} transactions in the past hour."
            )

        elif "takeover" in q or "ato" in q:
            sev = (ato_signals or {}).get("severity", "LOW")
            sig_list = (ato_signals or {}).get("detected_signals", [])
            bullets = "\n- ".join([f"{s['label']}: {s['description']}" for s in sig_list]) or "No acute ATO indicators detected."
            return (
                f"**Account Takeover Intelligence Evaluation ({sev} Severity):**\n"
                f"{(ato_signals or {}).get('headline', 'Potential account takeover indicators detected.')}\n\n"
                f"Detected Indicators:\n- {bullets}\n\n"
                f"Guidance: {(ato_signals or {}).get('action_guidance', 'Prompt customer verification recommended.')}"
            )

        elif "strongest" in q or "factors" in q or "contributed" in q:
            if top_risks:
                top = top_risks[0]
                return f"The strongest risk signal is **{top['feature'].replace('_', ' ').title()}** (+{top['shap_value']:.4f} SHAP impact). Context: {top['explanation']}."
            return "All signals are within standard baseline parameters."

        elif "investigate" in q or "next" in q or "first" in q:
            return (
                "**Recommended Investigation Steps for Analyst:**\n"
                "1. Perform out-of-band verification with the account holder to confirm authorization.\n"
                "2. Review hardware device history to see if the device was recently enrolled.\n"
                "3. Verify recipient account status and check for incoming rapid fund dissipation.\n"
                "4. Check for any prior failed login streaks on the customer account."
            )

        elif "summarize" in q or "case" in q:
            return (
                f"**Case Summary for {tx_data.get('transaction_id')}:**\n"
                f"Assessed Risk Score: {risk_score:.1f}/100 ({risk_level} Risk).\n"
                f"Key Anomaly: ৳{tx_data.get('amount', 0):,.2f} ({tx_data.get('amount_deviation', 1.0):.1f}x normal) sent via {tx_data.get('channel', 'APP')}.\n"
                f"Top Contributing Driver: {top_risks[0]['explanation'] if top_risks else 'Standard activity'}.\n"
                f"Final disposition requires certified human analyst determination."
            )

        return (
            f"Case Context for {tx_data.get('transaction_id')}:\n"
            f"Risk Score: {risk_score:.1f}/100 ({risk_level}). "
            f"Identified {len(top_risks)} elevated risk contributors via SHAP TreeExplainer. "
            f"All final decisions must be approved by the fraud operations team."
        )


gemini_service = GeminiInvestigationService()
