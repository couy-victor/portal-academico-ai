"""
Demonstração das novas funcionalidades do Academic Agent system.
Mostra como usar MCP, métricas, validação e tratamento de erros.
"""
import sys
import os
import time
import json

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.main import process_query, initialize_system, shutdown_system
from src.utils.metrics import metrics_collector
from src.mcp.integration import mcp_integration
from src.mcp.context_manager import ContextType, ContextScope
from src.utils.logging import logger
from src.config.settings import MCP_ENABLED, METRICS_ENABLED


def demo_basic_query():
    """Demonstra uma consulta básica."""
    print("\n" + "="*60)
    print("DEMO 1: Consulta Básica")
    print("="*60)
    
    user_query = "Quantas faltas tenho em Anatomia?"
    user_id = "12345"
    user_context = {
        "RA": "2023001234",
        "curso": "Medicina",
        "periodo": "2023.2"
    }
    
    print(f"Consulta: {user_query}")
    print(f"Usuário: {user_id}")
    print(f"Contexto: {json.dumps(user_context, indent=2)}")
    
    result = process_query(user_query, user_id, user_context)
    
    print(f"\nResposta:")
    print(json.dumps(result, indent=2, ensure_ascii=False))


def demo_emotional_support():
    """Demonstra suporte emocional."""
    print("\n" + "="*60)
    print("DEMO 2: Suporte Emocional")
    print("="*60)
    
    user_query = "Estou muito ansioso com as provas finais, não consigo dormir direito"
    user_id = "12346"
    user_context = {
        "RA": "2023001235",
        "curso": "Psicologia",
        "periodo": "2023.2"
    }
    
    print(f"Consulta: {user_query}")
    print(f"Usuário: {user_id}")
    
    result = process_query(user_query, user_id, user_context)
    
    print(f"\nResposta:")
    print(json.dumps(result, indent=2, ensure_ascii=False))


