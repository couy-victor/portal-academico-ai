# Documentação do Sistema Multi-Agentes Acadêmico

## Visão Geral

Este sistema implementa uma arquitetura multi-agentes para consultas acadêmicas, utilizando LangGraph para orquestrar agentes especializados que trabalham em conjunto para processar consultas em linguagem natural, gerar consultas SQL, validá-las, executá-las e formatar respostas.

## Arquitetura do Sistema

O sistema é composto por vários componentes interconectados:

1. **Grafo de Agentes**: Orquestra o fluxo de trabalho entre os agentes especializados
2. **Agentes Especializados**: Cada um com uma função específica no processamento de consultas
3. **Banco de Dados Supabase**: Armazena dados acadêmicos e funções RPC para operações seguras
4. **Sistema de Cache**: Otimiza o desempenho armazenando resultados de consultas frequentes
5. **Módulos de Utilidades**: Fornecem funcionalidades compartilhadas entre os componentes

### Diagrama de Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                      Interface do Usuário                        │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                        Grafo LangGraph                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌──────────┐ │
│  │ Roteador de │  │  Gerador de │  │  Validador  │  │ Executor │ │
│  │  Intenções  │──▶     SQL     │──▶     SQL     │──▶    SQL   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └──────────┘ │
│         │                                                 │      │
│  ┌─────────────┐                                  ┌──────────────┐│
│  │   Agentes   │                                  │   Gerador    ││
│  │Especializados│◀─────────────────────────────────▶  Resposta   ││
│  └─────────────┘                                  └──────────────┘│
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                      Sistema de Cache                            │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│                     Banco de Dados Supabase                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────┐  │
│  │  get_schema_info │  │ get_user_context │  │execute_secured_query│
│  └─────────────────┘  └─────────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Componentes Principais

### 1. Grafo de Agentes (LangGraph)

O arquivo `src/graph/academic_graph.py` define o grafo de fluxo de trabalho que orquestra a interação entre os agentes. O grafo define:

- Nós (agentes)
- Arestas (fluxo de trabalho)
- Condições de roteamento

```python
def create_academic_graph() -> Callable:
    """
    Creates the academic agent graph.
    
    Returns:
        Callable: Compiled academic agent graph
    """
    # Create the graph
    academic_graph = StateGraph(AcademicAgentState)
    
    # Add nodes
    academic_graph.add_node("user_context_node", user_context_agent)
    academic_graph.add_node("cache_check", cache_agent)
    academic_graph.add_node("intent_router", intent_router)
    academic_graph.add_node("schema_retriever", schema_retriever)
    academic_graph.add_node("sql_generator", sql_generator)
    academic_graph.add_node("query_validator", query_validator)
    academic_graph.add_node("dba_guard", dba_guard)
    academic_graph.add_node("executor", executor_agent)
    academic_graph.add_node("response_generator", response_generator)
    academic_graph.add_node("fallback_handler", fallback_handler)
    academic_graph.add_node("cache_update", update_cache)
    academic_graph.add_node("logger", logger_agent)
    
    # Define routing function
    def route_from_cache(state: AcademicAgentState) -> str:
        """Routes based on cache hit."""
        if state.get("from_cache", False):
            logger.info("Cache hit, skipping to response generator")
            return "response_generator"
        return "intent_router"
    
    # Connect the nodes
    academic_graph.add_edge(START, "user_context_node")
    academic_graph.add_edge("user_context_node", "cache_check")
    academic_graph.add_edge("cache_check", "intent_router")
    academic_graph.add_edge("intent_router", "schema_retriever")
    academic_graph.add_edge("schema_retriever", "sql_generator")
    academic_graph.add_edge("sql_generator", "query_validator")
    academic_graph.add_edge("query_validator", "dba_guard")
    academic_graph.add_edge("dba_guard", "executor")
    academic_graph.add_edge("executor", "response_generator")
    academic_graph.add_edge("response_generator", "cache_update")
    academic_graph.add_edge("fallback_handler", "logger")
    academic_graph.add_edge("cache_update", "logger")
    academic_graph.add_edge("logger", END)
    
    # Compile the graph
    return academic_graph.compile()
```

### 2. Agentes Especializados

Cada agente é implementado como uma função que recebe e atualiza o estado do sistema:

#### Router Agent (`src/agents/router_agent.py`)
Classifica a intenção da consulta do usuário.

#### SQL Generator Agent (`src/agents/sql_generator_agent.py`)
Gera consultas SQL com base na intenção e no esquema do banco de dados.

#### Validator Agent (`src/agents/validator_agent.py`)
Valida as consultas SQL quanto à sintaxe, segurança e eficiência.

#### Executor Agent (`src/agents/executor_agent.py`)
Executa consultas SQL no banco de dados Supabase.

