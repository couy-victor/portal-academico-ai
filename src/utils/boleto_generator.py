"""
Módulo para geração de boletos fictícios para o Portal Acadêmico AI.
"""
import os
import random
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle

# Caminho para a pasta de boletos
BOLETOS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "boletos")

# Garantir que a pasta de boletos exista
os.makedirs(BOLETOS_DIR, exist_ok=True)

def gerar_codigo_barras():
    """Gera um código de barras fictício."""
    return "".join([str(random.randint(0, 9)) for _ in range(48)])

def gerar_boleto_pdf(codigo_boleto, valor, data_vencimento, nome_aluno, ra):
    """
    Gera um PDF de boleto fictício.
    
    Args:
        codigo_boleto (str): Código único do boleto
        valor (float): Valor do boleto
        data_vencimento (str): Data de vencimento no formato DD/MM/AAAA
        nome_aluno (str): Nome do aluno
        ra (str): RA do aluno
        
    Returns:
        str: Caminho para o arquivo PDF gerado
    """
    # Criar nome do arquivo
    pdf_path = os.path.join(BOLETOS_DIR, f"{codigo_boleto}.pdf")
    
    # Criar PDF
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    
    # Adicionar cabeçalho
    c.setFont("Helvetica-Bold", 16)
    c.drawString(30, height - 40, "BOLETO BANCÁRIO")
    c.setFont("Helvetica", 12)
    c.drawString(30, height - 60, "UNISAL - Centro Universitário Salesiano de São Paulo")
    
    # Linha separadora
    c.line(30, height - 70, width - 30, height - 70)
    
    # Informações do boleto
    c.setFont("Helvetica-Bold", 12)
    c.drawString(30, height - 100, "Informações do Boleto:")
    
    c.setFont("Helvetica", 10)
    c.drawString(30, height - 120, f"Código do Boleto: {codigo_boleto}")
    c.drawString(30, height - 140, f"Valor: R$ {valor:.2f}")
    c.drawString(30, height - 160, f"Data de Vencimento: {data_vencimento}")
    c.drawString(30, height - 180, f"Nome do Aluno: {nome_aluno}")
    c.drawString(30, height - 200, f"RA: {ra}")
    
    # Linha separadora
    c.line(30, height - 220, width - 30, height - 220)
    
    # Código de barras (simulado)
    c.setFont("Helvetica", 8)
    codigo_barras = gerar_codigo_barras()
    c.drawString(30, height - 240, "Código de Barras:")
    c.setFont("Courier", 10)
    c.drawString(30, height - 260, codigo_barras[:24])
    c.drawString(30, height - 275, codigo_barras[24:])
    
    # Linha separadora
    c.line(30, height - 290, width - 30, height - 290)
    
    # Informações de pagamento
    c.setFont("Helvetica-Bold", 12)
    c.drawString(30, height - 310, "Informações de Pagamento:")
    
    c.setFont("Helvetica", 10)
    c.drawString(30, height - 330, "Banco: Banco Fictício S.A.")
    c.drawString(30, height - 350, "Agência: 1234")
    c.drawString(30, height - 370, "Conta: 56789-0")
    
    # Aviso
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.red)
    c.drawString(30, height - 420, "ESTE É UM BOLETO FICTÍCIO PARA FINS DE DEMONSTRAÇÃO")
    c.setFillColor(colors.black)
    
    # Informações adicionais
    c.setFont("Helvetica", 8)
    c.drawString(30, 30, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    c.drawString(width - 200, 30, "Portal Acadêmico AI - UNISAL")
    
    # Finalizar PDF
    c.save()
    
    return pdf_path

def gerar_boletos_vencidos(ra, nome_aluno, quantidade=3):
    """
    Gera boletos vencidos fictícios para um aluno.
    
    Args:
        ra (str): RA do aluno
        nome_aluno (str): Nome do aluno
        quantidade (int): Quantidade de boletos a serem gerados
        
    Returns:
        list: Lista de dicionários com informações dos boletos gerados
    """
    boletos = []
    
    # Data atual
    hoje = datetime.now()
    
    for i in range(quantidade):
        # Gerar código de boleto único
        codigo_boleto = f"{random.randint(10000000, 99999999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
        
        # Gerar valor aleatório entre 500 e 2000
        valor = random.uniform(500, 2000)
        
        # Gerar data de vencimento (entre 5 e 60 dias atrás)
        dias_atraso = random.randint(5, 60)
        data_vencimento = hoje - timedelta(days=dias_atraso)
        data_vencimento_str = data_vencimento.strftime("%d/%m/%Y")
        
        # Gerar PDF do boleto
        pdf_path = gerar_boleto_pdf(codigo_boleto, valor, data_vencimento_str, nome_aluno, ra)
        
        # Adicionar informações do boleto à lista
        boletos.append({
            "codigo": codigo_boleto,
            "valor": valor,
            "vencimento": data_vencimento_str,
            "dias_atraso": dias_atraso,
            "pdf_path": pdf_path
        })
    
    return boletos

def obter_boletos_vencidos(ra, nome_aluno="Estudante", quantidade=3, force_new=False):
    """
    Obtém boletos vencidos para um aluno. Se os boletos já existirem, retorna os existentes,
    caso contrário, gera novos boletos.
    
    Args:
        ra (str): RA do aluno
        nome_aluno (str): Nome do aluno
        quantidade (int): Quantidade de boletos
        force_new (bool): Se True, força a geração de novos boletos
        
    Returns:
        list: Lista de dicionários com informações dos boletos
    """
    # Verificar se já existem boletos para este RA
    boletos_existentes = []
    
    if not force_new:
        # Procurar por boletos existentes
        for filename in os.listdir(BOLETOS_DIR):
            if filename.endswith(".pdf"):
                # Verificar se o arquivo contém informações do RA
                # Isso é uma simplificação, na prática seria necessário um sistema mais robusto
                boleto_path = os.path.join(BOLETOS_DIR, filename)
                boleto_codigo = filename.replace(".pdf", "")
                
                # Adicionar à lista de boletos existentes
                # Aqui estamos criando informações fictícias, pois não temos como extrair do PDF
                boletos_existentes.append({
                    "codigo": boleto_codigo,
                    "valor": random.uniform(500, 2000),
                    "vencimento": (datetime.now() - timedelta(days=random.randint(5, 60))).strftime("%d/%m/%Y"),
                    "dias_atraso": random.randint(5, 60),
                    "pdf_path": boleto_path
                })
                
                if len(boletos_existentes) >= quantidade:
                    break
    
    # Se não houver boletos suficientes, gerar novos
    if len(boletos_existentes) < quantidade:
        return gerar_boletos_vencidos(ra, nome_aluno, quantidade)
    
    return boletos_existentes[:quantidade]
