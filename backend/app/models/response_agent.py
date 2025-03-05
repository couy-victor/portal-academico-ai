import os
# Garanta que está usando a versão correta
from openai import OpenAI  # Requer openai >= 1.0.0
from dotenv import load_dotenv
import json

# 🔥 Carregar variáveis do ambiente
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 🔥 Configurar o cliente OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

def formatar_resultados(dados):
    """
    Formata resultados de consultas SQL para apresentação amigável.
    """
    if not dados or len(dados) == 0:
        return "Não encontrei dados para sua consulta."
    
    try:
        if isinstance(dados, str):
            return dados
        
        # Se for uma lista de dicionários (resultados SQL)
        if isinstance(dados, list) and isinstance(dados[0], dict):
            # Extrair cabeçalhos
            cabecalhos = list(dados[0].keys())
            
            # Formatar como tabela de texto
            resultado = "| " + " | ".join(cabecalhos) + " |\n"
            resultado += "| " + " | ".join(["---" for _ in cabecalhos]) + " |\n"
            
            for item in dados:
                linha = "| " + " | ".join([str(item.get(col, "")) for col in cabecalhos]) + " |"
                resultado += linha + "\n"
            
            return resultado
        
        # Caso seja outro formato
        return str(dados)
    except Exception as e:
        print(f"❌ Erro ao formatar resultados: {e}")
        return str(dados)

def gerar_resposta_final(pergunta, resposta_processada):
    """
    Gera a resposta final formatada e amigável para o usuário.
    Utiliza a resposta do agente de processamento.
    """
    print(f"📌 Gerando resposta final para: {pergunta}")
    
    try:
        # Extrair informações da resposta processada
        status = resposta_processada.get("status", "error")
        mensagem = resposta_processada.get("message", "")
        dados = resposta_processada.get("data", "Não há dados disponíveis.")
        
        # Formatar os dados para apresentação
        dados_formatados = formatar_resultados(dados) if dados else "Não há dados disponíveis."
        
        # Preparar contexto para o modelo
        context = {
            "pergunta": pergunta,
            "status": status,
            "mensagem": mensagem,
            "dados": dados_formatados
        }
        
        # Instruções para o modelo
        system_prompt = """
        Você é um assistente educacional amigável e claro da UNISAL. 
        
        Sua tarefa é reformular as informações de resposta em uma linguagem natural e amigável.
        
        Regras:
        1. Seja conciso e direto - responda em até 5 frases curtas.
        2. Mantenha um tom educacional, profissional mas amigável.
        3. Se tiverem dados tabulares, apresente-os de forma organizada e legível.
        4. Se não houver dados ou ocorrer um erro, seja honesto e sugira alternativas.
        5. Apresente sempre a informação no contexto da pergunta original.
        """
        
        # Preparar o prompt do usuário com os dados para contextualização
        user_prompt = f"""
        Pergunta original: {context['pergunta']}
        
        Resultado da consulta:
        Status: {context['status']}
        Mensagem: {context['mensagem']}
        
        Dados encontrados:
        {context['dados']}
        
        Por favor, reformule isso em uma resposta natural e amigável.
        """
        
        # Chamar o modelo
        resposta = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        resposta_final = resposta.choices[0].message.content.strip()
        print(f"✅ Resposta final gerada com sucesso!")
        
        return resposta_final
    
    except Exception as e:
        print(f"❌ Erro ao gerar resposta final: {e}")
        return "Desculpe, ocorreu um erro ao processar sua solicitação. Por favor, tente novamente mais tarde."

def agente_resposta(pergunta, resposta_processada=None):
    """
    Processa a resposta final para o usuário.
    """
    print(f"📌 Agente de resposta acionado para: {pergunta}")
    
    # Se não recebeu resposta processada, gera uma resposta direta
    if resposta_processada is None:
        try:
            resposta = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Você é um assistente acadêmico da UNISAL. Seja conciso e útil."},
                    {"role": "user", "content": pergunta}
                ],
                max_tokens=150
            )
            resposta_final = resposta.choices[0].message.content.strip()
            print(f"✅ Resposta direta gerada: {resposta_final}")
            return resposta_final
        except Exception as e:
            print(f"❌ Erro ao gerar resposta direta: {e}")
            return "Desculpe, não consegui processar sua solicitação no momento."
    
    # Se recebeu resposta processada, formata e melhora
    return gerar_resposta_final(pergunta, resposta_processada)