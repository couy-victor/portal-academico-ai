"""
Script para testar o agente de tutoria com as novas melhorias.
"""
import json
import argparse
from typing import Dict, Any

from src.models.state import AcademicAgentState
from src.agents.tutor_agent import tutor_agent
from src.utils.logging import logger

def test_tutor_agent(query: str, knowledge_level: str = None, use_socratic: bool = False) -> Dict[str, Any]:
    """
    Testa o agente de tutoria com uma consulta específica.
    
    Args:
        query (str): Consulta do usuário
        knowledge_level (str, optional): Nível de conhecimento a ser simulado (iniciante, intermediário, avançado)
        use_socratic (bool, optional): Se deve forçar o uso da abordagem socrática
        
    Returns:
        Dict[str, Any]: Estado final após o processamento
    """
    # Modificar a consulta para forçar abordagem socrática se solicitado
    if use_socratic and "socratic" not in query.lower():
        query = f"[socratic] {query}"
    
    # Criar estado inicial
    state = AcademicAgentState(
        user_query=query,
        user_id="test_user",
        user_context={
            "RA": "123456",
            "curso": "Ciência da Computação",
            "semestre": "4"
        }
    )
    
    # Se um nível de conhecimento foi especificado, simular a avaliação prévia
    if knowledge_level:
        state["prior_knowledge"] = {
            "level": knowledge_level,
            "confidence": 0.9,
            "gaps": [],
            "strengths": [],
            "recommended_approach": f"Explicar no nível {knowledge_level}"
        }
    
    # Processar com o agente de tutoria
    print(f"\n🧠 Processando consulta: '{query}'")
    print(f"📚 Nível de conhecimento: {knowledge_level or 'Auto-detectado'}")
    print(f"🔄 Modo socrático: {'Ativado' if use_socratic else 'Auto-detectado'}\n")
    
    try:
        # Executar o agente de tutoria
        result_state = tutor_agent(state)
        
        # Verificar se temos uma resposta
        if "natural_response" in result_state:
            print("\n✅ Resposta gerada com sucesso!\n")
            
            # Mostrar informações sobre o processamento
            if "subject" in result_state and "topic" in result_state:
                print(f"📋 Assunto detectado: {result_state['subject']}")
                print(f"📋 Tópico detectado: {result_state['topic']}")
            
            if "prior_knowledge" in result_state:
                print(f"🧠 Nível de conhecimento avaliado: {result_state['prior_knowledge']['level']}")
                print(f"🧠 Confiança na avaliação: {result_state['prior_knowledge']['confidence']}")
            
            if "multi_level_explanation" in result_state:
                print(f"📚 Nível de explicação recomendado: {result_state['multi_level_explanation']['recommended_level']}")
            
            if "socratic_questions" in result_state:
                print(f"❓ Perguntas socráticas geradas: {len(result_state['socratic_questions'])}")
            
            if "socratic_dialogue" in result_state:
                print(f"💬 Diálogo socrático gerado: {len(result_state['socratic_dialogue'])} trocas")
            
            if "concept_map" in result_state:
                print(f"🔄 Mapa conceitual gerado: Sim")
            
            if "examples" in result_state:
                examples = [ex for ex in result_state["examples"] if ex.get("type") == "example"]
                exercises = [ex for ex in result_state["examples"] if ex.get("type") == "exercise"]
                print(f"📝 Exemplos gerados: {len(examples)}")
                print(f"✏️ Exercícios gerados: {len(exercises)}")
            
            # Mostrar a resposta
            print("\n" + "="*80)
            print("RESPOSTA FINAL:")
            print("="*80)
            print(result_state["natural_response"])
            print("="*80)
            
            # Perguntar se o usuário quer ver detalhes adicionais
            show_details = input("\nDeseja ver detalhes adicionais do processamento? (s/n): ").lower() == 's'
            
            if show_details:
                # Mostrar detalhes adicionais
                if "socratic_questions" in result_state:
                    print("\n" + "="*80)
                    print("PERGUNTAS SOCRÁTICAS:")
                    print("="*80)
                    for i, q in enumerate(result_state["socratic_questions"][:3]):
                        print(f"{i+1}. {q.get('question', '')}")
                        print(f"   Propósito: {q.get('purpose', '')}")
                        print()
                
                if "concept_map" in result_state and "text_representation" in result_state["concept_map"]:
                    print("\n" + "="*80)
                    print("MAPA CONCEITUAL:")
                    print("="*80)
                    print(result_state["concept_map"]["text_representation"])
                    print("="*80)
                
                if "multi_level_explanation" in result_state:
                    levels = ["basic", "intermediate", "advanced"]
                    selected_level = input("\nQual nível de explicação deseja ver? (1-Básico, 2-Intermediário, 3-Avançado): ")
                    
                    try:
                        level_idx = int(selected_level) - 1
                        if 0 <= level_idx < 3:
                            level = levels[level_idx]
                            print("\n" + "="*80)
                            print(f"EXPLICAÇÃO {level.upper()}:")
                            print("="*80)
                            explanation = result_state["multi_level_explanation"].get(level, {}).get("explanation", "")
                            print(explanation)
                            print("="*80)
                    except:
                        print("Seleção inválida.")
        else:
            print("\n❌ Falha ao gerar resposta.")
            if "error" in result_state:
                print(f"Erro: {result_state['error']}")
        
        return result_state
        
    except Exception as e:
        print(f"\n❌ Erro durante o processamento: {str(e)}")
        return {"error": str(e)}

def main():
    """
    Função principal para executar o teste via linha de comando.
    """
    parser = argparse.ArgumentParser(description="Testar o agente de tutoria")
    parser.add_argument("--query", type=str, help="Consulta para testar")
    parser.add_argument("--level", type=str, choices=["iniciante", "intermediário", "avançado"], 
                        help="Nível de conhecimento a simular")
    parser.add_argument("--socratic", action="store_true", help="Forçar abordagem socrática")
    
    args = parser.parse_args()
    
    # Se não houver consulta via argumento, solicitar interativamente
    if not args.query:
        print("\n🧪 TESTE DO AGENTE DE TUTORIA 🧪")
        print("\nExemplos de consultas para testar:")
        print("1. 'O que é programação orientada a objetos?'")
        print("2. 'Explique o teorema de Pitágoras'")
        print("3. 'Como funciona a fotossíntese?'")
        print("4. 'O que são estruturas de dados?'")
        print("5. 'Explique o que é inteligência artificial'")
        print("\nDica: Adicione '[socratic]' no início para forçar a abordagem socrática")
        
        query = input("\nDigite sua consulta: ")
        
        # Perguntar sobre o nível de conhecimento
        print("\nNível de conhecimento:")
        print("1. Iniciante")
        print("2. Intermediário")
        print("3. Avançado")
        print("4. Auto-detectar")
        
        level_choice = input("Escolha o nível (1-4): ")
        
        if level_choice == "1":
            level = "iniciante"
        elif level_choice == "2":
            level = "intermediário"
        elif level_choice == "3":
            level = "avançado"
        else:
            level = None
        
        # Verificar se deve usar abordagem socrática
        socratic = "[socratic]" in query.lower()
        if not socratic:
            socratic = input("\nForçar abordagem socrática? (s/n): ").lower() == 's'
    else:
        query = args.query
        level = args.level
        socratic = args.socratic
    
    # Executar o teste
    test_tutor_agent(query, level, socratic)

if __name__ == "__main__":
    main()
