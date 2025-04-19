```mermaid
graph TD
    START((START)) --> UserContextNode[User Context Node]
    UserContextNode --> CacheCheck[Cache Check]
    
    %% Conditional routing from cache check
    CacheCheck -->|Cache Miss| IntentRouter[Intent Router]
    CacheCheck -->|Cache Hit| ResponseGenerator[Response Generator]
    
    IntentRouter --> SchemaRetriever[Schema Retriever]
    SchemaRetriever --> SQLGenerator[SQL Generator]
    SQLGenerator --> QueryValidator[Query Validator]
    QueryValidator --> DBAGuard[DBA Guard]
    DBAGuard --> Executor[Executor]
    
    %% Conditional routing based on errors
    Executor -->|Error| FallbackHandler[Fallback Handler]
    Executor -->|Success| ResponseGenerator
    
    FallbackHandler --> Logger[Logger]
    ResponseGenerator --> CacheUpdate[Cache Update]
    CacheUpdate --> Logger
    Logger --> END((END))
    
    %% Styling
    classDef start fill:#6ADA6A,stroke:#324B4C,color:white;
    classDef end fill:#FF6961,stroke:#324B4C,color:white;
    classDef process fill:#9DC3E6,stroke:#324B4C,color:black;
    classDef decision fill:#FFD966,stroke:#324B4C,color:black;
    
    class START start;
    class END end;
    class UserContextNode,SchemaRetriever,SQLGenerator,QueryValidator,DBAGuard,Executor,ResponseGenerator,FallbackHandler,Logger,CacheUpdate process;
    class CacheCheck,IntentRouter decision;
```

## Descrição do Fluxo LangGraph

O diagrama acima representa o fluxo completo do nosso sistema multi-agentes implementado com LangGraph. Aqui está uma explicação detalhada de cada componente:

### Nós do Grafo

1. **START**: Ponto de entrada do grafo.
2. **User Context Node**: Recupera e enriquece o contexto do usuário (RA, disciplina, etc.).
3. **Cache Check**: Verifica se há uma resposta em cache para a consulta.
4. **Intent Router**: Classifica a intenção da pergunta do usuário (notas, faltas, etc.).
5. **Schema Retriever**: Recupera o schema do banco de dados.
6. **SQL Generator**: Gera a consulta SQL com base na intenção e no schema.
7. **Query Validator**: Valida a consulta SQL quanto à correção e segurança.
8. **DBA Guard**: Otimiza a consulta SQL para performance.
9. **Executor**: Executa a consulta SQL no Supabase.
10. **Response Generator**: Converte os resultados da consulta em linguagem natural.
11. **Fallback Handler**: Lida com erros e fornece respostas alternativas.
12. **Cache Update**: Atualiza o cache com a nova resposta.
13. **Logger**: Registra a interação para análise.
14. **END**: Ponto de saída do grafo.

### Fluxo de Execução

1. O fluxo começa no nó **START** e passa para o **User Context Node**.
2. O **User Context Node** recupera o contexto do usuário e passa para o **Cache Check**.
3. O **Cache Check** verifica se há uma resposta em cache:
   - Se houver um hit no cache, vai direto para o **Response Generator**.
   - Se não houver cache, continua para o **Intent Router**.
4. O **Intent Router** classifica a intenção e passa para o **Schema Retriever**.
5. O **Schema Retriever** recupera o schema e passa para o **SQL Generator**.
6. O **SQL Generator** gera a consulta SQL e passa para o **Query Validator**.
7. O **Query Validator** valida a consulta e passa para o **DBA Guard**.
8. O **DBA Guard** otimiza a consulta e passa para o **Executor**.
9. O **Executor** executa a consulta e, dependendo do resultado:
   - Se houver erro, vai para o **Fallback Handler**.
   - Se for bem-sucedido, vai para o **Response Generator**.
10. O **Response Generator** gera a resposta em linguagem natural e passa para o **Cache Update**.
11. O **Cache Update** atualiza o cache e passa para o **Logger**.
12. O **Logger** registra a interação e finaliza no nó **END**.

Este fluxo garante que cada consulta seja processada de forma eficiente, com validação adequada, tratamento de erros e caching para melhorar o desempenho.
