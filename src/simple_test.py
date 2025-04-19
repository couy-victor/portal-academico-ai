"""
Simple test script for the Academic Agent system.
"""
import os
import sys
from dotenv import load_dotenv

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.emotional_support_agent import emotional_support_agent
from src.agents.tutor_agent import tutor_agent
from src.agents.planning_agent import planning_agent
from src.models.state import AcademicAgentState

# Load environment variables
load_dotenv()

def test_emotional_support():
    """
    Tests the emotional support agent.
    """
    print("\n=== Testing Emotional Support Agent ===")
    
    # Define a test query
    test_query = "Estou muito ansioso com a prova de amanhã e não consigo me concentrar para estudar."
    
    # Create initial state
    state = AcademicAgentState(
        user_query=test_query,
        user_id="test_user",
        user_context={}
    )
    
    print(f"Query: {test_query}")
    
    try:
        # Run the emotional support agent
        updated_state = emotional_support_agent(state)
        
        # Check if we have a response
        if "natural_response" in updated_state:
            print(f"\nResponse:")
            print(updated_state["natural_response"])
        else:
            print("No response generated")
        
    except Exception as e:
        print(f"Error testing emotional support agent: {str(e)}")

def test_tutor():
    """
    Tests the tutor agent.
    """
    print("\n=== Testing Tutor Agent ===")
    
    # Define a test query
    test_query = "Pode me explicar o que é uma máquina de Turing e como ela funciona?"
    
    # Create initial state
    state = AcademicAgentState(
        user_query=test_query,
        user_id="test_user",
        user_context={}
    )
    
    print(f"Query: {test_query}")
    
    try:
        # Run the tutor agent
        updated_state = tutor_agent(state)
        
        # Check if we have a response
        if "natural_response" in updated_state:
            print(f"\nResponse:")
            print(updated_state["natural_response"])
        else:
            print("No response generated")
        
    except Exception as e:
        print(f"Error testing tutor agent: {str(e)}")

def test_planning():
    """
    Tests the planning agent.
    """
    print("\n=== Testing Planning Agent ===")
    
    # Define a test query
    test_query = "Preciso organizar meus estudos para as provas finais que começam em duas semanas."
    
    # Create initial state
    state = AcademicAgentState(
        user_query=test_query,
        user_id="test_user",
        user_context={}
    )
    
    print(f"Query: {test_query}")
    
    try:
        # Run the planning agent
        updated_state = planning_agent(state)
        
        # Check if we have a response
        if "natural_response" in updated_state:
            print(f"\nResponse:")
            print(updated_state["natural_response"])
        else:
            print("No response generated")
        
    except Exception as e:
        print(f"Error testing planning agent: {str(e)}")

def main():
    """
    Main function.
    """
    # Check if required environment variables are set
    required_vars = ["OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in the .env file.")
        return
    
    # Run the tests
    test_emotional_support()
    test_tutor()
    test_planning()

if __name__ == "__main__":
    main()
