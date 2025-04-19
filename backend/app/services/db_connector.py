from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Carregar as variáveis do ambiente
load_dotenv()

# URL do banco de dados
DATABASE_URL = os.getenv("DATABASE_URL")

# Criar conexão com o banco usando SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Cria uma nova sessão do banco de dados e a encerra automaticamente após o uso.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