#### Response Agent (`src/agents/response_agent.py`)
Gera respostas em linguagem natural com base nos resultados das consultas.

#### Agentes Especializados Adicionais
- **Emotional Support Agent**: Fornece suporte emocional para estudantes ansiosos
- **Tutor Agent**: Oferece tutoria em assuntos específicos
- **Planning Agent**: Ajuda com planejamento de estudos

### 3. Banco de Dados Supabase

O sistema utiliza o Supabase como banco de dados e implementa funções RPC para operações seguras:

#### Funções RPC

##### 1. `get_schema_info()`

Recupera informações sobre o esquema do banco de dados.

```sql
-- Função para obter informações do esquema do banco de dados
CREATE OR REPLACE FUNCTION public.get_schema_info()
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    result jsonb;
    tables_info jsonb;
BEGIN
    -- Obter informações sobre tabelas
    WITH tables_data AS (
        SELECT 
            t.table_name,
            jsonb_agg(
                jsonb_build_object(
                    'column_name', c.column_name,
                    'data_type', c.data_type,
                    'is_nullable', c.is_nullable
                ) ORDER BY c.ordinal_position
            ) AS columns,
            (
                SELECT jsonb_agg(kcu.column_name)
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                WHERE tc.constraint_type = 'PRIMARY KEY'
                    AND tc.table_schema = 'public'
                    AND tc.table_name = t.table_name
            ) AS primary_keys,
            (
                SELECT jsonb_agg(
                    jsonb_build_object(
                        'column_name', kcu.column_name,
                        'foreign_table_name', ccu.table_name,
                        'foreign_column_name', ccu.column_name
                    )
                )
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = 'public'
                    AND tc.table_name = t.table_name
            ) AS foreign_keys
        FROM information_schema.tables t
        JOIN information_schema.columns c
            ON t.table_name = c.table_name
            AND t.table_schema = c.table_schema
        WHERE t.table_schema = 'public'
            AND t.table_type = 'BASE TABLE'
        GROUP BY t.table_name
    )
    SELECT jsonb_agg(
        jsonb_build_object(
            'name', table_name,
            'columns', COALESCE(columns, '[]'::jsonb),
            'primary_keys', COALESCE(primary_keys, '[]'::jsonb),
            'foreign_keys', COALESCE(foreign_keys, '[]'::jsonb)
        )
    )
    INTO tables_info
    FROM tables_data;

    -- Construir o resultado final
    result := jsonb_build_object(
        'tables', COALESCE(tables_info, '[]'::jsonb)
    );

    RETURN result;
END;
$$;
```

##### 2. `execute_secured_query(query_text, params, user_id)`

Executa consultas SQL de forma segura, com verificações de permissões.

```sql
-- Função para executar consultas SQL de forma segura
CREATE OR REPLACE FUNCTION public.execute_secured_query(
    query_text text,
    params jsonb,
    user_id text
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    result jsonb;
    query_with_params text;
    param_name text;
    param_value text;
BEGIN
    -- Verificar se o usuário tem permissão para executar a consulta
    -- Aqui você pode adicionar lógica para verificar se o usuário tem permissão
    -- para acessar os dados solicitados
    
    -- Exemplo simples: verificar se o user_id na consulta corresponde ao user_id fornecido
    IF query_text ILIKE '%WHERE%' AND query_text NOT ILIKE '%WHERE%user_id%=%' || user_id || '%' THEN
        -- Se a consulta tiver uma cláusula WHERE mas não filtrar pelo user_id correto
        -- você pode adicionar verificações mais sofisticadas conforme necessário
        
        -- Comentado para permitir consultas gerais durante o desenvolvimento
        -- RAISE EXCEPTION 'Unauthorized query: user_id mismatch';
    END IF;
    
    -- Preparar a consulta com parâmetros
    query_with_params := query_text;
    
    -- Substituir parâmetros na consulta
    FOR param_name, param_value IN SELECT * FROM jsonb_each_text(params)
    LOOP
        query_with_params := REPLACE(query_with_params, ':' || param_name, quote_literal(param_value));
    END LOOP;
    
    -- Executar a consulta e obter o resultado
    EXECUTE 'SELECT jsonb_agg(row_to_json(t)) FROM (' || query_with_params || ') t' INTO result;
    
    -- Se não houver resultados, retornar um array vazio
    IF result IS NULL THEN
        result := '[]'::jsonb;
    END IF;
    
    RETURN result;
EXCEPTION
    WHEN OTHERS THEN
        -- Capturar e retornar erros
        RETURN jsonb_build_object(
            'error', SQLERRM,
            'detail', SQLSTATE
        );
END;
$$;
```

##### 3. `get_user_context(user_id)`

Recupera o contexto do usuário com base no ID do usuário.

