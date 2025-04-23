"""
Interactive test script for the Academic Agent system.
This script allows testing all agents interactively via command line.
"""
import os
import sys
import json
import argparse
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.main import process_query
from src.models.state import AcademicAgentState
from src.utils.cache import clear_cache

# Load environment variables
load_dotenv()

# Global context for the session
session_context = {
    "user_id": "interactive_user",
    "user_context": {},
    "history": []
}

def print_colored(text: str, color: str = "white") -> None:
    """
    Prints colored text to the console.

    Args:
        text (str): Text to print
        color (str): Color to use
    """
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m"
    }

    print(f"{colors.get(color, colors['white'])}{text}{colors['reset']}")

def print_header(title: str) -> None:
    """
    Prints a header to the console.

    Args:
        title (str): Header title
    """
    print("\n" + "=" * 80)
    print_colored(f" {title} ".center(80), "cyan")
    print("=" * 80)

def print_section(title: str) -> None:
    """
    Prints a section header to the console.

    Args:
        title (str): Section title
    """
    print("\n" + "-" * 80)
    print_colored(f" {title} ".center(80), "yellow")
    print("-" * 80)

def process_academic_query(query: str) -> Dict[str, Any]:
    """
    Processes an academic query.

    Args:
        query (str): User query

    Returns:
        Dict[str, Any]: Query result
    """
    print_section("Processando consulta acadêmica")

    try:
        # Clear cache to force a fresh query
        print("Limpando cache para forçar uma consulta nova...")
        clear_cache()

        # Process the query
        result = process_query(
            user_query=query,
            user_id=session_context["user_id"],
            user_context=session_context["user_context"]
        )

        # Add to history
        session_context["history"].append({
            "query": query,
            "response": result.get("response", ""),
            "type": "academic"
        })

        return result
    except Exception as e:
        error_msg = f"Erro ao processar consulta acadêmica: {str(e)}"
        print_colored(error_msg, "red")

        # Create a fallback response
        fallback_response = {
            "response": "Desculpe, não foi possível processar sua consulta acadêmica. Pode haver um problema com a conexão ao banco de dados ou com as configurações do sistema.",
            "error": error_msg,
            "intent": "unknown",
            "confidence": 0.0
        }

        # Add to history
        session_context["history"].append({
            "query": query,
            "response": fallback_response.get("response", ""),
            "type": "academic"
        })

        return fallback_response

def process_emotional_support_query(query: str) -> Dict[str, Any]:
    """
    Processes an emotional support query.

    Args:
        query (str): User query

    Returns:
        Dict[str, Any]: Query result
    """
    print_section("Processando consulta de apoio emocional")

    # TODO: Implement emotional support agent
    # For now, use a placeholder response
    result = {
        "response": "Esta funcionalidade de apoio emocional ainda está em desenvolvimento. " +
                   "Em breve você poderá receber suporte para ansiedade, estresse e outros desafios emocionais.",
        "intent": "emotional_support",
        "confidence": 0.9
    }

    # Add to history
    session_context["history"].append({
        "query": query,
        "response": result.get("response", ""),
        "type": "emotional_support"
    })

    return result

def process_tutor_query(query: str) -> Dict[str, Any]:
    """
    Processes a tutor query.

    Args:
        query (str): User query

    Returns:
        Dict[str, Any]: Query result
    """
    print_section("Processando consulta de tutoria")

    # TODO: Implement tutor agent
    # For now, use a placeholder response
    result = {
        "response": "Esta funcionalidade de tutoria ainda está em desenvolvimento. " +
                   "Em breve você poderá receber explicações detalhadas sobre matérias específicas.",
        "intent": "tutor",
        "confidence": 0.9
    }

    # Add to history
    session_context["history"].append({
        "query": query,
        "response": result.get("response", ""),
        "type": "tutor"
    })

    return result

