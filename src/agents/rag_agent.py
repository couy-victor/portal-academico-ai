"""
RAG (Retrieval Augmented Generation) Agent for the Academic Agent system.
Responsible for retrieving relevant information from documents to augment responses.
"""
import os
import json
import pickle
import time
from typing import Dict, Any, List, Optional, Tuple

import faiss
import numpy as np
from rank_bm25 import BM25Okapi
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from src.config.settings import (EMBEDDINGS_DIR, LLM_MODEL, LLM_TEMPERATURE,
                              USE_BM25, HYBRID_ALPHA, BM25_K1, BM25_B, RAG_STORAGE_TYPE,
                              CHUNK_SIZE, CHUNK_OVERLAP)
from src.database.supabase_client import supabase
from src.models.state import AcademicAgentState
from src.utils.logging import logger

# Initialize embeddings model
embeddings_model = OpenAIEmbeddings()

def rag_agent(state: AcademicAgentState) -> AcademicAgentState:
    """
    Retrieves relevant information from documents to augment responses.

    Args:
        state (AcademicAgentState): Current state

    Returns:
        AcademicAgentState: Updated state with retrieved information
    """
    # Skip if we already have an error or coming from cache
    if state.get("error") or state.get("from_cache", False):
        return state

    try:
        # Check if we have processed PDF chunks
        pdf_chunks = state.get("metadata", {}).get("pdf_chunks", [])

        if RAG_STORAGE_TYPE == "supabase":
            # Use Supabase for RAG
            if pdf_chunks:
                # If we have new chunks, add them to Supabase
                for chunk in pdf_chunks:
                    add_document_to_supabase(chunk["text"], {
                        "source": chunk.get("source", "Unknown"),
                        "chunk_index": chunk.get("chunk_index", 0),
                    })

            # Retrieve relevant chunks from Supabase
            relevant_chunks = search_documents_in_supabase(state["user_query"], top_k=5)

            if not relevant_chunks:
                logger.info("No relevant documents found in Supabase for RAG")
                return state

            retrieval_method = "supabase_vector"
        else:
            # Use local storage for RAG
            if not pdf_chunks:
                # Try to load from embeddings store
                pdf_chunks, index, bm25_index = load_embeddings_store()

                if not pdf_chunks:
                    logger.info("No PDF chunks available for RAG")
                    return state
            else:
                # Create embeddings for the chunks
                index, bm25_index = create_embeddings_index(pdf_chunks)

            # Retrieve relevant chunks using hybrid approach if BM25 is enabled
            relevant_chunks = retrieve_relevant_chunks(
                state["user_query"],
                pdf_chunks,
                index,
                bm25_index=bm25_index
            )

            retrieval_method = "hybrid" if USE_BM25 and bm25_index is not None else "embeddings"

        # Extract context from relevant chunks
        rag_context = extract_context_from_chunks(relevant_chunks, state["user_query"])

        # Update state with RAG results
        state["rag_documents"] = relevant_chunks
        state["rag_context"] = rag_context

        # Add retrieval method to metadata
        if "metadata" not in state:
            state["metadata"] = {}

        state["metadata"]["retrieval_method"] = retrieval_method

        # Log success
        logger.info(f"RAG retrieval completed with {len(relevant_chunks)} relevant chunks using {retrieval_method} approach")

    except Exception as e:
        error_msg = f"Error in RAG retrieval: {str(e)}"
        logger.error(error_msg)
        # Don't set error state, just log it - we want to continue the flow
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["rag_error"] = error_msg

    return state

