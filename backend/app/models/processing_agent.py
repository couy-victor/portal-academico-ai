import os
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine, text
from langchain.schema import SystemMessage, HumanMessage
from dotenv import load_dotenv
from app.models.rag_vectordb import consultar_banco_vetorial, inicializar_pgvector
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
import re

# 🔥 Carregar variáveis do ambiente
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

# 📌 Configurar logs no LangSmith
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_PROJECT"] = "portal-academico"

print("✅ Configuração de ambiente carregada!")

# 🔗 Conectar ao banco via SQLAlchemy
engine = create_engine(DATABASE_URL)
db = SQLDatabase(engine)

# 🔥 Configurar modelos LLM
llm_consulta = ChatOpenAI(
    model_name="gpt-3.5-turbo",
    openai_api_key=OPENAI_API_KEY,
    temperature=0.3,
    max_tokens=50,
    request_timeout=10
)

llm_rag = ChatOpenAI(
    model_name="gpt-3.5-turbo",
    openai_api_key=OPENAI_API_KEY,
    temperature=0.7,
    max_tokens=500,
    request_timeout=15
)

print(f"✅ Modelos gpt-3.5-turbo configurados!")

# 🔥 Inicializar conexão com banco vetorial
try:
    vectorstore = inicializar_pgvector()
    print("✅ Banco vetorial inicializado!")
except Exception as e:
    print(f"❌ Erro ao inicializar banco vetorial: {e}")
    vectorstore = None

# 🛠 Função para Carregar o Esquema do Banco de Dados
def get_database_schema():
    """
    Obtém o esquema do banco de dados PostgreSQL com mais detalhes, incluindo relações.
    """
    try:
        with engine.connect() as conn:
            # Obter lista de tabelas
            result = conn.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = result.fetchall()
            
            schema = "DATABASE SCHEMA:\n\n"
            
            # Para cada tabela, obter detalhes
            for table in tables:
                table_name = table[0]
                schema += f"TABLE: {table_name}\n"
                
                # Obter colunas
                result = conn.execute(text(f"""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}'
                    ORDER BY ordinal_position
                """))
                columns = result.fetchall()
                
                schema += "Columns:\n"
                for column in columns:
                    schema += f"  - {column[0]} ({column[1]})\n"
                
                # Obter chaves primárias
                result = conn.execute(text(f"""
                    SELECT c.column_name
                    FROM information_schema.table_constraints tc 
                    JOIN information_schema.constraint_column_usage AS ccu USING (constraint_schema, constraint_name) 
                    JOIN information_schema.columns AS c ON c.table_schema = tc.constraint_schema
                      AND tc.table_name = c.table_name AND ccu.column_name = c.column_name
                    WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_name = '{table_name}'
                """))
                pks = result.fetchall()
                
                if pks:
                    schema += "Primary Keys:\n"
                    for pk in pks:
                        schema += f"  - {pk[0]}\n"
                
                # Obter chaves estrangeiras
                result = conn.execute(text(f"""
                    SELECT
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM
                        information_schema.table_constraints AS tc
                        JOIN information_schema.key_column_usage AS kcu
                          ON tc.constraint_name = kcu.constraint_name
                          AND tc.table_schema = kcu.table_schema
                        JOIN information_schema.constraint_column_usage AS ccu
                          ON ccu.constraint_name = tc.constraint_name
                          AND ccu.table_schema = tc.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name='{table_name}'
                """))
                fks = result.fetchall()
                
                if fks:
                    schema += "Foreign Keys:\n"
                    for fk in fks:
                        schema += f"  - {fk[0]} REFERENCES {fk[1]}({fk[2]})\n"
                
                schema += "\n"
            
            # Adicionar exemplos de JOIN's corretos
            schema += "COMMON JOIN PATTERNS:\n"
            for table in tables:
                table_name = table[0]
                join_examples = []
                
                # Obter chaves estrangeiras para essa tabela
                result = conn.execute(text(f"""
                    SELECT
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM
                        information_schema.table_constraints AS tc
                        JOIN information_schema.key_column_usage AS kcu
                          ON tc.constraint_name = kcu.constraint_name
                          AND tc.table_schema = kcu.table_schema
                        JOIN information_schema.constraint_column_usage AS ccu
                          ON ccu.constraint_name = tc.constraint_name
                          AND ccu.table_schema = tc.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name='{table_name}'
                """))
                fks = result.fetchall()
                
                # Gerar exemplos de JOIN para cada chave estrangeira
                for fk in fks:
                    local_column = fk[0]
                    foreign_table = fk[1]
                    foreign_column = fk[2]
                    join_examples.append(
                        f"JOIN {foreign_table} ON {table_name}.{local_column} = {foreign_table}.{foreign_column}"
                    )
                
                # Obter tabelas que referenciam esta tabela
                result = conn.execute(text(f"""
                    SELECT
                        tc.table_name AS referencing_table,
                        kcu.column_name AS referencing_column,
                        ccu.column_name AS referenced_column
                    FROM
                        information_schema.table_constraints AS tc
                        JOIN information_schema.key_column_usage AS kcu
                          ON tc.constraint_name = kcu.constraint_name
                          AND tc.table_schema = kcu.table_schema
                        JOIN information_schema.constraint_column_usage AS ccu
                          ON ccu.constraint_name = tc.constraint_name
                          AND ccu.table_schema = tc.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY' 
                      AND ccu.table_name = '{table_name}'
                """))
                refs = result.fetchall()
                
                # Adicionar exemplos de JOIN para tabelas que referenciam esta
                for ref in refs:
                    ref_table = ref[0]
                    ref_column = ref[1]
                    local_column = ref[2]
                    join_examples.append(
                        f"JOIN {ref_table} ON {table_name}.{local_column} = {ref_table}.{ref_column}"
                    )
                
                if join_examples:
                    schema += f"For table '{table_name}':\n"
                    for example in join_examples:
                        schema += f"  - {example}\n"
            
            print("✅ Esquema do banco carregado com detalhes completos!")
            return schema
    except Exception as e:
        print(f"❌ Erro ao carregar esquema do banco: {e}")
        return ""

