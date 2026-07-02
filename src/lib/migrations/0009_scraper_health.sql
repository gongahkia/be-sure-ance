CREATE TABLE IF NOT EXISTS public.scraper_health (
    id SERIAL PRIMARY KEY,
    carrier_key TEXT NOT NULL,
    display_name TEXT NOT NULL,
    support_status TEXT NOT NULL CHECK (
        support_status IN ('supported', 'unsupported')
    ),
    last_success_at TIMESTAMPTZ,
    last_failure_at TIMESTAMPTZ,
    last_run_at TIMESTAMPTZ,
    last_error TEXT,
    row_count INT NOT NULL DEFAULT 0 CHECK (row_count >= 0),
    validation_status TEXT NOT NULL DEFAULT 'not_run' CHECK (
        validation_status IN ('passed', 'failed', 'error', 'no_baseline', 'not_run', 'unsupported')
    ),
    validation_checked_at TIMESTAMPTZ,
    validation_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT scraper_health_carrier_key_key UNIQUE (carrier_key)
);

CREATE INDEX IF NOT EXISTS idx_scraper_health_status
ON public.scraper_health (support_status, validation_status, last_run_at DESC);

ALTER TABLE public.scraper_health ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "public read access" ON public.scraper_health;
CREATE POLICY "public read access"
ON public.scraper_health FOR SELECT
TO anon, authenticated
USING (true);
REVOKE ALL ON TABLE public.scraper_health FROM anon, authenticated;
GRANT SELECT ON TABLE public.scraper_health TO anon, authenticated;
GRANT ALL ON TABLE public.scraper_health TO service_role;
REVOKE ALL ON SEQUENCE public.scraper_health_id_seq FROM anon, authenticated;
GRANT USAGE, SELECT ON SEQUENCE public.scraper_health_id_seq TO service_role;
