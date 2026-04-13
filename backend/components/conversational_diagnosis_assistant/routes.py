import logging
import re

from flask import jsonify, request

from components.multimodal_image_audio_diagnosis import get_inference_pipeline

from .intent_classifier import get_intent_classifier
from .session_manager import get_session_manager
from .knowledge_base import (
    CAUSE_INFO,
    DISEASE_KNOWLEDGE,
    HEALING_INFO,
    LIFESTYLE_ADVICE,
    SEVERITY_INFO,
    WORSENING_INFO,
)


logger = logging.getLogger(__name__)


def _normalize_confidence_level(confidence: float) -> str:
    if confidence >= 0.70:
        return "high"
    if confidence >= 0.45:
        return "medium"
    if confidence > 0.0:
        return "low"
    return "none"


def _is_message_vague(message: str) -> tuple[bool, list[str], list[str]]:
    """
    Detect if a symptom message is too vague for confident prediction.
    Returns: (is_vague, missing_info, follow_up_questions)
    """
    message_lower = message.lower()
    words = message_lower.split()
    word_count = len(words)

    has_location = any(
        loc in message_lower
        for loc in [
            "face",
            "arm",
            "leg",
            "hand",
            "foot",
            "back",
            "chest",
            "scalp",
            "neck",
            "elbow",
            "knee",
            "finger",
            "toe",
            "body",
            "forehead",
            "cheek",
            "nose",
            "chin",
            "shoulder",
            "stomach",
            "belly",
            "skin",
        ]
    )

    has_appearance = any(
        app in message_lower
        for app in [
            "red",
            "white",
            "scaly",
            "dry",
            "flaky",
            "oily",
            "bumpy",
            "pimple",
            "blister",
            "patch",
            "rash",
            "spot",
            "lesion",
            "sore",
            "swollen",
            "inflamed",
            "cracked",
            "peeling",
            "oozing",
            "crusty",
            "dark",
        ]
    )

    has_sensation = any(
        sens in message_lower
        for sens in [
            "itch",
            "itchy",
            "itching",
            "pain",
            "painful",
            "burning",
            "sting",
            "tender",
            "sore",
            "tingling",
            "numb",
            "hurt",
            "discomfort",
        ]
    )

    has_duration = any(
        dur in message_lower
        for dur in [
            "day",
            "week",
            "month",
            "year",
            "hour",
            "recently",
            "suddenly",
            "chronic",
            "long time",
            "few days",
            "started",
            "began",
            "since",
        ]
    )

    completeness_score = sum([has_location, has_appearance, has_sensation, has_duration]) / 4.0

    missing_info: list[str] = []
    follow_up_questions: list[str] = []

    if not has_location:
        missing_info.append("location")
        follow_up_questions.append("Where is it located?")
    if not has_appearance:
        missing_info.append("appearance")
        follow_up_questions.append("What does it look like?")
    if not has_sensation:
        missing_info.append("sensation")
        follow_up_questions.append("How does it feel?")
    if not has_duration:
        missing_info.append("duration")
        follow_up_questions.append("How long have you had it?")

    is_vague = (word_count < 4) or (completeness_score < 0.5)
    return is_vague, missing_info, follow_up_questions


def _is_valid_input(text: str) -> tuple[bool, str]:
    """
    Detect very low-signal / gibberish input. Returns (is_valid, reason).
    """
    text_lower = text.lower().strip()
    if len(text_lower) < 2:
        return False, "too_short"

    valid_short = {
        "hi",
        "hello",
        "hey",
        "help",
        "bye",
        "thanks",
        "ok",
        "yes",
        "no",
        "thank you",
        "goodbye",
    }
    if text_lower in valid_short:
        return True, "greeting"

    alpha_chars = sum(1 for c in text if c.isalpha() or c in " .,!?")
    if len(text) > 3 and alpha_chars / len(text) < 0.5:
        return False, "gibberish"

    vowels = set("aeiouAEIOU")
    consonants = sum(1 for c in text if c.isalpha() and c not in vowels)
    vowel_count = sum(1 for c in text if c in vowels)
    if len(text) > 4 and vowel_count == 0:
        return False, "gibberish"
    if vowel_count > 0 and consonants / vowel_count > 6:
        return False, "gibberish"
    if re.search(r"(.)\1{4,}", text):
        return False, "gibberish"

    return True, "valid"


