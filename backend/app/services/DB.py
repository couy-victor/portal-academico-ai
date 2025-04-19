import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Função para conectar ao banco de dados
def conectar_banco():
    """Cria uma conexão com o banco de dados e retorna um cursor."""
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco: {e}")
        return None

# Função para executar uma consulta SQL
def consultar_banco(query, params=None):
    """
    Executa uma query no banco e retorna os resultados.
    
    :param query: A string SQL da consulta
    :param params: Parâmetros opcionais para a query
    :return: Lista de resultados ou None se houver erro
    """
    conn = conectar_banco()
    if not conn:
        return None

    try:
        cur = conn.cursor()
        cur.execute(query, params if params else ())
        resultados = cur.fetchall()
        cur.close()
        conn.close()
        return resultados
    except Exception as e:
        print(f"❌ Erro ao executar query: {e}")
        return None
