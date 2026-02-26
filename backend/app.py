"""
SkinAI Flask Backend
=====================
Endpoints:
  GET  /api/health          – health check
  GET  /api/status          – model availability
  POST /api/chat            – conversational AI diagnosis (text, session memory)
  POST /api/analyze         – image-only diagnosis (ResNet-18)
  POST /api/analyze-fused   – multimodal diagnosis (image + text, fusion)
  POST /api/analyze-skin-care  – skin care advice (placeholder)
  GET  /api/history         – progress history (mock)
  GET  /api/stats           – symptom stats (mock)
  POST /api/progress        – log new progress entry (mock)
"""

import datetime
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from flask import Flask, jsonify, request
from flask_cors import CORS

# ── Configuration from environment ────────────────────────────────────────────
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')

DEBUG = FLASK_DEBUG  # verbose logging

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))

from inference import get_inference_pipeline
from inference.config import get_model_status

app = Flask(__name__)
CORS(
    app,
    resources={r"/api/*": {"origins": "*"}},
    supports_credentials=False,
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "OPTIONS"],
)

# ── Boot inference pipeline ───────────────────────────────────────────────────
try:
    inference_pipeline = get_inference_pipeline()
    print("✅ Inference pipeline ready")
except Exception as exc:
    print(f"❌ Failed to load inference pipeline: {exc}")
    inference_pipeline = None

# ── Mock data (history / stats) ───────────────────────────────────────────────
MOCK_HISTORY = [
    {"week": "Week 1", "date": "2025-11-01", "image_url": "assets/images/week1.png",
     "status": "Bad",      "score": 30,
     "metrics": {"redness": 90, "inflammation": 85, "scaling": 70, "texture": 60}},
    {"week": "Week 2", "date": "2025-11-08", "image_url": "assets/images/week2.png",
     "status": "Poor",     "score": 45,
     "metrics": {"redness": 80, "inflammation": 75, "scaling": 65, "texture": 65}},
    {"week": "Week 3", "date": "2025-11-15", "image_url": "assets/images/week3.png",
     "status": "Improving","score": 60,
     "metrics": {"redness": 60, "inflammation": 55, "scaling": 50, "texture": 70}},
    {"week": "Week 4", "date": "2025-11-22", "image_url": "assets/images/week4.png",
     "status": "Better",   "score": 75,
     "metrics": {"redness": 40, "inflammation": 35, "scaling": 30, "texture": 80}},
    {"week": "Week 5", "date": "2025-11-29", "image_url": "assets/images/week5.png",
     "status": "Good",     "score": 85,
     "metrics": {"redness": 20, "inflammation": 15, "scaling": 10, "texture": 90}},
    {"week": "Week 6", "date": "2025-12-06", "image_url": "assets/images/week6.png",
     "status": "Excellent","score": 95,
     "metrics": {"redness": 5,  "inflammation": 5,  "scaling": 0,  "texture": 95}},
]

MOCK_STATS = {
    "labels": ["Redness", "Itch", "Dryness", "Scaling"],
    "values": [20, 40, 25, 15],
}


# ── Health / status ───────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return jsonify({
        "ok":        True,
        "service":   "skinai-backend",
        "timestamp": datetime.datetime.now().isoformat(),
    })


@app.get("/api/status")
def status():
    return jsonify({
        "service":              "online",
        "models":               get_model_status(),
        "inference_available":  inference_pipeline is not None,
        "timestamp":            datetime.datetime.now().isoformat(),
    })


# ── Image analysis (ResNet-18) ────────────────────────────────────────────────

@app.route("/api/analyze", methods=["POST", "OPTIONS"])
def analyze():
    """
    Image-only skin disease diagnosis using ResNet-18.
    Accepts multipart/form-data with field 'image', OR falls back to mock data.
    """
    if request.method == "OPTIONS":
        return "", 204

    if inference_pipeline is None:
        return jsonify({"error": "Inference pipeline unavailable"}), 503

    # Try to read uploaded image bytes
    image_file = request.files.get("image") or request.files.get("file")
    if image_file:
        image_bytes = image_file.read()
        result = inference_pipeline.predict_from_image(image_bytes)
    else:
        # No image uploaded → use text fallback or return mock
        result = {
            "disease":    "Eczema",
            "confidence": 0.85,
            "treatments": [
                {"medicine": "Topical Corticosteroids", "advice": "Apply 1–2× daily"},
                {"medicine": "Emollients",              "advice": "Apply after bathing"},
            ],
            "model_used": "mock",
        }

    disease    = result.get("disease", "Unknown")
    confidence = result.get("confidence", 0.0)
    treatments = result.get("treatments", [])

    return jsonify({
        "prediction": disease,
        "confidence": confidence,
        "symptoms":   ["Redness", "Itching", "Dryness"],
        "triggers":   ["Stress", "Dry Air", "Soap"],
        "routine": {
            "morning":   "Gentle Cleanser, Moisturizer",
            "night":     "Topical treatment as prescribed",
            "treatment": f"Apply {treatments[0]['medicine'] if treatments else 'prescribed ointment'} as directed.",
        },
        "warnings":    ["If symptoms worsen or spread, see a dermatologist."],
        "treatments":  treatments,
        "model_used":  result.get("model_used", "resnet"),
    })


@app.route("/api/analyze-fused", methods=["POST", "OPTIONS"])
def analyze_fused():
    """
    Multimodal diagnosis: image (ResNet-18) + text (DistilBERT) → fused result.
    Accepts multipart/form-data: 'image' file + optional 'text' field.
    """
    if request.method == "OPTIONS":
        return "", 204

    if inference_pipeline is None:
        return jsonify({"error": "Inference pipeline unavailable"}), 503

    image_file = request.files.get("image") or request.files.get("file")
    text = request.form.get("text", "skin condition")

    if not image_file:
        return jsonify({"error": "No image provided"}), 400

    image_bytes = image_file.read()
    result = inference_pipeline.predict_fused(text, image_bytes)

    return jsonify({
        "disease":          result["disease"],
        "confidence":       result["confidence"],
        "image_disease":    result["image_disease"],
        "image_confidence": result["image_confidence"],
        "text_disease":     result["text_disease"],
        "text_confidence":  result["text_confidence"],
        "treatments":       result["treatments"],
        "model_used":       result["model_used"],
    })


@app.route("/api/analyze-skin-care", methods=["POST", "OPTIONS"])
def analyze_skin_care():
    if request.method == "OPTIONS":
        return "", 204
    return jsonify({
        "skin_type":  "Combination",
        "skin_color": "Fair - Medium",
        "recommendations": [
            "Use a gentle foaming cleanser.",
            "Apply a lightweight, oil-free moisturizer.",
            "Use sunscreen with SPF 30+ daily.",
            "Exfoliate 1–2 times a week with a mild chemical exfoliant.",
        ],
    })


# ── Vague Message Detection ───────────────────────────────────────────────────

def is_message_vague(message: str) -> tuple:
    """
    Detect if a symptom message is too vague for confident prediction.
    
    Returns: (is_vague: bool, missing_info: list[str], follow_up_questions: list[str])
    """
    message_lower = message.lower()
    words = message_lower.split()
    word_count = len(words)
    
    # Key symptom indicators
    has_location = any(loc in message_lower for loc in [
        'face', 'arm', 'leg', 'hand', 'foot', 'back', 'chest', 'scalp', 
        'neck', 'elbow', 'knee', 'finger', 'toe', 'body', 'forehead',
        'cheek', 'nose', 'chin', 'shoulder', 'stomach', 'belly', 'skin'
    ])
    
    has_appearance = any(app in message_lower for app in [
        'red', 'white', 'scaly', 'dry', 'flaky', 'oily', 'bumpy', 'pimple',
        'blister', 'patch', 'rash', 'spot', 'lesion', 'sore', 'swollen',
        'inflamed', 'cracked', 'peeling', 'oozing', 'crusty', 'dark'
    ])
    
    has_sensation = any(sens in message_lower for sens in [
        'itch', 'itchy', 'itching', 'pain', 'painful', 'burning', 'sting',
        'tender', 'sore', 'tingling', 'numb', 'hurt', 'discomfort'
    ])
    
    has_duration = any(dur in message_lower for dur in [
        'day', 'week', 'month', 'year', 'hour', 'recently', 'suddenly',
        'chronic', 'long time', 'few days', 'started', 'began', 'since'
    ])
    
    # Calculate completeness score
    info_present = [has_location, has_appearance, has_sensation, has_duration]
    completeness_score = sum(info_present) / 4.0
    
    # Build missing info list
    missing_info = []
    follow_up_questions = []
    
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
    
    # Message is vague if: too short OR missing 2+ key details
    is_vague = (word_count < 4) or (completeness_score < 0.5)
    
    return is_vague, missing_info, follow_up_questions


