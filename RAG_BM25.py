#!/usr/bin/env python3
"""
Sistema RAG para consulta à LGPD usando ChromaDB + BM25 (híbrido).
Versão: 3.1
Autores: Equipe Scoras Academy
"""

import os
import re
import asyncio
import logging
import time
from typing import Any, List, Dict
from dataclasses import dataclass

from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
from chromadb import Client
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from pypdf import PdfReader

from pydantic_ai import Agent, RunContext
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# --- Configuração de logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("LGPD_RAG_CHROMA_BM25")

# --- Carregar variáveis de ambiente ---
load_dotenv()
PDF_PATH            = os.getenv("PDF_PATH", "/home/anderson/scoras_academy/Projetos_praticos_de_IA/rag_bm25/LGPD.pdf")
CHROMA_DB_DIR       = os.getenv("CHROMA_DB_DIR", "./chroma_db")
EMBEDDING_MODEL     = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
LLM_MODEL_NAME      = os.getenv("LLM_MODEL_NAME", "groq:llama-3.3-70b-versatile")
ALPHA               = float(os.getenv("HYBRID_ALPHA", 0.5))  # peso para embeddings vs BM25
TOP_K               = int(os.getenv("TOP_K", 5))
CHUNK_SIZE          = int(os.getenv("CHUNK_SIZE", 500))
CHUNK_OVERLAP       = int(os.getenv("CHUNK_OVERLAP", 50))

# --- Modelos de dados ---
class SearchResult(BaseModel):
    """Resultado da busca com contextos relevantes encontrados."""
    context: str = Field(..., description="Trechos de texto recuperados do documento")
    source_ids: List[int] = Field(..., description="IDs das fontes de informação")
    similarity_scores: List[float] = Field(
        ..., 
        description="Pontuações de similaridade (0-1)",
        ge=0.0, le=1.0  # Validação de valores entre 0 e 1
    )

class LGPDResponse(BaseModel):
    """Resposta formatada sobre a LGPD."""
    answer: str = Field(..., description="Resposta detalhada à pergunta")
    sources: List[str] = Field(..., description="Referências às fontes utilizadas")
    confidence: float = Field(
        ..., 
        description="Nível de confiança na resposta (0-1)",
        ge=0.0, le=1.0  # Validação de valores entre 0 e 1
    )
    
    class Config:
        """Configuração do modelo com exemplos."""
        json_schema_extra = {
            "example": {
                "answer": "A LGPD estabelece que...",
                "sources": ["Trecho 1", "Trecho 3"],
                "confidence": 0.85
            }
        }

@dataclass
class RagDependencies:
    client: Any  # Usa tipo genérico
    embed_model: SentenceTransformer
    bm25: BM25Okapi
    chunk_texts: List[str]

# --- Processamento de PDF e chunking ---
class DocumentProcessor:

    @staticmethod
    def extract_text(pdf_path: str) -> str:
        logger.info(f"Extraindo texto de: {pdf_path}")
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += (page.extract_text() or "") + "\n"
        logger.info(f"Extração concluída: {len(text)} caracteres")
        return text

    @staticmethod
    def chunk_text(text: str,
                   chunk_size: int = CHUNK_SIZE,
                   overlap: int = CHUNK_OVERLAP
                   ) -> List[Dict[str, Any]]:
        logger.info(f"Chunkizando em pedaços de ~{chunk_size} chars (overlap {overlap})")
        sentences = re.split(r'(?<=[.!?])\s+', text.replace("\n", " "))
        chunks, curr, pos, idx = [], "", 0, 0
        for sent in sentences:
            if len(curr) + len(sent) < chunk_size:
                curr += sent + " "
            else:
                chunks.append({"id": idx, "text": curr.strip()})
                pos += len(curr)
                idx += 1
                curr = (curr[-overlap:] if overlap < len(curr) else curr) + sent + " "
        if curr.strip():
            chunks.append({"id": idx, "text": curr.strip()})
        logger.info(f"Gerados {len(chunks)} chunks")
        return chunks

# --- Armazenamento e recuperação vetorial no ChromaDB ---
class ChromaStore:

    def __init__(self, persist_dir: str):
        self.client = Client(Settings(
            persist_directory=persist_dir,
            anonymized_telemetry=False
        ))
        # Embedding function nativo do Chroma
        self.embed_func = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL
        )
        self.collection = self.client.get_or_create_collection(
            name="lgpd_collection",
            embedding_function=self.embed_func
        )

    def add_documents(self, chunks: List[Dict[str, Any]]):
        texts = [c["text"] for c in chunks]
        ids   = [str(c["id"]) for c in chunks]
        self.collection.add(
            documents=texts,
            ids=ids
        )
        logger.info(f"{len(chunks)} chunks indexados no ChromaDB")

    def query_embeddings(self, query: str, n_results: int) -> Dict[str, Any]:
        return self.collection.query(
            query_texts=[query],
            n_results=n_results,
            include=["documents","distances","ids"]
        )

