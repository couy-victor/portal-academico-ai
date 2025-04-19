"""
RAG (Retrieval Augmented Generation) Agent for the Academic Agent system.
Responsible for retrieving relevant information from documents to augment responses.
"""
import os
import json
import pickle
from typing import Dict, Any, List, Optional

import faiss
import numpy as np
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from src.config.settings import EMBEDDINGS_DIR, LLM_MODEL, LLM_TEMPERATURE
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
        
        if not pdf_chunks:
            # Try to load from embeddings store
            pdf_chunks, index = load_embeddings_store()
            
            if not pdf_chunks:
                logger.info("No PDF chunks available for RAG")
                return state
        else:
            # Create embeddings for the chunks
            index = create_embeddings_index(pdf_chunks)
        
        # Retrieve relevant chunks
        relevant_chunks = retrieve_relevant_chunks(state["user_query"], pdf_chunks, index)
        
        # Extract context from relevant chunks
        rag_context = extract_context_from_chunks(relevant_chunks, state["user_query"])
        
        # Update state with RAG results
        state["rag_documents"] = relevant_chunks
        state["rag_context"] = rag_context
        
        # Log success
        logger.info(f"RAG retrieval completed with {len(relevant_chunks)} relevant chunks")
        
    except Exception as e:
        error_msg = f"Error in RAG retrieval: {str(e)}"
        logger.error(error_msg)
        # Don't set error state, just log it - we want to continue the flow
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["rag_error"] = error_msg
    
    return state

def create_embeddings_index(chunks: List[Dict[str, Any]]) -> faiss.IndexFlatL2:
    """
    Creates a FAISS index for the chunks.
    
    Args:
        chunks (List[Dict[str, Any]]): List of text chunks
        
    Returns:
        faiss.IndexFlatL2: FAISS index
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
    
    # Save embeddings and index
    save_embeddings_store(chunks, index)
    
    return index

def save_embeddings_store(chunks: List[Dict[str, Any]], index: faiss.IndexFlatL2) -> None:
    """
    Saves chunks and FAISS index to disk.
    
    Args:
        chunks (List[Dict[str, Any]]): List of text chunks
        index (faiss.IndexFlatL2): FAISS index
    """
    # Ensure the directory exists
    os.makedirs(EMBEDDINGS_DIR, exist_ok=True)
    
    # Save chunks
    chunks_path = os.path.join(EMBEDDINGS_DIR, "chunks.json")
    with open(chunks_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    
    # Save index
    index_path = os.path.join(EMBEDDINGS_DIR, "index.faiss")
    faiss.write_index(index, index_path)
    
    logger.info(f"Saved {len(chunks)} chunks and FAISS index to {EMBEDDINGS_DIR}")

def load_embeddings_store() -> tuple:
    """
    Loads chunks and FAISS index from disk.
    
    Returns:
        tuple: (chunks, index)
    """
    chunks_path = os.path.join(EMBEDDINGS_DIR, "chunks.json")
    index_path = os.path.join(EMBEDDINGS_DIR, "index.faiss")
    
    # Check if files exist
    if not os.path.exists(chunks_path) or not os.path.exists(index_path):
        return [], None
    
    try:
        # Load chunks
        with open(chunks_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)
        
        # Load index
        index = faiss.read_index(index_path)
        
        logger.info(f"Loaded {len(chunks)} chunks and FAISS index from {EMBEDDINGS_DIR}")
        
        return chunks, index
    
    except Exception as e:
        logger.error(f"Error loading embeddings store: {str(e)}")
        return [], None

def retrieve_relevant_chunks(query: str, chunks: List[Dict[str, Any]], index: faiss.IndexFlatL2, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Retrieves relevant chunks for a query.
    
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
            relevant_chunks.append(chunk)
    
    # Sort by relevance score
    relevant_chunks.sort(key=lambda x: x["relevance_score"], reverse=True)
    
    return relevant_chunks

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
