"""
Test script for the Tavily web search functionality.
"""
import os
import sys
from dotenv import load_dotenv

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.tavily_agent import tavily_search_agent, extract_search_query, perform_web_search
from src.models.state import AcademicAgentState
from src.config.settings import TAVILY_API_KEY

# Load environment variables
load_dotenv()

def test_tavily():
    """
    Tests the Tavily web search functionality.
    """
    print("\n=== Testing Tavily Web Search ===\n")
    
    # Check if Tavily API key is set
    if not TAVILY_API_KEY:
        print("Error: TAVILY_API_KEY is not set in the environment variables.")
        print("Please set this variable in the .env file.")
        return
    
    # Define test queries
    test_queries = [
        "Quais cursos o unisal oferece?",
        "Quantos campus o unisal possui?"
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
        
        # Test search query extraction
        try:
            search_query = extract_search_query(state)
            print(f"\nExtracted Search Query: {search_query}")
            
            # Perform web search
            search_results = perform_web_search(search_query)
            
            print(f"\nFound {len(search_results)} search results:")
            
            for i, result in enumerate(search_results[:3]):  # Show top 3 for brevity
                print(f"\n[{i+1}] {result['title']}")
                print(f"URL: {result['url']}")
                print(f"Content: {result['content'][:200]}...")
            
            # Run the full Tavily agent
            updated_state = tavily_search_agent(state)
            
            if "web_search_context" in updated_state and updated_state["web_search_context"]:
                print("\nExtracted Context:")
                print(updated_state["web_search_context"][:500] + "..." if len(updated_state["web_search_context"]) > 500 else updated_state["web_search_context"])
            else:
                print("\nNo context extracted from search results.")
                
        except Exception as e:
            print(f"Error testing Tavily search: {str(e)}")
        
        print("\n" + "-" * 80)

if __name__ == "__main__":
    test_tavily()
