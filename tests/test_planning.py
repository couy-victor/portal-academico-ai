"""
Test script for the planning agent.
"""
import os
import sys
import argparse
from dotenv import load_dotenv

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.planning_agent import planning_agent
from src.models.state import AcademicAgentState
from src.utils.logging import logger

# Load environment variables
load_dotenv()

def parse_args():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(description="Test Planning Agent")
    parser.add_argument("--query", type=str, help="Query to test")
    parser.add_argument("--single_query", action="store_true", help="Run only a single query")
    args = parser.parse_args()
    
    # Print arguments for debugging
    print(f"\nArguments recebidos:")
    print(f"  --query: {args.query}")
    print(f"  --single_query: {args.single_query}")
    print(f"\nDiretório atual: {os.getcwd()}")
    
    return args

def test_planning():
    """
    Test the planning agent.
    """
    print("\n=== Testing Planning Agent ===\n")
    
    # Define test queries
    test_queries = [
        "Preciso organizar meus estudos para as provas finais que começam em duas semanas.",
        "Como posso criar um cronograma de estudos eficiente?",
        "Estou com dificuldade para gerenciar meu tempo entre trabalho e estudos."
    ]
    
    # Override test queries if a specific query is provided
    if args.query:
        test_queries = [args.query]
    
    # Test each query
    for query in test_queries:
        print("\n" + "=" * 80)
        print(f"Query: {query}")
        print("=" * 80)
        
        # Create initial state
        state = AcademicAgentState(
            user_query=query,
            user_id="test_user",
            user_context={}
        )
        
        # Run the planning agent
        try:
            updated_state = planning_agent(state)
            
            # Check if we have a response
            if "response" in updated_state:
                print("\nResponse:")
                print(updated_state["response"])
            else:
                print("\nNo response generated.")
                
        except Exception as e:
            print(f"Error testing planning agent: {str(e)}")
        
        print("\n" + "-" * 80)

if __name__ == "__main__":
    args = parse_args()
    test_planning()