def process_planning_query(query: str) -> Dict[str, Any]:
    """
    Processes a planning query.

    Args:
        query (str): User query

    Returns:
        Dict[str, Any]: Query result
    """
    print_section("Processando consulta de planejamento acadêmico")

    # TODO: Implement planning agent
    # For now, use a placeholder response
    result = {
        "response": "Esta funcionalidade de planejamento acadêmico ainda está em desenvolvimento. " +
                   "Em breve você poderá receber ajuda para organizar seus estudos e definir metas.",
        "intent": "planning",
        "confidence": 0.9
    }

    # Add to history
    session_context["history"].append({
        "query": query,
        "response": result.get("response", ""),
        "type": "planning"
    })

    return result

def detect_intent(query: str) -> str:
    """
    Detects the intent of a query.

    Args:
        query (str): User query

    Returns:
        str: Detected intent
    """
    # Keywords for each intent
    academic_keywords = ["nota", "falta", "disciplina", "professor", "horário", "calendário", "matrícula", "histórico"]
    emotional_keywords = ["ansiedade", "ansioso", "estresse", "estressado", "nervoso", "medo", "preocupado", "triste", "depressão", "burnout"]
    tutor_keywords = ["explicar", "entender", "dúvida", "conceito", "exemplo", "exercício", "matéria", "conteúdo", "aula"]
    planning_keywords = ["planejar", "organizar", "cronograma", "meta", "objetivo", "prazo", "tempo", "estudo", "preparar"]

    # Count keyword matches
    academic_count = sum(1 for keyword in academic_keywords if keyword in query.lower())
    emotional_count = sum(1 for keyword in emotional_keywords if keyword in query.lower())
    tutor_count = sum(1 for keyword in tutor_keywords if keyword in query.lower())
    planning_count = sum(1 for keyword in planning_keywords if keyword in query.lower())

    # Determine intent based on keyword count
    counts = {
        "academic": academic_count,
        "emotional_support": emotional_count,
        "tutor": tutor_count,
        "planning": planning_count
    }

    # Return the intent with the highest count, or academic if all are equal
    max_count = max(counts.values())
    if max_count == 0:
        return "academic"  # Default to academic if no keywords match

    for intent, count in counts.items():
        if count == max_count:
            return intent

    return "academic"  # Default to academic

def process_query_with_intent_detection(query: str) -> Dict[str, Any]:
    """
    Processes a query with intent detection.

    Args:
        query (str): User query

    Returns:
        Dict[str, Any]: Query result
    """
    # Detect intent
    intent = detect_intent(query)

    # Process query based on intent
    if intent == "emotional_support":
        return process_emotional_support_query(query)
    elif intent == "tutor":
        return process_tutor_query(query)
    elif intent == "planning":
        return process_planning_query(query)
    else:
        return process_academic_query(query)

def upload_pdf_interactive() -> None:
    """
    Uploads a PDF file interactively.
    """
    print_section("Upload de PDF")
    print_colored("Funcionalidade de upload de PDF não disponível nesta versão.", "yellow")

def set_user_context_interactive() -> None:
    """
    Sets user context interactively.
    """
    print_section("Configuração de Contexto do Usuário")

    # Ask for user ID
    user_id = input("Digite o ID do usuário (RA): ")
    if user_id:
        session_context["user_id"] = user_id

    # Ask for additional context
    print("\nDigite informações adicionais de contexto (deixe em branco para pular):")

    # Common context fields
    context_fields = [
        ("nome", "Nome completo"),
        ("curso_id", "ID do curso"),
        ("curso_nome", "Nome do curso"),
        ("periodo_atual", "Período atual (ex: 2023.2)"),
        ("disciplina_id", "ID da disciplina (opcional)"),
        ("disciplina_nome", "Nome da disciplina (opcional)")
    ]

    for field_key, field_desc in context_fields:
        value = input(f"{field_desc}: ")
        if value:
            session_context["user_context"][field_key] = value

    print_colored("\nContexto do usuário configurado:", "green")
    print(json.dumps(session_context["user_context"], indent=2, ensure_ascii=False))

