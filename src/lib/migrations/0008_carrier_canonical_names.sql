CREATE TABLE IF NOT EXISTS public.carrier_canonical_names (
    id SERIAL PRIMARY KEY,
    carrier_key TEXT NOT NULL,
    display_name TEXT NOT NULL,
    canonical_name TEXT NOT NULL,
    aliases TEXT[] NOT NULL DEFAULT '{}',
    mas_entity_name TEXT,
    mas_detail_url TEXT,
    mas_licence_types TEXT[] NOT NULL DEFAULT '{}',
    mas_match_status TEXT NOT NULL CHECK (
        mas_match_status IN ('matched', 'needs_review', 'unmatched')
    ),
    lia_member_name TEXT,
    lia_member_url TEXT,
    lia_member_category TEXT,
    lia_match_status TEXT NOT NULL CHECK (
        lia_match_status IN ('matched', 'needs_review', 'unmatched')
    ),
    source_urls TEXT[] NOT NULL DEFAULT '{}',
    mismatch_flags TEXT[] NOT NULL DEFAULT '{}',
    scraped_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_verified_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT carrier_canonical_names_carrier_key_key UNIQUE (carrier_key)
);

CREATE INDEX IF NOT EXISTS idx_carrier_canonical_names_key
ON public.carrier_canonical_names (carrier_key);

CREATE INDEX IF NOT EXISTS idx_carrier_canonical_names_status
ON public.carrier_canonical_names (mas_match_status, lia_match_status);

ALTER TABLE public.carrier_canonical_names ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "public read access" ON public.carrier_canonical_names;
CREATE POLICY "public read access"
ON public.carrier_canonical_names FOR SELECT
TO anon, authenticated
USING (true);
REVOKE ALL ON TABLE public.carrier_canonical_names FROM anon, authenticated;
GRANT SELECT ON TABLE public.carrier_canonical_names TO anon, authenticated;
GRANT ALL ON TABLE public.carrier_canonical_names TO service_role;
REVOKE ALL ON SEQUENCE public.carrier_canonical_names_id_seq FROM anon, authenticated;
GRANT USAGE, SELECT ON SEQUENCE public.carrier_canonical_names_id_seq TO service_role;

-- Sources:
-- MAS Financial Institutions Directory, Insurance sector:
-- https://eservices.mas.gov.sg/fid/institution?sector=Insurance
-- LIA Singapore member companies:
-- https://www.lia.org.sg/about-us/member-companies/