def _format_diagnosis_reply(disease: str, confidence: float, confidence_level: str) -> str:
    """
    Format a formal diagnosis response for the user.
    """
    msg = (
        f"Based on your symptoms, this is most consistent with **{disease}**.\n\n"
        f"*   **Severity Confidence**: {confidence_level.capitalize()} ({(confidence * 100):.1f}%)\n"
        "*   **Project Component**: Conversational Assistant\n"
    )

    # Unified Safety Disclaimer
    caveat = (
        "\n\n**⚠️ MEDICAL CAVEAT:** This is a provisional AI assessment for screening and educational purposes. "
        "It is NOT a definitive clinical diagnosis. Please consult a qualified dermatologist "
        "before starting any treatments or if symptoms worsen."
    )

    return msg + caveat


def register_routes(app) -> None:
    """
    Conversational diagnosis assistant routes.
    """

    @app.route("/api/chat", methods=["POST", "OPTIONS"])
    def chat():
        if request.method == "OPTIONS":
            return "", 204

        # Parse payload (JSON default; form-data supported for automation).
        if request.is_json:
            data = request.get_json(force=True, silent=True) or {}
            user_message = str(data.get("message", "")).strip()
            session_id = data.get("session_id")
            image_bytes = None
        else:
            user_message = (request.form.get("message", "") or "").strip()
            session_id = request.form.get("session_id")
            image_file = request.files.get("image") or request.files.get("file")
            image_bytes = image_file.read() if image_file else None

        if not user_message:
            return jsonify(
                {
                    "session_id": session_id,
                    "reply": "Please describe your symptoms so I can help.",
                    "predicted_disease": None,
                    "confidence": 0.0,
                    "confidence_level": "none",
                    "needs_more_info": True,
                    "follow_up_questions": ["What skin symptoms are you experiencing?"],
                    "recommended_treatments": [],
                    "model_status": "online",
                }
            ), 400

        is_valid, _reason = _is_valid_input(user_message)
        if not is_valid:
            return jsonify(
                {
                    "session_id": session_id,
                    "reply": (
                        "I didn't quite understand that. Please describe your symptoms with: "
                        "location, appearance (red, scaly, bumpy), and sensation (itchy, painful)."
                    ),
                    "predicted_disease": None,
                    "confidence": 0.0,
                    "confidence_level": "none",
                    "needs_more_info": True,
                    "follow_up_questions": ["What skin symptoms are you experiencing?"],
                    "recommended_treatments": [],
                    "model_status": "online",
                }
            )

        # Intent + session.
        try:
            intent_clf = get_intent_classifier()
            intent, _intent_conf = intent_clf.predict(user_message)
        except Exception as exc:
            logger.warning("Intent classifier error: %s", exc)
            intent = "symptom_description"

        session_mgr = get_session_manager()
        session = session_mgr.get_session(session_id) if session_id else None
        if not session:
            session_id = session_mgr.create_session(session_id)
            session = session_mgr.get_session(session_id)

        session.add_message("user", user_message)

        pipe = None
        automated_result = None
        if image_bytes:
            try:
                pipe = get_inference_pipeline()
                automated_result = pipe.smart_predict(user_message, image_bytes)
                intent = "symptom_description"
            except Exception as exc:
                logger.warning("Chat automated scan failed: %s", exc)

        response: dict = {
            "session_id": session_id,
            "predicted_disease": None,
            "confidence": 0.0,
            "confidence_level": "none",
            "needs_more_info": False,
            "follow_up_questions": [],
            "recommended_treatments": [],
            "reply": "",
            "model_status": "online",
            "automated_scan": automated_result,
        }

        # Primary diagnosis path.
        if intent == "symptom_description":
            try:
                if automated_result:
                    diag = automated_result.get("diagnosis", {}) or {}
                    disease = diag.get("disease")
                    confidence = float(diag.get("confidence", 0.0))
                else:
                    pipe = pipe or get_inference_pipeline()
                    pred = pipe.predict_disease(user_message)
                    disease = pred.get("disease")
                    confidence = float(pred.get("confidence", 0.0))

                is_vague, missing_info, vague_followup = _is_message_vague(user_message)
                confidence_level = _normalize_confidence_level(confidence)

                # Update session memory.
                if disease:
                    session_mgr.update_session(
                        session_id,
                        last_predicted_disease=disease,
                        last_confidence=confidence,
                    )

                if is_vague and len(missing_info) >= 3 and not automated_result:
                    response.update(
                        {
                            "reply": (
                                "I can help, but I need a bit more detail: where is it, what does it look like, "
                                "how does it feel, and how long has it been there?"
                            ),
                            "needs_more_info": True,
                            "follow_up_questions": vague_followup[:3],
                        }
                    )
                else:
                    if confidence_level == "high":
                        reply = _format_diagnosis_reply(disease, confidence, confidence_level) + "\n\nWould you like treatments, causes/triggers, or daily-care tips?"
                        needs_more_info = False
                        follow_up = []
                        treatments = []
                    elif confidence_level == "medium":
                        reply = (
                            f"This may be **{disease}**, but I need a bit more detail to be sure.\n\n"
                            "Tell me: where is it located, and how long has it been there?"
                        )
                        needs_more_info = True
                        follow_up = vague_followup[:2] if is_vague else []
                        treatments = []
                    else:
                        reply = (
                            f"This could be **{disease}**, but confidence is low.\n\n"
                            "If it is worsening, spreading, painful, or infected, please see a dermatologist."
                        )
                        needs_more_info = bool(is_vague)
                        follow_up = vague_followup[:2] if is_vague else []
                        treatments = []

                    response.update(
                        {
                            "predicted_disease": disease,
                            "confidence": float(confidence),
                            "confidence_level": confidence_level,
                            "needs_more_info": needs_more_info,
                            "follow_up_questions": follow_up,
                            "recommended_treatments": treatments,
                            "reply": reply,
                            "model_status": "online",
                        }
                    )

            except Exception as exc:
                logger.exception("Chat prediction failed")
                response.update(
                    {
                        "reply": f"Prediction error: {str(exc)[:120]}",
                        "needs_more_info": True,
                        "follow_up_questions": ["Could you describe your symptoms again?"],
                        "model_status": "error",
                    }
                )

        # Follow-ups based on session disease.
        else:
            disease = getattr(session, "last_predicted_disease", None)
            confidence = float(getattr(session, "last_confidence", 0.0) or 0.0)

            if not disease:
                response.update(
                    {
                        "reply": (
                            "I can answer questions about severity, causes, and treatments, but first describe your symptoms."
                        ),
                        "needs_more_info": True,
                        "follow_up_questions": ["What symptoms are you experiencing?"],
                    }
                )
                session.add_message("assistant", response["reply"])
                return jsonify(response)

            lowered = user_message.lower()
            if "treat" in lowered or "medicine" in lowered or "cream" in lowered:
                try:
                    pipe = pipe or get_inference_pipeline()
                    treatments = pipe._get_treatments(disease)  # type: ignore[attr-defined]
                except Exception:
                    treatments = []
                response.update(
                    {
                        "predicted_disease": disease,
                        "confidence": confidence,
                        "confidence_level": _normalize_confidence_level(confidence),
                        "recommended_treatments": treatments,
                        "reply": f"Here are common treatments for **{disease}**. If symptoms persist, see a dermatologist.",
                    }
                )
            elif any(k in lowered for k in ["cause", "trigger", "contagious"]):
                info = CAUSE_INFO.get(disease)
                if info:
                    response.update(
                        {
                            "predicted_disease": disease,
                            "confidence": confidence,
                            "confidence_level": _normalize_confidence_level(confidence),
                            "reply": (
                                f"**Causes/triggers for {disease}:**\n\n"
                                + "\n".join([f"- {c}" for c in info.get("main_causes", [])][:6])
                                + "\n\n"
                                + "\n".join([f"- {t}" for t in info.get("triggers", [])][:6])
                            ),
                        }
                    )
                else:
                    response["reply"] = f"I don't have cause/trigger details for {disease} yet."
            elif "sever" in lowered or "serious" in lowered or "danger" in lowered:
                info = SEVERITY_INFO.get(disease)
                if info:
                    response.update(
                        {
                            "predicted_disease": disease,
                            "confidence": confidence,
                            "confidence_level": _normalize_confidence_level(confidence),
                            "reply": (
                                f"**Severity for {disease}:** {info.get('level')}\n\n"
                                + (info.get("description") or "")
                                + "\n\nWarning signs:\n"
                                + "\n".join([f"- {s}" for s in info.get("warning_signs", [])][:6])
                            ),
                        }
                    )
                else:
                    response["reply"] = f"I don't have severity details for {disease} yet."
            elif "advice" in lowered or "tip" in lowered or "avoid" in lowered:
                info = LIFESTYLE_ADVICE.get(disease)
                if info:
                    response.update(
                        {
                            "predicted_disease": disease,
                            "confidence": confidence,
                            "confidence_level": _normalize_confidence_level(confidence),
                            "reply": (
                                f"**Lifestyle tips for {disease}:**\n\nDo:\n"
                                + "\n".join([f"- {t}" for t in info.get("do", [])][:6])
                                + "\n\nAvoid:\n"
                                + "\n".join([f"- {t}" for t in info.get("avoid", [])][:6])
                            ),
                        }
                    )
                else:
                    response["reply"] = f"I don't have lifestyle tips for {disease} yet."
            elif "heal" in lowered or "timeline" in lowered:
                info = HEALING_INFO.get(disease)
                if info:
                    response.update(
                        {
                            "predicted_disease": disease,
                            "confidence": confidence,
                            "confidence_level": _normalize_confidence_level(confidence),
                            "reply": (
                                f"**Healing time for {disease}:** {info.get('timeline')}\n\n"
                                + "\n".join([f"- {s}" for s in info.get("signs_improving", [])][:6])
                            ),
                        }
                    )
                else:
                    response["reply"] = f"I don't have healing timeline details for {disease} yet."
            elif "worse" in lowered or "spreading" in lowered or "warning" in lowered:
                info = WORSENING_INFO.get(disease)
                if info:
                    response.update(
                        {
                            "predicted_disease": disease,
                            "confidence": confidence,
                            "confidence_level": _normalize_confidence_level(confidence),
                            "reply": (
                                f"**Worsening warning signs for {disease}:**\n\n"
                                + "\n".join([f"- {s}" for s in info.get("warning_signs", [])][:6])
                                + "\n\n"
                                + (info.get("when_urgent") or "")
                            ),
                        }
                    )
                else:
                    response["reply"] = f"I don't have worsening details for {disease} yet."
            else:
                info = DISEASE_KNOWLEDGE.get(disease)
                if info:
                    response.update(
                        {
                            "predicted_disease": disease,
                            "confidence": confidence,
                            "confidence_level": _normalize_confidence_level(confidence),
                            "reply": (
                                f"**{disease}**\n\n"
                                f"{info.get('overview','')}\n\n"
                                f"Symptoms: {info.get('symptoms','')}\n\n"
                                f"Treatments: {info.get('treatments','')}"
                            ),
                        }
                    )
                else:
                    response["reply"] = (
                        f"What would you like to know about **{disease}**? You can ask about causes, treatments, or severity."
                    )

        session.add_message("assistant", response.get("reply", ""))
        return jsonify(response)

