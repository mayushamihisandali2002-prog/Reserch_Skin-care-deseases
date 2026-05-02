"""
Hybrid AI Service for SkinAI
====================
Uses Groq (text/chat) + Gemini (images)
"""
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

import os
import logging
import json
from typing import Any, Optional, Dict, List

logger = logging.getLogger(__name__)

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Response cache for speed
_response_cache = {}
_cache_max = 100

# Cache for Gemini module
_genai_cached = None

def _get_genai():
    global _genai_cached
    if _genai_cached is None:
        try:
            import google.generativeai as genai
            _genai_cached = genai
        except:
            pass
    return _genai_cached


class GeminiService:
    """Hybrid AI using Groq for text, Gemini for images"""
    
    _initialized = False
    _client = None
    _provider = None
    _groq_client = None
    _genai_client = None

    @classmethod
    def _initialize(cls):
        if cls._initialized:
            return
        
        global _genai_cached
        
        # Groq for text (fast)
        if GROQ_API_KEY:
            try:
                from groq import Groq
                cls._groq_client = Groq(api_key=GROQ_API_KEY)
                logger.info("✓ Groq ready")
            except Exception as e:
                logger.warning(f"Groq failed: {e}")
        
        # Gemini for images (lazy import)
        if GEMINI_API_KEY:
            try:
                genai = _get_genai()
                if genai:
                    genai.configure(api_key=GEMINI_API_KEY)
                    cls._genai_client = genai
                    logger.info("✓ Gemini ready")
            except Exception as e:
                logger.warning(f"Gemini failed: {e}")
        
        # Set primary (Groq is faster for text)
        if cls._groq_client:
            cls._client = cls._groq_client
            cls._provider = "groq"
        elif cls._genai_client:
            cls._client = cls._genai_client
            cls._provider = "gemini"
        else:
            cls._client = "missing"
            return
        
        cls._initialized = True

    @classmethod
    def is_available(cls) -> tuple[bool, str]:
        if not cls._initialized:
            cls._initialize()
        if cls._client == "missing":
            return False, "No API"
        return cls._initialized, cls._provider or "none"

    @classmethod
    def _get_groq(cls):
        if not cls._groq_client:
            cls._initialize()
        return cls._groq_client

    @classmethod
    def _generate(cls, prompt: str) -> str:
        if not cls._initialized:
            cls._initialize()
        
        if cls._provider == "groq":
            return cls._generate_groq(prompt)
        elif cls._provider == "gemini":
            return cls._generate_gemini(prompt)
        return ""

    @classmethod
    def _generate_groq(cls, prompt: str, use_fast: bool = False) -> str:
        """Groq generation — uses 70B for clinical responses, 8B for fast data extraction."""
        # Use 8B (fast) for structured extraction tasks, 70B for clinical conversations
        model = "llama-3.1-8b-instant" if use_fast else "llama-3.3-70b-versatile"
        try:
            response = cls._groq_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.65,
                max_tokens=1024,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"Groq ({model}) error: {e}")
            # Fallback to 8B if 70B fails
            if not use_fast:
                try:
                    response = cls._groq_client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.65,
                        max_tokens=1024,
                    )
                    return response.choices[0].message.content
                except Exception as fe:
                    logger.warning(f"Groq 8B fallback error: {fe}")
            return ""

    @classmethod
    def _generate_gemini(cls, prompt: str) -> str:
        """Gemini generation"""
        try:
            model = cls._genai_client.GenerativeModel('gemini-flash-latest')
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.warning(f"Gemini error: {e}")
            return ""

    @classmethod
    def _parse_json(cls, text: str) -> dict:
        """Robust parsing that finds a JSON object even if surrounded by text."""
        import re
        text = text.strip()
        
        try:
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                json_str = text[start:end+1]
                return json.loads(json_str)
        except Exception as e:
            logger.warning(f"Initial JSON bracket extraction failed: {e}")

        if text.startswith("```"):
            parts = text.split("```")
            if len(parts) > 1:
                text = parts[1]
                if text.startswith("json"):
                    text = text[4:].strip()
        
        try:
            return json.loads(text)
        except Exception as e:
            logger.warning(f"Final JSON load failed: {e}. Raw text: {text[:100]}...")
            raise e

    @classmethod
    def generate_title(cls, first_message: str) -> str:
        """Generate a short 3-4 word title for a chat session."""
        cls._initialize()
        prompt = f"Create a very short (3-4 words max) clinical title for a chat starting with: '{first_message}'. Return ONLY the title text."
        title = cls._generate(prompt).strip().replace('"', '')
        return title[:40]

    # ==== PUBLIC METHODS =====

    @classmethod
    def process_clinical_turn(cls, user_message: str, history: List[Dict], current_sd: Dict, ml_pred: Optional[Dict]) -> Dict:
        """
        Production-Grade 3-Step Pipeline:
        1. Intent Classification — Is this a greeting, a symptom report, or a general question?
        2. Fast Symptom Extraction (8B model) — Only if needed.
        3. Smart Clinical Response (70B model) — Contextual, natural, never leaks internals.
        """
        cls._initialize()
        if not cls._initialized:
            return {"reply": "Connection lost. Please try again.", "structured_data": current_sd, "is_final": False}

        # --- STEP 1: DETECT INTENT ---
        msg_lower = user_message.lower().strip()
        is_greeting = any(w in msg_lower for w in ["hello", "hi", "hey", "good morning", "good evening", "howdy", "what's up", "sup"])
        is_general_question = "?" in user_message and not any(w in msg_lower for w in ["rash", "itch", "skin", "bump", "lesion", "burn", "peel", "dry", "oily", "acne", "spot", "sore", "blister", "wound"])

        # --- STEP 2: FAST SYMPTOM EXTRACTION (skip for greetings) ---
        new_sd = current_sd
        if not is_greeting:
            extraction_prompt = f'Extract skin symptoms from this message into JSON. Message: "{user_message}". Current state: {json.dumps(current_sd)}. Return only: {{"structured_data": {{"symptoms": "", "location": "", "duration": "", "sensation": "", "triggers": "", "progression": ""}}}}'
            try:
                extraction_text = cls._generate_groq(extraction_prompt, use_fast=True) if cls._provider == "groq" else cls._generate(extraction_prompt)
                extracted = cls._parse_json(extraction_text)
                new_sd = extracted.get("structured_data", current_sd)
            except:
                new_sd = current_sd

        # --- STEP 3: GENERATE CLINICAL RESPONSE ---
        ml_disease = ml_pred.get("disease") if ml_pred else None
        ml_conf = ml_pred.get("confidence", 0) if ml_pred else 0
        has_scan = ml_disease and ml_disease not in ["None", "Unknown"]
        has_symptoms = any(v for v in new_sd.values() if v)
        has_history = len(history) > 1  # More than just the welcome message

        # Build context string (NEVER exposed to user, only used internally for reasoning)
        symptom_ctx = ", ".join([f"{k}: {v}" for k, v in new_sd.items() if v]) or "none yet"
        scan_ctx = f"{ml_disease} ({ml_conf:.0%} confidence)" if has_scan else "no scan performed"
        history_ctx = json.dumps(history[-8:]) if has_history else "[]"

        response_prompt = f"""You are SkinAI, a friendly and intelligent dermatology assistant — like having a brilliant doctor friend who explains things clearly.

CONVERSATION HISTORY (use this for context, do NOT repeat it):
{history_ctx}

INTERNAL CONTEXT (use this to reason, NEVER mention these technical details in your reply):
- Patient symptoms collected: {symptom_ctx}
- Image scan result: {scan_ctx}
- User's latest message: "{user_message}"

YOUR TASK: Write a single natural reply to the user's latest message.

RULES (follow strictly):
1. NEVER mention "ML Scan Data", "Symptom State", "confidence", "0%", or ANY technical system variable. These are internal — the user must NEVER see them.
2. If this is a GREETING ("Hello", "Hi", etc.) → Respond warmly in 2-3 sentences. Introduce yourself briefly and invite them to share their concern.
3. If they describe SYMPTOMS → Ask ONE focused follow-up question OR give a clear clinical insight. Do NOT list 5 questions at once.
4. If they ask a GENERAL DERMATOLOGY question → Answer it directly and informatively, like a knowledgeable doctor would.
5. Use **bold** for medical terms. Use bullet points only for lists of 3+ items.
6. Keep replies concise and scannable. Do NOT write paragraphs of text for simple questions.
7. If you have enough information to suggest a likely condition, name it confidently but include a brief disclaimer.
8. The conversation must feel natural — like Gemini, ChatGPT, or Claude.

RETURN ONLY valid JSON (no markdown code blocks around it):
{{"reply": "your natural response here (use \\n for line breaks)", "is_final": false, "predicted_disease": null, "chat_title": "3-word topic title"}}"""

        try:
            response_text = cls._generate(response_prompt)
            res = cls._parse_json(response_text)
            res["structured_data"] = new_sd

            if res.get("is_final") and not res.get("predicted_disease") and has_scan:
                res["predicted_disease"] = ml_disease

            return res
        except Exception as e:
            logger.error(f"Clinical response failed: {e}")
            # Context-aware fallback — never hardcoded
            if is_greeting:
                fallback = "Hello! I'm SkinAI, your dermatology assistant. What skin concern can I help you with today?"
            elif has_symptoms:
                fallback = f"I have some details about your condition. Could you tell me more about when it started or how it has changed?"
            else:
                fallback = "Could you describe your skin concern? For example, where it is, what it looks like, and how long you've had it?"
            return {"reply": fallback, "structured_data": new_sd, "is_final": False}

    @classmethod
    def generate_severity_rationale(cls, level: str, metrics: dict, disease: str = None, improvement_percent: float = None) -> str:
        """
        Translates raw biomarker scores into a 2-3 sentence professional clinical rationale.
        This is the 'Severity Interpreter' — makes numbers meaningful to the patient.
        """
        cls._initialize()
        if not cls._initialized:
            return ""

        redness = metrics.get('redness', 0)
        inflammation = metrics.get('inflammation', 0)
        scaling = metrics.get('scaling', 0)
        texture = metrics.get('texture', 0)

        # Build dynamic context hints for the AI
        redness_ctx = "high (active inflammatory flare likely)" if redness > 60 else "moderate" if redness > 35 else "low"
        scaling_ctx = "significant barrier disruption detected" if scaling > 50 else "mild scaling present" if scaling > 25 else "minimal"
        trend_ctx = f" The patient has shown a {abs(improvement_percent):.0f}% {'improvement' if improvement_percent > 0 else 'worsening'} in overall severity since their first scan." if improvement_percent is not None else ""
        disease_ctx = f" The condition under review is suspected to be {disease}." if disease else ""

        prompt = f"""You are a compassionate Senior Dermatologist writing a brief clinical summary for a patient's skin scan results.

BIOMARKER DATA:
- Overall Severity Grade: {level.upper()}
- Redness Index: {redness:.1f}% — {redness_ctx}
- Inflammation Score: {inflammation:.1f}%
- Scaling/Flakiness: {scaling:.1f}% — {scaling_ctx}
- Surface Texture Irregularity: {texture:.1f}/10{disease_ctx}{trend_ctx}

INSTRUCTIONS:
1. Write exactly 2-3 concise sentences explaining WHY the skin received this grade.
2. Connect the numbers to what they mean clinically (e.g. high redness = active vascular response, high scaling = barrier disruption).
3. Use professional but accessible language. AVOID jargon like 'entropy' — say 'surface irregularity' instead.
4. If scaling is > 50 or redness > 60, acknowledge it as a concern. If both are low, reassure the patient.
5. Tone: Authoritative yet empathetic, like a trusted doctor explaining a report.
6. Return ONLY the rationale text. No headers, no bullet points, no prefixes."""

        try:
            rationale = cls._generate_groq(prompt, use_fast=False).strip()
            # Sanitize: remove any accidental headers or prefixes
            for prefix in ["Rationale:", "Clinical Rationale:", "Summary:", "**"]:
                if rationale.startswith(prefix):
                    rationale = rationale[len(prefix):].strip()
            return rationale
        except Exception as e:
            logger.warning(f"Severity rationale generation failed: {e}")
            return ""

    @classmethod
    def generate_skincare_rationale(cls, skin_type: str, goals: list, safe_ingredients: list, avoid_ingredients: list) -> str:
        """
        Generates a personalized 'Doctor's Note' explaining the skincare recommendation.
        Tells the user WHY specific ingredients were chosen for their skin.
        """
        cls._initialize()
        if not cls._initialized:
            return ""

        goals_str = ', '.join(goals) if goals else 'general skin health'
        safe_str = ', '.join(safe_ingredients[:4]) if safe_ingredients else 'standard moisturizers'
        avoid_str = ', '.join(avoid_ingredients[:3]) if avoid_ingredients else 'none'

        prompt = f"""You are a friendly dermatologist explaining a skincare recommendation to a patient in 2-3 sentences.

PATIENT PROFILE:
- Skin Type: {skin_type}
- Primary Goals: {goals_str}
- Recommended Key Ingredients: {safe_str}
- Ingredients to Avoid: {avoid_str}

INSTRUCTIONS:
1. Explain in plain language WHY the top 1-2 recommended ingredients were chosen for this specific skin type and goal.
2. If there are ingredients to avoid, briefly explain why (e.g. 'Fragrance can trigger sensitivity flares').
3. Keep it friendly, concise, and personal — like a doctor talking directly to their patient.
4. Return ONLY the explanation text. No headers, no bullet points."""

        try:
            rationale = cls._generate_groq(prompt, use_fast=False).strip()
            return rationale
        except Exception as e:
            logger.warning(f"Skincare rationale generation failed: {e}")
            return ""

    @classmethod
    def analyze_tracking_context(
        cls,
        current_image_bytes: bytes,
        current_level: str,
        current_metrics: dict,
        journey_title: str = "",
        target_body_part: str = "",
        baseline_image_bytes: bytes = None,
        baseline_level: str = "",
        baseline_score: float = 0.0,
        current_score: float = 0.0,
        visit_number: int = 1,
    ) -> dict:
        """
        Master Multimodal Smart Guard for severity tracking.

        Uses Gemini Vision to:
        1. IDENTIFY  — Detect the body part shown in the current image.
        2. VERIFY    — Check consistency with the journey's locked target body part.
        3. COMPARE   — Visual + biomarker delta analysis against the baseline image.
        4. RATIONALE — Generate a clinical explanation for the current biomarkers.
        5. INSIGHT   — Write a healing progress summary comparing Day N to Day 1.
        """
        cls._initialize()
        if not cls._initialized or not cls._genai_client:
            # Graceful degradation: return a safe default without crashing
            return {
                "identified_body_part": "Unknown",
                "is_consistent_with_journey": True,
                "consistency_warning": None,
                "needs_clarification": False,
                "clarification_question": None,
                "clinical_rationale": "",
                "healing_insight": None,
                "severity_delta": None,
            }

        redness = current_metrics.get("redness", 0)
        inflammation = current_metrics.get("inflammation", 0)
        scaling = current_metrics.get("scaling", 0)
        texture = current_metrics.get("texture", 0)

        # Build severity delta context
        if baseline_score > 0 and visit_number > 1:
            delta = baseline_score - current_score
            delta_pct = round((delta / baseline_score) * 100, 1)
            delta_ctx = f"improved by {delta_pct}%" if delta > 0 else f"worsened by {abs(delta_pct)}%"
            baseline_ctx = f"""
BASELINE (Day 1 — Visit 1):
- Severity: {baseline_level}
- Score: {baseline_score:.2f}

CURRENT (Visit {visit_number}):
- Severity: {current_level}
- Score: {current_score:.2f}
- Overall change: Severity has {delta_ctx} since baseline."""
        else:
            baseline_ctx = f"This is the FIRST visit. No baseline comparison available yet."

        # Build the master prompt
        target_part_ctx = f'"{target_body_part}"' if target_body_part else "NOT SET (first visit — identify and lock the body part)"
        journey_ctx = f'"{journey_title}"' if journey_title else "New Journey"

        prompt = f"""You are a Senior Dermatologist and Clinical Image Analyst for a skin tracking app.
Your task is to validate a skin tracking journey and provide clinical insights from the provided image(s).

JOURNEY CONTEXT:
- Journey: {journey_ctx}
- Target Body Part (Locked): {target_part_ctx}
- Visit Number: {visit_number}

CURRENT SCAN BIOMARKERS:
- Severity Grade: {current_level.upper()}
- Redness Index: {redness:.1f}%
- Inflammation: {inflammation:.1f}%
- Scaling/Flakiness: {scaling:.1f}%
- Surface Texture: {texture:.1f}/10

{baseline_ctx}

YOUR TASKS:
1. IDENTIFY: Examine the current image and identify the specific body part shown.
   Examples: "Forehead", "Left Cheek", "Upper Back", "Left Forearm", "Scalp"
   Be specific — not just "Face" but "Right Cheek" or "Chin".

2. VERIFY: Compare your identified body part with the Target Body Part.
   - If they MATCH or Target is NOT SET → is_consistent_with_journey = true
   - If they DO NOT MATCH → is_consistent_with_journey = false, write a clear warning.
   - If you CANNOT confidently identify the body part → needs_clarification = true

3. COMPARE (only if visit > 1 and baseline image is provided):
   - Visually compare the two images for improvements: reduced redness, less swelling, clearer skin texture.
   - Write a specific healing_insight referencing BOTH visual and biomarker changes.

4. RATIONALE: Write 2 sentences explaining WHY the skin received this severity grade.
   Reference the specific biomarker that is driving the score.

5. DELTA SUMMARY: Provide a short severity_delta object with:
   - trend: "improving" | "worsening" | "stable" | "first_visit"
   - key_change: The single most important change observed (e.g. "Redness reduced by 15%")

CRITICAL RULES:
- Be empathetic but clinically accurate.
- Do NOT invent biomarker values — only use the ones provided.
- For is_consistent_with_journey, be strict: even if close (e.g. "Cheek" vs "Forehead"), flag it.
- If the image is unclear or too dark to identify the body part, set needs_clarification = true.

RETURN ONLY valid JSON — no markdown, no explanation outside the JSON:
{{
  "identified_body_part": "string",
  "is_consistent_with_journey": true,
  "consistency_warning": null,
  "needs_clarification": false,
  "clarification_question": null,
  "clinical_rationale": "2-sentence explanation",
  "healing_insight": "null or comparison string",
  "severity_delta": {{
    "trend": "first_visit",
    "key_change": "Baseline established."
  }}
}}"""

        try:
            model = cls._genai_client.GenerativeModel("gemini-1.5-flash-latest")
            parts = [prompt]

            # Always include current image
            if current_image_bytes:
                parts.append({"mime_type": "image/jpeg", "data": current_image_bytes})

            # Include baseline image for comparison if available
            if baseline_image_bytes and visit_number > 1:
                parts.append({"mime_type": "image/jpeg", "data": baseline_image_bytes})

            response = model.generate_content(parts)
            result = cls._parse_json(response.text.strip())

            # Ensure all expected keys exist with safe defaults
            return {
                "identified_body_part": result.get("identified_body_part", "Unknown"),
                "is_consistent_with_journey": result.get("is_consistent_with_journey", True),
                "consistency_warning": result.get("consistency_warning"),
                "needs_clarification": result.get("needs_clarification", False),
                "clarification_question": result.get("clarification_question"),
                "clinical_rationale": result.get("clinical_rationale", ""),
                "healing_insight": result.get("healing_insight"),
                "severity_delta": result.get("severity_delta", {"trend": "first_visit", "key_change": "Baseline established."}),
            }

        except Exception as e:
            logger.warning(f"Smart Guard multimodal analysis failed: {e}")
            return {
                "identified_body_part": "Unknown",
                "is_consistent_with_journey": True,
                "consistency_warning": None,
                "needs_clarification": False,
                "clarification_question": None,
                "clinical_rationale": "",
                "healing_insight": None,
                "severity_delta": {"trend": "unknown", "key_change": "Analysis unavailable."},
            }

    @classmethod
    def get_treatment_response(cls, disease: str) -> str:
        """Provide detailed treatment advice for a diagnosed disease."""
        cls._initialize()
        prompt = f"""
You are a clinical skin care assistant. The user wants treatments for '{disease}'.

TASK:
1) List 3-4 actionable at-home care tips.
2) List common over-the-counter (OTC) treatments if applicable.
3) Add a safety warning that they must consult a doctor before starting any treatment.
4) Keep it clear and professional.

Assistant:"""
        return cls._generate(prompt)

    @classmethod
    def validate_prediction(cls, user_symptoms: str, local_prediction: str, local_confidence: float) -> Dict:
        """Double-check local prediction"""
        cls._initialize()
        if not cls._initialized:
            return {"error": "unavailable"}
        
        prompt = f"""Validate: {local_prediction} ({local_confidence:.0%}) for symptoms: {user_symptoms}
Return JSON: {{"agreement": "agree|disagree|unsure", "your_diagnosis": "name", "your_confidence": 0-100}}"""
        
        text = cls._generate(prompt)
        if text:
            try:
                return cls._parse_json(text)
            except:
                pass
        return {"agreement": "unsure", "your_diagnosis": local_prediction}

    @classmethod
    def get_provider_info(cls) -> Dict:
        """Get current provider info"""
        cls._initialize()
        return {"provider": cls._provider or "none", "available": cls._initialized}

    @classmethod
    def analyze_skin_condition(cls, image_bytes: bytes, symptoms: str, local_pred: str = None, local_conf: float = 0.0) -> Dict:
        """Analyze - requires Gemini for images"""
        cls._initialize()
        
        # We MUST use Gemini for images
        image_client = cls._genai_client
        if not image_client:
            return {"error": "Gemini unavailable"}
        
        prompt = f"""
You are the Lead Clinical Dermatology Consultant for a Hybrid AI System.
Our system is IMAGE-DOMINANT. Your job is to provide a final diagnosis based PRIMARILY on the visual evidence, using the patient's symptoms only to clarify or refine the visual diagnosis.

TASK:
1. Verify if the provided image contains human skin or a skin condition.
2. If the image is NOT of human skin (e.g., animal, object, landscape, food), set "is_skin": false.
3. If it IS skin, analyze it based on: 
   - Visual Model Suggestion (PRIMARY SIGNAL): '{local_pred}' 
   - Patient Symptoms (SECONDARY CONTEXT): '{symptoms}'
   - Overall Confidence: {local_conf:.0%}
   *Note: If the Visual Model and Symptom Model disagree, default to trusting the Visual Model unless the symptoms completely contradict it or the visual model's suggestion is clinically impossible given the symptoms. Explain your decision in the reasoning.*

RETURN JSON ONLY:
{{
  "is_skin": true/false,
  "disease": "name (The unified final diagnosis)",
  "confidence": 0.0-1.0,
  "severity": "mild|moderate|severe",
  "reasoning": "clinical explanation, including how you used the symptoms to clarify the visual diagnosis",
  "treatment": [],
  "warning": "safety warning"
}}
"""
        
        try:
            # Prefer 1.5-flash for speed and reliability with multimodal
            model_name = 'gemini-1.5-flash-latest'
            model = image_client.GenerativeModel(model_name)
            
            if image_bytes:
                response = model.generate_content([prompt, {'mime_type': 'image/jpeg', 'data': image_bytes}])
            else:
                response = model.generate_content(prompt)
                
            return cls._parse_json(response.text.strip())
        except Exception as e:
            error_msg = str(e)
            logger.warning(f"Gemini failed: {error_msg}. Attempting Groq fallback...")
            
            # Fallback to Groq Text-only (Extremely reliable)
            try:
                groq_client = cls._get_groq()
                if groq_client:
                    # For Groq, we assume is_skin is True if the local models reached this stage
                    chat_completion = groq_client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt.replace("Verify if the provided image", "Analyze the case based on symptoms")}],
                        model="llama-3.3-70b-versatile",
                        response_format={"type": "json_object"}
                    )
                    return cls._parse_json(chat_completion.choices[0].message.content)
            except Exception as ge:
                logger.error(f"Groq fallback also failed: {ge}")
                
            return {"error": error_msg}