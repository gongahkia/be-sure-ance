CREATE TABLE IF NOT EXISTS public.moh_institutions (
    id SERIAL PRIMARY KEY,
    canonical_id TEXT NOT NULL,
    canonical_name TEXT NOT NULL,
    aliases TEXT[] NOT NULL DEFAULT '{}',
    organization_name TEXT,
    effective_date TEXT,
    source_dataset_id TEXT NOT NULL,
    source_record_id TEXT NOT NULL,
    source_url TEXT NOT NULL,
    scraped_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT moh_institutions_canonical_id_key UNIQUE (canonical_id)
);

CREATE INDEX IF NOT EXISTS idx_moh_institutions_name
ON public.moh_institutions (canonical_name);

CREATE INDEX IF NOT EXISTS idx_moh_institutions_source
ON public.moh_institutions (source_dataset_id, source_record_id);

ALTER TABLE public.moh_institutions ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "public read access" ON public.moh_institutions;
CREATE POLICY "public read access"
ON public.moh_institutions FOR SELECT
TO anon, authenticated
USING (true);
REVOKE ALL ON TABLE public.moh_institutions FROM anon, authenticated;
GRANT SELECT ON TABLE public.moh_institutions TO anon, authenticated;
GRANT ALL ON TABLE public.moh_institutions TO service_role;
REVOKE ALL ON SEQUENCE public.moh_institutions_id_seq FROM anon, authenticated;
GRANT USAGE, SELECT ON SEQUENCE public.moh_institutions_id_seq TO service_role;

-- Source: MOH NEHR participating institutions on data.gov.sg.
-- Dataset ID: d_2864c425e22ddb89969585820629adf8.
-- Writers must upsert with ON CONFLICT (canonical_id).
