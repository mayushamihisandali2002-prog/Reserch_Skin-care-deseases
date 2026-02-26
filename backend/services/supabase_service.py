# ============================================================================
# SUPABASE PYTHON SERVICE
# For Flask backend integration
# ============================================================================

import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from supabase import create_client, Client

class SupabaseService:
    """Supabase service for Python backend database operations."""
    
    _client: Optional[Client] = None
    
    # Supabase credentials (can be overridden by environment variables)
    SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://bsgvtoaadjulgccwqrdj.supabase.co')
    SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY', 'sb_publishable_WcVdg4dwPA_XPim3oSQ2bQ_EgS1O69P')
    
    @classmethod
    def get_client(cls) -> Client:
        """Get or create Supabase client."""
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
    ) -> Dict[str, Any]:
        """Save a skin analysis result."""
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
        }
        
        result = client.table('skin_analyses').insert(data).execute()
        return result.data[0] if result.data else None
    
    @classmethod
    def get_user_analyses(cls, user_id: str, limit: int = 20) -> List[Dict]:
        """Get skin analysis history for a user."""
        client = cls.get_client()
        
        result = client.table('skin_analyses') \
            .select('*') \
            .eq('user_id', user_id) \
            .order('created_at', desc=True) \
            .limit(limit) \
            .execute()
        
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
    def update_user_profile(cls, user_id: str, **kwargs) -> Dict[str, Any]:
        """Update a user's profile."""
        client = cls.get_client()
        
        result = client.table('profiles') \
            .update(kwargs) \
            .eq('id', user_id) \
            .execute()
        
        return result.data[0] if result.data else None
    
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
