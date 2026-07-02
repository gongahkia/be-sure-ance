DROP FUNCTION IF EXISTS public.execute_sql(TEXT);

CREATE OR REPLACE FUNCTION public.table_exists(
    table_name text
)
RETURNS boolean AS
$$
BEGIN
    RETURN EXISTS (
        SELECT 1
        FROM pg_tables
        WHERE tablename = table_name
    );
END;
$$ LANGUAGE plpgsql;

GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon, authenticated;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON SEQUENCES FROM anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO service_role;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$
DECLARE
    tbl_name TEXT;
    table_list TEXT[] := ARRAY[
        'aia',
        'aig',
        'allianz',
        'allied_world',
        'china_taiping',
        'direct_asia',
        'ergo',
        'etiqa',
        'fwd',
        'hl_assurance',
        'income',
        'liberty',
        'lonpac',
        'manulife',
        'prudential',
        'qbe',
        'raffles_health',
        'sompo',
        'uoi',
        'china_life',
        'chubb',
        'tokio_marine',
        'sunlife',
        'singlife',
        'great_eastern',
        'iii',
        'hsbc'
    ];
BEGIN
    FOREACH tbl_name IN ARRAY table_list LOOP
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS %I (
                id SERIAL PRIMARY KEY,
                plan_name TEXT,
                plan_benefits TEXT[],
                plan_description TEXT,
                plan_overview TEXT,
                plan_url TEXT,
                product_brochure_url TEXT
            )', tbl_name);
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', tbl_name);
        EXECUTE format('DROP POLICY IF EXISTS "public read access" ON %I', tbl_name);
        EXECUTE format(
            'CREATE POLICY "public read access" ON %I FOR SELECT TO anon, authenticated USING (true)',
            tbl_name
        );
        EXECUTE format('REVOKE ALL ON TABLE %I FROM anon, authenticated', tbl_name);
        EXECUTE format('GRANT SELECT ON TABLE %I TO anon, authenticated', tbl_name);
        EXECUTE format('GRANT ALL ON TABLE %I TO service_role', tbl_name);
    END LOOP;
END $$;

CREATE TABLE IF NOT EXISTS specialist_resources (
    id SERIAL PRIMARY KEY,
    insurer TEXT NOT NULL,
    plan_name TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_title TEXT,
    resource_url TEXT NOT NULL,
    resource_description TEXT,
    resource_keywords TEXT[],
    source_url TEXT
);

CREATE INDEX IF NOT EXISTS idx_specialist_resources_lookup
ON specialist_resources (insurer, plan_name);

ALTER TABLE specialist_resources ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "public read access" ON specialist_resources;
CREATE POLICY "public read access"
ON specialist_resources FOR SELECT
TO anon, authenticated
USING (true);
REVOKE ALL ON TABLE specialist_resources FROM anon, authenticated;
GRANT SELECT ON TABLE specialist_resources TO anon, authenticated;
GRANT ALL ON TABLE specialist_resources TO service_role;

CREATE TABLE IF NOT EXISTS plans (
    id SERIAL PRIMARY KEY,
    insurer TEXT NOT NULL,
    plan_name TEXT NOT NULL,
    plan_slug TEXT NOT NULL,
    plan_benefits TEXT[] NOT NULL DEFAULT '{}',
    plan_description TEXT,
    plan_overview TEXT,
    plan_url TEXT,
    product_brochure_url TEXT,
    scraped_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT plans_insurer_plan_slug_key UNIQUE (insurer, plan_slug)
);

CREATE INDEX IF NOT EXISTS idx_plans_insurer_slug
ON plans (insurer, plan_slug);

CREATE INDEX IF NOT EXISTS idx_plans_insurer
ON plans (insurer);

ALTER TABLE plans ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "public read access" ON plans;
CREATE POLICY "public read access"
ON plans FOR SELECT
TO anon, authenticated
USING (true);
REVOKE ALL ON TABLE plans FROM anon, authenticated;
GRANT SELECT ON TABLE plans TO anon, authenticated;
GRANT ALL ON TABLE plans TO service_role;
REVOKE ALL ON SEQUENCE plans_id_seq FROM anon, authenticated;
GRANT USAGE, SELECT ON SEQUENCE plans_id_seq TO service_role;