# Obtendo o esquema do banco de dados
db_schema = get_database_schema()
print(f"🔍 Esquema do Banco de Dados disponível")

def validar_query_sql(query, ra=None):
    """
    Valida e corrige problemas comuns em queries SQL.
    """
    if not query:
        return None
    
    # Verificar se a query está completa e não termina abruptamente
    truncation_patterns = [
        r'WHERE\s+[^=]+=\s*[\'"]\w+[\'"](?:\s+AND\s+)?(\w+\.\s*)$',  # WHERE x='y' AND z.
        r'JOIN\s+\w+\s+ON\s+\w+\.\w+\s*=\s*(\w+_?)$',  # JOIN x ON y.z = word_
        r'=\s*(\w+_)$',  # = word_
    ]
    
    for pattern in truncation_patterns:
        match = re.search(pattern, query)
        if match:
            print(f"⚠️ Query truncada detectada: {match.group(0)}")
            # Remover a parte truncada
            truncated_part = match.group(1)
            # Se for uma condição WHERE AND incompleta
            if "AND" in match.group(0):
                query = query.replace(f"AND {truncated_part}", "")
            # Se for um JOIN ou = incompleto, remova a expressão completa
            else:
                query = re.sub(pattern, "", query)
            print(f"✅ Removida parte truncada: '{truncated_part}'")
    
    # Detectar e corrigir JOINs incompletos
    join_pattern = r'JOIN\s+(\w+)\s+ON\s+(\w+)\.(\w+)(?!\s*=)'
    match = re.search(join_pattern, query)
    if match:
        print("⚠️ JOIN incompleto detectado, tentando corrigir...")
        table_name = match.group(1)
        left_table = match.group(2)
        left_column = match.group(3)
        
        # Se o JOIN termina com "JOIN aluno ON matricula.ra" sem completar
        if table_name.lower() == 'aluno' and left_column.lower() == 'ra':
            # Substitua pelo JOIN completo
            problematic_join = match.group(0)
            fixed_join = f"JOIN {table_name} ON {left_table}.{left_column} = {table_name}.ra"
            query = query.replace(problematic_join, fixed_join)
            print(f"✅ JOIN corrigido: {fixed_join}")
        else:
            # Tente dar um palpite para outros casos
            problematic_join = match.group(0)
            # Suponha que estamos unindo pela mesma coluna ou por ID
            if left_column.endswith('_id'):
                # Caso comum: left_table.tabela_id = tabela.id
                target_table = left_column[:-3]  # Remove '_id'
                if target_table.lower() == table_name.lower():
                    fixed_join = f"JOIN {table_name} ON {left_table}.{left_column} = {table_name}.id"
                    query = query.replace(problematic_join, fixed_join)
                    print(f"✅ JOIN corrigido com base em padrão ID: {fixed_join}")
    
    # Verificar e corrigir RA vazio
    if ra:
        if "ra = ''" in query.lower():
            print(f"⚠️ RA vazio detectado, substituindo por '{ra}'")
            query = query.replace("ra = ''", f"ra = '{ra}'")
        if "matricula.ra = ''" in query.lower():
            print(f"⚠️ RA vazio detectado, substituindo por '{ra}'")
            query = query.replace("matricula.ra = ''", f"matricula.ra = '{ra}'")
        if "m.ra = ''" in query.lower():
            print(f"⚠️ RA vazio detectado, substituindo por '{ra}'")
            query = query.replace("m.ra = ''", f"m.ra = '{ra}'")
        
        # Verificar se RA está sendo usado na query
        if "ra =" not in query.lower() and "matricula.ra" not in query.lower() and "m.ra" not in query.lower() and "aluno.ra" not in query.lower():
            print(f"⚠️ RA não encontrado na query, adicionando filtro para RA={ra}")
            # Verificar se tem WHERE na query
            if "where" in query.lower():
                # Adicionar AND com o RA
                query = query.replace("WHERE", f"WHERE matricula.ra = '{ra}' AND")
            else:
                # Adicionar WHERE com o RA
                query = query + f" WHERE matricula.ra = '{ra}'"
    
    # Verificar aspas não balanceadas
    if query.count("'") % 2 != 0:
        print("⚠️ Detectadas aspas não balanceadas na query, tentando corrigir...")
        
        # Casos específicos de correção
        if "WHERE m.ra = '25122775" in query:
            query = query.replace("WHERE m.ra = '25122775", "WHERE m.ra = '25122775'")
        elif "WHERE ra = '25122775" in query:
            query = query.replace("WHERE ra = '25122775", "WHERE ra = '25122775'")
        # RA entre aspas sem fechar aspas
        elif "'25122775" in query and "'25122775'" not in query:
            query = query.replace("'25122775", "'25122775'")
        # Corrigir caso geral
        elif query.count("'") % 2 != 0:
            last_quote_pos = query.rfind("'")
            if last_quote_pos > 0:
                # Se a última aspa estiver no final, adicione outra
                if last_quote_pos == len(query) - 1:
                    query = query + "'"
                # Caso contrário, adicione onde falta
                else:
                    parts = query.split("'")
                    if len(parts) % 2 == 0:  # Número ímpar de aspas
                        new_query = ""
                        for i, part in enumerate(parts):
                            new_query += part
                            if i < len(parts) - 1:
                                new_query += "'"
                            if i == len(parts) - 2:  # Adiciona uma aspa extra no penúltimo
                                new_query += "'"
                        query = new_query
    
    # Verificar cláusulas WHERE incompletas (WHERE x = y AND z.)
    where_and_pattern = r'WHERE\s+.*\sAND\s+(\w+\.\s*)$'
    match = re.search(where_and_pattern, query)
    if match:
        print(f"⚠️ Cláusula WHERE incompleta detectada: {match.group(0)}")
        # Remover a parte AND incompleta
        incomplete_part = match.group(1)
        fixed_where = query.replace(f"AND {incomplete_part}", "")
        query = fixed_where
        print(f"✅ WHERE corrigido: {fixed_where}")
    
    # Verificar ponto e vírgula no final (remover se existir)
    if query.strip().endswith(';'):
        query = query.strip()[:-1]
    
    # Remover espaços extras e tabulações
    query = ' '.join(query.split())
    
    # Verificação final para garantir que a query é válida
    required_patterns = {
        'SELECT': r'SELECT\s+.+\s+FROM',
        'FROM': r'FROM\s+\w+',
    }
    
    for key, pattern in required_patterns.items():
        if not re.search(pattern, query, re.IGNORECASE):
            print(f"⚠️ Query inválida: faltando padrão {key}")
            return None
    
    # Se a query terminar com "AND" ou "OR", remova-os
    query = re.sub(r'\s+(AND|OR)\s*$', '', query)
    
    # Remover comentários SQL '--'
    query = re.sub(r'--.*$', '', query)
    
    return query

