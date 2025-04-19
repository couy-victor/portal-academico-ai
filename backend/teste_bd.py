import os
import psycopg2
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()

# Pegar a URL do banco
db_url = os.getenv("DATABASE_URL")

if not db_url:
    print("❌ ERRO: A variável DATABASE_URL não foi carregada do .env.")
    exit()

try:
    # Conectar ao banco
    print("🔄 Conectando ao banco de dados...")
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    # Listar tabelas existentes
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
    tabelas = cur.fetchall()

    print("✅ Conexão bem-sucedida! Tabelas no banco de dados:")
    for tabela in tabelas:
        print(f" - {tabela[0]}")
    
    cur.close()
    conn.close()
except Exception as e:
    print("❌ ERRO ao conectar ao banco:", e)
