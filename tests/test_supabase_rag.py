"""
Test script for the Supabase RAG implementation.
"""
import os
import sys
import json
from dotenv import load_dotenv

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.rag_agent import search_documents_in_supabase, add_document_to_supabase, chunk_and_add_document
from src.config.settings import RAG_STORAGE_TYPE

# Load environment variables
load_dotenv()

def test_supabase_rag():
    """
    Tests the Supabase RAG implementation.
    """
    print("\n" + "-" * 80)
    print("                         Testing Supabase RAG")
    print("-" * 80)

    # Check if RAG_STORAGE_TYPE is set to "supabase"
    if RAG_STORAGE_TYPE != "supabase":
        print("WARNING: RAG_STORAGE_TYPE is not set to 'supabase'. Set it in .env file.")
        print("Current value:", RAG_STORAGE_TYPE)

    # Test query
    test_query = input("Digite sua consulta: ") or "Como é feito o cálculo de nota, das avaliações?"

    print("\n" + "=" * 80)
    print(f"Query: {test_query}")
    print("=" * 80)

    # Search for documents
    try:
        print("\nBuscando documentos relevantes...")
        results = search_documents_in_supabase(test_query, top_k=5)

        # Print results
        print(f"\nEncontrados {len(results)} documentos relevantes:")
        for i, result in enumerate(results):
            print(f"\n--- Documento {i+1} (score: {result['relevance_score']:.4f}) ---")
            print(f"Fonte: {result['source']}")
            print(f"Texto: {result['text'][:200]}...")

        # Print combined context
        print("\n" + "=" * 80)
        print("Contexto combinado:")
        print("-" * 80)
        combined_context = ""
        for i, result in enumerate(results):
            combined_context += f"[Documento: {result['source']}, Trecho: {i+1}]\n"
            combined_context += f"{result['text']}\n\n"

        print(combined_context)

    except Exception as e:
        print(f"Erro ao buscar documentos: {str(e)}")

    print("\n" + "-" * 80)

def test_add_document():
    """
    Tests adding a document to Supabase.
    """
    print("\n" + "-" * 80)
    print("                         Testing Add Document")
    print("-" * 80)

    # Test document
    test_content = input("Digite o conteúdo do documento (ou Enter para usar texto padrão): ") or "Este é um documento de teste para o sistema RAG com Supabase."
    test_source = input("Digite a fonte do documento (ou Enter para usar fonte padrão): ") or "Teste"

    print("\n" + "=" * 80)
    print(f"Conteúdo: {test_content}")
    print(f"Fonte: {test_source}")
    print("=" * 80)

    # Add document
    try:
        print("\nAdicionando documento ao Supabase...")
        doc_id = add_document_to_supabase(
            content=test_content,
            metadata={
                "source": test_source,
                "test": True
            }
        )

        print(f"\nDocumento adicionado com sucesso! ID: {doc_id}")

    except Exception as e:
        print(f"Erro ao adicionar documento: {str(e)}")

    print("\n" + "-" * 80)

def test_chunk_document():
    """
    Tests chunking and adding a document to Supabase.
    """
    print("\n" + "-" * 80)
    print("                         Testing Chunk Document")
    print("-" * 80)

    # Test document
    test_content = input("Digite o caminho para um arquivo (PDF ou texto) (ou Enter para usar texto padrão): ")

    if test_content and os.path.exists(test_content):
        # Check if it's a PDF file
        if test_content.lower().endswith('.pdf'):
            try:
                from pypdf import PdfReader
                reader = PdfReader(test_content)
                content = ""
                for i, page in enumerate(reader.pages):
                    print(f"Extraindo página {i+1}/{len(reader.pages)}...")
                    content += (page.extract_text() or "") + "\n"
                print(f"Texto extraído: {len(content)} caracteres")
            except Exception as e:
                print(f"Erro ao processar PDF: {str(e)}")
                content = "Este é um documento de teste longo para o sistema RAG com Supabase. " * 20
                source = "Documento de Teste (fallback)"
        else:
            # Assume it's a text file
            try:
                with open(test_content, "r", encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Try with a different encoding
                with open(test_content, "r", encoding="latin-1") as f:
                    content = f.read()
        source = os.path.basename(test_content)
    else:
        content = "Este é um documento de teste longo para o sistema RAG com Supabase. " * 20
        source = "Documento de Teste"

    print("\n" + "=" * 80)
    print(f"Fonte: {source}")
    print(f"Tamanho do conteúdo: {len(content)} caracteres")
    print("=" * 80)

    # Chunk and add document
    try:
        print("\nDividindo e adicionando documento ao Supabase...")
        chunk_ids = chunk_and_add_document(content, source)

        print(f"\nDocumento dividido e adicionado com sucesso! {len(chunk_ids)} chunks criados.")

    except Exception as e:
        print(f"Erro ao dividir e adicionar documento: {str(e)}")

    print("\n" + "-" * 80)

if __name__ == "__main__":
    # Ask which test to run
    print("Escolha o teste a ser executado:")
    print("1. Buscar documentos")
    print("2. Adicionar documento")
    print("3. Dividir e adicionar documento")
    print("4. Executar todos os testes")

    choice = input("Escolha (1-4): ")

    if choice == "1":
        test_supabase_rag()
    elif choice == "2":
        test_add_document()
    elif choice == "3":
        test_chunk_document()
    elif choice == "4":
        test_add_document()
        test_chunk_document()
        test_supabase_rag()
    else:
        print("Escolha inválida.")
