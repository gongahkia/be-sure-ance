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
        'hsbc',
        'plans',
        'specialist_resources',
        'plan_comparison_facts',
        'plan_facts',
        'moh_institutions',
        'claim_turnaround_metrics',
        'mas_regulatory_events'
    ];
BEGIN
    FOREACH tbl_name IN ARRAY table_list LOOP
        IF to_regclass(format('public.%I', tbl_name)) IS NOT NULL THEN
            EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', tbl_name);
            EXECUTE format('DROP POLICY IF EXISTS "public read access" ON public.%I', tbl_name);
            EXECUTE format(
                'CREATE POLICY "public read access" ON public.%I FOR SELECT TO anon, authenticated USING (true)',
                tbl_name
            );
            EXECUTE format('REVOKE ALL ON TABLE public.%I FROM anon, authenticated', tbl_name);
            EXECUTE format('GRANT SELECT ON TABLE public.%I TO anon, authenticated', tbl_name);
            EXECUTE format('GRANT ALL ON TABLE public.%I TO service_role', tbl_name);
        END IF;
    END LOOP;
END $$;
