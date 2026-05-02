-- ============================================================================
-- SKIN CARE TRACKING & PERSONALIZATION EXTENSION
-- ============================================================================

-- Safe to run after backend/database/schema.sql.
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 1. Extend Profiles for Personalization
ALTER TABLE public.profiles 
ADD COLUMN IF NOT EXISTS allergies TEXT[],
ADD COLUMN IF NOT EXISTS medical_history TEXT,
ADD COLUMN IF NOT EXISTS current_medications TEXT,
ADD COLUMN IF NOT EXISTS tracking_preference TEXT DEFAULT 'weekly' CHECK (tracking_preference IN ('daily', 'weekly', 'none'));

-- 2. Tracking Journeys (Progress Tracking for specific areas)
CREATE TABLE IF NOT EXISTS public.tracking_journeys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL, -- e.g., "Left Cheek Acne"
    body_part TEXT NOT NULL, -- e.g., "Face", "Forehead", "Cheek", "Neck", "Arm", "Leg"
    specific_location TEXT, -- e.g., "Near jawline"
    frequency TEXT DEFAULT 'weekly',
    initial_diagnosis TEXT,
    target_clearance_date DATE,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'archived')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2b. Severity Visits (Persistent severity tracking log)
CREATE TABLE IF NOT EXISTS public.severity_visits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    journey_id UUID REFERENCES public.tracking_journeys(id) ON DELETE SET NULL,
    severity_level TEXT NOT NULL CHECK (severity_level IN ('mild', 'moderate', 'severe', 'Mild', 'Moderate', 'Severe')),
    severity_score DECIMAL(6, 2) NOT NULL,
    confidence DECIMAL(5, 4),
    metrics_json JSONB DEFAULT '{}'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    image_path TEXT, -- Path to stored image for visual tracking
    captured_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Update Skin Analysis with Tracking Logic
ALTER TABLE public.skin_analyses 
ADD COLUMN IF NOT EXISTS journey_id UUID REFERENCES public.tracking_journeys(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS body_part_detected TEXT, -- AI detected part
ADD COLUMN IF NOT EXISTS image_metadata JSONB; -- EXIF data, quality metrics

-- 4. Enable RLS on Tracking Journeys
ALTER TABLE public.tracking_journeys ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.severity_visits ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can manage own tracking journeys" ON public.tracking_journeys;
CREATE POLICY "Users can manage own tracking journeys" ON public.tracking_journeys
    FOR ALL USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can manage own severity visits" ON public.severity_visits;
CREATE POLICY "Users can manage own severity visits" ON public.severity_visits
    FOR ALL USING (auth.uid() = user_id);

-- 5. Trigger for updated_at in journeys
DROP TRIGGER IF EXISTS update_tracking_journeys_updated_at ON public.tracking_journeys;
CREATE TRIGGER update_tracking_journeys_updated_at
    BEFORE UPDATE ON public.tracking_journeys
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Indexes
CREATE INDEX IF NOT EXISTS idx_tracking_journeys_user_id ON public.tracking_journeys(user_id);
CREATE INDEX IF NOT EXISTS idx_skin_analyses_journey_id ON public.skin_analyses(journey_id);
CREATE INDEX IF NOT EXISTS idx_severity_visits_user_id ON public.severity_visits(user_id);
CREATE INDEX IF NOT EXISTS idx_severity_visits_journey_id ON public.severity_visits(journey_id);
CREATE INDEX IF NOT EXISTS idx_severity_visits_captured_at ON public.severity_visits(captured_at DESC);
