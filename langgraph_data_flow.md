# Fluxo de Dados no Sistema Multi-Agentes Acadêmico

```mermaid
flowchart TD
    subgraph Input
        Query["Pergunta do Usuário\n'Quantas faltas eu tenho em\nTeoria da Computação?'"]
        Context["Contexto do Usuário\nRA: 201268\ndisciplina_id: 3e5e..."]
    end
    
    subgraph Processamento
        UserContext["User Context Agent\nAdiciona matricula, periodo_atual"]
        CacheCheck{"Cache Check\nVerifica cache"}
        IntentRouter["Intent Router\nClassifica como 'faltas'"]
        SchemaRetriever["Schema Retriever\nObtém estrutura do banco"]
        SQLGenerator["SQL Generator\nGera consulta SQL"]
        QueryValidator["Query Validator\nValida a consulta"]
        DBAGuard["DBA Guard\nOtimiza a consulta"]
        Executor["Executor\nExecuta a consulta"]
        FallbackHandler["Fallback Handler\nLida com erros"]
        ResponseGen["Response Generator\nGera resposta natural"]
        CacheUpdate["Cache Update\nAtualiza o cache"]
        Logger["Logger\nRegistra a interação"]
    end
    
    subgraph Output
        Response["Resposta Natural\n'Você tem 1 falta em Teoria da\nComputação, ocorrida em 10 de abril...'"]
    end
    
    Query & Context --> UserContext
    UserContext --> CacheCheck
    
    CacheCheck -->|Cache Miss| IntentRouter
    CacheCheck -->|Cache Hit| ResponseGen
    
    IntentRouter --> SchemaRetriever
    SchemaRetriever --> SQLGenerator
    
    SQLGenerator -->|"SELECT a.data, p.presente\nFROM aulas a\nJOIN presencas p..."| QueryValidator
    
    QueryValidator --> DBAGuard
    DBAGuard --> Executor
    
    Executor -->|Error| FallbackHandler
    Executor -->|"[{data: '2023-04-10', presente: false},\n{data: '2023-04-03', presente: true},...]"| ResponseGen
    
    FallbackHandler --> Logger
    ResponseGen --> Response
    ResponseGen --> CacheUpdate
    CacheUpdate --> Logger
    
    classDef default fill:#f9f9f9,stroke:#333,stroke-width:1px;
    classDef input fill:#d5e8d4,stroke:#82b366,stroke-width:1px;
    classDef output fill:#dae8fc,stroke:#6c8ebf,stroke-width:1px;
    classDef decision fill:#ffe6cc,stroke:#d79b00,stroke-width:1px;
    
    class Query,Context input;
    class Response output;
    class CacheCheck decision;
```

## Transformações de Dados em Cada Etapa

1. **Entrada**:
   - Pergunta do usuário: "Quantas faltas eu tenho em Teoria da Computação?"
   - Contexto do usuário: RA, disciplina_id, nome_disciplina

2. **User Context Agent**:
   - Adiciona: matricula (mapeada do RA), periodo_atual
   - Estado: `{user_query, user_id, user_context{RA, disciplina_id, matricula, periodo_atual}}`

3. **Cache Check**:
   - Verifica se há resposta em cache para esta consulta
   - Se hit: pula para Response Generator
   - Se miss: continua o fluxo

4. **Intent Router**:
   - Classifica a intenção como "faltas"
   - Adiciona: `{intent: "faltas", confidence: 0.95}`

5. **Schema Retriever**:
   - Obtém estrutura do banco de dados
   - Adiciona: `{schema_info: {tables: [...]}}`

6. **SQL Generator**:
   - Gera a consulta SQL
   - Adiciona: `{generated_sql: "SELECT a.data, p.presente FROM aulas a JOIN presencas p..."}`

7. **Query Validator**:
   - Valida a consulta SQL
   - Adiciona: `{validation_results: [...]}`

8. **DBA Guard**:
   - Otimiza a consulta (adiciona LIMIT, etc.)
   - Atualiza: `{generated_sql: "SELECT a.data, p.presente ... LIMIT 100"}`

9. **Executor**:
   - Executa a consulta no Supabase
   - Adiciona: `{query_results: [{data: "2023-04-10", presente: false}, ...]}`

10. **Response Generator**:
    - Converte resultados em linguagem natural
    - Adiciona: `{natural_response: "Você tem 1 falta em Teoria da Computação..."}`

11. **Cache Update**:
    - Armazena a resposta em cache
    - Não modifica o estado

12. **Logger**:
    - Registra a interação
    - Não modifica o estado

13. **Saída**:
    - Resposta natural para o usuário
