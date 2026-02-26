-- ============================================================================
-- SKIN CARE ASSISTANT - DATABASE SCHEMA
-- Database: PostgreSQL (Supabase)
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- USERS TABLE (extends Supabase auth.users)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    date_of_birth DATE,
    gender TEXT CHECK (gender IN ('male', 'female', 'other', 'prefer_not_to_say')),
    skin_type TEXT CHECK (skin_type IN ('oily', 'dry', 'combination', 'normal', 'sensitive')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- CHAT SESSIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    title TEXT DEFAULT 'New Conversation',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- CHAT MESSAGES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES public.chat_sessions(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    sender TEXT NOT NULL CHECK (sender IN ('user', 'bot')),
    message TEXT NOT NULL,
    -- AI response metadata (only for bot messages)
    predicted_disease TEXT,
    confidence DECIMAL(5, 4),
    confidence_level TEXT CHECK (confidence_level IN ('high', 'medium', 'low', 'none')),
    model_used TEXT,
    treatments JSONB,
    follow_up_questions JSONB,
    needs_more_info BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- SKIN ANALYSES TABLE (Image-based diagnoses)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.skin_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL,
    image_storage_path TEXT, -- Supabase storage path
    -- Analysis results
    predicted_disease TEXT,
    confidence DECIMAL(5, 4),
    confidence_level TEXT CHECK (confidence_level IN ('high', 'medium', 'low')),
    all_predictions JSONB, -- Full prediction probabilities
    treatments JSONB,
    model_used TEXT DEFAULT 'resnet18',
    -- Optional user-provided context
    body_location TEXT,
    symptoms_description TEXT,
    duration TEXT,
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- DIAGNOSIS HISTORY TABLE (Combined text + image diagnoses)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.diagnosis_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    -- Diagnosis info
    disease_name TEXT NOT NULL,
    confidence DECIMAL(5, 4),
    diagnosis_type TEXT CHECK (diagnosis_type IN ('text', 'image', 'fused')),
    -- Source references
    chat_message_id UUID REFERENCES public.chat_messages(id) ON DELETE SET NULL,
    skin_analysis_id UUID REFERENCES public.skin_analyses(id) ON DELETE SET NULL,
    -- User feedback
    user_confirmed BOOLEAN,
    user_notes TEXT,
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- TREATMENT TRACKING TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.treatment_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    diagnosis_id UUID REFERENCES public.diagnosis_history(id) ON DELETE SET NULL,
    -- Treatment info
    treatment_name TEXT NOT NULL,
    treatment_type TEXT CHECK (treatment_type IN ('medicine', 'lifestyle', 'topical', 'other')),
    dosage TEXT,
    frequency TEXT,
    -- Tracking
    start_date DATE DEFAULT CURRENT_DATE,
    end_date DATE,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'stopped', 'paused')),
    effectiveness_rating INTEGER CHECK (effectiveness_rating >= 1 AND effectiveness_rating <= 5),
    side_effects TEXT,
    notes TEXT,
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.skin_analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.diagnosis_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.treatment_tracking ENABLE ROW LEVEL SECURITY;

-- Profiles: Users can only access their own profile
CREATE POLICY "Users can view own profile" ON public.profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON public.profiles
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile" ON public.profiles
    FOR INSERT WITH CHECK (auth.uid() = id);

-- Chat sessions: Users can only access their own sessions
CREATE POLICY "Users can manage own chat sessions" ON public.chat_sessions
    FOR ALL USING (auth.uid() = user_id);

-- Chat messages: Users can only access their own messages
CREATE POLICY "Users can manage own chat messages" ON public.chat_messages
    FOR ALL USING (auth.uid() = user_id);

-- Skin analyses: Users can only access their own analyses
CREATE POLICY "Users can manage own skin analyses" ON public.skin_analyses
    FOR ALL USING (auth.uid() = user_id);

-- Diagnosis history: Users can only access their own history
CREATE POLICY "Users can manage own diagnosis history" ON public.diagnosis_history
    FOR ALL USING (auth.uid() = user_id);

-- Treatment tracking: Users can only access their own treatments
CREATE POLICY "Users can manage own treatments" ON public.treatment_tracking
    FOR ALL USING (auth.uid() = user_id);

-- ============================================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to tables with updated_at
CREATE TRIGGER update_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chat_sessions_updated_at
    BEFORE UPDATE ON public.chat_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_treatment_tracking_updated_at
    BEFORE UPDATE ON public.treatment_tracking
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Auto-create profile on user signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email)
    VALUES (NEW.id, NEW.email);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to create profile on signup
CREATE OR REPLACE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON public.chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON public.chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_user_id ON public.chat_messages(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON public.chat_messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_skin_analyses_user_id ON public.skin_analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_skin_analyses_created_at ON public.skin_analyses(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_diagnosis_history_user_id ON public.diagnosis_history(user_id);
CREATE INDEX IF NOT EXISTS idx_treatment_tracking_user_id ON public.treatment_tracking(user_id);

-- ============================================================================
-- STORAGE BUCKET FOR SKIN IMAGES
-- ============================================================================
-- Run this in Supabase Dashboard > Storage > Create new bucket
-- Bucket name: skin-images
-- Public: false (private - requires auth)
