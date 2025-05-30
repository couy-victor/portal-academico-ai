"""
Utilitários para o agente de planejamento acadêmico.

Este módulo contém funções para exportação de planos de estudo em diferentes formatos
(PDF, calendário, timeline) e outras utilidades relacionadas ao planejamento acadêmico.
"""

import os
import re
import json
from datetime import datetime, timedelta
from fpdf import FPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from ics import Calendar, Event
import streamlit as st
import base64

# Tentar importar markdown, mas não falhar se não estiver disponível
try:
    import markdown
except ImportError:
    # Função simples para substituir o módulo markdown se não estiver disponível
    def convert_markdown_to_html(text):
        return text
else:
    def convert_markdown_to_html(text):
        return markdown.markdown(text)

def extract_tasks_from_markdown(markdown_text):
    """
    Extrai tarefas de um texto markdown.

    Args:
        markdown_text (str): Texto markdown contendo o plano de estudos

    Returns:
        list: Lista de tarefas extraídas
    """
    tasks = []

    # Padrões para encontrar tarefas com datas em diferentes formatos
    patterns = [
        # Formato: - Tarefa - DD/MM/YYYY ou DD/MM
        r'[-*]\s+(.*?)(?:\s*-\s*|\s*\()((?:\d{1,2}\/\d{1,2}\/\d{4})|(?:\d{1,2}\/\d{1,2}))',

        # Formato: - Tarefa (Prazo: DD/MM/YYYY ou DD/MM)
        r'[-*]\s+(.*?)(?:Prazo:?\s*)((?:\d{1,2}\/\d{1,2}\/\d{4})|(?:\d{1,2}\/\d{1,2}))',

        # Formato: - Tarefa (Data: DD/MM/YYYY ou DD/MM)
        r'[-*]\s+(.*?)(?:Data:?\s*)((?:\d{1,2}\/\d{1,2}\/\d{4})|(?:\d{1,2}\/\d{1,2}))',

        # Formato: DD/MM/YYYY ou DD/MM: Tarefa
        r'((?:\d{1,2}\/\d{1,2}\/\d{4})|(?:\d{1,2}\/\d{1,2}))(?:\s*[-:]\s*)([^-\n\r]*)',

        # Formato: Dia DD/MM/YYYY ou DD/MM - Tarefa
        r'Dia\s+((?:\d{1,2}\/\d{1,2}\/\d{4})|(?:\d{1,2}\/\d{1,2}))(?:\s*[-:]\s*)([^-\n\r]*)',

        # Formato: Dia X: Tarefa
        r'Dia\s+(\d+)(?:\s*[-:]\s*)([^-\n\r]*)',

        # Formato: Dia X: [Data de Início] ou [Data +X]
        r'Dia\s+(\d+)(?:\s*[-:]\s*)\[(?:Data(?:\s*\+\s*\d+)?|Data de Início)\]([^-\n\r]*)'
    ]

    current_year = datetime.now().year
    current_date = datetime.now()

    # Processar cada padrão
    for pattern in patterns:
        matches = re.finditer(pattern, markdown_text)

        for match in matches:
            # Verificar se o padrão tem a data no primeiro ou segundo grupo
            if pattern.startswith(r'((?:\d{1,2}') or pattern.startswith(r'Dia'):
                # Data está no primeiro grupo, título no segundo
                date_str = match.group(1).strip()
                task_title = match.group(2).strip()
            else:
                # Título está no primeiro grupo, data no segundo
                task_title = match.group(1).strip()
                date_str = match.group(2).strip()

            # Verificar se é um padrão "Dia X"
            if pattern == r'Dia\s+(\d+)(?:\s*[-:]\s*)([^-\n\r]*)':
                try:
                    # Converter para número de dias
                    day_num = int(date_str)
                    # Criar data relativa (dia atual + número de dias)
                    task_date = current_date + timedelta(days=day_num-1)  # -1 porque Dia 1 é hoje
                    date_str = task_date.strftime("%d/%m/%Y")
                except ValueError:
                    # Se não conseguir converter, ignorar esta tarefa
                    continue
            else:
                # Adicionar o ano se não estiver presente
                if len(date_str.split('/')) == 2:
                    date_str = f"{date_str}/{current_year}"

                # Tentar converter para data
                try:
                    task_date = datetime.strptime(date_str, "%d/%m/%Y")
                except ValueError:
                    # Se não conseguir converter, ignorar esta tarefa
                    continue

            # Verificar se a tarefa já existe (para evitar duplicatas)
            duplicate = False
            for task in tasks:
                if task["title"] == task_title and task["date"] == task_date:
                    duplicate = True
                    break

            if not duplicate:
                tasks.append({
                    "title": task_title,
                    "date": task_date,
                    "date_str": date_str
                })

    # Procurar especificamente por padrões "Dia X: [Data]" ou "Dia X: [Data +Y]"
    day_pattern = r'Dia\s+(\d+)(?:\s*[-:]\s*)\[(?:Data(?:\s*\+\s*(\d+))?|Data de Início)\]'
    day_matches = re.finditer(day_pattern, markdown_text)

    for match in day_matches:
        day_num = int(match.group(1).strip())
        offset = 0
        if match.group(2):  # Se tiver um offset como em [Data +2]
            offset = int(match.group(2).strip())

        # Criar data relativa (dia atual + número de dias)
        task_date = current_date + timedelta(days=day_num-1+offset)  # -1 porque Dia 1 é hoje
        date_str = task_date.strftime("%d/%m/%Y")

        # Encontrar o texto da tarefa (pode estar na mesma linha ou na linha seguinte)
        line_with_day = re.search(f"Dia\\s+{day_num}.*", markdown_text)
        if line_with_day:
            line_text = line_with_day.group(0)
            # Remover a parte "Dia X: [Data]" para obter o título da tarefa
            task_title = re.sub(r'Dia\s+\d+\s*[-:]\s*\[.*?\]', '', line_text).strip()
            if not task_title:  # Se não houver texto na mesma linha
                # Procurar na próxima linha
                next_line_match = re.search(f"Dia\\s+{day_num}.*?\\n(.*?)(?:\\n|$)", markdown_text)
                if next_line_match and next_line_match.group(1).strip():
                    task_title = next_line_match.group(1).strip()
                else:
                    task_title = f"Tarefa do Dia {day_num}"

            # Adicionar a tarefa
            tasks.append({
                "title": task_title,
                "date": task_date,
                "date_str": date_str
            })

    # Ordenar tarefas por data
    tasks.sort(key=lambda x: x["date"])

    # Se não encontrou nenhuma tarefa, criar tarefas padrão baseadas no cronograma
    if not tasks:
        # Procurar por um cronograma no texto
        cronograma_match = re.search(r'Cronograma(?:\s+de\s+Estudos)?(?:\s*:)?', markdown_text)
        if cronograma_match:
            print(f"Encontrou um cronograma no texto: {cronograma_match.group(0)}")

            # Encontrar todas as linhas que começam com "Dia X:"
            dia_lines = re.findall(r'Dia\s+(\d+)(?:\s*[-:]\s*)(.*?)(?:\n|$)', markdown_text)
            print(f"Linhas de dias encontradas: {len(dia_lines)}")

            for dia_match in dia_lines:
                day_num = int(dia_match[0])
                task_title = dia_match[1].strip()
                print(f"Dia {day_num}: '{task_title}'")

                # Remover [Data] ou [Data de Início] do título
                if '[Data' in task_title:
                    print(f"  - Removendo [Data] do título: '{task_title}'")
                    task_title = re.sub(r'\[(?:Data(?:\s*\+\s*\d+)?|Data de Início)\]', '', task_title).strip()
                    print(f"  - Título após remoção: '{task_title}'")

                if not task_title:
                    task_title = f"Tarefa do Dia {day_num}"
                    print(f"  - Usando título padrão: '{task_title}'")

                # Criar data relativa
                task_date = current_date + timedelta(days=day_num-1)  # -1 porque Dia 1 é hoje
                date_str = task_date.strftime("%d/%m/%Y")
                print(f"  - Data calculada: {date_str}")

                # Adicionar a tarefa
                tasks.append({
                    "title": task_title,
                    "date": task_date,
                    "date_str": date_str
                })
                print(f"  - Tarefa adicionada: {task_title} ({date_str})")

            # Ordenar tarefas por data
            tasks.sort(key=lambda x: x["date"])
            print(f"Tarefas ordenadas por data: {len(tasks)}")

    return tasks

