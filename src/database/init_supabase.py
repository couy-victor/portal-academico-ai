"""
Script to initialize Supabase with necessary functions and tables.
"""
import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

def init_supabase():
    """
    Initializes Supabase with necessary functions and tables.
    """
    print("Initializing Supabase...")
    
    try:
        # Create get_schema_info function
        create_get_schema_info_function()
        
        # Create get_user_context function
        create_get_user_context_function()
        
        # Create execute_secured_query function
        create_execute_secured_query_function()
        
        print("Supabase initialization completed successfully.")
        
    except Exception as e:
        print(f"Error initializing Supabase: {str(e)}")

def create_get_schema_info_function():
    """
    Creates the get_schema_info function in Supabase.
    """
    print("Creating get_schema_info function...")
    
    # SQL for creating the function
    sql = """
    CREATE OR REPLACE FUNCTION get_schema_info()
    RETURNS JSONB
    LANGUAGE plpgsql
    SECURITY DEFINER
    AS $$
    DECLARE
        result JSONB;
        tables_json JSONB;
    BEGIN
        -- Get all tables
        WITH tables_info AS (
            SELECT
                t.table_name
            FROM
                information_schema.tables t
            WHERE
                t.table_schema = 'public'
                AND t.table_type = 'BASE TABLE'
            ORDER BY
                t.table_name
        ),
        all_tables AS (
            SELECT
                t.table_name,
                jsonb_agg(
                    jsonb_build_object(
                        'column_name', c.column_name,
                        'data_type', c.data_type,
                        'is_nullable', c.is_nullable,
                        'column_default', c.column_default,
                        'ordinal_position', c.ordinal_position
                    ) ORDER BY c.ordinal_position
                ) AS columns,
                (
                    SELECT
                        jsonb_agg(kcu.column_name)
                    FROM
                        information_schema.table_constraints tc
                        JOIN information_schema.key_column_usage kcu
                            ON tc.constraint_name = kcu.constraint_name
                            AND tc.table_schema = kcu.table_schema
                    WHERE
                        tc.constraint_type = 'PRIMARY KEY'
                        AND tc.table_schema = 'public'
                        AND tc.table_name = t.table_name
                ) AS primary_keys,
                (
                    SELECT
                        jsonb_agg(
                            jsonb_build_object(
                                'column_name', kcu.column_name,
                                'foreign_table_name', ccu.table_name,
                                'foreign_column_name', ccu.column_name
                            )
                        )
                    FROM
                        information_schema.table_constraints tc
                        JOIN information_schema.key_column_usage kcu
                            ON tc.constraint_name = kcu.constraint_name
                            AND tc.table_schema = kcu.table_schema
                        JOIN information_schema.constraint_column_usage ccu
                            ON ccu.constraint_name = tc.constraint_name
                            AND ccu.table_schema = tc.table_schema
                    WHERE
                        tc.constraint_type = 'FOREIGN KEY'
                        AND tc.table_schema = 'public'
                        AND tc.table_name = t.table_name
                ) AS foreign_keys
            FROM
                tables_info t
                JOIN information_schema.columns c
                    ON c.table_schema = 'public'
                    AND c.table_name = t.table_name
            GROUP BY
                t.table_name
        )
        SELECT
            jsonb_agg(
                jsonb_build_object(
                    'name', table_name,
                    'columns', COALESCE(columns, '[]'::jsonb),
                    'primary_keys', COALESCE(primary_keys, '[]'::jsonb),
                    'foreign_keys', COALESCE(foreign_keys, '[]'::jsonb)
                )
            )
        INTO
            tables_json
        FROM
            all_tables;
        
        -- Build final result
        result := jsonb_build_object(
            'tables', COALESCE(tables_json, '[]'::jsonb)
        );
        
        RETURN result;
    END;
    $$;
    
    -- Grant execute permission to authenticated users
    GRANT EXECUTE ON FUNCTION get_schema_info() TO authenticated;
    """
    
    # Execute the SQL
    try:
        response = supabase.from_('_dummy_').select('*').execute(
            count='exact',
            head=False,
            options={'query': sql}
        )
        
        print("get_schema_info function created successfully.")
        
    except Exception as e:
        print(f"Error creating get_schema_info function: {str(e)}")
        raise