def get_fallback_query(tipo_solicitacao, ra=None):
    """
    Retorna uma query de contingência para tipos comuns de solicitação.
    Usado quando a geração de query pelo LLM falha repetidamente.
    """
    if not ra:
        return None
    
    # Dicionário de queries de contingência para casos comuns
    contingency_queries = {
        "consultar_disciplinas": f"""
            SELECT disciplina.nome 
            FROM disciplina 
            JOIN matricula ON disciplina.id = matricula.disciplina_id 
            WHERE matricula.ra = '{ra}'
        """,
        
        "consultar_notas": f"""
            SELECT disciplina.nome, nota.valor
            FROM nota
            JOIN matricula ON nota.matricula_id = matricula.id
            JOIN disciplina ON matricula.disciplina_id = disciplina.id
            WHERE matricula.ra = '{ra}'
        """,
        
        "consultar_faltas": f"""
            SELECT disciplina.nome, falta.quantidade
            FROM falta
            JOIN matricula ON falta.matricula_id = matricula.id
            JOIN disciplina ON matricula.disciplina_id = disciplina.id
            WHERE matricula.ra = '{ra}'
        """,
        
        "consultar_boletos": f"""
            SELECT f.ra, f.valor, f.data_vencimento
            FROM financeiro as f
            JOIN aluno ON boleto.aluno_id = aluno.id
            WHERE aluno.ra = '{ra}' and f.status='Pendente'
        """,
        
        "consultar_coordenador": f"""
            SELECT professor.nome, curso.nome as curso
            FROM professor
            JOIN curso ON professor.id = curso.coordenador_id
            JOIN matricula ON curso.id = matricula.curso_id
            WHERE matricula.ra = '{ra}'
        """,
        
        "consultar_optativas": f"""
            SELECT disciplina.nome
            FROM disciplina 
            JOIN curso ON disciplina.curso_id = curso.id
            JOIN matricula ON curso.id = matricula.curso_id
            WHERE disciplina.optativa = true AND matricula.ra = '{ra}'
        """
    }
    
    # Retorna a query de contingência para o tipo solicitado
    # ou None se não houver uma query cadastrada
    return contingency_queries.get(tipo_solicitacao)

