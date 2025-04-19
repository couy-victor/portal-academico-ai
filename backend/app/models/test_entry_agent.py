from app.models.entry_agent import agente_entrada


# Exemplo de perguntas que os alunos podem fazer
perguntas_teste = [
    "Quais matérias eu tenho neste semestre?"
    "tenho boleto?"
]

for pergunta in perguntas_teste:
    print(f"\n💬 Pergunta: {pergunta}")
    resposta = agente_entrada(pergunta, "25690962")  # Passa um RA válido
    print(f"🤖 Resposta: {resposta}")
