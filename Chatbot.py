import streamlit as st
import os
import json
import sys
import base64
from datetime import datetime
from dotenv import load_dotenv
from streamlit_timeline import timeline

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

def display_pdf_download_buttons(pdf_paths):
    """
    Exibe botões para download de PDFs.

    Args:
        pdf_paths (list): Lista de caminhos para arquivos PDF
    """
    st.markdown("### Boletos Disponíveis para Download")

    for i, pdf_path in enumerate(pdf_paths):
        try:
            # Ler o arquivo PDF
            with open(pdf_path, "rb") as file:
                pdf_bytes = file.read()

            # Obter o nome do arquivo
            file_name = os.path.basename(pdf_path)

            # Criar botão de download
            st.download_button(
                label=f"📄 Baixar Boleto {i+1}",
                data=pdf_bytes,
                file_name=file_name,
                mime="application/pdf",
                key=f"download_pdf_{i}"
            )

            # Exibir visualização do PDF (opcional)
            with st.expander(f"Visualizar Boleto {i+1}"):
                # Codificar o PDF em base64
                b64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")

                # Exibir o PDF usando um iframe
                pdf_display = f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="500" type="application/pdf"></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Erro ao processar o PDF {i+1}: {str(e)}")

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

    # Opções específicas para o agente de planejamento
    if agent_type == "Planejamento Acadêmico":
        st.markdown("### Método de Estudo")
        study_method = st.radio(
            "Selecione o método de estudo preferido:",
            ["Pomodoro", "Active Recall", "Time Blocking", "Não especificado"],
            key="study_method",
            help="Pomodoro: blocos de tempo focado com pausas. Active Recall: teste ativo de conhecimento. Time Blocking: organização em blocos por disciplina."
        )

        # Configurações específicas para cada método
        if study_method == "Pomodoro":
            col1, col2, col3 = st.columns(3)
            with col1:
                focus_time = st.number_input("Tempo de foco (min)", min_value=5, max_value=60, value=25, step=5, key="focus_time")
            with col2:
                break_time = st.number_input("Pausa curta (min)", min_value=1, max_value=15, value=5, step=1, key="break_time")
            with col3:
                long_break = st.number_input("Pausa longa (min)", min_value=5, max_value=30, value=15, step=5, key="long_break")

        elif study_method == "Active Recall":
            review_frequency = st.selectbox(
                "Frequência de revisão:",
                ["Diária", "A cada 2 dias", "Semanal", "Personalizada"],
                key="review_frequency"
            )

            quiz_type = st.multiselect(
                "Tipos de teste:",
                ["Flashcards", "Auto-questionamento", "Resumos ativos", "Mapas mentais", "Explicação em voz alta"],
                default=["Flashcards", "Auto-questionamento"],
                key="quiz_type"
            )

        elif study_method == "Time Blocking":
            col1, col2 = st.columns(2)
            with col1:
                min_block = st.number_input("Duração mínima dos blocos (min)", min_value=15, max_value=120, value=30, step=15, key="min_block")
            with col2:
                priority_time = st.selectbox(
                    "Período de maior produtividade:",
                    ["Manhã", "Tarde", "Noite"],
                    key="priority_time"
                )

    # Botão para limpar o histórico
    if st.button("Limpar Conversa"):
        welcome_message = """
        👋 Olá! Eu sou o Bosquinho, seu assistente acadêmico aqui na UNISAL!

        Estou aqui para ajudar com:

        • 📚 Informações acadêmicas (notas, faltas, disciplinas)

        • 💰 Questões financeiras (boletos, mensalidades)

        • 🧠 Tutoria em diversas disciplinas

        • 😌 Suporte emocional para momentos difíceis

        • 📅 Planejamento de estudos e organização

        Para começar, por favor:
        1. Digite seu RA na barra lateral
        2. Selecione o tipo de assistente que deseja utilizar
        3. Faça sua pergunta no campo abaixo

        Como posso ajudar você hoje?
        """
        st.session_state.messages = [{"role": "assistant", "content": welcome_message}]
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
    elif st.session_state.agent_type == "Planejamento Acadêmico":
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
st.title("🎓 Portal Acadêmico - Bosquinho")
st.caption("Seu assistente acadêmico inteligente na UNISAL")