# 🛠 Função para Gerar Query SQL com GPT
def gerar_query_sql(pergunta, ra=None):
    """
    Gera uma query SQL baseada no esquema do banco de dados.
    """
    print(f"📌 Gerando query para a pergunta: {pergunta}")
    
    role_prompt = """
    Você é um especialista em SQL e especialista no esquema de banco de dados fornecido.

    Sua tarefa é gerar **somente** a query SQL que responda precisamente à pergunta do usuário, usando APENAS as tabelas e colunas que existem no esquema fornecido.

    **REGRAS CRÍTICAS**:
    - Leia o esquema completo ANTES de gerar a query
    - Use APENAS tabelas e colunas que existam explicitamente no esquema
    - Verifique ATENTAMENTE as relações entre tabelas usando os campos de chave estrangeira
    - Cada JOIN deve ter uma condição completa: JOIN tabela ON tabela1.coluna = tabela2.coluna
    - Nunca deixe um JOIN parcial ou incompleto
    - Nunca termine a query com uma condição WHERE parcial ou incompleta
    - Nunca termine a query com "AND" seguido de nada
    - Verifique se cada condição está completa antes de finalizar a query
    - Use nomes completos de tabelas e colunas (tabela.coluna) para evitar ambiguidades
    - Não inclua comentários SQL (--) na query
    - Retorne SOMENTE uma query SQL completa e válida
    """
    
    instruction = f"Esquema do banco de dados:\n{db_schema}\n"
    
    # Adiciona informações específicas sobre o RA se fornecido
    if ra:
        instruction += f"\nIMPORTANTE: O RA do aluno é '{ra}'. Use exatamente este valor ('{ra}') ao filtrar por RA.\n"
        
    instruction += f"Escreva a consulta SQL que responda à seguinte pergunta: {pergunta}\n"
    instruction += f"Se a pergunta for sobre dados específicos de um aluno, use o RA '{ra}' na condição WHERE."
    instruction += f"\n\nATENÇÃO: Sua query deve estar completa e pronta para execução. Exemplos:"
    instruction += f"\n- Correto: JOIN aluno ON matricula.ra = aluno.ra"
    instruction += f"\n- Incorreto: JOIN aluno ON matricula.ra"
    instruction += f"\n- Correto: WHERE periodo_letivo.ativo = 'S'"
    instruction += f"\n- Incorreto: WHERE periodo_letivo."
    instruction += f"\n\nVERIFIQUE sua query final e certifique-se de que todas as condições estão completas."
    
    messages = [
        SystemMessage(content=role_prompt), 
        HumanMessage(content=instruction)
    ]
    
    try:
        response = llm_consulta.invoke(messages)
        query_sql = response.content.strip()
        
        # Validar e corrigir a query, passando o RA
        query_sql = validar_query_sql(query_sql, ra)
        
        # Verificar se a query é válida após validação
        if not query_sql:
            print("❌ Não foi possível gerar uma query SQL válida")
            # Tentar uma abordagem mais simples
            simple_query = f"SELECT disciplina.nome FROM disciplina JOIN matricula ON disciplina.id = matricula.disciplina_id WHERE matricula.ra = '{ra}'"
            print(f"🔄 Usando query simplificada: {simple_query}")
            return simple_query
            
        print(f"✅ Query SQL Gerada: {query_sql}")
        return query_sql
    except Exception as e:
        print(f"❌ Erro ao gerar query SQL: {e}")
        if ra:
            # Fallback para query simples em caso de erro
            simple_query = f"SELECT disciplina.nome FROM disciplina JOIN matricula ON disciplina.id = matricula.disciplina_id WHERE matricula.ra = '{ra}'"
            print(f"🔄 Usando query simplificada em caso de erro: {simple_query}")
            return simple_query
        return None