CREATE TABLE IF NOT EXISTS plan_comparison_facts (
    id SERIAL PRIMARY KEY,
    insurer TEXT NOT NULL,
    plan_name TEXT NOT NULL,
    plan_slug TEXT NOT NULL,
    panel_network_size INT,
    claim_sla_days INT,
    exclusions TEXT[] NOT NULL DEFAULT '{}',
    waiting_period_days INT,
    coverage_tags TEXT[] NOT NULL DEFAULT '{}',
    brochure_hash TEXT,
    brochure_last_changed_at TIMESTAMPTZ,
    comparison_notes TEXT,
    source_url TEXT
);

ALTER TABLE plan_comparison_facts
    DROP COLUMN IF EXISTS premium_facts,
    DROP COLUMN IF EXISTS cost_sharing,
    DROP COLUMN IF EXISTS coverage_flags,
    DROP COLUMN IF EXISTS scenario_assumptions,
    ADD COLUMN IF NOT EXISTS panel_network_size INT,
    ADD COLUMN IF NOT EXISTS claim_sla_days INT,
    ADD COLUMN IF NOT EXISTS exclusions TEXT[] NOT NULL DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS waiting_period_days INT,
    ADD COLUMN IF NOT EXISTS coverage_tags TEXT[] NOT NULL DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS brochure_hash TEXT,
    ADD COLUMN IF NOT EXISTS brochure_last_changed_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_plan_comparison_facts_lookup
ON plan_comparison_facts (insurer, plan_slug);

ALTER TABLE plan_comparison_facts ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "public read access" ON plan_comparison_facts;
CREATE POLICY "public read access"
ON plan_comparison_facts FOR SELECT
TO anon, authenticated
USING (true);
REVOKE ALL ON TABLE plan_comparison_facts FROM anon, authenticated;
GRANT SELECT ON TABLE plan_comparison_facts TO anon, authenticated;
GRANT ALL ON TABLE plan_comparison_facts TO service_role;

