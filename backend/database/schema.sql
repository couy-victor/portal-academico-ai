import random
import psycopg2
from dotenv import load_dotenv
import os

# Carregar variáveis do ambiente
load_dotenv()
db_url = os.getenv("DATABASE_URL")

# Conectar ao banco de dados
conn = psycopg2.connect(db_url)
cur = conn.cursor()

try:
    print("📌 Buscando IDs das matrículas...")

    # Buscar todos os IDs das matrículas na tabela `matricula`
    cur.execute("SELECT id FROM matricula;")
    matricula_ids = [row[0] for row in cur.fetchall()]

    if not matricula_ids:
        print("❌ Nenhuma matrícula encontrada. Verifique a tabela 'matricula'.")
        conn.close()
        exit()

    print(f"✅ Encontradas {len(matricula_ids)} matrículas. Inserindo notas e faltas...")

    # Gerar notas e faltas para cada matrícula encontrada
    notas_faltas = []
    for matricula_id in matricula_ids:
        nota_1 = round(random.uniform(2, 10), 1)
        nota_2 = round(random.uniform(2, 10), 1)
        nota_final = round((nota_1 + nota_2) / 2, 1)
        faltas = random.randint(0, 15)

        notas_faltas.append((matricula_id, nota_1, nota_2, nota_final, faltas))

    # Inserir as notas e faltas na tabela
    cur.executemany("""
        INSERT INTO notas_faltas (matricula_id, nota_1, nota_2, nota_final, faltas)
        VALUES (%s, %s, %s, %s, %s);
    """, notas_faltas)

    # Commit após inserção
    conn.commit()
    print("✅ Notas e faltas inseridas com sucesso!")

except Exception as e:
    conn.rollback()
    print("❌ ERRO ao popular notas e faltas:", e)

finally:
    cur.close()
    conn.close()
