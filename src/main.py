"""
Main entry point for the Academic Agent system.
"""
import os
import json
import argparse
from typing import Dict, Any

from src.config.settings import OPENAI_API_KEY
from src.graph.academic_graph import create_academic_graph
from src.utils.logging import logger

def process_query(user_query: str, user_id: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Processes a user query through the academic agent workflow.

    Args:
        user_query (str): The user's query
        user_id (str): The user's ID
        user_context (Dict[str, Any], optional): Additional user context

    Returns:
        Dict[str, Any]: The final state after processing
    """
    # Validate inputs
    if not user_query:
        return {"error": "Query cannot be empty"}

    if not user_id:
        return {"error": "User ID cannot be empty"}

    # Initialize user context if not provided
    if user_context is None:
        user_context = {}

    # Add user_id to context
    user_context["user_id"] = user_id

    # Initialize state
    initial_state = {
        "user_query": user_query,
        "user_id": user_id,
        "user_context": user_context,
        "metadata": {}
    }

    # Log the incoming query
    logger.info(f"Processing query for user {user_id}: {user_query}")

    try:
        # Create and run the workflow
        academic_workflow = create_academic_graph()
        final_state = academic_workflow.invoke(initial_state)

        # Extract the response
        response = {
            "response": final_state.get("natural_response", ""),
            "from_cache": final_state.get("from_cache", False),
            "intent": final_state.get("intent", "unknown"),
            "confidence": final_state.get("confidence", 0.0),
            "main_category": final_state.get("main_category", "academic"),
            "main_confidence": final_state.get("main_confidence", 0.0),
            "error": final_state.get("error"),
            "metadata": final_state.get("metadata", {})
        }

        return response

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return {
            "error": f"Error processing query: {str(e)}",
            "response": "Desculpe, ocorreu um erro ao processar sua solicitação."
        }

def main():
    """
    Main function for command-line usage.
    """
    parser = argparse.ArgumentParser(description="Academic Agent CLI")
    parser.add_argument("--query", type=str, required=True, help="User query")
    parser.add_argument("--user_id", type=str, required=True, help="User ID")
    parser.add_argument("--context", type=str, help="User context as JSON string")

    args = parser.parse_args()

    # Parse user context if provided
    user_context = {}
    if args.context:
        try:
            user_context = json.loads(args.context)
        except json.JSONDecodeError:
            print("Error: Invalid JSON in context argument")
            return

    # Process the query
    result = process_query(args.query, args.user_id, user_context)

    # Print the result
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    # Check if OpenAI API key is set
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY environment variable is not set")
        exit(1)

    main()