CREATE TABLE IF NOT EXISTS comparison_shares (
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
ON comparison_shares (created_at DESC);

ALTER TABLE comparison_shares ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "public read access" ON comparison_shares;
CREATE POLICY "public read access"
ON comparison_shares FOR SELECT
TO anon, authenticated
USING (true);
REVOKE ALL ON TABLE comparison_shares FROM anon, authenticated;
GRANT SELECT ON TABLE comparison_shares TO anon, authenticated;
GRANT ALL ON TABLE comparison_shares TO service_role;

CREATE TABLE IF NOT EXISTS carrier_canonical_names (
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
ON carrier_canonical_names (carrier_key);

CREATE INDEX IF NOT EXISTS idx_carrier_canonical_names_status
ON carrier_canonical_names (mas_match_status, lia_match_status);

ALTER TABLE carrier_canonical_names ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "public read access" ON carrier_canonical_names;
CREATE POLICY "public read access"
ON carrier_canonical_names FOR SELECT
TO anon, authenticated
USING (true);
REVOKE ALL ON TABLE carrier_canonical_names FROM anon, authenticated;
GRANT SELECT ON TABLE carrier_canonical_names TO anon, authenticated;
GRANT ALL ON TABLE carrier_canonical_names TO service_role;
REVOKE ALL ON SEQUENCE carrier_canonical_names_id_seq FROM anon, authenticated;
GRANT USAGE, SELECT ON SEQUENCE carrier_canonical_names_id_seq TO service_role;

CREATE TABLE IF NOT EXISTS plan_facts (
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
ON plan_facts (insurer, plan_slug, field_name);

CREATE INDEX IF NOT EXISTS idx_plan_facts_lookup
ON plan_facts (insurer, plan_slug);

CREATE INDEX IF NOT EXISTS idx_plan_facts_source
ON plan_facts (source_type, last_verified_at);

ALTER TABLE plan_facts ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "public read access" ON plan_facts;
CREATE POLICY "public read access"
ON plan_facts FOR SELECT
TO anon, authenticated
USING (true);
REVOKE ALL ON TABLE plan_facts FROM anon, authenticated;
GRANT SELECT ON TABLE plan_facts TO anon, authenticated;
GRANT ALL ON TABLE plan_facts TO service_role;
REVOKE ALL ON SEQUENCE plan_facts_id_seq FROM anon, authenticated;
GRANT USAGE, SELECT ON SEQUENCE plan_facts_id_seq TO service_role;

CREATE TABLE IF NOT EXISTS brochure_version_history (
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
ON brochure_version_history (insurer, plan_slug, captured_at DESC);

CREATE INDEX IF NOT EXISTS idx_brochure_version_history_source
ON brochure_version_history (source_url, sha256);

ALTER TABLE brochure_version_history ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "public read access" ON brochure_version_history;
CREATE POLICY "public read access"
ON brochure_version_history FOR SELECT
TO anon, authenticated
USING (true);
REVOKE ALL ON TABLE brochure_version_history FROM anon, authenticated;
GRANT SELECT ON TABLE brochure_version_history TO anon, authenticated;
GRANT ALL ON TABLE brochure_version_history TO service_role;
REVOKE ALL ON SEQUENCE brochure_version_history_id_seq FROM anon, authenticated;
GRANT USAGE, SELECT ON SEQUENCE brochure_version_history_id_seq TO service_role;

CREATE TABLE IF NOT EXISTS brochure_change_alerts (
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
ON brochure_change_alerts (insurer, plan_slug, change_detected_at DESC);

ALTER TABLE brochure_change_alerts ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "public read access" ON brochure_change_alerts;
CREATE POLICY "public read access"
ON brochure_change_alerts FOR SELECT
TO anon, authenticated
USING (true);
REVOKE ALL ON TABLE brochure_change_alerts FROM anon, authenticated;
GRANT SELECT ON TABLE brochure_change_alerts TO anon, authenticated;
GRANT ALL ON TABLE brochure_change_alerts TO service_role;
REVOKE ALL ON SEQUENCE brochure_change_alerts_id_seq FROM anon, authenticated;
GRANT USAGE, SELECT ON SEQUENCE brochure_change_alerts_id_seq TO service_role;

CREATE TABLE IF NOT EXISTS moh_institutions (
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
ON moh_institutions (canonical_name);

CREATE INDEX IF NOT EXISTS idx_moh_institutions_source
ON moh_institutions (source_dataset_id, source_record_id);

ALTER TABLE moh_institutions ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "public read access" ON moh_institutions;
CREATE POLICY "public read access"
ON moh_institutions FOR SELECT
TO anon, authenticated
USING (true);
REVOKE ALL ON TABLE moh_institutions FROM anon, authenticated;
GRANT SELECT ON TABLE moh_institutions TO anon, authenticated;
GRANT ALL ON TABLE moh_institutions TO service_role;
REVOKE ALL ON SEQUENCE moh_institutions_id_seq FROM anon, authenticated;
GRANT USAGE, SELECT ON SEQUENCE moh_institutions_id_seq TO service_role;

CREATE TABLE IF NOT EXISTS claim_turnaround_metrics (
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
ON claim_turnaround_metrics (carrier_key, metric_key, source_year);

CREATE INDEX IF NOT EXISTS idx_claim_turnaround_metrics_source
ON claim_turnaround_metrics (source_type, source_year);

ALTER TABLE claim_turnaround_metrics ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "public read access" ON claim_turnaround_metrics;
CREATE POLICY "public read access"
ON claim_turnaround_metrics FOR SELECT
TO anon, authenticated
USING (true);
REVOKE ALL ON TABLE claim_turnaround_metrics FROM anon, authenticated;
GRANT SELECT ON TABLE claim_turnaround_metrics TO anon, authenticated;
GRANT ALL ON TABLE claim_turnaround_metrics TO service_role;
REVOKE ALL ON SEQUENCE claim_turnaround_metrics_id_seq FROM anon, authenticated;
GRANT USAGE, SELECT ON SEQUENCE claim_turnaround_metrics_id_seq TO service_role;

CREATE TABLE IF NOT EXISTS mas_regulatory_events (
    id SERIAL PRIMARY KEY,
    carrier_key TEXT NOT NULL,
    carrier_name TEXT NOT NULL,
    event_title TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_date DATE NOT NULL,
    source_url TEXT NOT NULL,
    source_type TEXT NOT NULL CHECK (
        source_type IN ('mas_news', 'mas_enforcement_page', 'manual_entry')
    ),
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
ON mas_regulatory_events (carrier_key, event_date DESC);

CREATE INDEX IF NOT EXISTS idx_mas_regulatory_events_source
ON mas_regulatory_events (source_type, event_date DESC);

ALTER TABLE mas_regulatory_events ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "public read access" ON mas_regulatory_events;
CREATE POLICY "public read access"
ON mas_regulatory_events FOR SELECT
TO anon, authenticated
USING (true);
REVOKE ALL ON TABLE mas_regulatory_events FROM anon, authenticated;
GRANT SELECT ON TABLE mas_regulatory_events TO anon, authenticated;
GRANT ALL ON TABLE mas_regulatory_events TO service_role;
REVOKE ALL ON SEQUENCE mas_regulatory_events_id_seq FROM anon, authenticated;
GRANT USAGE, SELECT ON SEQUENCE mas_regulatory_events_id_seq TO service_role;
