"""
Script para testar o agente de suporte emocional com as melhorias implementadas.
"""
import os
import sys
import json

# Adicionar o diretório raiz ao path para importar os módulos corretamente
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.emotional_support_agent import (
    emotional_state_detector,
    strategy_generator,
    resource_recommender,
    emotional_response_generator
)
from src.models.state import AcademicAgentState

def test_emotional_agent():
    """
    Testa o agente de suporte emocional com diferentes níveis de severidade.
    """
    # Casos de teste com diferentes níveis de severidade
    test_cases = [
        {
            "name": "Baixa severidade",
            "query": "Estou um pouco nervoso com a apresentação do trabalho amanhã.",
            "expected_severity": "baixa"
        },
        {
            "name": "Média severidade",
            "query": "Estou tendo dificuldade para me concentrar nos estudos e isso está me deixando ansioso.",
            "expected_severity": "média"
        },
        {
            "name": "Alta severidade",
            "query": "Estou em pânico, não consigo dormir há dias pensando nas provas, sinto que vou falhar em tudo e não sei o que fazer com minha vida.",
            "expected_severity": "alta"
        }
    ]

    # Executar os testes
    for test_case in test_cases:
        print(f"\n\n{'='*80}")
        print(f"Testando caso: {test_case['name']}")
        print(f"Query: {test_case['query']}")
        print(f"{'='*80}\n")

        # Inicializar o estado
        state = AcademicAgentState({"user_query": test_case["query"]})

        # Executar o pipeline do agente
        state = emotional_state_detector(state)
        state = strategy_generator(state)
        state = resource_recommender(state)
        state = emotional_response_generator(state)

        # Verificar os resultados
        print(f"Estado emocional detectado: {state.get('emotional_state', 'N/A')}")
        print(f"Problema específico: {state.get('emotional_issue', 'N/A')}")
        print(f"Severidade: {state.get('emotional_severity', 'N/A')}")
        
        # Verificar se a intervenção humana foi recomendada
        human_intervention = state.get("metadata", {}).get("human_intervention_recommended", False)
        print(f"Intervenção humana recomendada: {human_intervention}")
        
        # Imprimir a resposta natural
        print("\nResposta gerada:")
        print("-" * 80)
        print(state.get("natural_response", "N/A"))
        print("-" * 80)

        # Verificar se a intervenção humana foi recomendada quando a severidade é alta
        if state.get("emotional_severity", "").lower() == "alta":
            assert human_intervention, "Intervenção humana deveria ser recomendada para severidade alta"
            print("\n✅ Teste passou: Intervenção humana recomendada para severidade alta")
        else:
            assert not human_intervention, "Intervenção humana não deveria ser recomendada para severidade não-alta"
            print(f"\n✅ Teste passou: Intervenção humana não recomendada para severidade {state.get('emotional_severity', 'N/A')}")

if __name__ == "__main__":
    test_emotional_agent()
