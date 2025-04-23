"""
Test script for the Academic Query Agent.
"""
import os
import sys
from dotenv import load_dotenv

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.main import process_query

# Load environment variables
load_dotenv()

def test_academic_query():
    """
    Tests the academic query agent with various queries.
    """
    # Define test queries
    test_queries = [
        "Quantas faltas eu tenho na disciplina de Teoria da Computação?",
        "Qual é a minha nota em Cálculo?",
        "Quais são as disciplinas que estou cursando neste semestre?",
        "Quem é o professor de Banco de Dados?",
        "Quando é a próxima prova de Algoritmos?"
    ]
    
    # Define user context
    user_context = {
        "nome": "Ana Beatriz Sales",
        "curso_id": "055b7126-4b35-5756-a3f4-82b4bcc92146",
        "curso_nome": "Ciência da Computação",
        "periodo_atual": "2023",
        "disciplina_id": "CS101",
        "disciplina_nome": "Teoria da Computação"
    }
    
    # Process each query
    for query in test_queries:
        print("\n" + "=" * 80)
        print(f"Query: {query}")
        print("=" * 80)
        
        try:
            # Process the query
            result = process_query(
                user_query=query,
                user_id="test_user",
                user_context=user_context
            )
            
            # Print the response
            print(f"\nResponse: {result.get('response', 'No response')}")
            
            # Print additional information
            print("\nAdditional Information:")
            print(f"Intent: {result.get('intent', 'unknown')}")
            print(f"Confidence: {result.get('confidence', 0.0)}")
            
            # Print SQL if available
            if "generated_sql" in result:
                print(f"\nGenerated SQL: {result['generated_sql']}")
            
            # Print query results if available
            if "query_results" in result and result["query_results"]:
                print("\nQuery Results:")
                for i, row in enumerate(result["query_results"]):
                    print(f"Row {i+1}: {row}")
            
            # Print any errors
            if "error" in result and result["error"]:
                print(f"\nError: {result['error']}")
                
        except Exception as e:
            print(f"\nError processing query: {str(e)}")
        
        print("\n" + "-" * 80)

def main():
    """
    Main function.
    """
    # Check if required environment variables are set
    required_vars = ["OPENAI_API_KEY", "SUPABASE_URL", "SUPABASE_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in the .env file.")
        return
    
    # Run the test
    test_academic_query()

if __name__ == "__main__":
    main()