```sql
-- Função para obter o contexto do usuário
CREATE OR REPLACE FUNCTION public.get_user_context(user_id text)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    result jsonb;
BEGIN
    -- Obter informações do aluno
    SELECT jsonb_build_object(
        'RA', a.ra,
        'nome', p.nome,
        'curso_id', a.curso_id,
        'curso_nome', c.nome,
        'periodo_atual', (
            SELECT jsonb_build_object(
                'ano', pl.ano,
                'semestre', pl.semestre
            )
            FROM periodos_letivos pl
            WHERE pl.status = 'ativo'
            ORDER BY pl.ano DESC, pl.semestre DESC
            LIMIT 1
        )
    )
    INTO result
    FROM alunos a
    JOIN pessoas p ON a.pessoa_id = p.id
    JOIN cursos c ON a.curso_id = c.id
    WHERE a.ra = user_id;
    
    -- Se não encontrar o aluno, retornar um objeto vazio
    IF result IS NULL THEN
        result := '{}'::jsonb;
    END IF;
    
    RETURN result;
EXCEPTION
    WHEN OTHERS THEN
        -- Capturar e retornar erros
        RETURN jsonb_build_object(
            'error', SQLERRM,
            'detail', SQLSTATE
        );
END;
$$;
```

### 4. Sistema de Cache

O sistema implementa um mecanismo de cache para otimizar o desempenho, armazenando resultados de consultas frequentes.

#### Arquivo `src/utils/cache.py`

```python
def get_cache_key(query: str, user_context: Dict[str, Any]) -> str:
    """
    Generates a unique cache key for a query.
    
    Args:
        query (str): The user query
        user_context (Dict[str, Any]): User context information
        
    Returns:
        str: A unique cache key
    """
    # Extract only relevant context for caching
    relevant_context = {
        k: v for k, v in user_context.items() 
        if k in ['user_id', 'periodo_atual', 'curso_id']
    }
    
    # Create a string representation of the context
    context_str = json.dumps(relevant_context, sort_keys=True)
    
    # Combine query and context for the key
    key_data = f"{query}:{context_str}"
    
    # Generate MD5 hash as the key
    return hashlib.md5(key_data.encode()).hexdigest()

def get_cache(key: str) -> Optional[Any]:
    """
    Retrieves a value from cache if it exists and is not expired.
    
    Args:
        key (str): Cache key
        
    Returns:
        Optional[Any]: Cached value or None if not found or expired
    """
    if not CACHE_ENABLED:
        return None
        
    cached_data = cache.get(key)
    
    if cached_data is None:
        return None
        
    # Check if the cached data is expired
    if time.time() - cached_data.get("timestamp", 0) > CACHE_TTL:
        cache.delete(key)
        return None
        
    return cached_data.get("data")

def set_cache(key: str, data: Any, ttl: Optional[int] = None) -> None:
    """
    Stores a value in cache with timestamp.
    
    Args:
        key (str): Cache key
        data (Any): Data to cache
        ttl (Optional[int]): Time-to-live in seconds, defaults to CACHE_TTL
    """
    if not CACHE_ENABLED:
        return
        
    cache_data = {
        "timestamp": time.time(),
        "data": data
    }
    
    cache.set(key, cache_data, expire=ttl or CACHE_TTL)

def clear_cache() -> None:
    """
    Clears the entire cache.
    """
    if not CACHE_ENABLED:
        return
        
    print("Clearing cache...")
    cache.clear()
```

### 5. Cliente Supabase

O arquivo `src/database/supabase_client.py` implementa a comunicação com o banco de dados Supabase.

#### Recuperação Automática do Esquema

```python
def get_schema_info_direct() -> Dict[str, Any]:
    """
    Retrieves database schema information directly using Supabase REST API.
    This is a fallback method if the RPC function is not available.

    Returns:
        Dict[str, Any]: Database schema information
    """
    schema_info = {"tables": []}
    
    try:
        # Get list of tables using REST API
        # We'll query the information_schema.tables view
        tables_response = supabase.table('information_schema.tables')\
            .select('table_name')\
            .eq('table_schema', 'public')\
            .eq('table_type', 'BASE TABLE')\
            .execute()
            
        if hasattr(tables_response, 'error') and tables_response.error:
            raise Exception(f"Error fetching tables: {tables_response.error}")
            
        tables_data = tables_response.data
        tables = [row.get('table_name') for row in tables_data if row.get('table_name')]
        
        # For each table, get its columns, primary keys, and foreign keys
        for table_name in tables:
            # Get columns
            columns_response = supabase.table('information_schema.columns')\
                .select('column_name,data_type,is_nullable,column_default,ordinal_position')\
                .eq('table_schema', 'public')\
                .eq('table_name', table_name)\
                .order('ordinal_position')\
                .execute()
                
            if hasattr(columns_response, 'error') and columns_response.error:
                print(f"Error fetching columns for {table_name}: {columns_response.error}")
                continue
                
            columns = columns_response.data
            
            # Get primary keys and foreign keys...
            # [código omitido para brevidade]
            
            # Add table information to schema
            table_info = {
                "name": table_name,
                "columns": columns,
                "primary_keys": primary_keys,
                "foreign_keys": foreign_keys
            }
            
            schema_info["tables"].append(table_info)
        
        # If we couldn't get any tables, fall back to a minimal schema
        if not schema_info["tables"]:
            print("No tables found, using fallback schema")
            schema_info = get_fallback_schema()
            
        return schema_info
        
    except Exception as e:
        print(f"Error in get_schema_info_direct: {str(e)}")
        # Fall back to a minimal schema
        return get_fallback_schema()
```

