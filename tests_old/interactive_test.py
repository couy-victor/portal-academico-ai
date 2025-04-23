"""
Interactive test script for the academic query agent.
"""
import os
import sys
import json
import argparse
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.graph.academic_graph import academic_graph
from src.models.state import AcademicAgentState
from src.agents.emotional_support_agent import emotional_support_agent
from src.agents.tutor_agent import tutor_agent
from src.agents.planning_agent import planning_agent

# Load environment variables
load_dotenv()

# Global variables
session_context = {
    "user_id": "interactive_user",
    "history": []
}

# ANSI color codes
COLORS = {
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "white": "\033[97m",
    "reset": "\033[0m",
    "bold": "\033[1m",
    "underline": "\033[4m"
}

def print_colored(text: str, color: str = "white", bold: bool = False) -> None:
    """
    Print colored text.
    """
    color_code = COLORS.get(color, COLORS["white"])
    bold_code = COLORS["bold"] if bold else ""
    print(f"{color_code}{bold_code}{text}{COLORS['reset']}")

def print_section(title: str) -> None:
    """
    Print a section title.
    """
    print("\n" + "=" * 80)
    print_colored(f" {title} ", "blue", bold=True)
    print("=" * 80)

def process_academic_query(query: str) -> Dict[str, Any]:
    """
    Process an academic query.
    """
    # Create initial state
    state = AcademicAgentState(
        user_query=query,
        user_id=session_context["user_id"],
        user_context={}
    )
    
    # Add history to context if available
    if session_context["history"]:
        state["conversation_history"] = session_context["history"]
    
    # Run the academic graph
    try:
        result = academic_graph.invoke(state)
        
        # Add to history
        if "response" in result:
            session_context["history"].append({
                "role": "user",
                "content": query
            })
            session_context["history"].append({
                "role": "assistant",
                "content": result["response"]
            })
        
        return result
    except Exception as e:
        print_colored(f"Erro: {str(e)}", "red")
        return {"error": str(e)}

def process_emotional_support_query(query: str) -> Dict[str, Any]:
    """
    Process an emotional support query.
    """
    # Create initial state
    state = AcademicAgentState(
        user_query=query,
        user_id=session_context["user_id"],
        user_context={}
    )
    
    # Run the emotional support agent
    try:
        updated_state = emotional_support_agent(state)
        
        # Add to history
        if "response" in updated_state:
            session_context["history"].append({
                "role": "user",
                "content": query
            })
            session_context["history"].append({
                "role": "assistant",
                "content": updated_state["response"]
            })
        
        return updated_state
    except Exception as e:
        print_colored(f"Erro: {str(e)}", "red")
        return {"error": str(e)}

def process_tutor_query(query: str) -> Dict[str, Any]:
    """
    Process a tutor query.
    """
    # Create initial state
    state = AcademicAgentState(
        user_query=query,
        user_id=session_context["user_id"],
        user_context={}
    )
    
    # Run the tutor agent
    try:
        updated_state = tutor_agent(state)
        
        # Add to history
        if "response" in updated_state:
            session_context["history"].append({
                "role": "user",
                "content": query
            })
            session_context["history"].append({
                "role": "assistant",
                "content": updated_state["response"]
            })
        
        return updated_state
    except Exception as e:
        print_colored(f"Erro: {str(e)}", "red")
        return {"error": str(e)}

def process_planning_query(query: str) -> Dict[str, Any]:
    """
    Process a planning query.
    """
    # Create initial state
    state = AcademicAgentState(
        user_query=query,
        user_id=session_context["user_id"],
        user_context={}
    )
    
    # Run the planning agent
    try:
        updated_state = planning_agent(state)
        
        # Add to history
        if "response" in updated_state:
            session_context["history"].append({
                "role": "user",
                "content": query
            })
            session_context["history"].append({
                "role": "assistant",
                "content": updated_state["response"]
            })
        
        return updated_state
    except Exception as e:
        print_colored(f"Erro: {str(e)}", "red")
        return {"error": str(e)}

