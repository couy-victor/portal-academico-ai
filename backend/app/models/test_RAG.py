from app.models.entry_agent import agente_entrada

# Teste mais focado
perguntas_teste = [
    # Teste de SQL
    "Quais matérias eu tenho neste semestre?",
    
    # Teste de RAG
    "O que é a UNISAL?",
    "Quais cursos a UNISAL oferece?",
    
    # Teste de LLM geral
    "Como posso melhorar meus estudos?"
]

# Executar testes
for pergunta in perguntas_teste:
    print(f"\n{'='*30}")
    print(f"💬 Pergunta: {pergunta}")
    resposta = agente_entrada(pergunta, "25122775")
    print(f"🤖 Resposta: {resposta}")