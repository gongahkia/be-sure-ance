CREATE TABLE IF NOT EXISTS public.mas_regulatory_events (
    id SERIAL PRIMARY KEY,
    carrier_key TEXT NOT NULL,
    carrier_name TEXT NOT NULL,
    event_title TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_date DATE NOT NULL,
    source_url TEXT NOT NULL,
    source_type TEXT NOT NULL CHECK (source_type IN ('mas_news', 'mas_enforcement_page', 'manual_entry')),
    summary TEXT NOT NULL,
    matched_alias TEXT NOT NULL,
    match_confidence NUMERIC NOT NULL CHECK (match_confidence >= 0 AND match_confidence <= 1),
    match_status TEXT NOT NULL CHECK (match_status IN ('matched', 'needs_review')),
    source_published_at DATE NOT NULL,
    limitations TEXT[] NOT NULL DEFAULT '{}',
    scraped_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_verified_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT mas_regulatory_events_unique_source
        UNIQUE (carrier_key, event_title, source_url)
);

CREATE INDEX IF NOT EXISTS idx_mas_regulatory_events_carrier
ON public.mas_regulatory_events (carrier_key, event_date DESC);

CREATE INDEX IF NOT EXISTS idx_mas_regulatory_events_source
ON public.mas_regulatory_events (source_type, event_date DESC);

ALTER TABLE public.mas_regulatory_events ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "public read access" ON public.mas_regulatory_events;
CREATE POLICY "public read access"
ON public.mas_regulatory_events FOR SELECT
TO anon, authenticated
USING (true);
REVOKE ALL ON TABLE public.mas_regulatory_events FROM anon, authenticated;
GRANT SELECT ON TABLE public.mas_regulatory_events TO anon, authenticated;
GRANT ALL ON TABLE public.mas_regulatory_events TO service_role;
REVOKE ALL ON SEQUENCE public.mas_regulatory_events_id_seq FROM anon, authenticated;
GRANT USAGE, SELECT ON SEQUENCE public.mas_regulatory_events_id_seq TO service_role;