# --- Sistema RAG híbrido ChromaDB + BM25 ---
class LGPDRagSystem:

    def __init__(self):
        # Componentes
        self.processor = DocumentProcessor()
        self.chroma    = ChromaStore(CHROMA_DB_DIR)
        self.embedder  = SentenceTransformer(EMBEDDING_MODEL)
        self.bm25: BM25Okapi
        self.chunks: List[Dict[str, Any]]
        self.chunk_texts: List[str]

    async def initialize(self):
        # 1. Extrair + chunkizar
        text = self.processor.extract_text(PDF_PATH)
        self.chunks = self.processor.chunk_text(text)
        self.chunk_texts = [c["text"] for c in self.chunks]
        # 2. Indexar no ChromaDB
        self.chroma.add_documents(self.chunks)
        # 3. Construir índice BM25
        tokenized = [doc.split() for doc in self.chunk_texts]
        self.bm25   = BM25Okapi(tokenized)
        logger.info("Índice BM25 construído com rank-bm25")

    async def setup_agent(self):
        if not hasattr(self, "bm25"):
            await self.initialize()

        deps = RagDependencies(
            client=self.chroma.client,
            embed_model=self.embedder,
            bm25=self.bm25,
            chunk_texts=self.chunk_texts
        )

        system_prompt = """
Você é um especialista em Lei Geral de Proteção de Dados (LGPD) do Brasil, 
atuando como consultor jurídico especializado em proteção de dados.

DIRETRIZES LINGUÍSTICAS OBRIGATÓRIAS:
1. Responda EXCLUSIVAMENTE em português brasileiro formal
2. NUNCA utilize termos em inglês ou estrangeirismos
3. Use terminologia jurídica brasileira oficial conforme adotada na legislação nacional
4. Ao abordar conceitos técnicos, use SEMPRE os equivalentes oficiais em português

TRADUÇÕES OBRIGATÓRIAS:
- "accountability" → "responsabilização" ou "prestação de contas"
- "compliance" → "conformidade"
- "data protection" → "proteção de dados"
- "privacy by design" → "privacidade desde a concepção"
- "opt-in/opt-out" → "consentimento expresso/retirada de consentimento"
- "data controller" → "controlador de dados"
- "data subject" → "titular dos dados"
- "profiling" → "perfilamento"
- "legitimate interest" → "interesse legítimo"
- "data breach" → "violação de dados"
- "consent" → "consentimento"

DIRETRIZES DE CONTEÚDO:
1. Use APENAS as informações contidas nos trechos retornados pela ferramenta retrieve_context
2. Se não encontrar informação suficiente nos trechos, indique claramente que não pode responder com base no documento
3. Cite diretamente trechos relevantes quando apropriado, incluindo a numeração
4. Atribua a cada resposta um nível de confiança de 0 a 1, com base na qualidade dos trechos recuperados
5. Formate suas respostas de maneira clara e estruturada
6. Cite as seções ou artigos da LGPD quando relevante

Lembre-se: Você é um especialista jurídico brasileiro. Use linguagem formal, 
precisa e completamente em português do Brasil.
"""

        self.agent = Agent(
            LLM_MODEL_NAME,
            deps_type=RagDependencies,
            result_type=LGPDResponse,
            system_prompt=system_prompt
        )

        @self.agent.tool()
        async def retrieve_context(ctx: RunContext[RagDependencies], query: str) -> SearchResult:
            """
            Recupera contextos relevantes do documento LGPD usando busca híbrida.
            
            Combina:
            1) Embeddings semânticos via ChromaDB
            2) Algoritmo BM25 para correspondência de termos
            
            Args:
                ctx: Contexto de execução com dependências
                query: Consulta do usuário em linguagem natural
                
            Returns:
                SearchResult: Contextos recuperados com metadados
            """
            start_time = time.time()
            logger.info(f"Iniciando busca por: '{query}'")
            
            # 1) Busca por embeddings (ChromaDB)
            emb_res = self.chroma.query_embeddings(query, n_results=TOP_K*3)
            docs      = emb_res["documents"][0]
            ids       = [int(i) for i in emb_res["ids"][0]]
            distances = emb_res["distances"][0]
            sim_scores = [1 - d for d in distances]  # similaridade
            logger.info(f"Recuperados {len(docs)} documentos via embeddings")

            # 2) Busca BM25
            token_q = query.split()
            bm25_scores = ctx.deps.bm25.get_scores(token_q)
            # normalizar BM25 para [0,1]
            min_b, max_b = min(bm25_scores), max(bm25_scores) or 1.0
            norm_bm25 = [(s - min_b)/(max_b - min_b) for s in bm25_scores]
            logger.info(f"Calculados scores BM25 para {len(norm_bm25)} documentos")

            # 3) Combinar candidatos (união de embedding + BM25)
            candidates = set(ids)
            # também adiciona top BM25 puro
            top_bm25 = sorted(range(len(norm_bm25)),
                              key=lambda i: norm_bm25[i],
                              reverse=True)[:TOP_K*3]
            candidates.update(top_bm25)
            logger.info(f"Total de {len(candidates)} documentos candidatos após fusão")

            # 4) Calcular score híbrido e ordenar
            hybrid = []
            for idx in candidates:
                e = sim_scores[ids.index(idx)] if idx in ids else 0.0
                b = norm_bm25[idx]
                score = ALPHA * e + (1-ALPHA) * b
                hybrid.append((idx, score))
            hybrid.sort(key=lambda x: x[1], reverse=True)

            # 5) Selecionar top_k
            chosen = hybrid[:TOP_K]
            contexts, src_ids, scores = [], [], []
            for rank, (idx, score) in enumerate(chosen, start=1):
                text = ctx.deps.chunk_texts[idx]
                contexts.append(f"[Trecho {rank} (score={score:.2f})]\n{text}")
                src_ids.append(idx)
                scores.append(score)

            elapsed = time.time() - start_time
            logger.info(f"Busca concluída em {elapsed:.2f}s - Recuperados {len(chosen)} trechos finais")
            
            return SearchResult(
                context="\n\n---\n\n".join(contexts),
                source_ids=src_ids,
                similarity_scores=scores
            )

    async def ask(self, query: str) -> LGPDResponse:
        if not hasattr(self, "agent"):
            await self.setup_agent()
        deps = RagDependencies(
            client=self.chroma.client,
            embed_model=self.embedder,
            bm25=self.bm25,
            chunk_texts=self.chunk_texts
        )
        res = await self.agent.run(query, deps=deps)
        return res.data

