"""
Script to migrate documents from local storage to Supabase.
"""
import os
import sys

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.rag_agent import migrate_documents_to_supabase

def main():
    """
    Main function to migrate documents.
    """
    print("Starting migration process...")

    # Migrate documents
    print("\n=== Migrating documents to Supabase ===")
    migrate_documents_to_supabase()

    print("\nMigration process completed.")

if __name__ == "__main__":
    main()