# 🛠 Função para processar consultas RAG
def processar_rag(pergunta):
    """
    Processa consultas RAG usando o banco vetorial e gera uma resposta contextualizada.
    """
    print(f"🔎 Processando consulta RAG: {pergunta}")
    
    try:
        # Buscar documentos relevantes
        documentos = consultar_banco_vetorial(pergunta, limite=3)
        
        if not documentos:
            return "⚠️ Não encontrei informações relevantes sobre isso."
        
        # Extrair o conteúdo dos documentos
        contexto = "\n\n".join([doc.page_content for doc in documentos])
        
        # Criar prompt para o LLM
        template = """
        Você é um assistente acadêmico especializado em informações sobre a UNISAL.
        
        Use APENAS as informações fornecidas abaixo para responder à pergunta do usuário.
        Se a informação não estiver disponível no contexto, diga que você não tem essa informação.
        
        Contexto:
        {contexto}
        
        Pergunta: {pergunta}
        
        Sua resposta:
        """
        
        prompt = ChatPromptTemplate.from_template(template)
        
        # Criar cadeia de processamento RAG
        rag_chain = (
            {"contexto": lambda _: contexto, "pergunta": lambda x: x}
            | prompt
            | llm_rag
            | StrOutputParser()
        )
        
        # Executar a cadeia
        resposta = rag_chain.invoke(pergunta)
        print("✅ RAG processado com sucesso!")
        return resposta
    
    except Exception as e:
        print(f"❌ Erro ao processar RAG: {e}")
        return "⚠️ Ocorreu um erro ao buscar informações sobre a UNISAL."