def export_to_pdf(markdown_text, filename="plano_de_estudos.pdf"):
    """
    Exporta o plano de estudos para PDF.

    Args:
        markdown_text (str): Texto markdown contendo o plano de estudos
        filename (str): Nome do arquivo PDF

    Returns:
        str: Caminho para o arquivo PDF gerado
    """
    print("Iniciando exportação para PDF...")

    # Criar diretório temporário se não existir
    temp_dir = os.path.join(os.getcwd(), "temp")
    os.makedirs(temp_dir, exist_ok=True)

    # Caminho completo para o arquivo
    filepath = os.path.join(temp_dir, filename)

    try:
        # Criar PDF
        pdf = FPDF()
        pdf.add_page()

        # Configurar fonte
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="Plano de Estudos", ln=True, align='C')
        pdf.ln(10)

        # Adicionar conteúdo principal
        pdf.set_font("Arial", size=12)

        # Processar o texto markdown para extrair seções
        lines = markdown_text.split('\n')
        current_section = ""

        for line in lines:
            line = line.strip()
            if not line:
                continue

            try:
                # Verificar se é um título (começa com # ou é todo maiúsculo)
                if line.startswith('#') or line.isupper():
                    # Título de seção
                    pdf.set_font("Arial", 'B', 14)

                    # Limitar comprimento
                    title = line.replace('#', '').strip()
                    if len(title) > 70:
                        title = title[:67] + "..."

                    pdf.cell(0, 10, txt=title, ln=True)
                    pdf.set_font("Arial", size=12)
                    current_section = title

                # Verificar se é um item de lista
                elif line.startswith('-') or line.startswith('*') or line.startswith('•'):
                    # Item de lista
                    item_text = line[1:].strip()

                    # Limitar comprimento
                    if len(item_text) > 70:
                        chunks = [item_text[i:i+70] for i in range(0, len(item_text), 70)]
                        pdf.multi_cell(0, 10, txt=f"• {chunks[0]}...")
                    else:
                        pdf.multi_cell(0, 10, txt=f"• {item_text}")

                # Verificar se é um dia do cronograma
                elif line.lower().startswith('dia'):
                    # Dia do cronograma
                    pdf.set_font("Arial", 'B', 12)

                    # Limitar comprimento
                    if len(line) > 70:
                        line = line[:67] + "..."

                    pdf.multi_cell(0, 10, txt=line)
                    pdf.set_font("Arial", size=12)

                # Texto normal
                else:
                    # Limitar comprimento
                    if len(line) > 70:
                        chunks = [line[i:i+70] for i in range(0, len(line), 70)]
                        for chunk in chunks[:3]:  # Limitar a 3 linhas
                            pdf.multi_cell(0, 10, txt=chunk)
                        if len(chunks) > 3:
                            pdf.multi_cell(0, 10, txt="...")
                    else:
                        pdf.multi_cell(0, 10, txt=line)
            except Exception as line_error:
                print(f"Erro ao processar linha: {str(line_error)}")
                continue

        # Adicionar seção de tarefas
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, txt="Cronograma de Tarefas", ln=True)
        pdf.ln(5)

        # Extrair tarefas do markdown
        tasks = extract_tasks_from_markdown(markdown_text)

        # Adicionar tarefas ao PDF
        if tasks:
            pdf.set_font("Arial", size=12)
            for task in tasks:
                try:
                    # Limitar o comprimento do título da tarefa
                    title = task["title"]
                    if len(title) > 60:
                        title = title[:57] + "..."

                    # Adicionar a tarefa ao PDF
                    task_text = f"• {task['date_str']}: {title}"
                    pdf.multi_cell(0, 10, txt=task_text)
                except Exception as e:
                    print(f"Erro ao adicionar tarefa ao PDF: {str(e)}")
                    continue
        else:
            pdf.multi_cell(0, 10, txt="Nenhuma tarefa específica foi encontrada no plano.")

        # Adicionar nota de rodapé
        pdf.ln(10)
        pdf.set_font("Arial", 'I', 10)
        pdf.multi_cell(0, 10, txt="Nota: Este PDF contém um resumo do plano. Para ver o plano completo, consulte o assistente acadêmico.")

        # Salvar o PDF
        pdf.output(filepath)
        print(f"PDF salvo em: {filepath}")

        return filepath

    except Exception as e:
        import traceback
        print(f"Erro ao gerar PDF: {str(e)}")
        print(traceback.format_exc())

        # Criar um PDF de fallback extremamente simples
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, txt="Plano de Estudos", ln=True, align='C')
            pdf.set_font("Arial", size=12)

            # Adicionar pelo menos algum conteúdo
            pdf.multi_cell(0, 10, txt="Conteúdo do Plano de Estudos:")
            pdf.ln(5)

            # Adicionar os primeiros 500 caracteres do texto
            safe_text = markdown_text[:500] + "..." if len(markdown_text) > 500 else markdown_text

            # Dividir em linhas curtas
            chunks = [safe_text[i:i+70] for i in range(0, len(safe_text), 70)]
            for chunk in chunks:
                try:
                    pdf.multi_cell(0, 10, txt=chunk)
                except:
                    pass

            pdf.ln(10)
            pdf.multi_cell(0, 10, txt="Para ver o plano completo, consulte o assistente acadêmico.")

            # Salvar o PDF de fallback
            pdf.output(filepath)
            print(f"PDF de fallback salvo em: {filepath}")

            return filepath
        except Exception as fallback_error:
            print(f"Erro ao gerar PDF de fallback: {str(fallback_error)}")
            raise