def create_embeddings_index(chunks: List[Dict[str, Any]]) -> Tuple[faiss.IndexFlatL2, Optional[BM25Okapi]]:
    """
    Creates a FAISS index and BM25 index for the chunks.

    Args:
        chunks (List[Dict[str, Any]]): List of text chunks

    Returns:
        Tuple[faiss.IndexFlatL2, Optional[BM25Okapi]]: FAISS index and BM25 index
    """
    # Extract text from chunks
    texts = [chunk["text"] for chunk in chunks]

    # Generate embeddings
    embeddings = embeddings_model.embed_documents(texts)

    # Convert to numpy array
    embeddings_array = np.array(embeddings).astype('float32')

    # Create FAISS index
    dimension = embeddings_array.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings_array)

    # Create BM25 index if enabled
    bm25_index = None
    if USE_BM25:
        # Tokenize texts for BM25
        tokenized_texts = [text.lower().split() for text in texts]
        bm25_index = BM25Okapi(tokenized_texts, k1=BM25_K1, b=BM25_B)
        logger.info("BM25 index created successfully")

    # Save embeddings and indexes
    save_embeddings_store(chunks, index, bm25_index)

    return index, bm25_index

def save_embeddings_store(chunks: List[Dict[str, Any]], index: faiss.IndexFlatL2, bm25_index: Optional[BM25Okapi] = None) -> None:
    """
    Saves chunks, FAISS index, and BM25 index to disk.

    Args:
        chunks (List[Dict[str, Any]]): List of text chunks
        index (faiss.IndexFlatL2): FAISS index
        bm25_index (Optional[BM25Okapi]): BM25 index
    """
    # Ensure the directory exists
    os.makedirs(EMBEDDINGS_DIR, exist_ok=True)

    # Save chunks
    chunks_path = os.path.join(EMBEDDINGS_DIR, "chunks.json")
    with open(chunks_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    # Save FAISS index
    index_path = os.path.join(EMBEDDINGS_DIR, "index.faiss")
    faiss.write_index(index, index_path)

    # Save BM25 index if available
    if bm25_index is not None:
        bm25_path = os.path.join(EMBEDDINGS_DIR, "bm25.pickle")
        with open(bm25_path, "wb") as f:
            pickle.dump(bm25_index, f)

    log_message = f"Saved {len(chunks)} chunks and FAISS index to {EMBEDDINGS_DIR}"
    if bm25_index is not None:
        log_message += " with BM25 index"
    logger.info(log_message)

def load_embeddings_store() -> tuple:
    """
    Loads chunks, FAISS index, and BM25 index from disk.

    Returns:
        tuple: (chunks, index, bm25_index)
    """
    chunks_path = os.path.join(EMBEDDINGS_DIR, "chunks.json")
    index_path = os.path.join(EMBEDDINGS_DIR, "index.faiss")
    bm25_path = os.path.join(EMBEDDINGS_DIR, "bm25.pickle")

    # Check if essential files exist
    if not os.path.exists(chunks_path) or not os.path.exists(index_path):
        return [], None, None

    try:
        # Load chunks
        with open(chunks_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)

        # Load FAISS index
        index = faiss.read_index(index_path)

        # Load BM25 index if available and enabled
        bm25_index = None
        if USE_BM25 and os.path.exists(bm25_path):
            try:
                with open(bm25_path, "rb") as f:
                    bm25_index = pickle.load(f)
                logger.info("BM25 index loaded successfully")
            except Exception as e:
                logger.warning(f"Error loading BM25 index: {str(e)}. Will recreate if needed.")

        log_message = f"Loaded {len(chunks)} chunks and FAISS index from {EMBEDDINGS_DIR}"
        if bm25_index is not None:
            log_message += " with BM25 index"
        logger.info(log_message)

        return chunks, index, bm25_index

    except Exception as e:
        logger.error(f"Error loading embeddings store: {str(e)}")
        return [], None, None

# Funções para Supabase RAG
def add_document_to_supabase(content: str, metadata: Dict[str, Any] = None) -> str:
    """
    Adds a document to the Supabase vector store.

    Args:
        content (str): Document content
        metadata (Dict[str, Any], optional): Document metadata

    Returns:
        str: Document ID
    """
    # Generate embedding
    embedding = embeddings_model.embed_documents([content])[0]

    # Prepare metadata
    if metadata is None:
        metadata = {}

    # Add document to Supabase
    response = supabase.rpc(
        'add_document',
        {
            'p_content': content,
            'p_metadata': json.dumps(metadata),
            'p_embedding': embedding
        }
    ).execute()

    if hasattr(response, 'error') and response.error:
        raise Exception(f"Error adding document: {response.error.message}")

    return response.data

def search_documents_in_supabase(query: str, top_k: int = 5, filter_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    Searches for documents similar to the query in Supabase.

    Args:
        query (str): Query text
        top_k (int): Number of documents to retrieve
        filter_metadata (Dict[str, Any], optional): Filter by metadata

    Returns:
        List[Dict[str, Any]]: List of similar documents
    """
    start_time = time.time()
    logger.info(f"Searching for documents similar to: '{query}'")

    # Generate query embedding
    query_embedding = embeddings_model.embed_query(query)

    # Prepare filter
    filter_json = json.dumps(filter_metadata) if filter_metadata else None

    # Search documents in Supabase
    response = supabase.rpc(
        'search_documents',
        {
            'p_query_embedding': query_embedding,
            'p_match_count': top_k,
            'p_filter': filter_json
        }
    ).execute()

    if hasattr(response, 'error') and response.error:
        raise Exception(f"Error searching documents: {response.error.message}")

    results = response.data or []

    # Format results to match the expected format
    formatted_results = []
    for i, result in enumerate(results):
        formatted_result = {
            "id": str(result["id"]),
            "text": result["content"],
            "metadata": result["metadata"],
            "relevance_score": result["similarity"],
            "retrieval_method": "supabase_vector",
            "source": result["metadata"].get("source", "Unknown")
        }
        formatted_results.append(formatted_result)

    elapsed = time.time() - start_time
    logger.info(f"Supabase search completed in {elapsed:.2f}s - Found {len(formatted_results)} documents")

    return formatted_results

def chunk_and_add_document(content: str, source: str, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Chunks a document and adds each chunk to the Supabase vector store.

    Args:
        content (str): Document content
        source (str): Document source
        chunk_size (int): Size of each chunk
        chunk_overlap (int): Overlap between chunks

    Returns:
        List[str]: List of chunk IDs
    """
    logger.info(f"Chunking document '{source}' with size {len(content)} chars")
    logger.info(f"Using chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")

    # Validate inputs
    if not content or len(content.strip()) == 0:
        logger.warning("Empty content provided. Nothing to chunk.")
        return []

    # Use a simpler chunking approach for more reliability
    # Split by paragraphs first
    paragraphs = content.split('\n\n')
    paragraphs = [p for p in paragraphs if p.strip()]
    logger.info(f"Document split into {len(paragraphs)} paragraphs")

    # Combine paragraphs into chunks of approximately chunk_size
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        # If adding this paragraph would exceed chunk_size, save current chunk and start a new one
        if len(current_chunk) + len(para) > chunk_size and current_chunk:
            chunks.append(current_chunk)
            # Start new chunk with overlap from previous chunk if possible
            words = current_chunk.split()
            overlap_words = min(len(words), int(chunk_overlap / 5))  # Approximate words in overlap
            current_chunk = " ".join(words[-overlap_words:]) if overlap_words > 0 else ""

        # Add paragraph to current chunk
        if current_chunk and not current_chunk.endswith("\n"):
            current_chunk += "\n\n"
        current_chunk += para

    # Add the last chunk if it's not empty
    if current_chunk.strip():
        chunks.append(current_chunk)

    logger.info(f"Created {len(chunks)} chunks from document")

    # Add each chunk to the vector store
    chunk_ids = []
    for i, chunk in enumerate(chunks):
        try:
            logger.info(f"Processing chunk {i+1}/{len(chunks)} ({len(chunk)} chars)")

            metadata = {
                'source': source,
                'chunk_index': i,
                'total_chunks': len(chunks)
            }

            chunk_id = add_document_to_supabase(chunk, metadata)
            chunk_ids.append(chunk_id)
            logger.info(f"Added chunk {i+1}/{len(chunks)} to Supabase")

        except Exception as e:
            logger.error(f"Error adding chunk {i+1}/{len(chunks)}: {str(e)}")

    logger.info(f"Added {len(chunk_ids)} chunks from document '{source}' to Supabase")

    return chunk_ids

# Funções para armazenamento local (FAISS + BM25)
def retrieve_relevant_chunks(query: str, chunks: List[Dict[str, Any]], index: faiss.IndexFlatL2, top_k: int = 5, bm25_index: Optional[BM25Okapi] = None) -> List[Dict[str, Any]]:
    """
    Retrieves relevant chunks for a query using a hybrid approach (embeddings + BM25).

    Args:
        query (str): Query text
        chunks (List[Dict[str, Any]]): List of text chunks
        index (faiss.IndexFlatL2): FAISS index
        top_k (int): Number of chunks to retrieve
        bm25_index (Optional[BM25Okapi]): BM25 index

    Returns:
        List[Dict[str, Any]]: List of relevant chunks
    """
    start_time = time.time()
    logger.info(f"Iniciando busca por: '{query}'")

    # If BM25 is not enabled or index is not available, use only embeddings
    if not USE_BM25 or bm25_index is None:
        return retrieve_with_embeddings(query, chunks, index, top_k)

    # Use hybrid approach (embeddings + BM25)
    return retrieve_with_hybrid(query, chunks, index, bm25_index, top_k)

def retrieve_with_embeddings(query: str, chunks: List[Dict[str, Any]], index: faiss.IndexFlatL2, top_k: int) -> List[Dict[str, Any]]:
    """
    Retrieves relevant chunks using only embeddings.

    Args:
        query (str): Query text
        chunks (List[Dict[str, Any]]): List of text chunks
        index (faiss.IndexFlatL2): FAISS index
        top_k (int): Number of chunks to retrieve

    Returns:
        List[Dict[str, Any]]: List of relevant chunks
    """
    # Generate query embedding
    query_embedding = embeddings_model.embed_query(query)

    # Convert to numpy array
    query_array = np.array([query_embedding]).astype('float32')

    # Search index
    distances, indices = index.search(query_array, top_k)

    # Get relevant chunks
    relevant_chunks = []
    for i, idx in enumerate(indices[0]):
        if idx < len(chunks):
            chunk = chunks[idx].copy()
            chunk["relevance_score"] = float(1.0 / (1.0 + distances[0][i]))
            chunk["retrieval_method"] = "embeddings"
            relevant_chunks.append(chunk)

    # Sort by relevance score
    relevant_chunks.sort(key=lambda x: x["relevance_score"], reverse=True)
    logger.info(f"Recuperados {len(relevant_chunks)} documentos via embeddings")

    return relevant_chunks

def retrieve_with_hybrid(query: str, chunks: List[Dict[str, Any]], index: faiss.IndexFlatL2, bm25_index: BM25Okapi, top_k: int) -> List[Dict[str, Any]]:
    """
    Retrieves relevant chunks using a hybrid approach (embeddings + BM25).

    Args:
        query (str): Query text
        chunks (List[Dict[str, Any]]): List of text chunks
        index (faiss.IndexFlatL2): FAISS index
        bm25_index (BM25Okapi): BM25 index
        top_k (int): Number of chunks to retrieve

    Returns:
        List[Dict[str, Any]]: List of relevant chunks
    """
    start_time = time.time()  # Definir start_time aqui

    # 1) Busca por embeddings (FAISS)
    query_embedding = embeddings_model.embed_query(query)
    query_array = np.array([query_embedding]).astype('float32')
    distances, indices = index.search(query_array, top_k * 3)  # Recupera mais para combinar depois

    # Calcular scores de similaridade para embeddings
    emb_scores = {}
    for i, idx in enumerate(indices[0]):
        if idx < len(chunks):
            emb_scores[idx] = float(1.0 / (1.0 + distances[0][i]))

    logger.info(f"Recuperados {len(emb_scores)} documentos via embeddings")

    # 2) Busca BM25
    token_q = query.lower().split()
    bm25_scores_raw = bm25_index.get_scores(token_q)

    # Normalizar BM25 para [0,1]
    min_b, max_b = min(bm25_scores_raw), max(bm25_scores_raw) or 1.0
    norm_bm25 = {}
    for idx, score in enumerate(bm25_scores_raw):
        norm_bm25[idx] = (score - min_b) / (max_b - min_b) if max_b > min_b else 0.0

    logger.info(f"Calculados scores BM25 para {len(norm_bm25)} documentos")

    # 3) Combinar candidatos (união de embedding + BM25)
    candidates = set(emb_scores.keys())

    # Também adiciona top BM25 puro
    top_bm25_indices = sorted(range(len(bm25_scores_raw)),
                            key=lambda i: bm25_scores_raw[i],
                            reverse=True)[:top_k * 3]
    candidates.update(top_bm25_indices)

    logger.info(f"Total de {len(candidates)} documentos candidatos após fusão")

    # 4) Calcular score híbrido e ordenar
    hybrid_results = []
    for idx in candidates:
        if idx >= len(chunks):
            continue

        e_score = emb_scores.get(idx, 0.0)
        b_score = norm_bm25.get(idx, 0.0)
        hybrid_score = HYBRID_ALPHA * e_score + (1 - HYBRID_ALPHA) * b_score

        chunk = chunks[idx].copy()
        chunk["relevance_score"] = hybrid_score
        chunk["embedding_score"] = e_score
        chunk["bm25_score"] = b_score
        chunk["retrieval_method"] = "hybrid"
        hybrid_results.append(chunk)

    # Ordenar por score híbrido
    hybrid_results.sort(key=lambda x: x["relevance_score"], reverse=True)

    # Limitar ao top_k
    result = hybrid_results[:top_k]

    elapsed = time.time() - start_time
    logger.info(f"Busca híbrida concluída em {elapsed:.2f}s - Recuperados {len(result)} trechos finais")

    return result

def migrate_documents_to_supabase():
    """
    Migrates documents from local storage to Supabase.
    """
    # Check if chunks file exists
    chunks_path = os.path.join(EMBEDDINGS_DIR, "chunks.json")
    if not os.path.exists(chunks_path):
        logger.info("No chunks file found. Nothing to migrate.")
        return

    # Load chunks
    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    logger.info(f"Found {len(chunks)} chunks to migrate")

    # Migrate each chunk
    for i, chunk in enumerate(chunks):
        try:
            # Add document to Supabase
            add_document_to_supabase(
                content=chunk["text"],
                metadata={
                    "source": chunk.get("source", "Unknown"),
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
            )

            logger.info(f"Migrated chunk {i+1}/{len(chunks)}")

        except Exception as e:
            logger.error(f"Error migrating chunk {i+1}: {str(e)}")

    logger.info("Migration completed")

def extract_context_from_chunks(chunks: List[Dict[str, Any]], query: str) -> str:
    """
    Extracts context from relevant chunks.

    Args:
        chunks (List[Dict[str, Any]]): List of relevant chunks
        query (str): Query text

    Returns:
        str: Extracted context
    """
    if not chunks:
        return ""

    # Combine all chunks into a single context
    combined_context = ""
    for i, chunk in enumerate(chunks):
        combined_context += f"[Documento: {chunk['source']}, Trecho: {i+1}]\n"
        combined_context += f"{chunk['text']}\n\n"

    # For simple cases, just return the combined context
    if len(chunks) <= 2:
        return combined_context

    # For more chunks, use LLM to extract the most relevant information
    prompt = ChatPromptTemplate.from_template("""
    Você é um assistente especializado em extrair informações relevantes de documentos.

    Pergunta do usuário: {query}

    Trechos de documentos:
    {chunks}

    Extraia as informações mais relevantes dos trechos acima que ajudam a responder à pergunta do usuário.
    Organize as informações de forma coerente e concisa.
    Cite a fonte (documento e trecho) para cada informação extraída.

    Informações relevantes:
    """)

    # Initialize LLM
    llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE)

    # Prepare inputs
    inputs = {
        "query": query,
        "chunks": combined_context
    }

    # Execute the extraction
    response = llm.invoke(prompt.format_messages(**inputs))

    # Extract the context
    extracted_context = response.content.strip()

    return extracted_context
