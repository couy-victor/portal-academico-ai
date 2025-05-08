import streamlit as st
import os
import json
import sys
from dotenv import load_dotenv

# Adicionar o diretório raiz ao path para importações
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Tratamento de erros de importação
try:
    # Importar os agentes necessários
    from src.models.state import AcademicAgentState
    from src.agents.emotional_support_agent import emotional_support_agent
    from src.agents.tutor_agent import tutor_agent
    from src.agents.planning_agent import planning_agent
    from src.graph.academic_graph import create_academic_graph

    # Flag para indicar que as importações foram bem-sucedidas
    IMPORTS_SUCCESSFUL = True
except ImportError as e:
    st.error(f"Erro ao importar módulos: {str(e)}")
    st.warning("Certifique-se de que você está executando o Streamlit a partir do diretório raiz do projeto.")
    IMPORTS_SUCCESSFUL = False

# Carregar variáveis de ambiente
load_dotenv()

# Função para inicializar o estado do agente
def initialize_agent_state(query, ra):
    """
    Inicializa o estado do agente com a consulta e o RA do usuário.

    Args:
        query (str): Consulta do usuário
        ra (str): RA do aluno

    Returns:
        AcademicAgentState: Estado inicial do agente
    """
    return AcademicAgentState(
        user_query=query,
        user_id=ra,
        user_context={"RA": ra}
    )

# Configuração da barra lateral
with st.sidebar:
    st.title("Configurações")

    # Campo para o RA do aluno
    ra = st.text_input("RA do Aluno", key="student_ra", placeholder="Digite seu RA")

    # Seleção do agente
    agent_type = st.selectbox(
        "Selecione o tipo de assistente",
        ["Acadêmico", "Suporte Emocional", "Tutor", "Planejamento Acadêmico"],
        key="agent_type"
    )

    # Botão para limpar o histórico
    if st.button("Limpar Conversa"):
        st.session_state.messages = [{"role": "assistant", "content": "Olá! Como posso ajudar você hoje? Por favor, selecione o tipo de assistente na barra lateral e informe seu RA."}]
        st.rerun()

    # Exemplos de perguntas
    st.markdown("---")
    st.markdown("### Exemplos de Perguntas")

    if st.session_state.agent_type == "Acadêmico":
        examples = [
            "Quantas faltas eu tenho na disciplina Circuitos Digitais?",
            "Qual é a minha nota em Cálculo?",
            "Quais disciplinas estou matriculado neste semestre?"
        ]
    elif st.session_state.agent_type == "Suporte Emocional":
        examples = [
            "Estou muito ansioso com a prova de amanhã",
            "Não consigo me concentrar para estudar",
            "Estou me sentindo sobrecarregado com tantas tarefas"
        ]
    elif st.session_state.agent_type == "Tutor":
        examples = [
            "Pode me explicar o que é uma máquina de Turing?",
            "Como funciona a Lei de Ohm?",
            "O que são derivadas parciais?"
        ]
    else:  # Planejamento Acadêmico
        examples = [
            "Preciso organizar meus estudos para as provas finais",
            "Como posso criar um cronograma de estudos eficiente?",
            "Quais técnicas de estudo são mais eficazes?"
        ]

    for example in examples:
        if st.button(example, key=f"example_{example}"):
            # Adicionar exemplo como mensagem do usuário
            st.session_state.messages.append({"role": "user", "content": example})
            # Reexecutar o app para processar a mensagem
            st.rerun()

    # Informações adicionais
    st.markdown("---")
    st.markdown("### Sobre os Agentes")
    st.markdown("**Acadêmico**: Consultas sobre notas, faltas, disciplinas, etc.")
    st.markdown("**Suporte Emocional**: Ajuda com ansiedade, estresse, etc.")
    st.markdown("**Tutor**: Explicações sobre conteúdos acadêmicos")
    st.markdown("**Planejamento**: Ajuda com organização de estudos")

# Título principal
st.title("🎓 Portal Acadêmico AI")
st.caption("Assistente acadêmico inteligente para estudantes")

# Inicializar o histórico de mensagens
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Olá! Como posso ajudar você hoje? Por favor, selecione o tipo de assistente na barra lateral e informe seu RA."}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    # Verificar se as importações foram bem-sucedidas
    if not IMPORTS_SUCCESSFUL:
        st.error("Não é possível processar consultas devido a erros de importação.")
        st.stop()

    # Verificar se o RA foi fornecido
    if not st.session_state.student_ra:
        st.warning("Por favor, digite seu RA na barra lateral para continuar.")
        st.stop()

    # Adicionar a mensagem do usuário ao histórico
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # Criar o estado inicial para o agente
    state = initialize_agent_state(prompt, st.session_state.student_ra)

    # Processar a consulta com o agente apropriado
    with st.spinner("Processando sua consulta..."):
        try:
            if st.session_state.agent_type == "Acadêmico":
                # Criar e executar o grafo acadêmico
                academic_graph = create_academic_graph()
                result = academic_graph.invoke(state)
                response = result.get("natural_response", "Não foi possível processar sua consulta acadêmica.")

            elif st.session_state.agent_type == "Suporte Emocional":
                # Usar o agente de suporte emocional
                result = emotional_support_agent(state)
                response = result.get("natural_response", "Não foi possível processar sua consulta de suporte emocional.")

            elif st.session_state.agent_type == "Tutor":
                # Usar o agente tutor
                result = tutor_agent(state)
                response = result.get("natural_response", "Não foi possível processar sua consulta de tutoria.")

            elif st.session_state.agent_type == "Planejamento Acadêmico":
                # Usar o agente de planejamento
                result = planning_agent(state)
                response = result.get("natural_response", "Não foi possível processar sua consulta de planejamento.")

            else:
                response = "Por favor, selecione um tipo de assistente válido na barra lateral."

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            st.error(f"Ocorreu um erro ao processar sua consulta: {str(e)}")
            response = "Desculpe, ocorreu um erro ao processar sua consulta. Por favor, tente novamente mais tarde."

            # Registrar o erro detalhado (apenas para depuração)
            with st.expander("Detalhes do Erro (para desenvolvedores)"):
                st.code(error_details)

    # Adicionar a resposta ao histórico
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.chat_message("assistant").write(response)

    # Exibir informações de depuração (opcional)
    with st.expander("Informações de Depuração"):
        st.write("Tipo de Agente:", st.session_state.agent_type)
        st.write("RA:", st.session_state.student_ra)
        if 'result' in locals():
            # Converter o resultado para JSON, excluindo a resposta natural
            try:
                result_json = {k: v for k, v in result.items() if k != 'natural_response'}
                st.json(json.dumps(result_json, default=str))
            except Exception as json_error:
                st.error(f"Erro ao serializar o resultado: {str(json_error)}")
                st.write("Resultado bruto:", result)
