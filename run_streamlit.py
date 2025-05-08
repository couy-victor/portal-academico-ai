#!/usr/bin/env python
"""
Script para iniciar a interface Streamlit do Portal Acadêmico AI.
"""
import os
import subprocess
import sys
import webbrowser
from time import sleep

def check_dependencies():
    """Verifica se as dependências necessárias estão instaladas."""
    try:
        import streamlit
        import dotenv
        return True
    except ImportError as e:
        print(f"Erro: Dependência não encontrada - {e}")
        print("Instalando dependências...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit", "python-dotenv"])
        return False

def check_env_file():
    """Verifica se o arquivo .env existe."""
    if not os.path.exists(".env"):
        print("Aviso: Arquivo .env não encontrado.")
        print("Criando arquivo .env básico...")
        with open(".env", "w") as f:
            f.write("# Variáveis de ambiente para o Portal Acadêmico AI\n")
            f.write("OPENAI_API_KEY=\n")
            f.write("SUPABASE_URL=\n")
            f.write("SUPABASE_KEY=\n")
            f.write("TAVILY_API_KEY=\n")
        print("Arquivo .env criado. Por favor, preencha as variáveis de ambiente necessárias.")
        return False
    return True

def main():
    """Função principal para iniciar a interface Streamlit."""
    # Verificar dependências
    deps_ok = check_dependencies()
    if not deps_ok:
        print("Dependências instaladas. Reiniciando...")
        # Reiniciar o script após instalar dependências
        os.execv(sys.executable, [sys.executable] + sys.argv)
    
    # Verificar arquivo .env
    env_ok = check_env_file()
    if not env_ok:
        print("Por favor, preencha o arquivo .env com suas chaves de API antes de continuar.")
        input("Pressione Enter para continuar após preencher o arquivo .env...")
    
    # Iniciar Streamlit
    print("Iniciando interface Streamlit...")
    port = 8501
    url = f"http://localhost:{port}"
    
    # Abrir navegador após um pequeno atraso
    def open_browser():
        sleep(2)
        webbrowser.open(url)
    
    # Iniciar thread para abrir o navegador
    import threading
    threading.Thread(target=open_browser).start()
    
    # Executar Streamlit
    subprocess.run([sys.executable, "-m", "streamlit", "run", "Chatbot.py"])

if __name__ == "__main__":
    main()