def export_to_ics(markdown_text, filename="plano_de_estudos.ics"):
    """
    Exporta o plano de estudos para um arquivo de calendário ICS.

    Args:
        markdown_text (str): Texto markdown contendo o plano de estudos
        filename (str): Nome do arquivo ICS

    Returns:
        str: Caminho para o arquivo ICS gerado
    """
    # Criar diretório temporário se não existir
    temp_dir = os.path.join(os.getcwd(), "temp")
    os.makedirs(temp_dir, exist_ok=True)

    # Caminho completo para o arquivo
    filepath = os.path.join(temp_dir, filename)

    # Criar calendário
    cal = Calendar()

    # Extrair tarefas do markdown
    tasks = extract_tasks_from_markdown(markdown_text)

    # Adicionar eventos ao calendário
    for task in tasks:
        event = Event()
        event.name = task["title"]
        event.begin = task["date"]
        event.end = task["date"] + timedelta(hours=1)  # Duração padrão de 1 hora
        event.description = f"Tarefa do plano de estudos: {task['title']}"
        cal.events.add(event)

    # Salvar o calendário
    with open(filepath, 'w') as f:
        f.write(str(cal))

    return filepath

def create_timeline_data(markdown_text):
    """
    Cria dados para visualização de timeline no formato TimelineJS.

    Args:
        markdown_text (str): Texto markdown contendo o plano de estudos

    Returns:
        dict: Dados formatados para o componente streamlit-timeline
    """
    print("Iniciando criação de dados para timeline...")

    # Extrair tarefas do markdown
    tasks = extract_tasks_from_markdown(markdown_text)
    print(f"Tarefas extraídas: {len(tasks)}")

    # Criar eventos da timeline no formato correto
    timeline_events = []

    for i, task in enumerate(tasks):
        print(f"Processando tarefa {i+1}: {task['title']} ({task['date_str']})")

        # Extrair ano, mês e dia da data
        year = task["date"].year
        month = task["date"].month
        day = task["date"].day

        # Criar evento no formato TimelineJS
        event = {
            "start_date": {
                "year": str(year),
                "month": str(month),
                "day": str(day)
            },
            "text": {
                "headline": task["title"],
                "text": f"Data: {task['date_str']}"
            },
            "group": "Tarefas"
        }

        timeline_events.append(event)
        print(f"  - Evento adicionado à timeline: {task['title']} ({task['date_str']})")

    # Se não encontrou tarefas, criar alguns eventos de exemplo
    if not timeline_events:
        print("Nenhuma tarefa encontrada. Criando eventos de exemplo...")
        # Datas de exemplo baseadas na data atual
        today = datetime.now()

        # Criar datas para os próximos 5 dias
        for i in range(5):
            day_num = i + 1
            event_date = today + timedelta(days=i)

            # Criar conteúdo baseado no dia
            if i == 0:
                headline = "Início do plano de estudos"
                text = "Organização inicial e planejamento"
            elif i == 1:
                headline = "Revisão de conceitos básicos"
                text = "Revisar fundamentos importantes para as provas"
            elif i == 2:
                headline = "Prática de exercícios"
                text = "Resolver exercícios e problemas práticos"
            elif i == 3:
                headline = "Revisão de tópicos avançados"
                text = "Focar em tópicos mais complexos e desafiadores"
            else:
                headline = f"Atividade do dia {day_num}"
                text = "Preparação final para as avaliações"

            # Adicionar evento à timeline
            event = {
                "start_date": {
                    "year": str(event_date.year),
                    "month": str(event_date.month),
                    "day": str(event_date.day)
                },
                "text": {
                    "headline": headline,
                    "text": text
                },
                "group": "Exemplo"
            }

            timeline_events.append(event)

        print(f"Criados {len(timeline_events)} eventos de exemplo")

    # Criar dados da timeline no formato TimelineJS
    timeline_data = {
        "title": {
            "text": {
                "headline": "Plano de Estudos",
                "text": "Visualização do cronograma de tarefas"
            }
        },
        "events": timeline_events
    }

    print(f"Dados da timeline criados com {len(timeline_events)} eventos")
    return timeline_data

