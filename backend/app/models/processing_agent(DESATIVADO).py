from app.services.DB import consultar_banco
from app.services.rag import buscar_documento_rag
from app.models.response_agent import agente_resposta
import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# ✅ Cache otimizado para evitar buscas repetitivas
document_cache = {}

def gerar_query_sql(pergunta):
    """
    Gera uma query SQL segura baseada na pergunta do aluno usando RAG.
    """
    # 🔄 Se a estrutura do banco já estiver em cache, evita chamada repetitiva
    if "schema_banco" not in document_cache:
        document_cache["schema_banco"] = buscar_documento_rag("Estrutura do banco de dados acadêmico")

    schema_banco = document_cache["schema_banco"]

    if not schema_banco:
        return None  # Evita erro caso o RAG falhe

    prompt = f"""
    Você é um assistente especializado em SQL para bancos acadêmicos.
    Baseado na estrutura do banco abaixo, gere uma query segura:
    {schema_banco}

    Pergunta do usuário: '{pergunta}'
    """

    try:
        client = openai.OpenAI()
        resposta = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            messages=[
                {"role": "system", "content": "Gere queries SQL seguras sem modificar tabelas."},
                {"role": "user", "content": prompt}
            ]
        )
        query_sql = resposta.choices[0].message.content

        # 🚨 Bloqueia queries perigosas!
        if "DROP" in query_sql.upper() or "DELETE" in query_sql.upper():
            return None

        return query_sql
    except Exception as e:
        print(f"❌ Erro ao gerar query SQL: {e}")
        return None

def agente_processamento(tipo_solicitacao, ra, pergunta):
    """
    Executa a busca nos dados acadêmicos via SQL seguro ou RAG, se necessário.
    """

    # ✅ Primeiro, verifica se a resposta já está em cache
    if pergunta in document_cache:
        return f"📄 Informação encontrada no cache:\n{document_cache[pergunta]}"

    # 🔍 Primeiro, tenta buscar no banco de dados
    query_sql = gerar_query_sql(pergunta)
    if query_sql:
        resultado = consultar_banco(query_sql, {"ra": ra})
        if resultado:
            document_cache[pergunta] = resultado  # Salva no cache
            return f"📌 Resposta baseada no banco de dados:\n{resultado}"

    # 🔄 Se não encontrou no banco, busca no RAG
    documentos_relevantes = buscar_documento_rag(pergunta)
    if documentos_relevantes:
        contexto = " ".join(documentos_relevantes)
        document_cache[pergunta] = contexto  # Salva no cache
        return agente_resposta(f"📄 Informação encontrada via RAG:\n{contexto}")

    # ❌ Se nada for encontrado, retorna resposta padrão
    return agente_resposta("❌ Não foi possível encontrar informações relevantes.")
