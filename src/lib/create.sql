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
        'uoi'
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