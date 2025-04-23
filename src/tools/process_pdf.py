"""
Script to process a PDF file and store it in Supabase.
"""
import os
import sys
import time
from pypdf import PdfReader

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.rag_agent import chunk_and_add_document
from src.config.settings import PDF_STORAGE_DIR

def process_pdf_document(pdf_path, source_name=None):
    """
    Processes a PDF document and stores it in the vector database.

    Args:
        pdf_path (str): Path to the PDF file
        source_name (str, optional): Name of the source. If None, uses the file name.

    Returns:
        List[str]: IDs of the created chunks
    """
    # Extract source name if not provided
    if source_name is None:
        source_name = os.path.basename(pdf_path)

    print(f"Processing PDF: {pdf_path}")
    print(f"Source name: {source_name}")

    # Read the PDF
    start_time = time.time()
    reader = PdfReader(pdf_path)
    text = ""
    for i, page in enumerate(reader.pages):
        page_text = page.extract_text() or ""
        text += page_text + "\n"
        print(f"Extracted page {i+1}/{len(reader.pages)} ({len(page_text)} chars)")

    print(f"Total extracted text: {len(text)} characters")
    extract_time = time.time() - start_time
    print(f"Extraction completed in {extract_time:.2f} seconds")

    # Chunk and add to Supabase
    print("\nChunking and adding to Supabase...")
    start_time = time.time()
    chunk_ids = chunk_and_add_document(text, source_name)
    process_time = time.time() - start_time

    print(f"Document '{source_name}' processed: {len(chunk_ids)} chunks created")
    print(f"Processing completed in {process_time:.2f} seconds")

    return chunk_ids

def main():
    """
    Main function to process the PDF file.
    """
    # Define the PDF file path
    pdf_file = "pee_bancodados_pe_edit+rev.pdf"
    pdf_path = os.path.join(PDF_STORAGE_DIR, pdf_file)

    # Check if the file exists
    if not os.path.exists(pdf_path):
        print(f"Error: File not found at {pdf_path}")
        return

    # Process the PDF
    try:
        print(f"Starting to process {pdf_file}...")
        chunk_ids = process_pdf_document(pdf_path)
        print(f"\nSuccess! {len(chunk_ids)} chunks created and stored in Supabase.")
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")

if __name__ == "__main__":
    main()
