CREATE OR REPLACE FUNCTION public.execute_sql(query TEXT)
RETURNS void AS $$
BEGIN
    EXECUTE query;
END;
$$ LANGUAGE plpgsql;

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
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated, service_role;

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

GRANT ALL ON TABLE specialist_resources TO anon, authenticated, service_role;

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

GRANT ALL ON TABLE plan_comparison_facts TO anon, authenticated, service_role;
