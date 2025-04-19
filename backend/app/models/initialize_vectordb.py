import os
import json
from dotenv import load_dotenv
from langchain_community.document_loaders import WebBaseLoader, DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from sqlalchemy import create_engine, text
from tqdm.auto import tqdm
import numpy as np
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Carregar variáveis de ambiente
load_dotenv()
PGVECTOR_CONNECTION_STRING = os.getenv("PGVECTOR_CONNECTION_STRING")

def inicializar_banco_vetorial(reset_db=False):
    """
    Inicializa a conexão com o banco vetorial e carrega documentos da UNISAL.
    
    Parâmetros:
    reset_db (bool): Se True, apaga todos os documentos existentes antes de carregar novos.
    """
    print("🚀 Inicializando banco vetorial...")
    
    # Criar conexão com o banco
    engine = create_engine(PGVECTOR_CONNECTION_STRING)
    
    # Verificar se a extensão pgvector está instalada
    with engine.connect() as conn:
        result = conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'"))
        if not result.fetchone():
            print("❌ Extensão pgvector não encontrada! Execute 'CREATE EXTENSION vector;' no banco.")
            return False
        
        print("✅ Extensão pgvector encontrada!")
        
        # Se reset_db for True, limpar tabelas existentes
        if reset_db:
            print("🔄 Apagando documentos existentes...")
            conn.execute(text("TRUNCATE TABLE unisal_documentos"))
            conn.execute(text("TRUNCATE TABLE rag_ingestao"))
            conn.execute(text("TRUNCATE TABLE rag_consultas"))
            conn.commit()
            print("✅ Tabelas limpas com sucesso!")
    
    # URLs principais para processar
    urls_base = [
        "https://www.unisal.br/",
        "https://www.unisal.br/cursos",
        "https://www.unisal.br/institucional/sobre-a-unisal",
        "https://www.unisal.br/vestibular",
        "https://www.unisal.br/graduacao",
        "https://www.unisal.br/pos-graduacao",
        "https://www.unisal.br/extensao",
        "https://www.unisal.br/noticias",
        "https://www.unisal.br/campus"
    ]
    
    # Expandir URLs para incluir páginas secundárias
    urls = expandir_urls(urls_base)
    
    # Configurar modelo de embeddings
    print("🔄 Carregando modelo de embeddings...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    # Processar URLs
    for url in urls:
        try:
            print(f"🔄 Processando URL: {url}")
            
            # Registrar início do processamento
            with engine.connect() as conn:
                conn.execute(
                    text("INSERT INTO rag_ingestao (url, status) VALUES (:url, 'processando')"),
                    {"url": url}
                )
                conn.commit()
            
            # Carregar documentos com configurações otimizadas
            loader = WebBaseLoader(
                url,
                header_template={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                verify_ssl=False,  # Importante para alguns sites com certificados problemáticos
                requests_per_second=3  # Taxa limitada para não sobrecarregar o servidor
            )
            documentos = loader.load()
            
            # Identificar título da página e categoria
            titulo = extrair_titulo_pagina(url, documentos)
            categoria = categorizar_url(url)
            
            # Prepara o processador de texto com sobreposição otimizada
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=800,           # Tamanho menor para chunks mais precisos
                chunk_overlap=150,        # Sobreposição otimizada
                separators=["\n\n", "\n", ". ", " ", ""],
                keep_separator=True
            )
            chunks = text_splitter.split_documents(documentos)
            
            print(f"📄 Criados {len(chunks)} chunks para: {url}")
            
            # Processar chunks e gerar embeddings
            for chunk in tqdm(chunks, desc=f"Embeddings para {url}"):
                # Pré-processar texto para melhorar qualidade
                texto_processado = preprocessar_texto(chunk.page_content)
                
                if len(texto_processado.strip()) < 50:  # Ignorar chunks muito pequenos
                    continue
                
                # Gerar embedding
                embedding_vector = embeddings.embed_query(texto_processado)
                
                # Dados de metadata
                metadata = chunk.metadata.copy() if hasattr(chunk, 'metadata') else {}
                metadata['url'] = url
                metadata['titulo'] = titulo
                metadata['categoria'] = categoria
                metadata_json = json.dumps(metadata)
                
                # Inserir no banco de dados
                with engine.connect() as conn:
                    conn.execute(
                        text("""
                        INSERT INTO unisal_documentos 
                        (content, content_vector, metadata, source_url, titulo, categoria) 
                        VALUES 
                        (:content, :content_vector, :metadata, :source_url, :titulo, :categoria)
                        """),
                        {
                            "content": texto_processado,
                            "content_vector": embedding_vector,
                            "metadata": metadata_json,
                            "source_url": url,
                            "titulo": titulo,
                            "categoria": categoria
                        }
                    )
                    conn.commit()
            
            # Registrar sucesso
            with engine.connect() as conn:
                conn.execute(
                    text("UPDATE rag_ingestao SET status = 'sucesso' WHERE url = :url"),
                    {"url": url}
                )
                conn.commit()
                
            print(f"✅ URL processada com sucesso: {url}")
            
        except Exception as e:
            print(f"❌ Erro ao processar URL {url}: {str(e)}")
            
            # Registrar erro
            with engine.connect() as conn:
                conn.execute(
                    text("UPDATE rag_ingestao SET status = 'erro', detalhes = :detalhes WHERE url = :url"),
                    {"url": url, "detalhes": str(e)}
                )
                conn.commit()
    
    print("✅ Inicialização do banco vetorial concluída!")
    return True

def expandir_urls(urls_base, max_por_base=5, max_depth=1):
    """
    Expande a lista de URLs base para incluir links internos relevantes.
    """
    print("🔍 Expandindo URLs para capturar mais conteúdo...")
    urls_expandidas = set(urls_base)
    dominio_base = "unisal.br"
    
    for url_base in urls_base:
        try:
            response = requests.get(url_base, 
                                   headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                                   timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                links = soup.find_all('a', href=True)
                
                # Filtrar apenas links internos relevantes
                links_internos = []
                for link in links:
                    href = link['href']
                    url_completa = urljoin(url_base, href)
                    
                    # Verificar se é link interno para o domínio da UNISAL
                    if dominio_base in url_completa and not url_completa.endswith(('.pdf', '.jpg', '.png', '.doc')):
                        links_internos.append(url_completa)
                
                # Adicionar até max_por_base links internos
                count = 0
                for link in links_internos:
                    if link not in urls_expandidas and count < max_por_base:
                        urls_expandidas.add(link)
                        count += 1
                        print(f"  + Adicionado: {link}")
        except Exception as e:
            print(f"⚠️ Erro ao expandir URLs a partir de {url_base}: {str(e)}")
    
    print(f"✅ URLs expandidas: {len(urls_expandidas)} URLs para processamento")
    return list(urls_expandidas)

def extrair_titulo_pagina(url, documentos):
    """
    Extrai o título da página a partir dos documentos ou da URL.
    """
    # Tentar extrair dos metadados do documento
    if documentos and hasattr(documentos[0], 'metadata') and 'title' in documentos[0].metadata:
        return documentos[0].metadata['title']
    
    # Extrair da URL se não encontrar nos metadados
    path = urlparse(url).path
    segmentos = [s for s in path.split('/') if s]
    
    if segmentos:
        # Pegar o último segmento da URL e formatar
        ultimo_segmento = segmentos[-1].replace('-', ' ').replace('_', ' ').capitalize()
        return ultimo_segmento
    
    return "Página UNISAL"

def categorizar_url(url):
    """
    Categoriza a URL com base no caminho.
    """
    categorias = {
        'cursos': 'Cursos',
        'graduacao': 'Graduação',
        'pos-graduacao': 'Pós-Graduação',
        'extensao': 'Extensão',
        'vestibular': 'Vestibular',
        'noticias': 'Notícias',
        'campus': 'Campus',
        'sobre-a-unisal': 'Institucional',
        'institucional': 'Institucional'
    }
    
    for chave, valor in categorias.items():
        if chave in url.lower():
            return valor
    
    return "Geral"

def preprocessar_texto(texto):
    """
    Pré-processa o texto para melhorar a qualidade dos embeddings.
    """
    # Remover múltiplos espaços em branco e quebras de linha
    texto = re.sub(r'\s+', ' ', texto).strip()
    
    # Remover caracteres especiais
    texto = re.sub(r'[^\w\s.,?!:;()\u00C0-\u00FF-]', '', texto)
    
    # Remover textos de menu, footer e outros elementos comuns em páginas web
    padroes_para_remover = [
        r'Menu\s*Principal', 
        r'Copyright\s*\d{4}', 
        r'Todos\s*os\s*direitos\s*reservados',
        r'Política\s*de\s*Privacidade'
    ]
    
    for padrao in padroes_para_remover:
        texto = re.sub(padrao, '', texto, flags=re.IGNORECASE)
    
    return texto

def testar_consulta(texto_consulta):
    """
    Testa uma consulta no banco vetorial.
    """
    print(f"🔍 Testando consulta: '{texto_consulta}'")
    
    try:
        # Conectar ao banco
        engine = create_engine(PGVECTOR_CONNECTION_STRING)
        
        # Gerar embedding para a consulta
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        query_embedding = embeddings.embed_query(texto_consulta)
        
        # Buscar documentos similares
        with engine.connect() as conn:
            query = text("""
            SELECT 
                id, content, 1 - (content_vector <=> :query_embedding) as similarity,
                source_url, titulo, categoria
            FROM 
                unisal_documentos
            ORDER BY 
                content_vector <=> :query_embedding
            LIMIT 5
            """)
            
            result = conn.execute(query, {"query_embedding": query_embedding})
            documentos = result.fetchall()
        
        # Mostrar resultados
        print(f"\n📊 {len(documentos)} documentos encontrados:")
        for i, doc in enumerate(documentos):
            print(f"\n--- Documento {i+1} (Similaridade: {doc.similarity:.4f}) ---")
            print(f"Título: {doc.titulo}")
            print(f"Categoria: {doc.categoria}")
            print(f"Fonte: {doc.source_url}")
            print(f"Conteúdo: {doc.content[:150]}...")
        
        # Registrar a consulta
        with engine.connect() as conn:
            conn.execute(
                text("""
                INSERT INTO rag_consultas 
                (consulta, documentos_ids) 
                VALUES 
                (:consulta, :documentos_ids)
                """),
                {
                    "consulta": texto_consulta,
                    "documentos_ids": [doc.id for doc in documentos]
                }
            )
            conn.commit()
        
        return documentos
    
    except Exception as e:
        print(f"❌ Erro ao testar consulta: {str(e)}")
        return None

if __name__ == "__main__":
    print("=== Inicialização do Banco Vetorial para RAG da UNISAL ===")
    
    # Perguntar se deseja resetar o banco
    reset = input("Deseja limpar todas as tabelas antes de iniciar? (s/n): ").lower() == 's'
    
    # Inicializar banco
    if inicializar_banco_vetorial(reset_db=reset):
        # Testar consultas
        perguntas_teste = [
            "Quais cursos de graduação a UNISAL oferece?",
            "Como funciona o vestibular da UNISAL?",
            "Quais são os campi da UNISAL?",
            "Quais são os cursos de pós-graduação disponíveis?"
        ]
        
        for pergunta in perguntas_teste:
            testar_consulta(pergunta)