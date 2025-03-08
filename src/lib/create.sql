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