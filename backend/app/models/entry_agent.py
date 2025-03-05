from langgraph.graph import StateGraph, END
from app.models.processing_agent import agente_processamento
from app.models.response_agent import agente_resposta
from typing import TypedDict, Dict, Any, List, Optional
import re

# ✅ Definição do estado do fluxo
class EstadoFluxo(TypedDict):
    """
    Define o estado do fluxo de processamento da solicitação.
    """
    pergunta: str  # Pergunta original do usuário
    ra: Optional[str]  # Registro acadêmico do aluno (se disponível)
    tipo: str  # Tipo de solicitação (processamento ou resposta)
    contexto: Dict  # Contexto adicional para processamento
    resposta_intermediaria: Optional[Dict]  # Resposta do processamento
    resposta_final: Optional[str]  # Resposta formatada final

def classificar_solicitacao(pergunta: str) -> str:
    """
    Classifica a solicitação do aluno e decide qual tipo de processamento aplicar.
    Retorna o tipo de solicitação identificado.
    """
    # Mapeamento de palavras-chave para tipos de solicitação
    tipos = {
        "boleto": "consultar_boletos",
        "pagamento": "consultar_boletos",
        "financeiro": "consultar_boletos",
        "nota": "consultar_notas",
        "aprovado": "consultar_notas",
        "reprova": "consultar_notas",
        "disci": "consultar_disciplinas",
        "matéria": "consultar_disciplinas",
        "materia": "consultar_disciplinas",
        "aula": "consultar_disciplinas",
        "coord": "consultar_coordenador",
        "falta": "consultar_faltas",
        "ausência": "consultar_faltas",
        "ausencia": "consultar_faltas",
        "presença": "consultar_faltas",
        "presenca": "consultar_faltas",
        "optativa": "consultar_optativas",
        "eletiva": "consultar_optativas",
        "unisal": "consultar_unisal",
        "faculdade": "consultar_unisal",
        "instituição": "consultar_unisal",
        "instituicao": "consultar_unisal"
    }
    
    # Procura palavras-chave na pergunta
    pergunta_lower = pergunta.lower()
    for chave, tipo in tipos.items():
        if chave in pergunta_lower:
            print(f"🔍 Palavra-chave '{chave}' encontrada -> {tipo}")
            return tipo
    
    print("📌 Nenhuma palavra-chave específica encontrada -> consulta_geral")
    return "consulta_geral"

def extrair_ra(pergunta: str) -> Optional[str]:
    """
    Tenta extrair um RA (Registro Acadêmico) da pergunta.
    Retorna o RA encontrado ou None.
    """
    # Padrões comuns de RAs (ajustar conforme o formato usado pela instituição)
    padrao_ra = r'\b\d{8}\b'  # Exemplo: 8 dígitos consecutivos
    
    match = re.search(padrao_ra, pergunta)
    if match:
        ra_encontrado = match.group(0)
        print(f"📌 RA encontrado na pergunta: {ra_encontrado}")
        return ra_encontrado
    
    return None

def iniciar_fluxo(state):
    """
    Inicializa o estado do fluxo com a pergunta e RA.
    """
    # Extrair pergunta e RA do estado
    pergunta = state.get("pergunta", "")
    ra = state.get("ra")
    
    print(f"📥 Entrada: {pergunta}")
    
    # Tenta extrair RA da pergunta se não foi fornecido
    ra_extraido = extrair_ra(pergunta) if ra is None else ra
    
    # Classificar a solicitação
    tipo_solicitacao = classificar_solicitacao(pergunta)
    print(f"🔀 Direcionando para: {tipo_solicitacao}")
    
    # Inicializar o estado
    return {
        "pergunta": pergunta,
        "ra": ra_extraido,
        "tipo": tipo_solicitacao,
        "contexto": {"tipo_solicitacao": tipo_solicitacao},
        "resposta_intermediaria": None,
        "resposta_final": None
    }

def processar_solicitacao(state: EstadoFluxo) -> EstadoFluxo:
    """
    Processa a solicitação usando o agente de processamento.
    """
    print(f"🔄 Processando solicitação do tipo: {state['tipo']}")
    
    # Se for consulta geral, pula o processamento
    if state["tipo"] == "consulta_geral":
        return {
            **state,
            "resposta_intermediaria": {
                "status": "skip",
                "message": "Consulta geral, sem processamento específico necessário."
            }
        }
    
    # Caso contrário, chama o agente de processamento
    resposta = agente_processamento(
        state["contexto"]["tipo_solicitacao"], 
        state["ra"], 
        state["pergunta"]
    )
    
    return {
        **state,
        "resposta_intermediaria": resposta
    }

def gerar_resposta_final(state: EstadoFluxo) -> EstadoFluxo:
    """
    Gera a resposta final usando o agente de resposta.
    """
    print(f"🔄 Gerando resposta final")
    
    # Se tivermos uma resposta intermediária, usamos para elaborar a resposta final
    if state["resposta_intermediaria"]:
        resposta_final = agente_resposta(state["pergunta"], state["resposta_intermediaria"])
    else:
        # Caso contrário, geramos uma resposta direta
        resposta_final = agente_resposta(state["pergunta"])
    
    return {
        **state,
        "resposta_final": resposta_final
    }

def decidir_proximo_passo(state: EstadoFluxo) -> str:
    """
    Decide qual é o próximo passo no fluxo com base no estado atual.
    """
    if state["tipo"] == "consulta_geral":
        print("⏭️ Encaminhando diretamente para resposta")
        return "resposta"
    else:
        print("⏭️ Encaminhando para processamento")
        return "processamento"

def agente_entrada(pergunta, ra=None):
    """
    Função principal do agente de entrada que inicia o fluxo e retorna a resposta final.
    Esta é a interface usada pelos testes e aplicações externas.
    """
    # Construir e executar o grafo
    workflow = construir_grafo()
    
    # Criar estado inicial corretamente
    estado_inicial = {
        "pergunta": pergunta,
        "ra": ra
    }
    
    resultado = workflow.invoke(estado_inicial)
    
    # Retornar apenas a resposta final formatada
    return resultado["resposta_final"]

def construir_grafo():
    """
    Constrói e compila o grafo de estados do LangGraph.
    """
    # 🚀 Criando o fluxo no LangGraph
    graph = StateGraph(state_schema=EstadoFluxo)
    
    # Adicionar nós
    graph.add_node("entrada", iniciar_fluxo)
    graph.add_node("processamento", processar_solicitacao)
    graph.add_node("resposta", gerar_resposta_final)
    
    # Configurar ponto de entrada
    graph.set_entry_point("entrada")
    
    # Adicionar arestas condicionais
    graph.add_conditional_edges(
        "entrada",
        decidir_proximo_passo,
        {
            "resposta": "resposta",
            "processamento": "processamento"
        }
    )
    
    # Adicionar aresta direta
    graph.add_edge("processamento", "resposta")
    
    # Definir nó de saída
    graph.add_edge("resposta", END)
    
    # Compilar o grafo
    return graph.compile()