CREATE TABLE IF NOT EXISTS public.plans (
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
ON public.plans (insurer, plan_slug);

CREATE INDEX IF NOT EXISTS idx_plans_insurer
ON public.plans (insurer);

ALTER TABLE public.plans ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "public read access" ON public.plans;
CREATE POLICY "public read access"
ON public.plans FOR SELECT
TO anon, authenticated
USING (true);
REVOKE ALL ON TABLE public.plans FROM anon, authenticated;
GRANT SELECT ON TABLE public.plans TO anon, authenticated;
GRANT ALL ON TABLE public.plans TO service_role;
REVOKE ALL ON SEQUENCE public.plans_id_seq FROM anon, authenticated;
GRANT USAGE, SELECT ON SEQUENCE public.plans_id_seq TO service_role;

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
        IF to_regclass(format('public.%I', tbl_name)) IS NOT NULL THEN
            EXECUTE format(
                $sql$
                WITH source_rows AS (
                    SELECT
                        %L::TEXT AS insurer,
                        NULLIF(trim(plan_name), '') AS plan_name,
                        COALESCE(plan_benefits, '{}'::TEXT[]) AS plan_benefits,
                        plan_description,
                        plan_overview,
                        plan_url,
                        product_brochure_url,
                        now() AS scraped_at,
                        id AS source_id
                    FROM public.%I
                    WHERE NULLIF(trim(plan_name), '') IS NOT NULL
                ),
                slugged AS (
                    SELECT
                        *,
                        COALESCE(
                            NULLIF(
                                trim(
                                    both '-' from lower(
                                        regexp_replace(plan_name, '[^a-zA-Z0-9]+', '-', 'g')
                                    )
                                ),
                                ''
                            ),
                            'plan-' || source_id
                        ) AS base_slug
                    FROM source_rows
                ),
                deduped AS (
                    SELECT
                        *,
                        row_number() OVER (
                            PARTITION BY insurer, base_slug
                            ORDER BY source_id
                        ) AS duplicate_index
                    FROM slugged
                )
                INSERT INTO public.plans (
                    insurer,
                    plan_name,
                    plan_slug,
                    plan_benefits,
                    plan_description,
                    plan_overview,
                    plan_url,
                    product_brochure_url,
                    scraped_at
                )
                SELECT
                    insurer,
                    plan_name,
                    CASE
                        WHEN duplicate_index = 1 THEN base_slug
                        ELSE base_slug || '-' || duplicate_index
                    END AS plan_slug,
                    plan_benefits,
                    plan_description,
                    plan_overview,
                    plan_url,
                    product_brochure_url,
                    scraped_at
                FROM deduped
                ON CONFLICT (insurer, plan_slug) DO UPDATE SET
                    plan_name = EXCLUDED.plan_name,
                    plan_benefits = EXCLUDED.plan_benefits,
                    plan_description = EXCLUDED.plan_description,
                    plan_overview = EXCLUDED.plan_overview,
                    plan_url = EXCLUDED.plan_url,
                    product_brochure_url = EXCLUDED.product_brochure_url,
                    scraped_at = EXCLUDED.scraped_at
                $sql$,
                tbl_name,
                tbl_name
            );
        END IF;
    END LOOP;
END $$;

-- Old per-insurer tables are intentionally left in place for one migration window.
-- They remain public read-only under the RLS/grants from 0000_enforce_readonly_rls.sql.
