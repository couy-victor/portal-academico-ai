"""
Test script for the RAG (Retrieval Augmented Generation) functionality.
"""
import os
import sys
from dotenv import load_dotenv

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.rag_agent import rag_agent, create_embeddings_index, load_embeddings_store
from src.models.state import AcademicAgentState
from src.config.settings import PDF_STORAGE_DIR, EMBEDDINGS_DIR

# Load environment variables
load_dotenv()

def process_pdf_files():
    """
    Processes PDF files in the PDF_STORAGE_DIR and creates embeddings.
    """
    from langchain_community.document_loaders import PyPDFLoader
    from langchain.text_splitter import RecursiveCharacterTextSplitter

    print(f"Looking for PDF files in {PDF_STORAGE_DIR}...")

    # Check if the directory exists
    if not os.path.exists(PDF_STORAGE_DIR):
        print(f"Directory {PDF_STORAGE_DIR} does not exist.")
        return []

    # Get all PDF files in the directory
    pdf_files = [f for f in os.listdir(PDF_STORAGE_DIR) if f.endswith('.pdf')]

    if not pdf_files:
        print("No PDF files found.")
        return []

    print(f"Found {len(pdf_files)} PDF files: {', '.join(pdf_files)}")

    # Process each PDF file
    all_chunks = []

    for pdf_file in pdf_files:
        pdf_path = os.path.join(PDF_STORAGE_DIR, pdf_file)
        print(f"Processing {pdf_file}...")

        try:
            # Load the PDF
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()

            # Split the documents into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
            )
            chunks = text_splitter.split_documents(documents)

            # Convert to the format expected by the RAG agent
            for i, chunk in enumerate(chunks):
                all_chunks.append({
                    "text": chunk.page_content,
                    "source": pdf_file,
                    "page": chunk.metadata.get("page", 0),
                    "chunk_id": f"{pdf_file}-{i}"
                })

            print(f"Extracted {len(chunks)} chunks from {pdf_file}")

        except Exception as e:
            print(f"Error processing {pdf_file}: {str(e)}")

    print(f"Total chunks extracted: {len(all_chunks)}")
    return all_chunks

def test_rag():
    """
    Tests the RAG functionality.
    """
    print("\n=== Testing RAG (Retrieval Augmented Generation) ===\n")

    # Check if embeddings already exist
    chunks, index, _ = load_embeddings_store()

    if not chunks:
        print("No existing embeddings found. Processing PDF files...")
        chunks = process_pdf_files()

        if not chunks:
            print("No chunks extracted from PDFs. Cannot proceed with RAG testing.")
            return

        print("Creating embeddings index...")
        index, _ = create_embeddings_index(chunks)
    else:
        print(f"Loaded {len(chunks)} existing chunks from embeddings store.")

    # Get test query from user
    test_query = input("Digite sua consulta (ou Enter para usar a consulta padrão): ") or "Como é feito o cálculo de nota das avaliações?"

    print("\n" + "=" * 80)
    print(f"Query: {test_query}")
    print("=" * 80)

    # Create initial state
    state = AcademicAgentState(
        user_query=test_query,
        user_id="test_user",
        user_context={}
    )

    # Add chunks to state for testing
    state["metadata"] = {"pdf_chunks": chunks}

    # Run the RAG agent
    try:
        updated_state = rag_agent(state)

        # Check if we have RAG results
        if "rag_documents" in updated_state and updated_state["rag_documents"]:
            print(f"\nRetrieved {len(updated_state['rag_documents'])} relevant documents:")

            for i, doc in enumerate(updated_state["rag_documents"][:3]):  # Show top 3 for brevity
                print(f"\n[{i+1}] Source: {doc['source']}, Page: {doc.get('page', 'N/A')}")
                print(f"Relevance: {doc.get('relevance_score', 0.0):.4f}")
                print(f"Text: {doc['text'][:200]}...")

            if "rag_context" in updated_state and updated_state["rag_context"]:
                print("\nExtracted Context:")
                print(updated_state["rag_context"][:500] + "..." if len(updated_state["rag_context"]) > 500 else updated_state["rag_context"])
        else:
            print("No relevant documents found.")

    except Exception as e:
        print(f"Error testing RAG: {str(e)}")

    print("\n" + "-" * 80)

if __name__ == "__main__":
    test_rag()
