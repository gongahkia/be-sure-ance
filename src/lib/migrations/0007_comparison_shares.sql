CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS public.comparison_shares (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    selected_plans JSONB NOT NULL,
    view_count INT NOT NULL DEFAULT 0 CHECK (view_count >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_viewed_at TIMESTAMPTZ,
    CONSTRAINT comparison_shares_plan_count
        CHECK (
            jsonb_typeof(selected_plans) = 'array'
            AND jsonb_array_length(selected_plans) BETWEEN 1 AND 3
        )
);

CREATE INDEX IF NOT EXISTS idx_comparison_shares_created_at
ON public.comparison_shares (created_at DESC);

ALTER TABLE public.comparison_shares ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "public read access" ON public.comparison_shares;
CREATE POLICY "public read access"
ON public.comparison_shares FOR SELECT
TO anon, authenticated
USING (true);
REVOKE ALL ON TABLE public.comparison_shares FROM anon, authenticated;
GRANT SELECT ON TABLE public.comparison_shares TO anon, authenticated;
GRANT ALL ON TABLE public.comparison_shares TO service_role;
