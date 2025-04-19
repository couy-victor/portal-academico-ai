# Diagrama de Fluxo do Sistema Multi-Agentes com LangGraph

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                   START                                     │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ User Context Node                                                           │
│                                                                             │
│ Recupera e enriquece o contexto do usuário (RA, disciplina, etc.)          │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Cache Check                                                                 │
│                                                                             │
│ Verifica se há uma resposta em cache para a consulta                        │
└───────────────────┬───────────────────────────────────┬─────────────────────┘
                    │                                   │
                    ▼                                   ▼
┌─────────────────────────────────┐     ┌─────────────────────────────────────┐
│ Cache Miss                      │     │ Cache Hit                           │
└───────────────┬─────────────────┘     └─────────────────┬───────────────────┘
                │                                         │
                ▼                                         │
┌─────────────────────────────────┐                       │
│ Intent Router                   │                       │
│                                 │                       │
│ Classifica a intenção da        │                       │
│ pergunta do usuário             │                       │
└───────────────┬─────────────────┘                       │
                │                                         │
                ▼                                         │
┌─────────────────────────────────┐                       │
│ Schema Retriever                │                       │
│                                 │                       │
│ Recupera o schema do banco      │                       │
│ de dados                        │                       │
└───────────────┬─────────────────┘                       │
                │                                         │
                ▼                                         │
┌─────────────────────────────────┐                       │
│ SQL Generator                   │                       │
│                                 │                       │
│ Gera a consulta SQL com base    │                       │
│ na intenção e no schema         │                       │
└───────────────┬─────────────────┘                       │
                │                                         │
                ▼                                         │
┌─────────────────────────────────┐                       │
│ Query Validator                 │                       │
│                                 │                       │
│ Valida a consulta SQL quanto    │                       │
│ à correção e segurança          │                       │
└───────────────┬─────────────────┘                       │
                │                                         │
                ▼                                         │
┌─────────────────────────────────┐                       │
│ DBA Guard                       │                       │
│                                 │                       │
│ Otimiza a consulta SQL para     │                       │
│ performance                     │                       │
└───────────────┬─────────────────┘                       │
                │                                         │
                ▼                                         │
┌─────────────────────────────────┐                       │
│ Executor                        │                       │
│                                 │                       │
│ Executa a consulta SQL no       │                       │
│ Supabase                        │                       │
└───────────────┬─────────────────┘                       │
                │                                         │
    ┌───────────┴───────────┐                             │
    │                       │                             │
    ▼                       ▼                             │
┌─────────────┐     ┌─────────────────┐                   │
│ Error       │     │ Success         │                   │
└──────┬──────┘     └────────┬────────┘                   │
       │                     │                            │
       ▼                     │                            │
┌─────────────┐              │                            │
│ Fallback    │              │                            │
│ Handler     │              │                            │
└──────┬──────┘              │                            │
       │                     │                            │
       └─────────────────────┘                            │
                │                                         │
                ▼                                         │
┌─────────────────────────────────┐                       │
│ Response Generator              │◄──────────────────────┘
│                                 │
│ Converte os resultados da       │
│ consulta em linguagem natural   │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│ Cache Update                    │
│                                 │
│ Atualiza o cache com a nova     │
│ resposta                        │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│ Logger                          │
│                                 │
│ Registra a interação para       │
│ análise                         │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│                END              │
└─────────────────────────────────┘
```

## Descrição do Fluxo

1. **START**: Ponto de entrada do grafo.

2. **User Context Node**: Recupera e enriquece o contexto do usuário (RA, disciplina, etc.).
   - Mapeia o RA para matrícula se necessário
   - Adiciona informações padrão se não encontrar no banco

3. **Cache Check**: Verifica se há uma resposta em cache para a consulta.
   - Se houver um hit no cache, vai direto para o Response Generator
   - Se não houver cache, continua o fluxo normal

4. **Intent Router**: Classifica a intenção da pergunta do usuário.
   - Identifica se é sobre notas, faltas, horários, etc.
   - Atribui um nível de confiança à classificação

5. **Schema Retriever**: Recupera o schema do banco de dados.
   - Obtém informações sobre tabelas, colunas, chaves primárias e estrangeiras
   - Usa cache para evitar consultas frequentes ao banco

6. **SQL Generator**: Gera a consulta SQL com base na intenção e no schema.
   - Usa técnica ReAct para raciocinar sobre a consulta
   - Parametriza a consulta para evitar injeção SQL

7. **Query Validator**: Valida a consulta SQL quanto à correção e segurança.
   - Verifica sintaxe SQL
   - Identifica possíveis problemas de segurança
   - Sugere correções se necessário

8. **DBA Guard**: Otimiza a consulta SQL para performance.
   - Adiciona LIMIT se necessário
   - Verifica uso de índices
   - Evita consultas que possam causar problemas de performance

9. **Executor**: Executa a consulta SQL no Supabase.
   - Sanitiza e parametriza a consulta
   - Executa via função RPC segura
   - Captura erros e resultados

10. **Fallback Handler**: Lida com erros e fornece respostas alternativas.
    - Gera respostas amigáveis para erros
    - Sugere alternativas ao usuário

11. **Response Generator**: Converte os resultados da consulta em linguagem natural.
    - Formata os resultados de forma amigável
    - Personaliza a resposta com base no contexto do usuário

12. **Cache Update**: Atualiza o cache com a nova resposta.
    - Armazena resultados para consultas futuras
    - Define tempo de expiração apropriado

13. **Logger**: Registra a interação para análise.
    - Armazena métricas de desempenho
    - Registra erros e sucessos
    - Facilita análise posterior

14. **END**: Ponto de saída do grafo.
