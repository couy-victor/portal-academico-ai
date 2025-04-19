# Diagrama de Fluxo LangGraph - Sistema Multi-Agentes Acadêmico

```mermaid
flowchart TD
    START([START]) --> UserContext[User Context Node]
    UserContext --> CacheCheck{Cache Check}
    
    CacheCheck -->|Cache Miss| IntentRouter[Intent Router]
    CacheCheck -->|Cache Hit| ResponseGen[Response Generator]
    
    IntentRouter --> SchemaRetriever[Schema Retriever]
    SchemaRetriever --> SQLGenerator[SQL Generator]
    SQLGenerator --> QueryValidator[Query Validator]
    QueryValidator --> DBAGuard[DBA Guard]
    DBAGuard --> Executor[Executor]
    
    Executor -->|Error| FallbackHandler[Fallback Handler]
    Executor -->|Success| ResponseGen
    
    FallbackHandler --> Logger[Logger]
    ResponseGen --> CacheUpdate[Cache Update]
    CacheUpdate --> Logger
    Logger --> END([END])
    
    %% Descrições dos nós
    classDef default fill:#f9f9f9,stroke:#333,stroke-width:1px;
    classDef decision fill:#ffe6cc,stroke:#d79b00,stroke-width:1px;
    classDef start fill:#d5e8d4,stroke:#82b366,stroke-width:1px;
    classDef end fill:#f8cecc,stroke:#b85450,stroke-width:1px;
    
    class CacheCheck decision;
    class START,END start,end;
```

## Descrição dos Componentes

1. **User Context Node**: Recupera e enriquece o contexto do usuário (RA, disciplina, etc.)
2. **Cache Check**: Verifica se há uma resposta em cache para a consulta
3. **Intent Router**: Classifica a intenção da pergunta do usuário
4. **Schema Retriever**: Recupera o schema do banco de dados
5. **SQL Generator**: Gera a consulta SQL com base na intenção e no schema
6. **Query Validator**: Valida a consulta SQL quanto à correção e segurança
7. **DBA Guard**: Otimiza a consulta SQL para performance
8. **Executor**: Executa a consulta SQL no Supabase
9. **Fallback Handler**: Lida com erros e fornece respostas alternativas
10. **Response Generator**: Converte os resultados da consulta em linguagem natural
11. **Cache Update**: Atualiza o cache com a nova resposta
12. **Logger**: Registra a interação para análise
