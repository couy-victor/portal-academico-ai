from app.services.DB import consultar_banco

query = "SELECT * FROM aluno LIMIT 5;"
resultado = consultar_banco(query)

print("🎯 Resultado da consulta:", resultado)
