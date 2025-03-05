import random
from datetime import date
from calendar import monthrange
import psycopg2
from faker import Faker
from dotenv import load_dotenv
import os

# Carregar variáveis do ambiente
load_dotenv()
db_url = os.getenv("DATABASE_URL")

# Conectar ao banco de dados
conn = psycopg2.connect(db_url)
cur = conn.cursor()

# Inicializar Faker para gerar dados fictícios
fake = Faker("pt_BR")

# Listas auxiliares
cursos = [
    ("Engenharia de Computação", 3600, "Bacharelado", 1500.00),
    ("Nutrição", 3200, "Bacharelado", 1200.00),
    ("Administração", 3000, "Bacharelado", 1100.00),
    ("Direito", 3800, "Bacharelado", 1800.00),
    ("Medicina", 7500, "Bacharelado", 4500.00)
]

status_matricula = ["Cursando", "Aprovado", "Reprovado", "Cancelado"]
status_financeiro = ["Pendente", "Pago", "Vencido"]
metodos_pagamento = ["PIX", "Boleto"]

try:
    print("📌 Inserindo cursos...")
    cur.executemany("INSERT INTO curso (nome, carga_horaria, grau, mensalidade) VALUES (%s, %s, %s, %s);", cursos)

    print("📌 Inserindo pessoas...")
    pessoas = []
    for _ in range(50):  # Criando 50 pessoas (Alunos, Professores e Coordenadores)
        pessoas.append((
            fake.name(),
            fake.email(),
            fake.cpf(),
            fake.phone_number(),
            fake.date_of_birth(minimum_age=18, maximum_age=60)
        ))
    cur.executemany("INSERT INTO pessoa (nome, email, cpf, telefone, data_nascimento) VALUES (%s, %s, %s, %s, %s);", pessoas)

    print("📌 Inserindo períodos letivos...")
    periodos = []
    for ano in range(2023, 2025):
        for semestre in [1, 2]:
            data_inicio = date(ano, 1 if semestre == 1 else 7, 1)
            ultimo_dia = monthrange(ano, 6 if semestre == 1 else 12)[1]
            data_fim = date(ano, 6 if semestre == 1 else 12, ultimo_dia)
            periodos.append((ano, semestre, data_inicio, data_fim))
    cur.executemany("INSERT INTO periodo_letivo (ano, semestre, data_inicio, data_fim) VALUES (%s, %s, %s, %s);", periodos)

    print("📌 Buscando IDs necessários...")
    cur.execute("SELECT id FROM curso;")
    curso_ids = [row[0] for row in cur.fetchall()]

    cur.execute("SELECT id FROM pessoa;")
    pessoa_ids = [row[0] for row in cur.fetchall()]

    cur.execute("SELECT id FROM periodo_letivo;")
    periodo_ids = [row[0] for row in cur.fetchall()]

    print("📌 Inserindo alunos...")
    alunos = []
    for i in range(30):
        ra = f"25{random.randint(100000, 999999)}"
        alunos.append((
            ra,
            pessoa_ids[i],
            random.choice(curso_ids),
            "Ativo",
            fake.date_between(start_date="-4y", end_date="today")
        ))
    cur.executemany("INSERT INTO aluno (ra, pessoa_id, curso_id, status, data_ingresso) VALUES (%s, %s, %s, %s, %s);", alunos)

    print("📌 Inserindo professores...")
    professores = [(pessoa_ids[i],) for i in range(30, 40)]
    cur.executemany("INSERT INTO professor (pessoa_id) VALUES (%s);", professores)

    print("📌 Inserindo coordenadores...")
    coordenadores = [(pessoa_ids[i], random.choice(curso_ids)) for i in range(40, 50)]
    cur.executemany("INSERT INTO coordenador (pessoa_id, curso_id) VALUES (%s, %s);", coordenadores)

    print("📌 Inserindo disciplinas...")
    disciplinas = []
    for curso_id in curso_ids:
        for _ in range(4):  # Cada curso tem 4 disciplinas
            disciplinas.append((
                fake.word().capitalize() + " Avançada",
                random.randint(40, 120),
                curso_id
            ))
    cur.executemany("INSERT INTO disciplina (nome, carga_horaria, curso_id) VALUES (%s, %s, %s);", disciplinas)

    cur.execute("SELECT id FROM disciplina;")
    disciplina_ids = [row[0] for row in cur.fetchall()]

    # 📌 RECUPERANDO IDs dos professores corretamente antes de associar
    cur.execute("SELECT id FROM professor;")
    professor_ids = [row[0] for row in cur.fetchall()]

    print("📌 Associando professores às disciplinas...")
    disciplina_professor = [(random.choice(disciplina_ids), random.choice(professor_ids)) for _ in range(15)]
    cur.executemany("INSERT INTO disciplina_professor (disciplina_id, professor_id) VALUES (%s, %s);", disciplina_professor)

    print("📌 Inserindo matrículas...")
    matriculas = []
    for aluno in alunos:
        for _ in range(2):
            matriculas.append((
                aluno[0],
                random.choice(disciplina_ids),
                random.choice(periodo_ids),
                random.choice(status_matricula)
            ))
    cur.executemany("INSERT INTO matricula (ra, disciplina_id, periodo_letivo_id, status) VALUES (%s, %s, %s, %s);", matriculas)

    print("📌 Inserindo boletos financeiros...")
    financeiro = []
    for aluno in alunos:
        financeiro.append((
            aluno[0],
            round(random.uniform(500, 2000), 2),
            fake.date_between(start_date="-3y", end_date="today"),
            random.choice(status_financeiro),
            fake.uuid4(),
            random.choice(metodos_pagamento)
        ))
    cur.executemany("INSERT INTO financeiro (ra, valor, vencimento, status, codigo_boleto, metodo_pagamento) VALUES (%s, %s, %s, %s, %s, %s);", financeiro)

    conn.commit()
    print("✅ Todas as tabelas foram populadas com sucesso!")

except Exception as e:
    conn.rollback()
    print("❌ ERRO ao popular o banco de dados:", e)

finally:
    cur.close()
    conn.close()
