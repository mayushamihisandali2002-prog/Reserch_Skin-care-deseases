# ============================================================================
# SUPABASE PYTHON SERVICE
# For Flask backend integration
# ============================================================================

import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

BACKEND_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"

if BACKEND_ENV_PATH.exists():
    load_dotenv(BACKEND_ENV_PATH, override=False)

class SupabaseService:
    """Supabase service for Python backend database operations."""
    
    _client: Optional[Client] = None
    
    # Backend must use a server-side key, never the publishable/anon key.
    SUPABASE_URL = os.getenv('SUPABASE_URL', '').strip()
    SUPABASE_KEY = (
        os.getenv('SUPABASE_SECRET_KEY')
        or os.getenv('SUPABASE_SERVICE_KEY')
        or ''
    ).strip()
    
    @classmethod
    def get_client(cls) -> Client:
        """Get or create Supabase client."""
        if not cls.SUPABASE_URL or not cls.SUPABASE_KEY:
            raise RuntimeError(
                "Supabase backend is not configured. Set SUPABASE_URL and "
                "SUPABASE_SECRET_KEY in the local .env file."
            )
        if cls._client is None:
            cls._client = create_client(cls.SUPABASE_URL, cls.SUPABASE_KEY)
        return cls._client
    
    @classmethod
    def initialize(cls, url: str = None, key: str = None):
        """Initialize Supabase with custom credentials."""
        if url:
            cls.SUPABASE_URL = url
        if key:
            cls.SUPABASE_KEY = key
        cls._client = create_client(cls.SUPABASE_URL, cls.SUPABASE_KEY)
    
    # =========================================================================
    # CHAT SESSION OPERATIONS
    # =========================================================================

    @classmethod
    def ensure_chat_session(
        cls,
        user_id: str,
        session_id: str,
        title: str = "New Conversation",
    ) -> Optional[Dict[str, Any]]:
        """Return an existing chat session or create it if missing."""
        client = cls.get_client()

        existing = (
            client.table('chat_sessions')
            .select('*')
            .eq('id', session_id)
            .limit(1)
            .execute()
        )
        if existing.data:
            return existing.data[0]

        data = {
            'id': session_id,
            'user_id': user_id,
            'title': title,
        }
        result = client.table('chat_sessions').insert(data).execute()
        return result.data[0] if result.data else None

    @classmethod
    def update_chat_session_title(cls, session_id: str, title: str):
        """Update the title of a chat session."""
        client = cls.get_client()
        client.table('chat_sessions').update({'title': title}).eq('id', session_id).execute()

    @classmethod
    def get_user_sessions(cls, user_id: str) -> List[Dict]:
        """List all chat sessions for a user."""
        client = cls.get_client()
        result = client.table('chat_sessions') \
            .select('*') \
            .eq('user_id', user_id) \
            .order('created_at', desc=True) \
            .execute()
        return result.data or []

    @classmethod
    def delete_chat_session(cls, session_id: str):
        """Delete a chat session and its messages."""
        client = cls.get_client()
        # Messages will be deleted by cascade if DB is set up, or manually:
        client.table('chat_messages').delete().eq('session_id', session_id).execute()
        client.table('chat_sessions').delete().eq('id', session_id).execute()

    # =========================================================================
    # CHAT MESSAGE OPERATIONS
    # =========================================================================
    
    @classmethod
    def save_chat_message(
        cls,
        user_id: str,
        session_id: str,
        sender: str,  # 'user' or 'bot'
        message: str,
        predicted_disease: str = None,
        confidence: float = None,
        confidence_level: str = None,
        model_used: str = None,
        treatments: List[Dict] = None,
        follow_up_questions: List[str] = None,
        needs_more_info: bool = False,
    ) -> Dict[str, Any]:
        """Save a chat message to the database."""
        client = cls.get_client()
        
        data = {
            'user_id': user_id,
            'session_id': session_id,
            'sender': sender,
            'message': message,
            'predicted_disease': predicted_disease,
            'confidence': confidence,
            'confidence_level': confidence_level,
            'model_used': model_used,
            'treatments': treatments,
            'follow_up_questions': follow_up_questions,
            'needs_more_info': needs_more_info,
        }
        
        result = client.table('chat_messages').insert(data).execute()
        return result.data[0] if result.data else None
    
    @classmethod
    def get_chat_history(cls, session_id: str, limit: int = 100) -> List[Dict]:
        """Get chat history for a session."""
        client = cls.get_client()
        
        result = client.table('chat_messages') \
            .select('*') \
            .eq('session_id', session_id) \
            .order('created_at', desc=False) \
            .limit(limit) \
            .execute()
        
        return result.data or []
    
    # =========================================================================
    # SKIN ANALYSIS OPERATIONS
    # =========================================================================
    
    @classmethod
    def save_skin_analysis(
        cls,
        user_id: str,
        image_url: str,
        predicted_disease: str,
        confidence: float,
        confidence_level: str,
        all_predictions: Dict = None,
        treatments: List[Dict] = None,
        body_location: str = None,
        symptoms_description: str = None,
        duration: str = None,
        model_used: str = 'resnet18',
        journey_id: str = None,
        body_part_detected: str = None,
        image_metadata: Dict = None,
    ) -> Dict[str, Any]:
        """Save a skin analysis result with journey tracking support."""
        client = cls.get_client()
        
        data = {
            'user_id': user_id,
            'image_url': image_url,
            'predicted_disease': predicted_disease,
            'confidence': confidence,
            'confidence_level': confidence_level,
            'all_predictions': all_predictions,
            'treatments': treatments,
            'body_location': body_location,
            'symptoms_description': symptoms_description,
            'duration': duration,
            'model_used': model_used,
            'journey_id': journey_id,
            'body_part_detected': body_part_detected,
            'image_metadata': image_metadata,
        }
        
        result = client.table('skin_analyses').insert(data).execute()
        return result.data[0] if result.data else None
    
    @classmethod
    def get_user_analyses(
        cls,
        user_id: str,
        limit: int = 20,
        journey_id: str = None,
    ) -> List[Dict]:
        """Get skin analysis history for a user."""
        client = cls.get_client()

        query = (
            client.table('skin_analyses')
            .select('*')
            .eq('user_id', user_id)
        )
        if journey_id:
            query = query.eq('journey_id', journey_id)

        result = query.order('created_at', desc=True).limit(limit).execute()
        
        return result.data or []
    
    # =========================================================================
    # DIAGNOSIS HISTORY OPERATIONS
    # =========================================================================
    
    @classmethod
    def save_diagnosis(
        cls,
        user_id: str,
        disease_name: str,
        confidence: float,
        diagnosis_type: str,  # 'text', 'image', or 'fused'
        chat_message_id: str = None,
        skin_analysis_id: str = None,
    ) -> Dict[str, Any]:
        """Save a diagnosis to history."""
        client = cls.get_client()
        
        data = {
            'user_id': user_id,
            'disease_name': disease_name,
            'confidence': confidence,
            'diagnosis_type': diagnosis_type,
            'chat_message_id': chat_message_id,
            'skin_analysis_id': skin_analysis_id,
        }
        
        result = client.table('diagnosis_history').insert(data).execute()
        return result.data[0] if result.data else None
    
    @classmethod
    def get_diagnosis_history(cls, user_id: str, limit: int = 50) -> List[Dict]:
        """Get diagnosis history for a user."""
        client = cls.get_client()
        
        result = client.table('diagnosis_history') \
            .select('*') \
            .eq('user_id', user_id) \
            .order('created_at', desc=True) \
            .limit(limit) \
            .execute()
        
        return result.data or []
    
    # =========================================================================
    # USER PROFILE OPERATIONS
    # =========================================================================
    
    @classmethod
    def get_user_profile(cls, user_id: str) -> Optional[Dict]:
        """Get a user's profile."""
        client = cls.get_client()
        
        result = client.table('profiles') \
            .select('*') \
            .eq('id', user_id) \
            .single() \
            .execute()
        
        return result.data
    
    @classmethod
    def update_user_profile(cls, user_id: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a user's profile with personalization fields."""
        client = cls.get_client()
        
        # Filter allowed fields
        allowed_fields = [
            'full_name', 'skin_type', 'gender', 'date_of_birth', 
            'allergies', 'medical_history', 'current_medications', 
            'tracking_preference'
        ]
        updates = {k: v for k, v in profile_data.items() if k in allowed_fields}
        
        result = client.table('profiles') \
            .update(updates) \
            .eq('id', user_id) \
            .execute()
        
        return result.data[0] if result.data else None

    # =========================================================================
    # TRACKING JOURNEY OPERATIONS
    # =========================================================================

    @classmethod
    def create_journey(cls, user_id: str, title: str, body_part: str, frequency: str = 'weekly') -> Dict[str, Any]:
        """Create a new tracking journey for a user."""
        client = cls.get_client()
        
        data = {
            'user_id': user_id,
            'title': title,
            'body_part': body_part,
            'frequency': frequency,
            'status': 'active'
        }
        
        result = client.table('tracking_journeys').insert(data).execute()
        return result.data[0] if result.data else None

    @classmethod
    def get_user_journeys(cls, user_id: str) -> List[Dict]:
        """List all tracking journeys for a user."""
        client = cls.get_client()
        
        result = client.table('tracking_journeys') \
            .select('*') \
            .eq('user_id', user_id) \
            .order('created_at', desc=True) \
            .execute()
        
        return result.data or []

    @classmethod
    def get_journey_part(cls, journey_id: str) -> Optional[str]:
        """Retrieve the target body part for a journey."""
        client = cls.get_client()
        
        result = client.table('tracking_journeys') \
            .select('body_part') \
            .eq('id', journey_id) \
            .single() \
            .execute()
        
        return result.data['body_part'] if result.data else None

    # =========================================================================
    # SEVERITY TRACKING OPERATIONS
    # =========================================================================

    @classmethod
    def save_severity_visit(
        cls,
        user_id: str,
        severity_level: str,
        severity_score: float,
        confidence: float,
        metrics: Optional[Dict[str, Any]] = None,
        journey_id: str = None,
        metadata: Optional[Dict[str, Any]] = None,
        captured_at: str = None,
    ) -> Dict[str, Any]:
        """Persist a severity tracking visit for a user."""
        client = cls.get_client()

        data = {
            'user_id': user_id,
            'journey_id': journey_id,
            'severity_level': severity_level,
            'severity_score': severity_score,
            'confidence': confidence,
            'metrics_json': metrics or {},
            'metadata': metadata or {},
            'captured_at': captured_at or datetime.utcnow().isoformat(),
        }

        result = client.table('severity_visits').insert(data).execute()
        return result.data[0] if result.data else None

    @classmethod
    def get_severity_visits(
        cls,
        user_id: str,
        limit: int = 100,
        journey_id: str = None,
    ) -> List[Dict]:
        """Return persisted severity visits for a user."""
        client = cls.get_client()

        query = (
            client.table('severity_visits')
            .select('*')
            .eq('user_id', user_id)
        )
        if journey_id:
            query = query.eq('journey_id', journey_id)

        result = query.order('captured_at', desc=False).limit(limit).execute()
        return result.data or []
    
    # =========================================================================
    # TREATMENT TRACKING OPERATIONS
    # =========================================================================
    
    @classmethod
    def add_treatment(
        cls,
        user_id: str,
        treatment_name: str,
        treatment_type: str = None,
        dosage: str = None,
        frequency: str = None,
        diagnosis_id: str = None,
        notes: str = None,
    ) -> Dict[str, Any]:
        """Add a treatment to track."""
        client = cls.get_client()
        
        data = {
            'user_id': user_id,
            'treatment_name': treatment_name,
            'treatment_type': treatment_type,
            'dosage': dosage,
            'frequency': frequency,
            'diagnosis_id': diagnosis_id,
            'notes': notes,
        }
        
        result = client.table('treatment_tracking').insert(data).execute()
        return result.data[0] if result.data else None
    
    @classmethod
    def get_active_treatments(cls, user_id: str) -> List[Dict]:
        """Get active treatments for a user."""
        client = cls.get_client()
        
        result = client.table('treatment_tracking') \
            .select('*') \
            .eq('user_id', user_id) \
            .eq('status', 'active') \
            .order('start_date', desc=True) \
            .execute()
        
        return result.data or []


# ============================================================================
# USAGE EXAMPLE
# ============================================================================
if __name__ == '__main__':
    # Initialize with environment variables or direct values
    SupabaseService.initialize(
        url='YOUR_SUPABASE_URL',
        key='YOUR_SUPABASE_SERVICE_KEY'
    )
    
    # Test connection
    print("Supabase connected successfully!")