# ── Chat endpoint (DistilBERT + session memory + intent routing) ──────────────

@app.route("/api/chat", methods=["POST", "OPTIONS"])
def chat():
    """
    Production-grade conversational AI chat endpoint.
    Implements xAI-like behavior: intent routing, session memory, DistilBERT prediction.

    Request body (JSON):
    {
        "session_id": "optional-uuid",
        "message"   : "I have itchy red patches on my arms"
    }

    Response (JSON):
    {
        "session_id"           : str,
        "reply"                : str,
        "predicted_disease"    : str | null,
        "confidence"           : float,
        "confidence_level"     : "high"|"medium"|"low"|"none",
        "needs_more_info"      : bool,
        "follow_up_questions"  : list[str],
        "recommended_treatments": list[{medicine, advice}],
        "model_status"         : str,
    }
    """
    if request.method == "OPTIONS":
        return "", 204

    try:
        from inference.intent_classifier import get_intent_classifier
        from inference.session_manager import get_session_manager

        data         = request.get_json(force=True, silent=True) or {}
        user_message = data.get("message", "").strip()
        session_id   = data.get("session_id")

        # ── Empty message guard ───────────────────────────────────────────────
        if not user_message:
            return jsonify({
                "session_id":           session_id,
                "reply":                "Please describe your symptoms so I can help diagnose your condition.",
                "predicted_disease":    None,
                "confidence":           0.0,
                "confidence_level":     "none",
                "needs_more_info":      True,
                "follow_up_questions":  [],
                "recommended_treatments": [],
                "model_status":         "online",
            }), 400

        # ── Input validation (detect gibberish/non-meaningful text) ───────────
        def is_valid_input(text: str) -> tuple[bool, str]:
            """
            Validate user input - detect gibberish, random characters, etc.
            Returns (is_valid, reason)
            """
            import re
            
            text_lower = text.lower().strip()
            
            # Check for minimum meaningful content
            if len(text) < 2:
                return False, "too_short"
            
            # Common greetings and valid short phrases (allow these)
            VALID_SHORT = {'hi', 'hello', 'hey', 'help', 'bye', 'thanks', 'ok', 'yes', 'no', 'thank you', 'goodbye'}
            if text_lower in VALID_SHORT:
                return True, "greeting"
            
            # Check if mostly alphabetic or common punctuation
            alpha_chars = sum(1 for c in text if c.isalpha() or c in ' .,!?')
            if len(text) > 3 and alpha_chars / len(text) < 0.5:
                return False, "gibberish"
            
            # Detect random character sequences (no vowels, too many consonants)
            vowels = set('aeiouAEIOU')
            consonants = sum(1 for c in text if c.isalpha() and c not in vowels)
            vowel_count = sum(1 for c in text if c in vowels)
            
            # If text is longer than 4 chars and has no vowels = likely gibberish
            if len(text) > 4 and vowel_count == 0:
                return False, "gibberish"
            
            # If consonant to vowel ratio is too high (>5:1) = likely gibberish
            if vowel_count > 0 and consonants / vowel_count > 6:
                return False, "gibberish"
            
            # Check for repeating characters (like "aaaaaaa")
            if re.search(r'(.)\1{4,}', text):
                return False, "gibberish"
            
            # Check for random uppercase mixed with lowercase (like "fgDFDTYAFscYHAG")
            if len(text) > 5:
                upper_count = sum(1 for c in text if c.isupper())
                lower_count = sum(1 for c in text if c.islower())
                if upper_count > 2 and lower_count > 2 and 0.3 < upper_count / len(text) < 0.7:
                    # Random mix of upper/lower - likely gibberish
                    if not any(word in text.lower() for word in ['i', 'my', 'is', 'have', 'the', 'skin', 'red', 'itchy']):
                        return False, "gibberish"
            
            return True, "valid"
        
        is_valid, validation_reason = is_valid_input(user_message)
        
        if not is_valid:
            return jsonify({
                "session_id":           session_id,
                "reply":                "I didn't quite understand that. Could you please describe your skin symptoms in more detail? For example: location, appearance (red, scaly, bumpy), and any sensations (itchy, painful).",
                "predicted_disease":    None,
                "confidence":           0.0,
                "confidence_level":     "none",
                "needs_more_info":      True,
                "follow_up_questions":  ["What skin symptoms are you experiencing?"],
                "recommended_treatments": [],
                "model_status":         "online",
            })

        # ── Intent classification ─────────────────────────────────────────────
        try:
            intent_clf = get_intent_classifier()
            intent, intent_conf = intent_clf.predict(user_message)
        except Exception as exc:
            if DEBUG:
                print(f"Intent classifier error: {exc}")
            intent, intent_conf = "symptom_description", 0.5

        # ── Session management ────────────────────────────────────────────────
        session_mgr = get_session_manager()
        session = session_mgr.get_session(session_id) if session_id else None
        if not session:
            session_id = session_mgr.create_session(session_id)
            session = session_mgr.get_session(session_id)

        # Log user message
        session.add_message("user", user_message)

        # ── Smart intent override rules ───────────────────────────────────────
        # Rule 1: Short follow-up with existing high-confidence prediction
        #         → treat as clarification, not re-prediction
        if (
            session.last_predicted_disease is not None
            and len(user_message.split()) <= 8
            and intent == "symptom_description"
            and session.last_confidence >= 0.60
        ):
            intent = "clarify_existing"

        # Rule 2: Treatment-related keywords + existing prediction
        #         → switch to ask_treatment (but NOT if already a specific intent)
        TREATMENT_KEYWORDS = [
            "treatment", "apply", "use the", "dosage", "dose", "how should i apply",
            "medicine", "ointment", "cream", "frequency", "how many times",
            "per day", "how often", "for how long", "times a day",
            "remedy", "cure", "fix it", "emollient", "lotion", "medication",
        ]
        
        # Exclude these phrases from treatment detection
        EXCLUDE_TREATMENT = ['what can you do', 'how can you help', 'what do you do']
        
        # Only override to treatment if intent is not already specific
        NON_OVERRIDE_INTENTS = ['ask_severity', 'ask_advice', 'ask_causes', 'ask_about_disease', 'other']
        
        lowered = user_message.lower()
        is_excluded = any(ex in lowered for ex in EXCLUDE_TREATMENT)
        
        if session.last_predicted_disease and intent not in NON_OVERRIDE_INTENTS and not is_excluded:
            if any(k in lowered for k in TREATMENT_KEYWORDS):
                intent = "ask_treatment"
        
        # Rule 3: Severity-related keywords → ask_severity
        SEVERITY_KEYWORDS = [
            'serious', 'dangerous', 'worried', 'severe', 'bad', 'worse',
            'emergency', 'urgent', 'hospital', 'harm', 'safe', 'normal'
        ]
        if session.last_predicted_disease:
            lowered = user_message.lower()
            if any(k in lowered for k in SEVERITY_KEYWORDS) and intent == 'symptom_description':
                intent = "ask_severity"
        
        # Rule 4: Advice-related keywords → ask_advice
        ADVICE_KEYWORDS = [
            'else can i', 'what else', 'tips', 'advice', 'lifestyle',
            'home remedy', 'home remedies', 'prevent', 'avoid', 'help my skin',
            'daily', 'routine', 'foods', 'diet'
        ]
        if session.last_predicted_disease:
            lowered = user_message.lower()
            if any(k in lowered for k in ADVICE_KEYWORDS) and intent not in NON_OVERRIDE_INTENTS:
                intent = "ask_advice"
        
        # Rule 5: Cause-related keywords → ask_causes
        CAUSE_KEYWORDS = [
            'cause', 'causes', 'why do i', 'how did i get', 'trigger',
            'contagious', 'spread', 'genetic', 'hereditary', 'started'
        ]
        if session.last_predicted_disease:
            lowered = user_message.lower()
            if any(k in lowered for k in CAUSE_KEYWORDS) and intent not in NON_OVERRIDE_INTENTS:
                intent = "ask_causes"

        # ── Build response skeleton ───────────────────────────────────────────
        response: dict = {
            "session_id":            session_id,
            "predicted_disease":     None,
            "confidence":            0.0,
            "confidence_level":      "none",
            "needs_more_info":       False,
            "follow_up_questions":   [],
            "recommended_treatments": [],
            "reply":                 "",
            "model_status":          "online",
        }

        # ── Intent routing ────────────────────────────────────────────────────

        if intent == "symptom_description":
            # ──────────────────────────────────────────────────────────────────
            # First check if the message is too vague
            # ──────────────────────────────────────────────────────────────────
            is_vague, missing_info, vague_followup = is_message_vague(user_message)
            
            if is_vague and len(missing_info) >= 3:
                # Very vague message — need more info before prediction
                response.update({
                    "predicted_disease":     None,
                    "confidence":            0.0,
                    "confidence_level":      "none",
                    "needs_more_info":       True,
                    "follow_up_questions":   [],
                    "recommended_treatments": [],
                    "reply": (
                        "I'd like to help! Could you tell me a bit more about what you're experiencing?\n\n"
                        "For example, what does it look like, how does it feel, and where is it on your body?"
                    ),
                    "model_status":          "online",
                })
            elif inference_pipeline:
                # Run DistilBERT disease prediction
                try:
                    result     = inference_pipeline.predict_disease(user_message)
                    disease    = result.get("disease")
                    confidence = result.get("confidence", 0.0)
                    treatments = result.get("treatments", [])
                    followup   = result.get("followup_questions", [])
                    model_used = result.get("model_used", "unknown")

                    # Boost follow-up with specific missing info
                    if is_vague and vague_followup:
                        followup = vague_followup[:2] + followup[:1]

                    # Update session memory
                    session_mgr.update_session(
                        session_id,
                        last_predicted_disease=disease,
                        last_confidence=confidence,
                    )

                    # Confidence tier
                    if confidence >= 0.70:
                        confidence_level = "high"
                        certainty_text   = "Based on your symptoms, I believe this is"
                    elif confidence >= 0.45:
                        confidence_level = "medium"
                        certainty_text   = "Based on your description, this appears to be"
                    else:
                        confidence_level = "low"
                        certainty_text   = "Your symptoms suggest this might be"

                    # Compose reply - conversational style like ChatGPT
                    # Don't dump treatments immediately, let user ask
                    if confidence >= 0.70:
                        reply = (
                            f"\n\n{certainty_text} **{disease}**.\n\n"
                            f"This is a common skin condition that's typically manageable with proper care.\n\n"
                            f"Would you like to know about treatments, causes, or tips for managing it?"
                        )
                        needs_more_info = False
                        # Clear treatments from initial response - user should ask
                        treatments = []
                    elif confidence >= 0.45:
                        reply = (
                            f"\n\n{certainty_text} **{disease}**.\n\n"
                            f"Could you tell me a bit more to help me give you better guidance? "
                            f"How long have you had it and how does it feel?"
                        )
                        needs_more_info = True
                        treatments = []
                    else:
                        # Low confidence - but still show the prediction!
                        # Only ask for more info if the message was actually vague
                        if is_vague and missing_info:
                            # Message is actually vague - ask for more details
                            reply = (
                                f"\n\nBased on what you've shared, this could be **{disease}**.\n\n"
                                f"Could you tell me more about what it looks like and how it feels? "
                                f"That will help me give you better guidance."
                            )
                            followup = []
                            needs_more_info = True
                            treatments = []
                        else:
                            # Message has details, but model confidence is low
                            reply = (
                                f"\n\n{certainty_text} **{disease}**.\n\n"
                                f"This condition can sometimes overlap with other skin conditions, "
                                f"so I'd recommend consulting a dermatologist for a definitive diagnosis.\n\n"
                                f"Would you like to know about treatments, causes, or tips for managing it?"
                            )
                            followup = []
                            needs_more_info = False
                            treatments = []

                    response.update({
                        "predicted_disease":      disease,
                        "confidence":             float(confidence),
                        "confidence_level":       confidence_level,
                        "recommended_treatments": treatments,
                        "follow_up_questions":    followup if needs_more_info else [],
                        "needs_more_info":        needs_more_info,
                        "reply":                  reply,
                        "model_status":           model_used,
                    })

                except Exception as exc:
                    if DEBUG:
                        import traceback; traceback.print_exc()
                    response["reply"] = f"Prediction error: {str(exc)[:100]}"
            else:
                response["reply"] = "The AI service is temporarily unavailable. Please try again later."

        elif intent == "clarify_existing":
            # ──────────────────────────────────────────────────────────────────
            # User added detail to an already-predicted disease
            # ──────────────────────────────────────────────────────────────────
            disease    = session.last_predicted_disease
            treatments = []
            if inference_pipeline and disease:
                treatments = inference_pipeline._get_treatments(disease)

            response.update({
                "predicted_disease":      disease,
                "confidence":             session.last_confidence,
                "confidence_level":       "high" if session.last_confidence >= 0.70 else "medium",
                "recommended_treatments": treatments,
                "needs_more_info":        False,
                "follow_up_questions":    [],
                "reply": (
                    f"Thanks for the additional details. Based on everything you've shared, "
                    f"I still believe this is **{disease}**.\n\n"
                    f"Is there anything specific you'd like to know?\n"
                    f"• Treatment options\n"
                    f"• Causes and triggers\n"
                    f"• Lifestyle advice\n\n"
                    f"If you notice new symptoms like blistering, rapid spreading, or fever, "
                    f"please consult a dermatologist immediately."
                ),
            })

        elif intent == "ask_treatment":
            # ──────────────────────────────────────────────────────────────────
            # "What is the treatment?" — use session memory, don't re-predict
            # ──────────────────────────────────────────────────────────────────
            disease = session.last_predicted_disease

            if disease and inference_pipeline:
                treatments = inference_pipeline._get_treatments(disease)

                usage_guidance = (
                    "Apply a thin layer to affected areas 2–3 times daily. "
                    "Best applied within a few minutes after washing when skin is still slightly damp."
                )

                meds_text = "\n".join(
                    [f"  • **{t['medicine']}** — {t['advice']}" for t in treatments[:4]]
                ) or "No specific treatments in my database."

                response.update({
                    "predicted_disease":      disease,
                    "confidence":             session.last_confidence,
                    "confidence_level":       "high" if session.last_confidence >= 0.70 else "medium",
                    "recommended_treatments": treatments,
                    "reply": (
                        f"\n\nHere are the recommended treatments for **{disease}**:\n\n"
                        f"{meds_text}\n\n"
                        f"💡 **Application tip:** {usage_guidance}\n\n"
                        f"For best results, be consistent with your treatment routine. "
                        f"If you don't see improvement within 2 weeks, please see a dermatologist.\n\n"
                        f"Would you like to know about causes or lifestyle tips?"
                    ),
                })
            else:
                response.update({
                    "reply": (
                        "I'd be happy to suggest treatments, but I need to understand your symptoms first.\n\n"
                        "Could you describe what you're experiencing? For example:\n"
                        "• What does it look like? (red, scaly, bumpy)\n"
                        "• How does it feel? (itchy, painful)\n"
                        "• Where is it located?"
                    ),
                    "follow_up_questions": ["What symptoms are you experiencing?"],
                    "needs_more_info":     True,
                })

        elif intent == "ask_severity":
            # ──────────────────────────────────────────────────────────────────
            # "Is this serious?" — provide condition-specific severity info
            # ──────────────────────────────────────────────────────────────────
            disease = session.last_predicted_disease
            
            SEVERITY_INFO = {
                "Eczema": {
                    "level": "Mild to Moderate",
                    "description": "Eczema is generally not dangerous but can significantly impact quality of life.",
                    "warning_signs": ["Severe cracking or bleeding", "Signs of infection (pus, fever)", "Spreading rapidly", "Affecting sleep or daily activities"],
                    "outlook": "Most cases are manageable with proper treatment. Flare-ups come and go, but symptoms can be controlled."
                },
                "Dermatitis": {
                    "level": "Usually Mild",
                    "description": "Contact dermatitis is typically not serious and resolves once the irritant is removed.",
                    "warning_signs": ["Widespread rash covering large areas", "Difficulty breathing (allergic reaction)", "Blistering or oozing", "No improvement after 2 weeks"],
                    "outlook": "Excellent prognosis. Identifying and avoiding triggers prevents recurrence."
                },
                "Psoriasis": {
                    "level": "Chronic but Manageable",
                    "description": "Psoriasis is a chronic autoimmune condition. While not life-threatening, it requires ongoing management.",
                    "warning_signs": ["Joint pain or stiffness (psoriatic arthritis)", "Plaques covering >10% of body", "Pustular or erythrodermic flare-ups", "Severe nail changes"],
                    "outlook": "Not curable but highly treatable. Many people achieve significant symptom control with modern treatments."
                },
                "Acne": {
                    "level": "Mild to Moderate",
                    "description": "Acne is very common and not dangerous, though severe cases can cause scarring.",
                    "warning_signs": ["Deep, painful cysts or nodules", "Scarring occurring", "No response to over-the-counter treatments", "Significant emotional distress"],
                    "outlook": "Most acne clears with treatment. Early intervention prevents scarring."
                },
                "Urticaria": {
                    "level": "Usually Mild (Can Be Urgent)",
                    "description": "Hives are typically harmless and temporary, but watch for signs of anaphylaxis.",
                    "warning_signs": ["Difficulty breathing or swallowing", "Swelling of face, lips, or throat", "Dizziness or feeling faint", "Rapid heartbeat"],
                    "outlook": "Acute hives usually resolve within 24-48 hours. Chronic cases may need investigation."
                }
            }
            
            if disease and disease in SEVERITY_INFO:
                info = SEVERITY_INFO[disease]
                response.update({
                    "predicted_disease": disease,
                    "confidence": session.last_confidence,
                    "confidence_level": "high" if session.last_confidence >= 0.70 else "medium",
                    "reply": (
                        f"\n\n**About {disease} Severity:**\n\n"
                        f"📊 **Typical Severity:** {info['level']}\n\n"
                        f"{info['description']}\n\n"
                        f"🚨 **Seek medical attention if you notice:**\n"
                        + "\n".join([f"  • {sign}" for sign in info['warning_signs']]) +
                        f"\n\n✨ **Outlook:** {info['outlook']}\n\n"
                        f"Is there anything else you'd like to know about {disease}?"
                    ),
                })
            else:
                response.update({
                    "reply": (
                        "⚠️ **Let's follow the proper workflow!**\n\n"
                        "I can't assess severity without knowing your condition first.\n\n"
                        "**Step 1:** Describe your symptoms (e.g., 'I have flaky, scaling patches')\n"
                        "**Step 2:** Then I can assess how serious your condition is\n\n"
                        "What skin symptoms are you experiencing?"
                    ),
                    "needs_more_info": True,
                    "follow_up_questions": ["What skin symptoms are you experiencing?"]
                })

        elif intent == "ask_advice":
            # ──────────────────────────────────────────────────────────────────
            # "What else can I do?" — lifestyle and self-care advice
            # ──────────────────────────────────────────────────────────────────
            disease = session.last_predicted_disease
            
            LIFESTYLE_ADVICE = {
                "Eczema": {
                    "do": ["Moisturize immediately after bathing", "Use fragrance-free products", "Wear soft, breathable fabrics (cotton)", "Keep nails short to reduce scratching damage", "Use a humidifier in dry weather"],
                    "avoid": ["Hot showers (use lukewarm water)", "Harsh soaps and detergents", "Wool and synthetic fabrics", "Known triggers (dust, certain foods)", "Scratching when itchy"],
                    "home_remedies": ["Oatmeal baths can soothe itching", "Coconut oil as a natural moisturizer", "Cool compresses for flare-ups", "Wet wrap therapy for severe patches"]
                },
                "Dermatitis": {
                    "do": ["Identify and remove the irritant/allergen", "Keep the area clean and dry", "Apply cool compresses", "Use hypoallergenic products", "Wear protective gloves when cleaning"],
                    "avoid": ["Contact with known irritants", "Scratching or rubbing the area", "Tight clothing on affected areas", "Overheating", "Strong fragrances"],
                    "home_remedies": ["Aloe vera gel for soothing", "Cold compresses to reduce itching", "Gentle cleansing with mild soap", "Petroleum jelly as a barrier"]
                },
                "Psoriasis": {
                    "do": ["Take daily baths (brief, lukewarm)", "Moisturize heavily after bathing", "Get moderate sun exposure", "Manage stress levels", "Maintain a healthy weight"],
                    "avoid": ["Alcohol consumption", "Smoking", "Skin injuries (cuts, scrapes)", "Stress", "Certain medications (consult doctor)"],
                    "home_remedies": ["Dead Sea salt baths", "Tea tree oil (diluted)", "Aloe vera for scaling", "Fish oil supplements (consult doctor)"]
                },
                "Acne": {
                    "do": ["Wash face twice daily gently", "Use non-comedogenic products", "Change pillowcases frequently", "Stay hydrated", "Maintain consistent sleep schedule"],
                    "avoid": ["Touching your face", "Popping or picking pimples", "Heavy makeup", "Over-washing (irritates skin)", "Greasy hair products near face"],
                    "home_remedies": ["Tea tree oil (spot treatment)", "Honey masks (antibacterial)", "Green tea extract", "Ice cubes for inflammation"]
                },
                "Urticaria": {
                    "do": ["Keep a symptom diary", "Wear loose, comfortable clothing", "Stay cool", "Take antihistamines as needed", "Apply calamine lotion"],
                    "avoid": ["Known triggers (foods, medications)", "Extreme temperatures", "Tight clothing", "Stress and anxiety", "Alcohol"],
                    "home_remedies": ["Cool compresses", "Oatmeal baths", "Aloe vera gel", "Baking soda paste for itching"]
                }
            }
            
            if disease and disease in LIFESTYLE_ADVICE:
                advice = LIFESTYLE_ADVICE[disease]
                response.update({
                    "predicted_disease": disease,
                    "confidence": session.last_confidence,
                    "confidence_level": "high" if session.last_confidence >= 0.70 else "medium",
                    "reply": (
                        f"\n\n**Tips for Managing {disease}:**\n\n"
                        f"✅ **What helps:**\n"
                        + "\n".join([f"  • {tip}" for tip in advice['do'][:5]]) +
                        f"\n\n❌ **What to avoid:**\n"
                        + "\n".join([f"  • {tip}" for tip in advice['avoid'][:5]]) +
                        f"\n\n🏠 **Home remedies that may help:**\n"
                        + "\n".join([f"  • {tip}" for tip in advice['home_remedies'][:4]]) +
                        f"\n\nWould you like to know anything else about managing {disease}?"
                    ),
                })
            else:
                response.update({
                    "reply": (
                        "⚠️ **Let's follow the proper workflow!**\n\n"
                        "I'd love to give you lifestyle advice, but first I need to identify your condition.\n\n"
                        "**Step 1:** Describe your symptoms (e.g., 'I have bumps and dry skin')\n"
                        "**Step 2:** Then I can provide personalized lifestyle tips\n\n"
                        "What skin symptoms are you experiencing?"
                    ),
                    "needs_more_info": True,
                    "follow_up_questions": ["What skin symptoms are you experiencing?"]
                })

        elif intent == "ask_causes":
            # ──────────────────────────────────────────────────────────────────
            # "What causes this?" — explain causes and triggers
            # ──────────────────────────────────────────────────────────────────
            disease = session.last_predicted_disease
            
            CAUSE_INFO = {
                "Eczema": {
                    "main_causes": ["Genetic factors (family history)", "Immune system dysfunction", "Skin barrier defects"],
                    "triggers": ["Dry skin", "Irritants (soaps, detergents)", "Allergens (dust, pollen, pet dander)", "Stress", "Hot/cold temperatures", "Certain foods"],
                    "is_contagious": False,
                    "risk_factors": ["Family history of eczema, allergies, or asthma", "Living in urban areas", "Having sensitive skin"]
                },
                "Dermatitis": {
                    "main_causes": ["Direct contact with irritants or allergens", "Sensitivity to chemicals"],
                    "triggers": ["Soaps and detergents", "Metals (nickel)", "Plants (poison ivy)", "Cosmetics and perfumes", "Latex", "Certain fabrics"],
                    "is_contagious": False,
                    "risk_factors": ["Occupational exposure (healthcare, cleaning)", "Pre-existing allergies", "Frequent hand washing"]
                },
                "Psoriasis": {
                    "main_causes": ["Autoimmune disorder", "Genetic predisposition", "Overactive immune response"],
                    "triggers": ["Stress", "Skin injuries", "Infections (strep throat)", "Certain medications", "Cold weather", "Smoking and alcohol"],
                    "is_contagious": False,
                    "risk_factors": ["Family history", "Viral infections", "Smoking", "Obesity", "Stress"]
                },
                "Acne": {
                    "main_causes": ["Excess sebum production", "Clogged hair follicles", "Bacteria (P. acnes)", "Hormonal changes"],
                    "triggers": ["Hormonal fluctuations", "Certain medications", "Diet (high glycemic foods)", "Stress", "Friction from helmets/clothing", "Oily cosmetics"],
                    "is_contagious": False,
                    "risk_factors": ["Puberty", "Family history", "Hormonal conditions", "Certain medications"]
                },
                "Urticaria": {
                    "main_causes": ["Allergic reactions", "Histamine release", "Unknown (chronic idiopathic)"],
                    "triggers": ["Foods (shellfish, nuts, eggs)", "Medications (NSAIDs, antibiotics)", "Insect stings", "Physical stimuli (pressure, cold, heat)", "Infections", "Stress"],
                    "is_contagious": False,
                    "risk_factors": ["History of allergies", "Autoimmune conditions", "Infections", "Family history"]
                }
            }
            
            if disease and disease in CAUSE_INFO:
                info = CAUSE_INFO[disease]
                contagious_text = "❌ **Not contagious** — you cannot spread this to others." if not info['is_contagious'] else "⚠️ **May be contagious** — consult a doctor about precautions."
                response.update({
                    "predicted_disease": disease,
                    "confidence": session.last_confidence,
                    "confidence_level": "high" if session.last_confidence >= 0.70 else "medium",
                    "reply": (
                        f"\n\n**Understanding {disease}:**\n\n"
                        f"🔬 **Main causes:**\n"
                        + "\n".join([f"  • {cause}" for cause in info['main_causes']]) +
                        f"\n\n⚡ **Common triggers:**\n"
                        + "\n".join([f"  • {trigger}" for trigger in info['triggers'][:6]]) +
                        f"\n\n{contagious_text}\n\n"
                        f"Understanding your triggers can help you prevent flare-ups. "
                        f"Would you like tips on managing {disease}?"
                    ),
                })
            else:
                response.update({
                    "reply": (
                        "I can explain the causes once I know what condition you're dealing with. "
                        "Could you describe your symptoms first?"
                    ),
                    "needs_more_info": True,
                    "follow_up_questions": ["What skin symptoms are you experiencing?"]
                })

        elif intent == "ask_healing":
            # ──────────────────────────────────────────────────────────────────
            # "Is this healing?" "How long to heal?" "Am I getting better?"
            # ──────────────────────────────────────────────────────────────────
            disease = session.last_predicted_disease
            
            HEALING_INFO = {
                "Eczema": {
                    "timeline": "2-4 weeks with proper treatment",
                    "signs_improving": ["Less itching", "Reduced redness", "Skin becoming smoother", "Smaller affected areas", "Less frequent flare-ups"],
                    "factors": "Healing depends on avoiding triggers, consistent moisturizing, and following treatment plans. Most people see improvement within the first week.",
                    "can_cure": False,
                    "outlook": "Eczema is manageable but chronic. With proper care, you can have long periods without flare-ups."
                },
                "Dermatitis": {
                    "timeline": "1-3 weeks after removing the irritant",
                    "signs_improving": ["Itching subsides", "Redness fades", "Skin texture normalizes", "No new patches forming"],
                    "factors": "Once the trigger is removed, skin usually heals well. Avoidance of the irritant is key to staying clear.",
                    "can_cure": True,
                    "outlook": "Contact dermatitis can fully resolve if you avoid what caused it."
                },
                "Psoriasis": {
                    "timeline": "4-8 weeks for significant improvement",
                    "signs_improving": ["Scales thinning", "Patches shrinking", "Less silvery appearance", "Reduced itching"],
                    "factors": "Psoriasis is chronic but treatable. Consistency with medication and lifestyle changes helps a lot.",
                    "can_cure": False,
                    "outlook": "While there's no cure, many people achieve clear or nearly clear skin with treatment."
                },
                "Acne": {
                    "timeline": "4-8 weeks to see improvement",
                    "signs_improving": ["Fewer new breakouts", "Existing pimples healing", "Less inflammation", "Smaller pores appearance"],
                    "factors": "Patience is key with acne treatment. It often gets slightly worse before getting better as skin purges.",
                    "can_cure": True,
                    "outlook": "Most acne clears up with consistent treatment, though it may take a few months."
                },
                "Urticaria": {
                    "timeline": "24-48 hours for acute episodes",
                    "signs_improving": ["Hives fading", "Less itching", "No new welts appearing", "Swelling reducing"],
                    "factors": "Acute hives often resolve quickly. Chronic urticaria may take longer to manage.",
                    "can_cure": True,
                    "outlook": "Most cases resolve on their own. Chronic cases need ongoing management but are controllable."
                }
            }
            
            if disease and disease in HEALING_INFO:
                info = HEALING_INFO[disease]
                cure_text = "✅ This condition **can be cured** with proper treatment." if info['can_cure'] else "This is a **chronic condition** but very manageable with the right care."
                response.update({
                    "predicted_disease": disease,
                    "confidence": session.last_confidence,
                    "reply": (
                        f"Great question! Here's what to expect with **{disease}**:\n\n"
                        f"⏱️ **Typical healing time:** {info['timeline']}\n\n"
                        f"**Signs you're improving:**\n"
                        + "\n".join([f"  • {sign}" for sign in info['signs_improving']]) +
                        f"\n\n{cure_text}\n\n"
                        f"💡 {info['factors']}\n\n"
                        f"Is there anything specific about your recovery you'd like to know?"
                    ),
                })
            else:
                response.update({
                    "reply": (
                        "I'd love to tell you about healing expectations, but I need to know your condition first.\n\n"
                        "Could you describe your symptoms? For example:\n"
                        "• What does your skin look like?\n"
                        "• Is it itchy, painful, or burning?"
                    ),
                    "needs_more_info": True,
                })

        elif intent == "ask_worsening":
            # ──────────────────────────────────────────────────────────────────
            # "Is this getting worse?" "What if it spreads?" "Warning signs"
            # ──────────────────────────────────────────────────────────────────
            disease = session.last_predicted_disease
            
            WORSENING_INFO = {
                "Eczema": {
                    "warning_signs": ["Spreading to new areas rapidly", "Skin cracking or bleeding", "Yellow crusting (possible infection)", "Fever or feeling unwell", "Severe pain instead of just itching"],
                    "when_urgent": "If you see signs of infection (oozing, yellow crust, red streaks, fever), see a doctor within 24 hours.",
                    "prevention": "Keep skin moisturized, avoid scratching, identify and avoid triggers.",
                    "spreading": "Eczema isn't contagious and typically stays localized, but scratching can cause it to spread on your own body."
                },
                "Dermatitis": {
                    "warning_signs": ["Blistering or weeping", "Signs of infection", "Spreading despite treatment", "Affecting your face or genitals", "Difficulty breathing (allergic reaction)"],
                    "when_urgent": "Seek immediate care if you have trouble breathing, severe swelling, or widespread blistering.",
                    "prevention": "Identify and completely avoid the irritant/allergen.",
                    "spreading": "It spreads only if you continue contact with the irritant. It's not contagious to others."
                },
                "Psoriasis": {
                    "warning_signs": ["Rapid spread to large areas", "Pustules forming", "Joint pain or stiffness", "Entire body turning red (erythrodermic)", "Fever with skin symptoms"],
                    "when_urgent": "Erythrodermic psoriasis (full body redness) is a medical emergency. Also seek care for joint pain.",
                    "prevention": "Manage stress, avoid skin injuries, limit alcohol, and stay consistent with treatment.",
                    "spreading": "Psoriasis can spread to new areas on your body but is NOT contagious to others."
                },
                "Acne": {
                    "warning_signs": ["Deep, painful cysts forming", "Scarring developing", "Spreading to neck, chest, back", "Not responding to OTC treatment for 3+ months", "Causing emotional distress"],
                    "when_urgent": "See a dermatologist if you develop cystic acne or scarring, or if OTC treatments aren't working.",
                    "prevention": "Don't pick or squeeze, keep routine consistent, avoid touching your face.",
                    "spreading": "Acne isn't contagious. Spreading on your body is due to hormones/oil production, not infection."
                },
                "Urticaria": {
                    "warning_signs": ["Swelling of lips, tongue, or throat", "Difficulty breathing", "Dizziness or fainting", "Hives lasting more than 6 weeks", "Fever with hives"],
                    "when_urgent": "**EMERGENCY:** If you have throat swelling, difficulty breathing, or dizziness, call emergency services immediately.",
                    "prevention": "Identify triggers, carry antihistamines, consider an epinephrine auto-injector if you have severe allergies.",
                    "spreading": "Hives can appear anywhere and move around your body, but they're not contagious."
                }
            }
            
            if disease and disease in WORSENING_INFO:
                info = WORSENING_INFO[disease]
                response.update({
                    "predicted_disease": disease,
                    "confidence": session.last_confidence,
                    "reply": (
                        f"I understand your concern about **{disease}** getting worse. Here's what to watch for:\n\n"
                        f"🚨 **Warning signs to watch:**\n"
                        + "\n".join([f"  • {sign}" for sign in info['warning_signs']]) +
                        f"\n\n⚠️ **When to see a doctor:** {info['when_urgent']}\n\n"
                        f"📍 **About spreading:** {info['spreading']}\n\n"
                        f"💡 **Prevention:** {info['prevention']}\n\n"
                        f"Are you noticing any of these warning signs?"
                    ),
                })
            else:
                response.update({
                    "reply": (
                        "I can definitely help you understand warning signs and what to watch for.\n\n"
                        "First, could you tell me what symptoms you're experiencing? "
                        "That way I can give you specific guidance on what changes might be concerning."
                    ),
                    "needs_more_info": True,
                })

        elif intent == "general_question":
            # ──────────────────────────────────────────────────────────────────
            # General questions - ChatGPT-like informative responses
            # ──────────────────────────────────────────────────────────────────
            disease = session.last_predicted_disease
            lowered = user_message.lower()
            
            # Comprehensive disease knowledge base
            DISEASE_KNOWLEDGE = {
                "Eczema": {
                    "overview": "Eczema, also known as atopic dermatitis, is a chronic inflammatory skin condition that affects about 10-20% of people worldwide.",
                    "symptoms": "dry, itchy skin that can become red, cracked, and inflamed. It often appears in patches on the face, inside elbows, behind knees, and on hands.",
                    "causes": "a combination of genetic factors, immune system dysfunction, and environmental triggers. It's not contagious.",
                    "treatments": "moisturizers to keep skin hydrated, topical corticosteroids for flare-ups, antihistamines for itching, and avoiding known triggers.",
                    "tips": "Moisturize regularly, use fragrance-free products, avoid hot showers, wear soft cotton clothing, and manage stress."
                },
                "Dermatitis": {
                    "overview": "Dermatitis refers to inflammation of the skin and covers several types including contact dermatitis and seborrheic dermatitis.",
                    "symptoms": "red, itchy, swollen skin that may blister, ooze, or become scaly. The appearance depends on the type and cause.",
                    "causes": "contact with irritants (soaps, chemicals), allergens (nickel, plants), or it can be related to sebum production on the scalp.",
                    "treatments": "avoiding triggers, topical corticosteroids, moisturizers, and antihistamines. For seborrheic dermatitis, medicated shampoos help.",
                    "tips": "Identify and avoid your triggers, patch test new products, keep skin moisturized, and wear protective gloves when needed."
                },
                "Psoriasis": {
                    "overview": "Psoriasis is a chronic autoimmune condition where skin cells multiply 10x faster than normal, causing thick, scaly patches.",
                    "symptoms": "red, raised patches covered with silvery-white scales, often on elbows, knees, scalp, and lower back. Can be itchy or painful.",
                    "causes": "an overactive immune system that attacks healthy skin cells. It's genetic and can be triggered by stress, infections, or injuries.",
                    "treatments": "topical treatments (corticosteroids, vitamin D), phototherapy (UV light), and systemic medications for severe cases.",
                    "tips": "Keep skin moisturized, avoid skin injuries, manage stress, limit alcohol, and get regular sun exposure (but avoid sunburn)."
                },
                "Acne": {
                    "overview": "Acne is the most common skin condition, affecting up to 85% of people between ages 12-24. It can persist into adulthood.",
                    "symptoms": "pimples, blackheads, whiteheads, and in severe cases, painful cysts or nodules. Usually appears on face, chest, and back.",
                    "causes": "excess oil production, clogged pores, bacteria (P. acnes), and hormonal changes. Diet and stress can worsen it.",
                    "treatments": "benzoyl peroxide, salicylic acid, retinoids, antibiotics (topical or oral), and for severe cases, isotretinoin.",
                    "tips": "Wash face twice daily, don't pick at acne, use non-comedogenic products, change pillowcases regularly, and stay hydrated."
                },
                "Urticaria": {
                    "overview": "Urticaria, commonly known as hives, are raised, itchy welts that can appear suddenly and usually resolve within 24 hours.",
                    "symptoms": "red or skin-colored welts of various sizes that blanch (turn white) when pressed. They can appear anywhere and may merge together.",
                    "causes": "allergic reactions (food, medications), infections, stress, temperature changes, or sometimes no identifiable cause.",
                    "treatments": "antihistamines are the main treatment, avoiding known triggers, and for severe cases, corticosteroids or epinephrine.",
                    "tips": "Keep a diary to identify triggers, avoid tight clothing, use cool compresses for relief, and manage stress."
                }
            }
            
            if disease and disease in DISEASE_KNOWLEDGE:
                info = DISEASE_KNOWLEDGE[disease]
                # Context-aware informative response - actually provide information!
                response.update({
                    "predicted_disease": disease,
                    "confidence": session.last_confidence,
                    "reply": (
                        f"**{disease}** - {info['overview']}\n\n"
                        f"**Common symptoms:** {info['symptoms']}\n\n"
                        f"**What causes it:** {info['causes']}\n\n"
                        f"**Treatment options:** {info['treatments']}\n\n"
                        f"**Daily tips:** {info['tips']}\n\n"
                        f"Is there anything specific about {disease} you'd like me to explain further?"
                    ),
                })
            elif disease:
                # Fallback for diseases not in knowledge base
                response.update({
                    "predicted_disease": disease,
                    "confidence": session.last_confidence,
                    "reply": (
                        f"**{disease}** is a skin condition that can vary in severity and presentation.\n\n"
                        f"For the most accurate information about your specific case, I'd recommend consulting a dermatologist "
                        f"who can examine your skin directly.\n\n"
                        f"In the meantime, what specific aspect would you like to know about - symptoms, causes, or treatments?"
                    ),
                })
            else:
                response.update({
                    "reply": (
                        "I'm a skin care assistant that can help you understand various skin conditions.\n\n"
                        "I have detailed knowledge about **Eczema**, **Dermatitis**, **Psoriasis**, **Acne**, and **Urticaria** "
                        "including their symptoms, causes, treatments, and daily care tips.\n\n"
                        "Describe your symptoms and I'll help identify what might be causing them!"
                    ),
                })

        elif intent == "ask_about_disease":
            # ──────────────────────────────────────────────────────────────────
            # "What is eczema?" or "Tell me about psoriasis"
            # ──────────────────────────────────────────────────────────────────
            # Try to extract disease name from message
            lowered = user_message.lower()
            mentioned_disease = None
            for d_name in ["eczema", "dermatitis", "psoriasis", "acne", "urticaria"]:
                if d_name in lowered:
                    mentioned_disease = d_name.title()
                    break
            
            # Use session disease if no specific one mentioned
            target_disease = mentioned_disease or session.last_predicted_disease
            
            # Check if asking about causes
            if target_disease and any(w in lowered for w in ['cause', 'causes', 'why', 'trigger', 'contagious']):
                # Redirect to causes handler logic
                CAUSE_INFO = {
                    "Eczema": {
                        "main_causes": ["Genetic factors (family history)", "Immune system dysfunction", "Skin barrier defects"],
                        "triggers": ["Dry skin", "Irritants (soaps, detergents)", "Allergens (dust, pollen, pet dander)", "Stress", "Hot/cold temperatures", "Certain foods"],
                        "is_contagious": False,
                        "description": "Eczema is a chronic inflammatory skin condition that causes dry, itchy, and inflamed skin."
                    },
                    "Dermatitis": {
                        "main_causes": ["Direct contact with irritants or allergens", "Sensitivity to chemicals"],
                        "triggers": ["Soaps and detergents", "Metals (nickel)", "Plants (poison ivy)", "Cosmetics and perfumes", "Latex"],
                        "is_contagious": False,
                        "description": "Dermatitis refers to skin inflammation, often from contact with irritants or allergens."
                    },
                    "Psoriasis": {
                        "main_causes": ["Autoimmune disorder", "Genetic predisposition", "Overactive immune response"],
                        "triggers": ["Stress", "Skin injuries", "Infections (strep throat)", "Certain medications", "Cold weather"],
                        "is_contagious": False,
                        "description": "Psoriasis is a chronic autoimmune condition that speeds up skin cell growth, causing thick, scaly patches."
                    },
                    "Acne": {
                        "main_causes": ["Excess sebum production", "Clogged hair follicles", "Bacteria (P. acnes)", "Hormonal changes"],
                        "triggers": ["Hormonal fluctuations", "Certain medications", "Diet (high glycemic foods)", "Stress", "Oily cosmetics"],
                        "is_contagious": False,
                        "description": "Acne is a skin condition where hair follicles become clogged with oil and dead skin cells."
                    },
                    "Urticaria": {
                        "main_causes": ["Allergic reactions", "Histamine release", "Unknown (chronic idiopathic)"],
                        "triggers": ["Foods (shellfish, nuts, eggs)", "Medications", "Insect stings", "Physical stimuli", "Infections"],
                        "is_contagious": False,
                        "description": "Urticaria (hives) are itchy, raised welts caused by histamine release in the skin."
                    }
                }
                
                if target_disease in CAUSE_INFO:
                    info = CAUSE_INFO[target_disease]
                    contagious_text = "❌ **Not contagious** — you cannot spread this to others." if not info['is_contagious'] else "⚠️ **May be contagious**"
                    response.update({
                        "predicted_disease": target_disease,
                        "confidence": session.last_confidence if target_disease == session.last_predicted_disease else 0.0,
                        "reply": (
                            f"\n\n**About {target_disease}:**\n\n"
                            f"📖 {info['description']}\n\n"
                            f"🔬 **Primary Causes:**\n"
                            + "\n".join([f"  • {cause}" for cause in info['main_causes']]) +
                            f"\n\n⚡ **Common Triggers:**\n"
                            + "\n".join([f"  • {trigger}" for trigger in info['triggers'][:5]]) +
                            f"\n\n{contagious_text}"
                        ),
                    })
                else:
                    response.update({
                        "reply": (
                            "I can provide information about Eczema, Dermatitis, Psoriasis, Acne, or Urticaria. "
                            "Which condition would you like to know about?"
                        ),
                        "follow_up_questions": ["Which skin condition would you like to learn about?"],
                    })
            elif target_disease:
                # General info about the disease - provide comprehensive information like ChatGPT
                DISEASE_FULL_INFO = {
                    "Eczema": (
                        "**Eczema** (atopic dermatitis) is a chronic inflammatory skin condition affecting 10-20% of people.\n\n"
                        "**What it looks like:** Dry, itchy patches that can be red, cracked, or oozing. Common on face, "
                        "elbows, knees, and hands.\n\n"
                        "**Causes:** Genetic factors, immune dysfunction, and a compromised skin barrier. "
                        "Triggered by dry air, irritants, stress, and allergens.\n\n"
                        "**Treatment:** Daily moisturizing, topical corticosteroids during flares, antihistamines for itch, "
                        "and avoiding triggers. Severe cases may need immunosuppressants."
                    ),
                    "Dermatitis": (
                        "**Dermatitis** refers to skin inflammation from various causes.\n\n"
                        "**What it looks like:** Red, itchy, swollen skin that may blister or peel. Location depends on the trigger.\n\n"
                        "**Causes:** Contact with irritants (soaps, chemicals) or allergens (nickel, latex, plants). "
                        "Seborrheic dermatitis affects oily areas like the scalp.\n\n"
                        "**Treatment:** Identify and avoid triggers, topical steroids, moisturizers, and for seborrheic type, "
                        "medicated shampoos with ketoconazole or selenium sulfide."
                    ),
                    "Psoriasis": (
                        "**Psoriasis** is a chronic autoimmune condition where skin cells multiply 10x faster than normal.\n\n"
                        "**What it looks like:** Thick, red patches covered with silvery scales. Common on elbows, knees, "
                        "scalp, and lower back. Can affect nails too.\n\n"
                        "**Causes:** Overactive immune system with genetic factors. Triggered by stress, infections, "
                        "skin injuries, and certain medications.\n\n"
                        "**Treatment:** Topical treatments (steroids, vitamin D), phototherapy with UV light, and "
                        "systemic medications (methotrexate, biologics) for severe cases."
                    ),
                    "Acne": (
                        "**Acne** is the most common skin condition, affecting up to 85% of teenagers and many adults.\n\n"
                        "**What it looks like:** Pimples, blackheads, whiteheads, and in severe cases, painful cysts. "
                        "Usually on face, chest, shoulders, and back.\n\n"
                        "**Causes:** Excess oil, clogged pores, bacteria (P. acnes), and hormones. Worsened by stress, "
                        "certain foods, and some cosmetics.\n\n"
                        "**Treatment:** Benzoyl peroxide, salicylic acid, retinoids for mild cases. Antibiotics or "
                        "isotretinoin (Accutane) for moderate to severe acne."
                    ),
                    "Urticaria": (
                        "**Urticaria** (hives) are raised, itchy welts that appear suddenly and usually fade within 24 hours.\n\n"
                        "**What it looks like:** Red or skin-colored bumps of varying sizes. They blanch (turn white) "
                        "when pressed and can appear anywhere on the body.\n\n"
                        "**Causes:** Allergic reactions (food, medications), infections, stress, temperature changes, "
                        "or sometimes no identifiable cause (chronic idiopathic urticaria).\n\n"
                        "**Treatment:** Antihistamines are first-line treatment. Avoid known triggers. Severe reactions "
                        "may require corticosteroids or epinephrine."
                    )
                }
                
                response.update({
                    "predicted_disease": target_disease,
                    "confidence": session.last_confidence if target_disease == session.last_predicted_disease else 0.0,
                    "reply": (
                        DISEASE_FULL_INFO.get(target_disease, f"**{target_disease}** is a skin condition. Let me know what specific aspect you'd like to learn about.") +
                        f"\n\nWould you like more details about anything specific?"
                    ),
                })
            else:
                response.update({
                    "reply": (
                        "I can provide information about various skin conditions. "
                        "If you describe your symptoms, I can give you personalized guidance!"
                    ),
                    "follow_up_questions": ["What symptoms are you experiencing?"],
                    "needs_more_info": True,
                })

        else:  # "other" — greeting / off-topic / unknown
            lowered = user_message.lower().strip()
            words = lowered.split()
            disease = session.last_predicted_disease
            
            # Common greetings
            GREETINGS = {'hi', 'hello', 'hey', 'hola', 'good morning', 'good afternoon', 'good evening', 'morning', 'afternoon', 'evening'}
            is_greeting = lowered in GREETINGS or any(g in lowered for g in ['hello', 'good morning', 'good afternoon', 'good evening'])
            
            # Check for various conversational patterns
            if any(w in lowered for w in ['thank', 'thanks', 'thx', 'appreciate']):
                if disease:
                    response["reply"] = (
                        f"You're welcome! Happy I could help with your {disease}.\n\n"
                        f"Quick reminders:\n"
                        f"• Stay consistent with treatment\n"
                        f"• Watch for any changes\n"
                        f"• Consult a dermatologist if it persists\n\n"
                        f"Feel free to ask if anything else comes up!"
                    )
                else:
                    response["reply"] = "You're welcome! Let me know if you have any skin concerns I can help with."
                    
            elif any(w in lowered for w in ['bye', 'goodbye', 'see you', 'later', 'take care']):
                response["reply"] = (
                    "Take care! Remember to stick with your treatment routine. "
                    "Feel free to come back anytime you have questions!"
                )
                
            elif any(w in lowered for w in ['help', 'what can you do', 'how do you work', 'what are you', 'what is this']):
                response["reply"] = (
                    "I'm an AI assistant specializing in skin health.\n\n"
                    "I can help identify conditions, recommend treatments, explain causes, "
                    "and provide guidance on when to see a dermatologist.\n\n"
                    "What would you like to know?"
                )
                
            elif is_greeting:
                response["reply"] = (
                    "Hey! 👋 How can I help you today?\n\n"
                    "Feel free to describe any skin concerns you're experiencing, "
                    "or ask me anything about skin conditions."
                )
                
            elif any(w in lowered for w in ['yes', 'yeah', 'yep', 'sure', 'okay', 'ok', 'yea']):
                # Affirmative response - context aware
                if disease:
                    response["reply"] = (
                        f"Great! What would you like to know about {disease}?\n\n"
                        f"I can tell you about treatments, causes, healing time, warning signs, or daily care tips."
                    )
                else:
                    response["reply"] = "Sure! What would you like to know? You can describe your symptoms or ask me anything about skin conditions."
                    
            elif any(w in lowered for w in ['no', 'nope', 'nah', 'not really']):
                # Negative response
                if disease:
                    response["reply"] = (
                        f"No worries! Let me know if you have any other questions about {disease} or anything else skin-related."
                    )
                else:
                    response["reply"] = "No problem! I'm here whenever you need help with any skin concerns."
                    
            elif any(w in lowered for w in ['maybe', 'not sure', 'idk', 'i dont know', "don't know", 'confused']):
                # Uncertain response
                if disease:
                    response["reply"] = (
                        f"That's okay! Based on our conversation about {disease}, here are some things you might want to know:\n\n"
                        f"• How long will it take to heal?\n"
                        f"• What should I watch out for?\n"
                        f"• Any tips for daily care?\n\n"
                        f"Just pick one or ask something else!"
                    )
                else:
                    response["reply"] = (
                        "No worries, I can help you figure this out!\n\n"
                        "Try describing what you're experiencing:\n"
                        "• What does it look like?\n"
                        "• How does it feel?\n"
                        "• Where is it on your body?"
                    )
                    
            elif any(w in lowered for w in ['doctor', 'dermatologist', 'hospital', 'clinic', 'appointment']):
                # Questions about professional care
                if disease:
                    response["reply"] = (
                        f"Good thinking to consider professional help for {disease}!\n\n"
                        f"**When to see a dermatologist:**\n"
                        f"• If symptoms aren't improving after 2 weeks of treatment\n"
                        f"• If the condition is spreading or getting worse\n"
                        f"• If you notice signs of infection\n"
                        f"• If it's affecting your quality of life\n\n"
                        f"A dermatologist can prescribe stronger treatments and provide a proper diagnosis. Would you like tips on what to tell them?"
                    )
                else:
                    response["reply"] = (
                        "Seeing a dermatologist is always a good idea for persistent skin issues!\n\n"
                        "They can provide:\n"
                        "• Accurate diagnosis\n"
                        "• Prescription treatments\n"
                        "• Personalized care plans\n\n"
                        "In the meantime, would you like to describe your symptoms? I can give you some initial guidance."
                    )
                    
            elif any(w in lowered for w in ['worse', 'bad', 'spreading', 'getting bigger', 'more']):
                # Concerns about worsening
                if disease:
                    response["reply"] = (
                        f"I understand you're worried about {disease} getting worse. That's a valid concern.\n\n"
                        f"Would you like me to tell you:\n"
                        f"• Warning signs to watch for?\n"
                        f"• When you should see a doctor?\n"
                        f"• What might be causing it to flare up?"
                    )
                else:
                    response["reply"] = (
                        "I hear your concern about things getting worse. To help you better, could you describe what's happening?\n\n"
                        "Tell me:\n"
                        "• What does it look like now?\n"
                        "• How has it changed?\n"
                        "• Any other symptoms?"
                    )
                    
            elif any(w in lowered for w in ['better', 'improving', 'healing', 'working']):
                # Questions about improvement
                if disease:
                    response["reply"] = (
                        f"Great that you're thinking about progress! For {disease}:\n\n"
                        f"**Signs of improvement:**\n"
                        f"• Less itching/discomfort\n"
                        f"• Reduced redness or swelling\n"
                        f"• Affected area getting smaller\n\n"
                        f"Would you like to know typical healing timelines or what else you can do to speed recovery?"
                    )
                else:
                    response["reply"] = (
                        "I'd be happy to help you understand if things are improving!\n\n"
                        "Could you first describe what you're dealing with? Then I can tell you what improvement typically looks like for your specific situation."
                    )
                    
            else:
                # General fallback - be helpful and conversational
                if disease:
                    response["reply"] = (
                        f"I'm here to help with any questions about {disease} or skin care in general.\n\n"
                        f"Some things I can help with:\n"
                        f"• Is it healing properly?\n"
                        f"• What warning signs should I watch for?\n"
                        f"• How can I manage it day-to-day?\n"
                        f"• Should I see a doctor?\n\n"
                        f"What's on your mind?"
                    )
                else:
                    response["reply"] = (
                        "I'm your skin care assistant - I'm here to help!\n\n"
                        "I can answer questions about:\n"
                        "• Common skin conditions (eczema, psoriasis, acne, etc.)\n"
                        "• Treatments and medications\n"
                        "• Healing expectations\n"
                        "• When to see a doctor\n\n"
                        "What would you like to know? Or just describe your symptoms and I'll help identify what might be going on."
                    )
            response["follow_up_questions"] = []

        # ── Log reply and return ──────────────────────────────────────────────
        session.add_message("assistant", response.get("reply", ""))
        return jsonify(response)

    except Exception as exc:
        if DEBUG:
            import traceback; traceback.print_exc()
        return jsonify({
            "reply":                 f"An internal error occurred: {str(exc)[:100]}",
            "predicted_disease":     None,
            "confidence":            0.0,
            "confidence_level":      "none",
            "recommended_treatments": [],
            "follow_up_questions":   [],
            "needs_more_info":       True,
            "model_status":          "error",
        }), 500


