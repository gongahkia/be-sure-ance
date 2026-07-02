CREATE TABLE IF NOT EXISTS public.brochure_version_history (
    id SERIAL PRIMARY KEY,
    insurer TEXT NOT NULL,
    plan_slug TEXT NOT NULL,
    plan_name TEXT NOT NULL,
    source_url TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    storage_bucket TEXT NOT NULL,
    storage_key TEXT NOT NULL,
    size_bytes INT NOT NULL,
    content_type TEXT NOT NULL,
    source_last_modified_at TEXT,
    first_seen_at TIMESTAMPTZ NOT NULL,
    last_seen_at TIMESTAMPTZ NOT NULL,
    captured_at TIMESTAMPTZ NOT NULL,
    extracted_text TEXT,
    text_sha256 TEXT,
    CONSTRAINT brochure_version_history_unique_hash
        UNIQUE (insurer, plan_slug, source_url, sha256)
);

CREATE INDEX IF NOT EXISTS idx_brochure_version_history_lookup
ON public.brochure_version_history (insurer, plan_slug, captured_at DESC);

CREATE INDEX IF NOT EXISTS idx_brochure_version_history_source
ON public.brochure_version_history (source_url, sha256);

ALTER TABLE public.brochure_version_history ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "public read access" ON public.brochure_version_history;
CREATE POLICY "public read access"
ON public.brochure_version_history FOR SELECT
TO anon, authenticated
USING (true);
REVOKE ALL ON TABLE public.brochure_version_history FROM anon, authenticated;
GRANT SELECT ON TABLE public.brochure_version_history TO anon, authenticated;
GRANT ALL ON TABLE public.brochure_version_history TO service_role;
REVOKE ALL ON SEQUENCE public.brochure_version_history_id_seq FROM anon, authenticated;
GRANT USAGE, SELECT ON SEQUENCE public.brochure_version_history_id_seq TO service_role;

CREATE TABLE IF NOT EXISTS public.brochure_change_alerts (
    id SERIAL PRIMARY KEY,
    insurer TEXT NOT NULL,
    plan_slug TEXT NOT NULL,
    plan_name TEXT NOT NULL,
    source_url TEXT NOT NULL,
    previous_sha256 TEXT NOT NULL,
    current_sha256 TEXT NOT NULL,
    previous_captured_at TIMESTAMPTZ,
    current_captured_at TIMESTAMPTZ NOT NULL,
    change_detected_at TIMESTAMPTZ NOT NULL,
    alert_status TEXT NOT NULL CHECK (alert_status IN ('pending', 'sent', 'suppressed')),
    summary TEXT NOT NULL,
    text_diff TEXT,
    html_diff TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT brochure_change_alerts_unique_change
        UNIQUE (insurer, plan_slug, source_url, previous_sha256, current_sha256)
);

CREATE INDEX IF NOT EXISTS idx_brochure_change_alerts_lookup
ON public.brochure_change_alerts (insurer, plan_slug, change_detected_at DESC);

ALTER TABLE public.brochure_change_alerts ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "public read access" ON public.brochure_change_alerts;
CREATE POLICY "public read access"
ON public.brochure_change_alerts FOR SELECT
TO anon, authenticated
USING (true);
REVOKE ALL ON TABLE public.brochure_change_alerts FROM anon, authenticated;
GRANT SELECT ON TABLE public.brochure_change_alerts TO anon, authenticated;
GRANT ALL ON TABLE public.brochure_change_alerts TO service_role;
REVOKE ALL ON SEQUENCE public.brochure_change_alerts_id_seq FROM anon, authenticated;
GRANT USAGE, SELECT ON SEQUENCE public.brochure_change_alerts_id_seq TO service_role;