def set_context() -> None:
    """
    Set the context for the session.
    """
    print_section("Configuração de Contexto")
    
    # Get user ID
    user_id = input("Digite o RA do aluno (ou deixe em branco para usar o padrão): ")
    if user_id:
        session_context["user_id"] = user_id
        print_colored(f"RA configurado: {user_id}", "green")
    else:
        print_colored(f"Usando RA padrão: {session_context['user_id']}", "yellow")
    
    # Clear history
    clear_history = input("Limpar histórico de conversa? (s/n): ").lower()
    if clear_history == "s":
        session_context["history"] = []
        print_colored("Histórico de conversa limpo.", "green")

def show_history() -> None:
    """
    Show the conversation history.
    """
    print_section("Histórico de Conversa")
    
    if not session_context["history"]:
        print_colored("Nenhuma conversa registrada.", "yellow")
        return
    
    for i, message in enumerate(session_context["history"]):
        role = message["role"]
        content = message["content"]
        
        if role == "user":
            print_colored(f"Usuário: {content}", "cyan")
        else:
            print_colored(f"Assistente: {content}", "green")
        
        if i < len(session_context["history"]) - 1:
            print("-" * 40)

def upload_pdf_interactive() -> None:
    """
    Uploads a PDF file interactively.
    """
    print_section("Upload de PDF")
    print_colored("Funcionalidade de upload de PDF não disponível nesta versão.", "yellow")

def interactive_loop() -> None:
    """
    Run the interactive loop.
    """
    print_section("Portal Acadêmico AI - Modo Interativo")
    print_colored("Bem-vindo ao Portal Acadêmico AI!", "green", bold=True)
    print("Este é um modo interativo para testar o assistente acadêmico.")
    print(f"RA atual: {session_context['user_id']}")
    print("\nDigite suas perguntas ou comandos abaixo.")
    
    while True:
        print("\n" + "-" * 80)
        query = input("\nPergunta: ").strip()
        
        if not query:
            continue
        
        if query.lower() in ["sair", "exit", "quit", "q"]:
            print_colored("Encerrando sessão. Até logo!", "green", bold=True)
            break
        
        if query.lower() in ["contexto", "context"]:
            set_context()
            continue
        
        if query.lower() in ["pdf", "upload"]:
            upload_pdf_interactive()
            continue
        
        if query.lower() in ["histórico", "history"]:
            show_history()
            continue
        
        if query.lower() in ["ajuda", "help", "?"]:
            print_colored("Comandos disponíveis:", "cyan")
            print("- Para sair: 'sair' ou 'exit'")
            print("- Para configurar contexto: 'contexto'")
            print("- Para ver o histórico: 'histórico'")
            continue
        
        # Process the query
        print_colored("\nProcessando consulta...", "blue")
        
        # Determine the type of query
        if any(keyword in query.lower() for keyword in ["ansioso", "ansiedade", "nervoso", "estresse", "preocupado"]):
            print_colored("Detectado: Consulta de suporte emocional", "magenta")
            result = process_emotional_support_query(query)
        elif any(keyword in query.lower() for keyword in ["explique", "explica", "o que é", "como funciona", "defina"]):
            print_colored("Detectado: Consulta de tutoria", "magenta")
            result = process_tutor_query(query)
        elif any(keyword in query.lower() for keyword in ["planejar", "organizar", "cronograma", "estudos", "planejamento"]):
            print_colored("Detectado: Consulta de planejamento", "magenta")
            result = process_planning_query(query)
        else:
            print_colored("Detectado: Consulta acadêmica", "magenta")
            result = process_academic_query(query)
        
        # Print the result
        if "error" in result:
            print_colored(f"\nErro: {result['error']}", "red")
        elif "response" in result:
            print_colored("\nResposta:", "green")
            print(result["response"])
        else:
            print_colored("\nNenhuma resposta gerada.", "yellow")

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

    # Run the interactive loop
    interactive_loop()

if __name__ == "__main__":
    main()