# ── History / stats / progress (mock) ─────────────────────────────────────────

@app.route("/api/history", methods=["GET"])
def history():
    return jsonify(MOCK_HISTORY)


@app.route("/api/stats", methods=["GET"])
def stats():
    return jsonify(MOCK_STATS)


@app.route("/api/progress", methods=["POST"])
def add_progress():
    new_entry = {
        "week":      f"Week {len(MOCK_HISTORY) + 1}",
        "date":      datetime.date.today().isoformat(),
        "image_url": "assets/images/placeholder.png",
        "status":    "Improving",
        "score":     85 + (len(MOCK_HISTORY) % 15),
        "metrics":   {"redness": 10, "inflammation": 10, "scaling": 5, "texture": 92},
    }
    MOCK_HISTORY.append(new_entry)
    return jsonify({
        "message":   "Progress logged successfully",
        "analysis":  "Inflammation has reduced by 15% compared to last week.",
        "new_entry": new_entry,
    })


if __name__ == "__main__":
    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║               SKIN CARE ASSISTANT - API SERVER                   ║
╠══════════════════════════════════════════════════════════════════╣
║  Environment: {FLASK_ENV:<15}                                    ║
║  Debug Mode:  {str(FLASK_DEBUG):<15}                             ║
║  Server:      http://{HOST}:{PORT}                               ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    app.run(debug=FLASK_DEBUG, port=PORT, host=HOST)
