"""
Test script for the academic query agent.
"""
import os
import sys
import json
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.graph.academic_graph import academic_graph
from src.models.state import AcademicAgentState

# Load environment variables
load_dotenv()

def test_academic_query():
    """
    Test the academic query agent.
    """
    # Define test queries
    test_queries = [
        "Quantas faltas eu tenho em Banco de Dados?",
        "Qual é a minha nota em Banco de Dados?",
        "Quais são as minhas disciplinas?",
        "Qual é a minha situação em Banco de Dados?",
        "Quantas faltas eu tenho em todas as disciplinas?"
    ]
    
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
        
        # Run the academic graph
        try:
            result = academic_graph.invoke(state)
            
            # Print the result
            print("\nResult:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # Print the response
            if "response" in result:
                print("\nResponse:")
                print(result["response"])
            
        except Exception as e:
            print(f"Error: {str(e)}")
        
        print("\n" + "-" * 80)

if __name__ == "__main__":
    test_academic_query()
