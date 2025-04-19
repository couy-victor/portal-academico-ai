import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import PGVector
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from sqlalchemy import create_engine, text

# Carregar variáveis de ambiente
load_dotenv()
CONNECTION_STRING = os.getenv("PGVECTOR_CONNECTION_STRING")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Configurar embeddings
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def inicializar_pgvector():
    """
    Inicializa a conexão com o banco vetorial PGVector.
    Retorna o objeto PGVector para uso com RAG.
    """
    try:
        print("🔄 Conectando ao banco de dados vetorial...")
        # Você pode conectar a um banco existente ou criar um novo
        vectorstore = PGVector(
            connection_string=CONNECTION_STRING,
            embedding_function=embeddings,
            collection_name="unisal_documents"
        )
        
        print("✅ Conexão com banco vetorial estabelecida!")
        return vectorstore
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco vetorial: {e}")
        return None

def consultar_banco_vetorial(query_text, limite=5):
    """
    Consulta o banco vetorial com o texto da pergunta.
    Retorna os documentos mais relevantes.
    """
    try:
        print(f"🔍 Consultando banco vetorial: '{query_text}'")
        vectorstore = PGVector(
            connection_string=CONNECTION_STRING,
            embedding_function=embeddings,
            collection_name="unisal_documents"
        )
        
        # Realizar busca por similaridade
        docs = vectorstore.similarity_search(query_text, k=limite)
        
        print(f"✅ Encontrados {len(docs)} documentos relevantes")
        return docs
    except Exception as e:
        print(f"❌ Erro ao consultar banco vetorial: {e}")
        return []

def expandir_consulta(pergunta):
    """
    Expande a consulta original para aumentar a cobertura de resultados relevantes.
    """
    try:
        # Usar o LLM para gerar termos relacionados
        llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            openai_api_key=OPENAI_API_KEY,
            temperature=0.3,
            max_tokens=150
        )
        
        system_prompt = """
        Você é um especialista em expansão de consultas para sistemas de recuperação de informação.
        
        Sua tarefa é gerar uma versão expandida da consulta do usuário, adicionando termos relacionados 
        que possam ajudar a encontrar informações relevantes sobre a UNISAL (Universidade Salesiana).
        
        Não adicione mais de 3-5 termos relacionados e mantenha a consulta clara.
        Retorne apenas a consulta expandida, sem explicações.
        """
        
        user_prompt = f"""
        Consulta original: {pergunta}
        
        Expanda esta consulta adicionando termos relacionados relevantes para melhorar 
        a recuperação de informações sobre a UNISAL (instituição de ensino superior).
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = llm.invoke(messages)
        expanded_query = response.content.strip()
        
        print(f"🔄 Consulta original: '{pergunta}'")
        print(f"🔄 Consulta expandida: '{expanded_query}'")
        
        return expanded_query
    except Exception as e:
        print(f"⚠️ Erro ao expandir consulta: {e}")
        # Em caso de erro, retorna a consulta original
        return pergunta

def processar_rag(pergunta):
    """
    Processa consultas RAG usando o banco vetorial e gera uma resposta contextualizada.
    Versão melhorada que recupera mais documentos e usa uma janela de contexto maior.
    """
    print(f"🔎 Processando consulta RAG: {pergunta}")
    
    try:
        # Expandir a consulta para capturar mais termos relevantes
        expanded_query = expandir_consulta(pergunta)
        
        # Buscar documentos relevantes com limite maior
        documentos = consultar_banco_vetorial(expanded_query, limite=5)
        
        if not documentos or len(documentos) == 0:
            print("⚠️ Nenhum documento encontrado com a consulta expandida, tentando consulta original")
            documentos = consultar_banco_vetorial(pergunta, limite=5)
            
        if not documentos or len(documentos) == 0:
            return "⚠️ Não encontrei informações relevantes sobre isso na base de conhecimento da UNISAL."
        
        # Extrair o conteúdo dos documentos com metadados
        contextos = []
        for i, doc in enumerate(documentos):
            fonte = doc.metadata.get('source', 'Desconhecida') if hasattr(doc, 'metadata') else 'Desconhecida'
            contextos.append(f"Documento {i+1} (Fonte: {fonte}):\n{doc.page_content}")
        
        contexto_completo = "\n\n" + "\n\n".join(contextos)
        
        # Criar prompt aprimorado para o LLM com instruções detalhadas
        template = """
        Você é um assistente acadêmico especializado em informações sobre a UNISAL (Universidade Salesiana).
        
        Use as informações fornecidas abaixo para responder à pergunta do usuário de forma completa e informativa.
        
        Se a pergunta não puder ser completamente respondida com as informações disponíveis, construa a melhor resposta possível
        com o que está disponível e indique educadamente quais partes da pergunta não puderam ser respondidas.
        
        Contexto:
        {contexto}
        
        Pergunta: {pergunta}
        
        Instruções para resposta:
        1. Seja específico e detalhado
        2. Cite as informações relevantes do contexto
        3. Estruture a resposta de forma clara e organizada
        4. Mantenha um tom profissional e amigável
        5. Se houver informações contraditórias, mencione as diferentes perspectivas
        
        Sua resposta completa:
        """
        
        prompt = ChatPromptTemplate.from_template(template)
        
        # Ajustar o modelo para respostas mais elaboradas
        rag_llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            openai_api_key=OPENAI_API_KEY,
            temperature=0.5,  # Equilíbrio entre criatividade e precisão
            max_tokens=800,   # Permitir respostas mais longas
            request_timeout=20
        )
        
        # Criar cadeia de processamento RAG
        rag_chain = (
            {"contexto": lambda _: contexto_completo, "pergunta": lambda x: x}
            | prompt
            | rag_llm
            | StrOutputParser()
        )
        
        # Executar a cadeia
        resposta = rag_chain.invoke(pergunta)
        print("✅ RAG processado com sucesso!")
        
        # Guardar log dos documentos usados para análise (opcional)
        print(f"📚 Utilizados {len(documentos)} documentos para gerar a resposta")
        
        # Registrar a consulta e documentos usados no banco de dados para análise
        try:
            engine = create_engine(CONNECTION_STRING)
            with engine.connect() as conn:
                conn.execute(
                    text("""
                    INSERT INTO rag_consultas 
                    (consulta, resposta, documentos_ids) 
                    VALUES 
                    (:consulta, :resposta, :documentos_ids)
                    """),
                    {
                        "consulta": pergunta,
                        "resposta": resposta,
                        "documentos_ids": [doc.metadata.get('id', 0) for doc in documentos if hasattr(doc, 'metadata')]
                    }
                )
                conn.commit()
        except Exception as log_error:
            print(f"⚠️ Erro ao registrar consulta: {log_error}")
        
        return resposta
    
    except Exception as e:
        print(f"❌ Erro ao processar RAG: {e}")
        return "⚠️ Ocorreu um erro ao buscar informações sobre a UNISAL. Por favor, tente reformular sua pergunta ou entre em contato com a secretaria."

# Exemplo de uso
if __name__ == "__main__":
    # Para inicializar o banco
    vectorstore = inicializar_pgvector()
    
    # Para testar consulta
    pergunta_teste = "Quais cursos de graduação a UNISAL oferece?"
    resposta = processar_rag(pergunta_teste)
    print(f"\nResposta: {resposta}")