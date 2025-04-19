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

# Caminho para o arquivo alters.sql
alters_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database", "alters.sql"))

if not os.path.exists(alters_path):
    print(f"❌ ERRO: O arquivo {alters_path} não foi encontrado.")
    exit()

try:
    # Conectar ao banco
    print("🔄 Conectando ao banco de dados para aplicar alterações...")
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    with open(alters_path, "r") as file:
        alters_sql = file.read().strip()  # Remove espaços extras

    if not alters_sql:
        print("⚠️ O arquivo alters.sql está vazio. Nenhuma alteração foi aplicada.")
    else:
        # Executar cada comando separadamente para garantir que tudo rode corretamente
        commands = alters_sql.split(";")  # Divide os comandos por ";"
        for command in commands:
            command = command.strip()
            if command:  # Evita comandos vazios
                print(f"📌 Executando: {command[:100]}...")  # Mostra parte do comando
                cur.execute(command)
        
        conn.commit()
        print("✅ Alterações aplicadas com sucesso!")

    cur.close()
    conn.close()
except Exception as e:
    print("❌ ERRO ao aplicar as alterações:", e)