def show_history() -> None:
    """
    Shows the conversation history.
    """
    print_section("Histórico de Conversas")

    if not session_context["history"]:
        print("Nenhuma conversa registrada.")
        return

    for i, entry in enumerate(session_context["history"]):
        print(f"\n[{i+1}] Tipo: {entry['type']}")
        print_colored(f"P: {entry['query']}", "yellow")
        print_colored(f"R: {entry['response']}", "green")

def interactive_loop() -> None:
    """
    Runs the interactive test loop.
    """
    print_header("Sistema Multi-Agentes Acadêmico - Teste Interativo")

    # Set initial user context
    set_user_context_interactive()

    while True:
        print("\n" + "=" * 80)
        print_colored("Digite uma pergunta ou comando:", "cyan")
        print("- Para sair: 'sair' ou 'exit'")
        print("- Para configurar contexto: 'contexto'")
        print("- Para ver o histórico: 'histórico'")
        print("=" * 80 + "\n")

        # Get user input
        user_input = input("> ")

        # Process commands
        if user_input.lower() in ["sair", "exit", "quit", "q"]:
            print_colored("\nEncerrando o teste interativo. Até logo!", "cyan")
            break
        elif user_input.lower() in ["contexto", "context"]:
            set_user_context_interactive()
            continue
        elif user_input.lower() in ["pdf", "upload"]:
            upload_pdf_interactive()
            continue
        elif user_input.lower() in ["histórico", "historico", "history"]:
            show_history()
            continue

        # Process query
        try:
            result = process_query_with_intent_detection(user_input)

            # Print response
            print_colored("\nResposta:", "green")
            print(result.get("response", "Sem resposta"))

            # Print additional information
            print("\nInformações adicionais:")
            print(f"- Intenção detectada: {result.get('intent', 'desconhecida')}")
            print(f"- Confiança: {result.get('confidence', 0.0)}")
            print(f"- Origem: {'cache' if result.get('from_cache', False) else 'geração em tempo real'}")

            # Print any errors
            if "error" in result and result["error"]:
                print_colored(f"\nErro: {result['error']}", "red")

        except Exception as e:
            print_colored(f"\nErro ao processar a consulta: {str(e)}", "red")

def parse_args():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(description="Interactive test for Academic Agent system")
    parser.add_argument("--query", type=str, help="Query to test")
    parser.add_argument("--user_id", type=str, default="interactive_user", help="User ID for the query")
    parser.add_argument("--mode", type=str, choices=["academic", "emotional", "tutor", "planning"],
                      default="academic", help="Mode to test")
    return parser.parse_args()

def main():
    """
    Main function.
    """
    # Check if required environment variables are set
    required_vars = ["OPENAI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print_colored(f"Erro: Variáveis de ambiente necessárias não configuradas: {', '.join(missing_vars)}", "red")
        print("Configure essas variáveis no arquivo .env.")
        return

    # Check if Supabase variables are set (optional for testing)
    supabase_vars = ["SUPABASE_URL", "SUPABASE_KEY"]
    missing_supabase_vars = [var for var in supabase_vars if not os.getenv(var)]

    if missing_supabase_vars:
        print_colored(f"Aviso: Variáveis do Supabase não configuradas: {', '.join(missing_supabase_vars)}", "yellow")
        print("Algumas funcionalidades relacionadas ao banco de dados não estarão disponíveis.")

    # Parse command line arguments
    args = parse_args()

    # If query is provided, process it directly
    if args.query:
        # Set user ID in session context
        session_context["user_id"] = args.user_id

        # Process query based on mode
        if args.mode == "academic":
            result = process_academic_query(args.query)
        elif args.mode == "emotional":
            result = process_emotional_support_query(args.query)
        elif args.mode == "tutor":
            result = process_tutor_query(args.query)
        elif args.mode == "planning":
            result = process_planning_query(args.query)
        else:
            result = process_academic_query(args.query)

        # Print the response
        print_colored("\nResposta:", "green")
        print(result.get("response", ""))
    else:
        # Run the interactive loop
        interactive_loop()

if __name__ == "__main__":
    main()
