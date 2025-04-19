import os
import psycopg2
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()

# Pegar a URL do banco
db_url = os.getenv("DATABASE_URL")

if not db_url:
    print("❌ ERRO: A variável DATABASE_URL não foi carregada.")
    exit()

# Ajustando o caminho para o schema.sql, subindo um nível
schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database", "alters.sql"))

if not os.path.exists(schema_path):
    print(f"❌ ERRO: O arquivo schema.sql não foi encontrado no caminho: {schema_path}.")
    exit()

with open(schema_path, "r") as file:
    schema_sql = file.read()

try:
    # Conectar ao banco e executar o schema
    print("🔄 Aplicando o schema no banco de dados...")
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute(schema_sql)
    conn.commit()
    
    print("✅ Schema aplicado com sucesso!")
    
    cur.close()
    conn.close()
except Exception as e:
    print("❌ ERRO ao aplicar o schema:", e)
