import os
import json
import logging
from flask import jsonify, request

from services.gemini_service import GeminiService
from services.supabase_service import SupabaseService
from components.multimodal_image_audio_diagnosis import get_inference_pipeline
from .session_manager import get_session_manager

logger = logging.getLogger(__name__)

def _normalize_confidence(confidence: float) -> str:
    if confidence >= 0.70: return "high"
    if confidence >= 0.45: return "medium"
    if confidence > 0.0: return "low"
    return "none"

def register_routes(app):
    @app.route("/api/chat", methods=["POST"])
    def chat():
        if request.is_json:
            data = request.get_json(force=True, silent=True) or {}
            user_message = str(data.get("message", "")).strip()
            session_id = data.get("session_id")
            user_id = data.get("user_id")
        else:
            user_message = (request.form.get("message", "") or "").strip()
            session_id = request.form.get("session_id")
            user_id = request.form.get("user_id")
            
        if not user_message:
            return jsonify({"session_id": session_id, "reply": "Hello. Please describe any skin issues you have.", "needs_more_info": True})
            
        uid = user_id or "anonymous"
        session_mgr = get_session_manager()
        session = session_mgr.get_session(session_id) if session_id else None
        
        is_new = False
        if not session:
            session_id = session_mgr.create_session(session_id)
            session = session_mgr.get_session(session_id)
            is_new = True
            if uid != "anonymous": 
                try:
                    SupabaseService.ensure_chat_session(uid, session_id)
                except Exception as e:
                    logger.warning(f"Supabase ensure_chat_session failed: {e}")
            
        # Title Generation
        if uid != "anonymous" and (is_new or not session.conversation_history):
            try:
                title = GeminiService.generate_title(user_message)
                SupabaseService.update_chat_session_title(session_id, title)
            except: pass

        session.add_message("user", user_message)
        if uid != "anonymous": 
            try:
                SupabaseService.save_chat_message(uid, session_id, "user", user_message)
            except Exception as e:
                logger.warning(f"Supabase save_chat_message (user) failed: {e}")
        
        # 1. ALWAYS RUN ML IN BACKGROUND (IF DATA EXISTS)
        sd = session.structured_data
        ml_pred = None
        if any(sd.values()):
            try:
                text = " ".join([str(v) for v in sd.values() if v])
                ml_pred = get_inference_pipeline().predict_disease(text)
            except: pass

        # 2. UNIFIED AI BRAIN (Extraction + Triage + Random Chat + Decision)
        result = GeminiService.process_clinical_turn(
            user_message, 
            session.conversation_history, 
            sd, 
            ml_pred
        )
        
        session.structured_data = result.get("structured_data", sd)
        reply = result.get("reply", "I see. Tell me more.")
        is_final = result.get("is_final", False)
        disease = result.get("predicted_disease")
        chat_title = result.get("chat_title")
        
        # Update Session Title dynamically if AI suggests one
        if chat_title:
            try:
                if uid != "anonymous":
                    SupabaseService.update_chat_session_title(session_id, chat_title)
            except: pass

        if is_final and disease:
            session.last_predicted_disease = disease
            session.last_confidence = 0.95 # Mark as confident since AI decided

        session.add_message("assistant", reply)
        if uid != "anonymous":
            try:
                SupabaseService.save_chat_message(
                    uid, session_id, "bot", reply, 
                    predicted_disease=disease if is_final else None,
                    needs_more_info=not is_final
                )
            except Exception as e:
                logger.warning(f"Supabase save_chat_message (bot) failed: {e}")
        
        return jsonify({
            "session_id": session_id,
            "reply": reply,
            "predicted_disease": disease if is_final else None,
            "confidence_level": "high" if is_final else "none",
            "needs_more_info": not is_final,
            "conversation_history": session.conversation_history[-10:],
            "chat_title": chat_title
        })

    @app.route("/api/chat/history", methods=["GET"])
    def chat_history():
        session_id = request.args.get("session_id")
        if not session_id:
            return jsonify({"error": "session_id required"}), 400
        history = SupabaseService.get_chat_history(session_id)
        return jsonify(history)

    @app.route("/api/chat/sessions/<user_id>", methods=["GET"])
    def chat_sessions(user_id):
        sessions = SupabaseService.get_user_sessions(user_id)
        return jsonify({"sessions": sessions})

    @app.route("/api/chat/sessions/<session_id>", methods=["DELETE"])
    def delete_session(session_id):
        SupabaseService.delete_chat_session(session_id)
        return jsonify({"success": True})
