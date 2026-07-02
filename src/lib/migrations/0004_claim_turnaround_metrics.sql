CREATE TABLE IF NOT EXISTS public.claim_turnaround_metrics (
    id SERIAL PRIMARY KEY,
    carrier_key TEXT NOT NULL,
    carrier_name TEXT NOT NULL,
    metric_key TEXT NOT NULL,
    metric_label TEXT NOT NULL,
    metric_value JSONB NOT NULL,
    metric_unit TEXT NOT NULL,
    rank INT,
    source_year INT NOT NULL,
    source_url TEXT NOT NULL,
    source_type TEXT NOT NULL CHECK (
        source_type IN ('lia_consumer_guide', 'lia_annual_results_pdf', 'manual_entry')
    ),
    limitations TEXT[] NOT NULL DEFAULT '{}',
    scraped_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_verified_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT claim_turnaround_metrics_unique_source
        UNIQUE (carrier_key, metric_key, source_year, source_url)
);

CREATE INDEX IF NOT EXISTS idx_claim_turnaround_metrics_lookup
ON public.claim_turnaround_metrics (carrier_key, metric_key, source_year);

CREATE INDEX IF NOT EXISTS idx_claim_turnaround_metrics_source
ON public.claim_turnaround_metrics (source_type, source_year);

ALTER TABLE public.claim_turnaround_metrics ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "public read access" ON public.claim_turnaround_metrics;
CREATE POLICY "public read access"
ON public.claim_turnaround_metrics FOR SELECT
TO anon, authenticated
USING (true);
REVOKE ALL ON TABLE public.claim_turnaround_metrics FROM anon, authenticated;
GRANT SELECT ON TABLE public.claim_turnaround_metrics TO anon, authenticated;
GRANT ALL ON TABLE public.claim_turnaround_metrics TO service_role;
REVOKE ALL ON SEQUENCE public.claim_turnaround_metrics_id_seq FROM anon, authenticated;
GRANT USAGE, SELECT ON SEQUENCE public.claim_turnaround_metrics_id_seq TO service_role;