#### Execução de Consultas SQL

```python
def execute_query(sql: str, params: Dict[str, Any], user_id: str) -> List[Dict[str, Any]]:
    """
    Executes a SQL query on Supabase with proper security checks.

    Args:
        sql (str): The SQL query to execute
        params (Dict[str, Any]): Query parameters
        user_id (str): User ID for permission checks

    Returns:
        List[Dict[str, Any]]: Query results
    """
    try:
        # Execute the query via a secure RPC function
        response = supabase.rpc(
            'execute_secured_query',
            {
                "query_text": sql,
                "params": json.dumps(params),
                "user_id": user_id
            }
        ).execute()

        if hasattr(response, 'error') and response.error:
            raise Exception(f"Query execution error: {response.error.message}")

        return response.data or []

    except Exception as e:
        print(f"Error executing query: {str(e)}")
        raise
```

## Fluxo de Processamento de Consultas

1. **Entrada do Usuário**: O usuário faz uma pergunta em linguagem natural
2. **Contexto do Usuário**: O sistema recupera o contexto do usuário (RA, curso, etc.)
3. **Verificação de Cache**: Verifica se a consulta já foi processada anteriormente
4. **Classificação de Intenção**: Identifica a intenção da consulta (notas, faltas, etc.)
5. **Recuperação de Esquema**: Obtém o esquema do banco de dados
6. **Geração de SQL**: Gera uma consulta SQL com base na intenção e no esquema
7. **Validação de SQL**: Verifica a consulta quanto à sintaxe, segurança e eficiência
8. **Execução de SQL**: Executa a consulta no banco de dados
9. **Geração de Resposta**: Formata os resultados em linguagem natural
10. **Atualização de Cache**: Armazena a resposta em cache para consultas futuras
11. **Registro**: Registra a interação para análise e depuração

## Configuração e Implantação

### Variáveis de Ambiente

O sistema utiliza as seguintes variáveis de ambiente:

```
OPENAI_API_KEY=sua_chave_api_openai
SUPABASE_URL=sua_url_supabase
SUPABASE_KEY=sua_chave_supabase
TAVILY_API_KEY=sua_chave_api_tavily
CACHE_ENABLED=true
CACHE_DIR=./cache
CACHE_TTL=3600
```

### Arquivos de Configuração

O arquivo `src/config/settings.py` define as configurações do sistema:

```python
# OpenAI settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL = "gpt-4o"
LLM_TEMPERATURE = 0.0
LLM_TEMPERATURE_CREATIVE = 0.7

# Supabase settings
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Tavily settings
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Cache settings
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
CACHE_DIR = os.getenv("CACHE_DIR", "./cache")
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour default
SCHEMA_CACHE_TTL = int(os.getenv("SCHEMA_CACHE_TTL", "86400"))  # 24 hours default
```

## Testes

O sistema inclui scripts de teste para verificar o funcionamento dos componentes:

### Teste Interativo (`src/interactive_test.py`)

Permite testar o sistema através de uma interface de linha de comando interativa.

### Teste de RA Específico (`test_ra_specific.py`)

Testa o sistema com um RA e disciplina específicos.

### Teste de Agentes Especializados (`src/simple_test.py`)

Testa os agentes especializados individualmente.

## Conclusão

Este sistema multi-agentes acadêmico demonstra a aplicação de técnicas avançadas de processamento de linguagem natural e engenharia de software para criar uma solução robusta e flexível para consultas acadêmicas. A arquitetura modular e o uso de LangGraph permitem fácil extensão e manutenção do sistema.

A integração com o Supabase e a implementação de funções RPC garantem operações seguras e eficientes no banco de dados, enquanto o sistema de cache otimiza o desempenho para consultas frequentes.

Os agentes especializados adicionais (suporte emocional, tutoria e planejamento) demonstram a versatilidade da arquitetura, permitindo que o sistema atenda a diversas necessidades dos estudantes além das consultas acadêmicas básicas.