# 🛠 Agente de Processamento
def agente_processamento(tipo_solicitacao, ra, pergunta):
    """
    Decide entre gerar SQL dinamicamente, buscar no RAG ou usar IA para perguntas abertas.
    """
    print(f"🔎 Processando solicitação: {tipo_solicitacao}")

    # Garantir que o RA seja uma string válida
    if ra is None or ra == "":
        ra = None
    else:
        ra = str(ra).strip()

    # Solicitações que requerem acesso ao banco de dados
    if tipo_solicitacao in ["consultar_boletos", "consultar_notas", "consultar_faltas", "consultar_disciplinas", "consultar_coordenador", "consultar_optativas"]:
        try:
            # Verificar se temos RA para consultas que necessitam dele
            if not ra and tipo_solicitacao not in ["consultar_coordenador", "consultar_optativas"]:
                return {
                    "status": "error",
                    "message": "Por favor, informe seu RA para consultar dados acadêmicos."
                }
                
            query_sql = gerar_query_sql(pergunta, ra)
            if query_sql:
                print(f"📊 Query Gerada: {query_sql}")
                
                # Validação adicional antes de executar
                if "'" in query_sql and query_sql.count("'") % 2 != 0:
                    print("⚠️ Alerta: Query SQL ainda possui aspas não balanceadas após correção")
                    
                # Execução segura
                try:
                    with engine.connect() as conn:
                        resultado = conn.execute(text(query_sql)).fetchall()
                        
                        # Verificar se há resultados
                        if resultado and len(resultado) > 0:
                            # Converter resultados para formato mais legível
                            resultados_formatados = []
                            for row in resultado:
                                resultados_formatados.append(dict(row._mapping))
                            
                            return {
                                "status": "success",
                                "data": resultados_formatados,
                                "message": "Dados encontrados com sucesso."
                            }
                        else:
                            return {
                                "status": "empty",
                                "data": [],
                                "message": "Nenhum dado encontrado para esta consulta."
                            }
                except Exception as sql_error:
                    print(f"❌ Erro na execução SQL: {sql_error}")
                    error_str = str(sql_error)
                    
                    # Extrair informações de erro para feedback
                    error_feedback = "Erro na SQL: "
                    
                    # Detectar problemas específicos
                    if "column" in error_str and "does not exist" in error_str:
                        # Tentar extrair o nome da coluna que não existe
                        import re
                        column_match = re.search(r'column\s+([^\s]+)\s+does not exist', error_str)
                        if column_match:
                            bad_column = column_match.group(1)
                            error_feedback += f"A coluna '{bad_column}' não existe no banco de dados. "
                    
                    elif "argument of JOIN/ON must be type boolean" in error_str:
                        error_feedback += "JOIN incompleto. Cada JOIN deve ter uma condição completa de igualdade (JOIN tabela ON coluna1 = coluna2). "
                    
                    elif "unterminated quoted string" in error_str:
                        error_feedback += "Aspas não fechadas. "
                    
                    elif "syntax error" in error_str:
                        error_feedback += "Erro de sintaxe SQL. "
                    
                    # Tentar gerar uma nova query com feedback do erro
                    print(f"🔄 Tentando regenerar a query com feedback do erro: {error_feedback}")
                    
                    # Reforçar as instruções específicas para corrigir o problema
                    extra_instructions = ""
                    if "JOIN/ON" in error_str:
                        extra_instructions = "MUITO IMPORTANTE: Certifique-se de que cada JOIN tenha uma condição completa com '=' entre as colunas relacionadas. Exemplo: JOIN aluno ON matricula.ra = aluno.ra"
                    elif "syntax error" in error_str:
                        extra_instructions = "MUITO IMPORTANTE: Certifique-se de que sua query SQL está completa e não termina abruptamente. Não termine com uma palavra parcial ou cláusula incompleta."
                    
                    query_sql = gerar_query_sql(f"IMPORTANTE: {error_feedback} {extra_instructions} {pergunta}", ra)
                    
                    if query_sql:
                        print(f"📊 Nova Query Gerada: {query_sql}")
                        try:
                            with engine.connect() as conn:
                                resultado = conn.execute(text(query_sql)).fetchall()
                                
                                if resultado and len(resultado) > 0:
                                    resultados_formatados = []
                                    for row in resultado:
                                        resultados_formatados.append(dict(row._mapping))
                                    
                                    return {
                                        "status": "success",
                                        "data": resultados_formatados,
                                        "message": "Dados encontrados com sucesso (segunda tentativa)."
                                    }
                                else:
                                    return {
                                        "status": "empty",
                                        "data": [],
                                        "message": "Nenhum dado encontrado para esta consulta."
                                    }
                        except Exception as second_error:
                            print(f"❌ Erro na segunda tentativa: {second_error}")
                            
                            # Tentar usar uma query de contingência
                            contingency_query = get_fallback_query(tipo_solicitacao, ra)
                            if contingency_query:
                                print(f"🚨 Usando query de contingência para {tipo_solicitacao}")
                                try:
                                    with engine.connect() as conn:
                                        resultado = conn.execute(text(contingency_query)).fetchall()
                                        
                                        if resultado and len(resultado) > 0:
                                            resultados_formatados = []
                                            for row in resultado:
                                                resultados_formatados.append(dict(row._mapping))
                                            
                                            return {
                                                "status": "success",
                                                "data": resultados_formatados,
                                                "message": "Dados encontrados com sucesso (usando query de contingência)."
                                            }
                                        else:
                                            return {
                                                "status": "empty",
                                                "data": [],
                                                "message": "Nenhum dado encontrado para esta consulta."
                                            }
                                except Exception as contingency_error:
                                    print(f"❌ Erro na query de contingência: {contingency_error}")
                    
                    return {
                        "status": "error",
                        "message": "Erro ao consultar o banco de dados. Por favor, reformule sua pergunta.",
                        "error_details": error_str
                    }
            else:
                # Se não foi possível gerar uma query, tentar usar a query de contingência
                contingency_query = get_fallback_query(tipo_solicitacao, ra)
                if contingency_query:
                    print(f"🚨 Usando query de contingência para {tipo_solicitacao}")
                    try:
                        with engine.connect() as conn:
                            resultado = conn.execute(text(contingency_query)).fetchall()
                            
                            if resultado and len(resultado) > 0:
                                resultados_formatados = []
                                for row in resultado:
                                    resultados_formatados.append(dict(row._mapping))
                                
                                return {
                                    "status": "success",
                                    "data": resultados_formatados,
                                    "message": "Dados encontrados com sucesso (usando query pré-definida)."
                                }
                            else:
                                return {
                                    "status": "empty",
                                    "data": [],
                                    "message": "Nenhum dado encontrado para esta consulta."
                                }
                    except Exception as contingency_error:
                        print(f"❌ Erro na query de contingência: {contingency_error}")
                
                return {
                    "status": "error",
                    "message": "Não foi possível gerar a consulta SQL."
                }
        except Exception as e:
            print(f"❌ Erro ao executar a consulta SQL: {e}")
            return {
                "status": "error",
                "message": f"Erro ao consultar o banco de dados: {str(e)}"
            }

    # Solicitações sobre a UNISAL (usando RAG)
    if tipo_solicitacao == "consultar_unisal":
        try:
            resposta = processar_rag(pergunta)
            return {
                "status": "success",
                "data": resposta,
                "message": "Informações encontradas via RAG."
            }
        except Exception as e:
            print(f"❌ Erro ao buscar no RAG: {e}")
            return {
                "status": "error",
                "message": "Erro ao buscar informações sobre a UNISAL."
            }

    # Perguntas gerais (fallback para LLM)
    try:
        system_prompt = """
        Você é um assistente acadêmico útil e conciso da UNISAL.
        Responda à pergunta do usuário de forma educada e direta.
        Mantenha as respostas curtas e objetivas, com no máximo 3 frases.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=pergunta)
        ]
        
        resposta = llm_consulta.invoke(messages)
        print("✅ GPT gerou uma resposta com sucesso!")
        
        return {
            "status": "success",
            "data": resposta.content.strip(),
            "message": "Resposta gerada com IA."
        }
    except Exception as e:
        print(f"❌ Erro ao chamar GPT: {e}")
        return {
            "status": "error",
            "message": "Não consegui gerar uma resposta no momento."
        }