def create_get_user_context_function():
    """
    Creates the get_user_context function in Supabase.
    """
    print("Creating get_user_context function...")
    
    # SQL for creating the function
    sql = """
    CREATE OR REPLACE FUNCTION get_user_context(p_user_id UUID)
    RETURNS JSONB
    LANGUAGE plpgsql
    SECURITY DEFINER
    AS $$
    DECLARE
        result JSONB;
        user_record RECORD;
    BEGIN
        -- Get user information
        -- This is just an example - adjust according to your actual schema
        SELECT
            a.id,
            a.nome,
            a.matricula,
            a.curso_id,
            c.nome AS curso_nome,
            (
                SELECT
                    p.codigo
                FROM
                    periodos p
                WHERE
                    p.data_inicio <= CURRENT_DATE
                    AND p.data_fim >= CURRENT_DATE
                ORDER BY
                    p.data_inicio DESC
                LIMIT 1
            ) AS periodo_atual
        INTO
            user_record
        FROM
            alunos a
            JOIN cursos c ON a.curso_id = c.id
        WHERE
            a.id = p_user_id;
        
        -- Build result
        IF user_record IS NOT NULL THEN
            result := jsonb_build_object(
                'user_id', user_record.id,
                'nome', user_record.nome,
                'matricula', user_record.matricula,
                'curso_id', user_record.curso_id,
                'curso_nome', user_record.curso_nome,
                'periodo_atual', user_record.periodo_atual
            );
        ELSE
            -- Return empty object if user not found
            result := '{}'::jsonb;
        END IF;
        
        RETURN result;
    END;
    $$;
    
    -- Grant execute permission to authenticated users
    GRANT EXECUTE ON FUNCTION get_user_context(UUID) TO authenticated;
    """
    
    # Execute the SQL
    try:
        response = supabase.from_('_dummy_').select('*').execute(
            count='exact',
            head=False,
            options={'query': sql}
        )
        
        print("get_user_context function created successfully.")
        
    except Exception as e:
        print(f"Error creating get_user_context function: {str(e)}")
        raise

def create_execute_secured_query_function():
    """
    Creates the execute_secured_query function in Supabase.
    """
    print("Creating execute_secured_query function...")
    
    # SQL for creating the function
    sql = """
    CREATE OR REPLACE FUNCTION execute_secured_query(
        query_text TEXT,
        params JSONB,
        user_id UUID
    )
    RETURNS JSONB
    LANGUAGE plpgsql
    SECURITY DEFINER
    AS $$
    DECLARE
        result JSONB;
        param_name TEXT;
        param_value TEXT;
        final_query TEXT;
        start_time TIMESTAMPTZ;
        end_time TIMESTAMPTZ;
    BEGIN
        -- Security checks
        -- 1. Check if query is SELECT only
        IF NOT (query_text ~* '^\\s*SELECT\\s+') THEN
            RAISE EXCEPTION 'Only SELECT queries are allowed';
        END IF;
        
        -- 2. Check for dangerous patterns
        IF query_text ~* '(;|--|/\\*|\\*/|@@|@|COPY|FILE|EXECUTE|GRANT|REVOKE|TRUNCATE|DROP|CREATE|ALTER)' THEN
            RAISE EXCEPTION 'Query contains potentially dangerous patterns';
        END IF;
        
        -- 3. Ensure user can only access their own data
        IF query_text !~* ('user_id\\s*=\\s*:user_id') AND params ? 'user_id' THEN
            RAISE EXCEPTION 'Queries must filter by user_id for security';
        END IF;
        
        -- Prepare the query with parameters
        final_query := query_text;
        
        -- Replace parameters
        FOR param_name, param_value IN SELECT * FROM jsonb_each_text(params)
        LOOP
            final_query := REPLACE(final_query, ':' || param_name, quote_literal(param_value));
        END LOOP;
        
        -- Record start time
        start_time := clock_timestamp();
        
        -- Execute the query
        EXECUTE 'SELECT jsonb_agg(row_to_json(t)) FROM (' || final_query || ') t' INTO result;
        
        -- Record end time
        end_time := clock_timestamp();
        
        -- Log the query (optional)
        INSERT INTO query_logs (
            user_id,
            query_text,
            execution_time_ms,
            executed_at
        ) VALUES (
            user_id,
            final_query,
            EXTRACT(EPOCH FROM (end_time - start_time)) * 1000,
            start_time
        );
        
        -- Return empty array instead of null
        IF result IS NULL THEN
            result := '[]'::jsonb;
        END IF;
        
        RETURN result;
    END;
    $$;
    
    -- Grant execute permission to authenticated users
    GRANT EXECUTE ON FUNCTION execute_secured_query(TEXT, JSONB, UUID) TO authenticated;
    
    -- Create query_logs table if it doesn't exist
    CREATE TABLE IF NOT EXISTS query_logs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL,
        query_text TEXT NOT NULL,
        execution_time_ms FLOAT NOT NULL,
        executed_at TIMESTAMPTZ NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """
    
    # Execute the SQL
    try:
        response = supabase.from_('_dummy_').select('*').execute(
            count='exact',
            head=False,
            options={'query': sql}
        )
        
        print("execute_secured_query function created successfully.")
        
    except Exception as e:
        print(f"Error creating execute_secured_query function: {str(e)}")
        raise

if __name__ == "__main__":
    init_supabase()