# --- Sessão interativa ---
async def interactive_session():
    """Sessão interativa para consulta ao sistema RAG da LGPD."""
    print("\n" + "="*60)
    print("   Sistema RAG LGPD (ChromaDB + BM25 Híbrido)   ".center(60))
    print("="*60 + "\n")
    
    system = LGPDRagSystem()
    try:
        print("Inicializando sistema... (pode levar alguns instantes)")
        # Adicionar medição de tempo para inicialização
        start_time = time.time()
        await system.initialize()
        init_time = time.time() - start_time
        print(f"✓ Sistema inicializado em {init_time:.1f}s e pronto para consultas!\n")
        print("Dicas:")
        print("- Faça perguntas específicas sobre a LGPD")
        print("- Pergunte sobre artigos, definições ou obrigações")
        print("- Digite 'sair' para encerrar a sessão\n")
        
        while True:
            q = input("\nO que deseja saber sobre a LGPD? (ou 'sair')\n> ").strip()
            if q.lower() in ("sair","exit","quit"):
                break
            
            if not q:
                print("Por favor, digite uma pergunta.")
                continue
                
            print("\nBuscando informações relevantes...")
            start_time = time.time()
            resp = await system.ask(q)
            query_time = time.time() - start_time
            
            print("\n" + "="*60)
            print(f"Resposta (confiança: {resp.confidence:.2f}):")
            print("-"*60)
            print(resp.answer)
            print("\nFontes utilizadas:")
            for source in resp.sources:
                print(f"- {source}")
            print(f"\nTempo de resposta: {query_time:.2f}s")
            print("="*60)
    
    except KeyboardInterrupt:
        print("\n\nOperação interrompida pelo usuário.")
    except Exception as e:
        logger.error(f"Erro durante execução: {e}")
        print(f"\n\nErro durante a execução: {e}")
    
    print("\nEncerrando sessão. Obrigado por utilizar o sistema RAG LGPD!\n")

if __name__ == "__main__":
    asyncio.run(interactive_session())