def export_to_reportlab_pdf(markdown_text, filename="plano_de_estudos_reportlab.pdf"):
    """
    Exporta o plano de estudos para PDF usando ReportLab (abordagem similar aos boletos).

    Args:
        markdown_text (str): Texto markdown contendo o plano de estudos
        filename (str): Nome do arquivo PDF

    Returns:
        str: Caminho para o arquivo PDF gerado
    """
    print("Iniciando exportação para PDF com ReportLab...")

    # Criar diretório temporário se não existir
    temp_dir = os.path.join(os.getcwd(), "temp")
    os.makedirs(temp_dir, exist_ok=True)

    # Caminho completo para o arquivo
    filepath = os.path.join(temp_dir, filename)

    try:
        # Criar PDF
        c = canvas.Canvas(filepath, pagesize=letter)
        width, height = letter

        # Adicionar cabeçalho
        c.setFont("Helvetica-Bold", 16)
        c.drawString(30, height - 40, "PLANO DE ESTUDOS")
        c.setFont("Helvetica", 12)
        c.drawString(30, height - 60, "Assistente Acadêmico - UNISAL")

        # Linha separadora
        c.line(30, height - 70, width - 30, height - 70)

        # Processar o texto markdown para extrair seções
        lines = markdown_text.split('\n')
        y_position = height - 100

        for line in lines:
            line = line.strip()
            if not line:
                continue

            try:
                # Verificar se é um título (começa com # ou é todo maiúsculo)
                if line.startswith('#') or line.isupper():
                    # Título de seção
                    c.setFont("Helvetica-Bold", 14)
                    title = line.replace('#', '').strip()

                    # Limitar comprimento
                    if len(title) > 70:
                        title = title[:67] + "..."

                    c.drawString(30, y_position, title)
                    y_position -= 20
                    c.setFont("Helvetica", 12)

                # Verificar se é um item de lista
                elif line.startswith('-') or line.startswith('*') or line.startswith('•'):
                    # Item de lista
                    item_text = line[1:].strip()

                    # Limitar comprimento e quebrar em múltiplas linhas se necessário
                    if len(item_text) > 80:
                        chunks = [item_text[i:i+80] for i in range(0, len(item_text), 80)]
                        c.drawString(40, y_position, f"• {chunks[0]}...")
                        y_position -= 15
                    else:
                        c.drawString(40, y_position, f"• {item_text}")
                        y_position -= 15

                # Verificar se é um dia do cronograma
                elif line.lower().startswith('dia'):
                    # Dia do cronograma
                    c.setFont("Helvetica-Bold", 12)

                    # Limitar comprimento
                    if len(line) > 80:
                        line = line[:77] + "..."

                    c.drawString(30, y_position, line)
                    y_position -= 20
                    c.setFont("Helvetica", 12)

                # Texto normal
                else:
                    # Limitar comprimento e quebrar em múltiplas linhas se necessário
                    if len(line) > 80:
                        chunks = [line[i:i+80] for i in range(0, len(line), 80)]
                        for chunk in chunks[:3]:  # Limitar a 3 linhas
                            c.drawString(30, y_position, chunk)
                            y_position -= 15
                        if len(chunks) > 3:
                            c.drawString(30, y_position, "...")
                            y_position -= 15
                    else:
                        c.drawString(30, y_position, line)
                        y_position -= 15

                # Verificar se precisamos de uma nova página
                if y_position < 100:
                    c.showPage()
                    y_position = height - 40
                    c.setFont("Helvetica", 12)
            except Exception as line_error:
                print(f"Erro ao processar linha: {str(line_error)}")
                continue

        # Extrair tarefas do markdown
        tasks = extract_tasks_from_markdown(markdown_text)

        # Verificar se precisamos de uma nova página para as tarefas
        if y_position < 200:
            c.showPage()
            y_position = height - 40

        # Adicionar seção de tarefas
        c.setFont("Helvetica-Bold", 14)
        c.drawString(30, y_position, "Cronograma de Tarefas")
        y_position -= 25

        # Adicionar tarefas ao PDF
        if tasks:
            c.setFont("Helvetica", 12)
            for task in tasks:
                try:
                    # Limitar o comprimento do título da tarefa
                    title = task["title"]
                    if len(title) > 60:
                        title = title[:57] + "..."

                    # Adicionar a tarefa ao PDF
                    task_text = f"• {task['date_str']}: {title}"
                    c.drawString(40, y_position, task_text)
                    y_position -= 20

                    # Verificar se precisamos de uma nova página
                    if y_position < 100:
                        c.showPage()
                        y_position = height - 40
                        c.setFont("Helvetica", 12)
                except Exception as e:
                    print(f"Erro ao adicionar tarefa ao PDF: {str(e)}")
                    continue
        else:
            c.drawString(40, y_position, "Nenhuma tarefa específica foi encontrada no plano.")
            y_position -= 20

        # Adicionar nota de rodapé
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(30, 30, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        c.drawString(width - 200, 30, "Assistente Acadêmico - UNISAL")

        # Finalizar PDF
        c.save()
        print(f"PDF salvo em: {filepath}")

        return filepath

    except Exception as e:
        import traceback
        print(f"Erro ao gerar PDF com ReportLab: {str(e)}")
        print(traceback.format_exc())

        # Criar um PDF de fallback extremamente simples
        try:
            c = canvas.Canvas(filepath, pagesize=letter)
            width, height = letter

            c.setFont("Helvetica-Bold", 16)
            c.drawString(30, height - 40, "PLANO DE ESTUDOS")
            c.setFont("Helvetica", 12)
            c.drawString(30, height - 60, "Assistente Acadêmico - UNISAL")

            c.line(30, height - 70, width - 30, height - 70)

            c.drawString(30, height - 100, "Não foi possível gerar o PDF completo.")
            c.drawString(30, height - 120, "Por favor, consulte o plano no assistente acadêmico.")

            c.save()
            print(f"PDF de fallback salvo em: {filepath}")

            return filepath
        except Exception as fallback_error:
            print(f"Erro ao gerar PDF de fallback: {str(fallback_error)}")
            raise

def get_download_link(file_path, link_text, mime_type):
    """
    Cria um link de download para um arquivo.

    Args:
        file_path (str): Caminho para o arquivo
        link_text (str): Texto do link
        mime_type (str): Tipo MIME do arquivo

    Returns:
        str: HTML para o link de download
    """
    with open(file_path, "rb") as file:
        file_bytes = file.read()
        b64 = base64.b64encode(file_bytes).decode()
        href = f'<a href="data:{mime_type};base64,{b64}" download="{os.path.basename(file_path)}">{link_text}</a>'
        return href
