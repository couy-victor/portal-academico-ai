"""
Test script for the academic query agent with a specific RA (student ID).
"""
import os
import sys
import json
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.graph.academic_graph import create_academic_graph
from src.models.state import AcademicAgentState
from src.utils.cache import clear_cache

# Load environment variables
load_dotenv()

def test_ra_specific():
    """
    Test the academic query agent with a specific RA (student ID).
    """
    # Clear cache to force a new query
    print("Limpando cache para forçar uma consulta nova...")
    clear_cache()

    # Define test queries
    test_queries = [
        "como é feito o calculo para a nota?"
    ]

    # Define the RA (student ID) to test with
    ra = "228773"

    # Test each query
    for query in test_queries:
        print("\n" + "=" * 80)
        print(f"Query: {query}")
        print(f"RA: {ra}")
        print("=" * 80)

        # Create initial state
        state = AcademicAgentState(
            user_query=query,
            user_id=ra,
            user_context={}
        )

        # Run the academic graph
        try:
            # Create the academic graph
            academic_graph = create_academic_graph()
            # Invoke the graph
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
    test_ra_specific()