def demo_mcp_context():
    """Demonstra o uso do MCP para contexto."""
    print("\n" + "="*60)
    print("DEMO 3: MCP Context Management")
    print("="*60)
    
    if not MCP_ENABLED:
        print("MCP está desabilitado. Habilite MCP_ENABLED=True no .env")
        return
    
    # Definir contexto personalizado
    user_id = "12347"
    
    # Adicionar contexto do usuário
    mcp_integration.context_manager.set_context(
        key=f"user_profile:{user_id}",
        data={
            "name": "João Silva",
            "course": "Engenharia",
            "semester": "5º",
            "preferences": {
                "study_method": "visual",
                "notification_time": "morning"
            }
        },
        context_type=ContextType.USER_PROFILE,
        scope=ContextScope.SESSION,
        ttl_seconds=3600
    )
    
    # Fazer consulta que usará o contexto
    user_query = "Como posso melhorar meu desempenho em Cálculo?"
    result = process_query(user_query, user_id)
    
    print(f"Consulta: {user_query}")
    print(f"Usuário: {user_id}")
    print(f"\nResposta:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Mostrar contexto armazenado
    context_info = mcp_integration.context_manager.get_context_info(f"user_profile:{user_id}")
    if context_info:
        print(f"\nInformações do contexto:")
        print(json.dumps(context_info, indent=2, ensure_ascii=False))


def demo_metrics():
    """Demonstra as métricas do sistema."""
    print("\n" + "="*60)
    print("DEMO 4: Sistema de Métricas")
    print("="*60)
    
    if not METRICS_ENABLED:
        print("Métricas estão desabilitadas. Habilite METRICS_ENABLED=True no .env")
        return
    
    # Fazer algumas consultas para gerar métricas
    queries = [
        ("Qual minha nota em Física?", "12348"),
        ("Quantas faltas tenho?", "12349"),
        ("Estou com dificuldades em Matemática", "12350")
    ]
    
    print("Executando consultas para gerar métricas...")
    
    for query, user_id in queries:
        print(f"  - {query}")
        result = process_query(query, user_id)
        time.sleep(0.5)  # Pequena pausa entre consultas
    
    # Obter resumo de performance
    performance_summary = metrics_collector.get_performance_summary()
    print(f"\nResumo de Performance:")
    print(json.dumps(performance_summary, indent=2, ensure_ascii=False))
    
    # Obter status de saúde do sistema
    health_status = metrics_collector.get_health_status()
    print(f"\nStatus de Saúde do Sistema:")
    print(json.dumps(health_status, indent=2, ensure_ascii=False))


def demo_error_handling():
    """Demonstra o tratamento de erros."""
    print("\n" + "="*60)
    print("DEMO 5: Tratamento de Erros")
    print("="*60)
    
    # Consulta com entrada inválida
    print("Testando consulta vazia...")
    result = process_query("", "12351")
    print(f"Resultado: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # Consulta com user_id inválido
    print("\nTestando user_id vazio...")
    result = process_query("Teste", "")
    print(f"Resultado: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # Consulta que pode gerar erro interno
    print("\nTestando consulta complexa...")
    result = process_query("Query muito complexa que pode gerar erro interno", "12352")
    print(f"Resultado: {json.dumps(result, indent=2, ensure_ascii=False)}")


def demo_conversation_context():
    """Demonstra contexto de conversação."""
    print("\n" + "="*60)
    print("DEMO 6: Contexto de Conversação")
    print("="*60)
    
    if not MCP_ENABLED:
        print("MCP está desabilitado. Habilite MCP_ENABLED=True no .env")
        return
    
    user_id = "12353"
    
    # Primeira consulta
    print("Primeira consulta:")
    query1 = "Qual minha nota em Química?"
    result1 = process_query(query1, user_id)
    print(f"Q: {query1}")
    print(f"R: {result1.get('response', 'Sem resposta')}")
    
    time.sleep(1)
    
    # Segunda consulta relacionada
    print("\nSegunda consulta (relacionada):")
    query2 = "E quantas faltas tenho nessa matéria?"
    result2 = process_query(query2, user_id)
    print(f"Q: {query2}")
    print(f"R: {result2.get('response', 'Sem resposta')}")
    
    # Mostrar histórico de conversação
    session_id = f"session_{user_id}"
    conversation_data = mcp_integration.context_manager.get_context(f"conversation:{session_id}")
    
    if conversation_data:
        print(f"\nHistórico de conversação:")
        print(json.dumps(conversation_data, indent=2, ensure_ascii=False))


def main():
    """Função principal da demonstração."""
    print("🤖 DEMONSTRAÇÃO DO ACADEMIC AGENT SYSTEM")
    print("Novas funcionalidades: MCP, Métricas, Validação e Tratamento de Erros")
    
    # Inicializar sistema
    initialize_system()
    
    try:
        # Executar demonstrações
        demo_basic_query()
        demo_emotional_support()
        demo_mcp_context()
        demo_metrics()
        demo_error_handling()
        demo_conversation_context()
        
        print("\n" + "="*60)
        print("DEMONSTRAÇÃO CONCLUÍDA")
        print("="*60)
        print("\nRecursos demonstrados:")
        print("✅ Consultas básicas com validação")
        print("✅ Suporte emocional avançado")
        print("✅ Gerenciamento de contexto com MCP")
        print("✅ Sistema de métricas e monitoramento")
        print("✅ Tratamento robusto de erros")
        print("✅ Contexto de conversação persistente")
        
        if MCP_ENABLED:
            print("\n📊 MCP Status: ATIVO")
        else:
            print("\n📊 MCP Status: INATIVO (configure MCP_ENABLED=True)")
            
        if METRICS_ENABLED:
            print("📈 Métricas: ATIVAS")
        else:
            print("📈 Métricas: INATIVAS (configure METRICS_ENABLED=True)")
    
    except KeyboardInterrupt:
        print("\n\nDemonstração interrompida pelo usuário.")
    
    except Exception as e:
        print(f"\n\nErro durante demonstração: {str(e)}")
        logger.error(f"Erro na demonstração: {str(e)}")
    
    finally:
        # Shutdown sistema
        shutdown_system()


if __name__ == "__main__":
    main()
