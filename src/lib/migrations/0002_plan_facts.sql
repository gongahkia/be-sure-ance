CREATE TABLE IF NOT EXISTS public.plan_facts (
    id SERIAL PRIMARY KEY,
    insurer TEXT NOT NULL,
    plan_slug TEXT NOT NULL,
    field_name TEXT NOT NULL,
    field_value JSONB NOT NULL,
    source_url TEXT NOT NULL,
    source_type TEXT NOT NULL CHECK (
        source_type IN ('brochure_pdf', 'product_page', 'manual_entry')
    ),
    scraped_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_verified_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_plan_facts_unique_fact
ON public.plan_facts (insurer, plan_slug, field_name);

CREATE INDEX IF NOT EXISTS idx_plan_facts_lookup
ON public.plan_facts (insurer, plan_slug);

CREATE INDEX IF NOT EXISTS idx_plan_facts_source
ON public.plan_facts (source_type, last_verified_at);

ALTER TABLE public.plan_facts ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "public read access" ON public.plan_facts;
CREATE POLICY "public read access"
ON public.plan_facts FOR SELECT
TO anon, authenticated
USING (true);
REVOKE ALL ON TABLE public.plan_facts FROM anon, authenticated;
GRANT SELECT ON TABLE public.plan_facts TO anon, authenticated;
GRANT ALL ON TABLE public.plan_facts TO service_role;
REVOKE ALL ON SEQUENCE public.plan_facts_id_seq FROM anon, authenticated;
GRANT USAGE, SELECT ON SEQUENCE public.plan_facts_id_seq TO service_role;

-- Writers must upsert with:
-- ON CONFLICT (insurer, plan_slug, field_name) DO UPDATE SET
--     field_value = EXCLUDED.field_value,
--     source_url = EXCLUDED.source_url,
--     source_type = EXCLUDED.source_type,
--     scraped_at = EXCLUDED.scraped_at,
--     last_verified_at = EXCLUDED.last_verified_at
