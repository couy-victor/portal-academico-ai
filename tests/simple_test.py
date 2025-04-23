"""
Simple test script for the Academic Agent system.
"""
import os
import sys
import argparse
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
    global test_query_emotional
    test_query_emotional = "Estou muito ansioso com a prova de amanhã e não consigo me concentrar para estudar."

    # Create initial state
    state = AcademicAgentState(
        user_query=test_query_emotional,
        user_id="test_user",
        user_context={}
    )

    print(f"Query: {test_query_emotional}")

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
    global test_query_tutor
    test_query_tutor = "Pode me explicar o que é uma máquina de Turing e como ela funciona?"

    # Create initial state
    state = AcademicAgentState(
        user_query=test_query_tutor,
        user_id="test_user",
        user_context={}
    )

    print(f"Query: {test_query_tutor}")

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
    global test_query_planning
    test_query_planning = "Preciso organizar meus estudos para as provas finais que começam em duas semanas."

    # Create initial state
    state = AcademicAgentState(
        user_query=test_query_planning,
        user_id="test_user",
        user_context={}
    )

    print(f"Query: {test_query_planning}")

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

def parse_args():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(description="Test specialized agents")
    parser.add_argument("--mode", type=str, choices=["emotional", "tutor", "planning"], help="Agent mode to test")
    parser.add_argument("--query", type=str, help="Query to test")
    return parser.parse_args()

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

    # Parse command line arguments
    args = parse_args()

    # If mode and query are provided, run only that specific test
    if args.mode and args.query:
        if args.mode == "emotional":
            # Override the test query
            global test_query_emotional
            test_query_emotional = args.query
            test_emotional_support()
        elif args.mode == "tutor":
            global test_query_tutor
            test_query_tutor = args.query
            test_tutor()
        elif args.mode == "planning":
            global test_query_planning
            test_query_planning = args.query
            test_planning()
    else:
        # Run all tests
        test_emotional_support()
        test_tutor()
        test_planning()

if __name__ == "__main__":
    main()