# Inicializar o histórico de mensagens
if "messages" not in st.session_state:
    welcome_message = """
    👋 Olá! Eu sou o Bosquinho, seu assistente acadêmico aqui no UNISAL!

    Estou aqui para ajudar com:

    • 📚 Informações acadêmicas (notas, faltas, disciplinas)

    • 💰 Questões financeiras (boletos, mensalidades)

    • 🧠 Tutoria em diversas disciplinas

    • 😌 Suporte emocional para momentos difíceis

    • 📅 Planejamento de estudos e organização

    Para começar, por favor:
    1. Digite seu RA na barra lateral
    2. Selecione o tipo de assistente que deseja utilizar
    3. Faça sua pergunta no campo abaixo

    Como posso ajudar você hoje?
    """
    st.session_state["messages"] = [{"role": "assistant", "content": welcome_message}]

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
                # Adicionar parâmetros do método de estudo ao estado
                if "study_method" in st.session_state:
                    method = st.session_state.study_method.lower()
                    if method == "pomodoro":
                        state["study_method"] = "pomodoro"
                        state["focus_time"] = st.session_state.get("focus_time", 25)
                        state["break_time"] = st.session_state.get("break_time", 5)
                        state["long_break"] = st.session_state.get("long_break", 15)
                    elif method == "active recall":
                        state["study_method"] = "active_recall"
                        state["review_frequency"] = st.session_state.get("review_frequency", "Diária").lower()
                        state["quiz_type"] = ", ".join(st.session_state.get("quiz_type", ["Flashcards", "Auto-questionamento"])).lower()
                    elif method == "time blocking":
                        state["study_method"] = "time_blocking"
                        state["min_block"] = st.session_state.get("min_block", 30)
                        state["priority_time"] = st.session_state.get("priority_time", "Manhã").lower()
                    else:
                        state["study_method"] = "não_especificado"

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

    # Exibir opções de exportação e visualização para o agente de planejamento
    if 'result' in locals() and st.session_state.agent_type == "Planejamento Acadêmico" and response:
        try:
            # Importar utilitários de planejamento
            from src.utils.planning_utils import export_to_pdf, export_to_ics, create_timeline_data

            # Inicializar variáveis de estado se não existirem
            if "planning_pdf_ready" not in st.session_state:
                st.session_state.planning_pdf_ready = False
                st.session_state.planning_pdf_path = ""

            if "planning_ics_ready" not in st.session_state:
                st.session_state.planning_ics_ready = False
                st.session_state.planning_ics_path = ""

            if "planning_timeline_data" not in st.session_state:
                st.session_state.planning_timeline_data = None

            # Criar container para as opções de exportação
            with st.expander("📊 Opções de Visualização e Exportação do Plano", expanded=True):
                st.markdown("### Visualizar e Exportar seu Plano de Estudos")

                # Botões de exportação
                col1, col2 = st.columns(2)

                # Função para gerar PDF
                def generate_pdf():
                    st.write("Iniciando geração de PDF...")
                    try:
                        # Log do conteúdo da resposta (primeiros 100 caracteres)
                        st.write(f"Conteúdo da resposta (primeiros 100 caracteres): {response[:100]}...")

                        # Gerar PDF
                        pdf_path = export_to_pdf(response)
                        st.write(f"PDF gerado em: {pdf_path}")

                        # Atualizar estado
                        st.session_state.planning_pdf_path = pdf_path
                        st.session_state.planning_pdf_ready = True
                        st.write("Estado atualizado: PDF pronto para download")
                    except Exception as e:
                        import traceback
                        st.error(f"Erro ao gerar PDF: {str(e)}")
                        st.code(traceback.format_exc())

                # Função para gerar ICS
                def generate_ics():
                    st.write("Iniciando geração de arquivo de calendário...")
                    try:
                        # Gerar ICS
                        ics_path = export_to_ics(response)
                        st.write(f"Arquivo de calendário gerado em: {ics_path}")

                        # Atualizar estado
                        st.session_state.planning_ics_path = ics_path
                        st.session_state.planning_ics_ready = True
                        st.write("Estado atualizado: Arquivo de calendário pronto para download")
                    except Exception as e:
                        import traceback
                        st.error(f"Erro ao gerar arquivo de calendário: {str(e)}")
                        st.code(traceback.format_exc())

                # Função para gerar dados da timeline
                def generate_timeline_data():
                    st.write("Iniciando geração de dados da timeline...")
                    try:
                        # Extrair tarefas do texto
                        from src.utils.planning_utils import extract_tasks_from_markdown
                        tasks = extract_tasks_from_markdown(response)
                        st.write(f"Tarefas extraídas: {len(tasks)}")
                        for i, task in enumerate(tasks[:3]):  # Mostrar até 3 tarefas para debug
                            st.write(f"Tarefa {i+1}: {task['title']} - {task['date_str']}")

                        # Gerar dados da timeline
                        timeline_data = create_timeline_data(response)
                        st.write(f"Eventos na timeline: {len(timeline_data['events'])}")

                        # Atualizar estado
                        st.session_state.planning_timeline_data = timeline_data
                        st.write("Estado atualizado: Dados da timeline prontos")
                    except Exception as e:
                        import traceback
                        st.error(f"Erro ao criar dados da timeline: {str(e)}")
                        st.code(traceback.format_exc())

                # Botão para PDF
                with col1:
                    # Abordagem direta: gerar PDF e oferecer download em um único botão
                    try:
                        # Gerar PDF usando ReportLab (abordagem similar aos boletos)
                        from src.utils.planning_utils import export_to_reportlab_pdf
                        pdf_path = export_to_reportlab_pdf(response)

                        # Ler o arquivo PDF
                        with open(pdf_path, "rb") as pdf_file:
                            pdf_bytes = pdf_file.read()

                            # Botão de download
                            st.download_button(
                                label="📄 Baixar Plano em PDF",
                                data=pdf_bytes,
                                file_name="plano_de_estudos.pdf",
                                mime="application/pdf",
                                key="download_pdf_button"
                            )
                        st.success("PDF gerado com sucesso! Clique no botão acima para baixar.")
                    except Exception as e:
                        import traceback
                        st.error(f"Erro ao gerar PDF: {str(e)}")
                        st.code(traceback.format_exc())

                # Botão para ICS
                with col2:
                    # Abordagem direta: gerar ICS e oferecer download em um único botão
                    try:
                        # Gerar ICS diretamente
                        ics_path = export_to_ics(response)

                        # Ler o arquivo ICS
                        with open(ics_path, "rb") as ics_file:
                            ics_bytes = ics_file.read()

                            # Botão de download
                            st.download_button(
                                label="📅 Baixar Calendário (ICS)",
                                data=ics_bytes,
                                file_name="plano_de_estudos.ics",
                                mime="text/calendar",
                                key="download_ics_button"
                            )
                        st.success("Arquivo de calendário gerado com sucesso! Clique no botão acima para baixar.")
                        st.info("Dica: Importe este arquivo no Google Calendar, Outlook ou outro aplicativo de calendário.")
                    except Exception as e:
                        import traceback
                        st.error(f"Erro ao gerar arquivo de calendário: {str(e)}")
                        st.code(traceback.format_exc())

                # Visualização de timeline
                st.markdown("### Visualização do Cronograma")

                # Abordagem direta: gerar e exibir a timeline em um único passo
                try:
                    # Gerar dados da timeline diretamente
                    timeline_data = create_timeline_data(response)

                    # Verificar se temos eventos
                    if timeline_data["events"]:
                        # Mostrar lista de tarefas em formato de tabela
                        st.subheader("📋 Cronograma de Tarefas")

                        # Criar dados para a tabela
                        table_data = {
                            "Data": [],
                            "Tarefa": []
                        }

                        for event in timeline_data["events"]:
                            # Extrair data do formato TimelineJS
                            start_date = event["start_date"]
                            year = start_date["year"]
                            month = start_date["month"]
                            day = start_date["day"]

                            # Formatar a data como DD/MM/YYYY
                            formatted_date = f"{day.zfill(2)}/{month.zfill(2)}/{year}"

                            # Extrair o título do evento
                            headline = event["text"]["headline"]

                            table_data["Data"].append(formatted_date)
                            table_data["Tarefa"].append(headline)

                        # Exibir tabela
                        st.dataframe(table_data, use_container_width=True)
                        st.success(f"✅ {len(timeline_data['events'])} tarefas encontradas no plano.")

                        # Exibir a timeline usando a função timeline
                        st.subheader("📊 Visualização Interativa")
                        try:
                            # Converter o timeline_data para string JSON
                            import json
                            timeline_json = json.dumps(timeline_data)

                            # Exibir a timeline usando a função timeline
                            timeline(timeline_json, height=400)
                        except Exception as timeline_error:
                            st.info(f"A visualização interativa não está disponível. Erro: {str(timeline_error)}")

                        # Adicionar botão para abrir a timeline em uma nova aba
                        st.subheader("📊 Visualização em Nova Aba")

                        # Criar arquivo HTML para visualização em nova aba
                        timeline_html = f"""
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <title>Cronograma de Estudos</title>
                            <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
                            <script type="text/javascript">
                                google.charts.load('current', {{'packages':['timeline']}});
                                google.charts.setOnLoadCallback(drawChart);

                                function drawChart() {{
                                    var container = document.getElementById('timeline');
                                    var chart = new google.visualization.Timeline(container);
                                    var dataTable = new google.visualization.DataTable();

                                    dataTable.addColumn({{ type: 'string', id: 'Task' }});
                                    dataTable.addColumn({{ type: 'date', id: 'Start' }});
                                    dataTable.addColumn({{ type: 'date', id: 'End' }});

                                    var rows = [];

                                    {{% for event in timeline_data["events"] %}}
                                        var year = parseInt("{event['start_date']['year']}");
                                        var month = parseInt("{event['start_date']['month']}") - 1; // JS months are 0-based
                                        var day = parseInt("{event['start_date']['day']}");

                                        var start_date = new Date(year, month, day);
                                        var end_date = new Date(year, month, day);
                                        end_date.setDate(end_date.getDate() + 1);

                                        rows.push(["{event['text']['headline']}", start_date, end_date]);
                                    {{% endfor %}}

                                    dataTable.addRows(rows);

                                    var options = {{
                                        timeline: {{ colorByRowLabel: true }},
                                        backgroundColor: '#f9f9f9',
                                        alternatingRowStyle: true,
                                        height: 600
                                    }};

                                    chart.draw(dataTable, options);
                                }}
                            </script>
                            <style>
                                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f9f9f9; }}
                                h1 {{ color: #435334; text-align: center; }}
                                #timeline {{ width: 100%; height: 600px; }}
                                .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; background-color: white; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
                                .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #666; }}
                            </style>
                        </head>
                        <body>
                            <div class="container">
                                <h1>Cronograma de Estudos</h1>
                                <div id="timeline"></div>
                                <div class="footer">
                                    Gerado pelo Assistente Acadêmico - UNISAL<br>
                                    {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
                                </div>
                            </div>
                        </body>
                        </html>
                        """

                        # Substituir os marcadores de template pelos valores reais
                        for event in timeline_data["events"]:
                            # Extrair dados do evento
                            year = event["start_date"]["year"]
                            month = event["start_date"]["month"]
                            day = event["start_date"]["day"]
                            headline = event["text"]["headline"].replace('"', '\\"')

                            # Substituir o marcador de início do loop
                            template_marker = f"{{% for event in timeline_data[\"events\"] %}}"
                            replacement = ""
                            timeline_html = timeline_html.replace(template_marker, replacement, 1)

                            # Substituir os marcadores de data
                            template_marker = "{event['start_date']['year']}"
                            timeline_html = timeline_html.replace(template_marker, year, 1)

                            template_marker = "{event['start_date']['month']}"
                            timeline_html = timeline_html.replace(template_marker, month, 1)

                            template_marker = "{event['start_date']['day']}"
                            timeline_html = timeline_html.replace(template_marker, day, 1)

                            # Substituir o marcador de título
                            template_marker = "{event['text']['headline']}"
                            timeline_html = timeline_html.replace(template_marker, headline, 1)

                        # Remover o marcador de fim do loop
                        timeline_html = timeline_html.replace("{{% endfor %}}", "")

                        # Criar um arquivo HTML temporário
                        temp_dir = os.path.join(os.getcwd(), "temp")
                        os.makedirs(temp_dir, exist_ok=True)
                        html_path = os.path.join(temp_dir, "timeline_chart.html")

                        with open(html_path, "w", encoding="utf-8") as f:
                            f.write(timeline_html)

                        # Exibir o caminho do arquivo
                        st.info("Para visualizar o cronograma em uma nova aba, abra o arquivo HTML gerado:")
                        st.code(os.path.abspath(html_path), language="bash")

                        # Adicionar instruções para o usuário
                        st.markdown("""
                        1. Copie o caminho acima
                        2. Cole na barra de endereços do seu navegador
                        3. Pressione Enter para abrir o cronograma em tela cheia
                        """)
                    else:
                        st.warning("Não foi possível encontrar tarefas com datas no plano.")
                        st.info("Sugestão: Inclua datas específicas no formato DD/MM/YYYY ou mencione 'Dia X' no seu plano.")

                except Exception as e:
                    import traceback
                    st.error(f"Erro ao processar a timeline: {str(e)}")
                    st.code(traceback.format_exc())

                # Adicionar dica sobre o formato das datas
                st.info("💡 Dica: Para melhor visualização, o plano deve incluir tarefas com datas no formato DD/MM/YYYY ou no formato 'Dia X: [Descrição]'.")

        except Exception as e:
            st.warning(f"Não foi possível processar as opções de exportação: {str(e)}")

    # Exibir botões de download de PDFs se houver boletos disponíveis
    if 'result' in locals():
        # Verificar se é uma consulta sobre boletos (em qualquer agente)
        if "boleto" in prompt.lower() or "vencido" in prompt.lower() or "mensalidade" in prompt.lower():
            # Processar boletos
            from src.utils.boleto_generator import obter_boletos_vencidos

            try:
                # Obter RA do aluno
                ra = st.session_state.student_ra

                # Obter nome do aluno (fictício para demonstração)
                nome_aluno = "Estudante da UNISAL"

                # Obter boletos vencidos
                boletos = obter_boletos_vencidos(ra, nome_aluno, quantidade=3)

                # Exibir botões de download
                if boletos:
                    pdf_paths = [boleto["pdf_path"] for boleto in boletos]
                    display_pdf_download_buttons(pdf_paths)
            except Exception as e:
                st.warning(f"Não foi possível gerar os PDFs dos boletos: {str(e)}")



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
