# Sistema Multi-Agentes Acadêmico com LangGraph

Este projeto implementa um sistema multi-agentes usando LangGraph para responder perguntas sobre dados acadêmicos armazenados no Supabase, fornecer apoio emocional, tutoria e planejamento acadêmico.

## Arquitetura

O sistema utiliza uma arquitetura de multi-agentes organizada em subgrafos especializados:

### Roteamento Principal
1. **Agente de Contexto do Usuário**: Recupera e enriquece o contexto do usuário
2. **Agente de Cache**: Verifica se há respostas em cache para a consulta
3. **Agente de Roteamento Principal**: Classifica a consulta em uma das categorias principais (acadêmica, emocional, tutoria, planejamento)

### Subgrafo Acadêmico
1. **Agente de Roteamento Acadêmico**: Classifica a intenção da pergunta acadêmica
2. **Agente de Schema**: Recupera informações do schema do banco de dados
3. **Agente Gerador de SQL**: Gera consultas SQL com base na intenção e schema
4. **Agente Validador**: Valida as consultas SQL quanto à correção e segurança
5. **Agente DBA Guard**: Otimiza as consultas para performance
6. **Agente Executor**: Executa as consultas no Supabase

### Subgrafo de Apoio Emocional
1. **Detector de Estado Emocional**: Identifica o estado emocional e necessidade do aluno
2. **Gerador de Estratégias**: Sugere técnicas específicas para o problema identificado
3. **Recomendador de Recursos**: Oferece recursos sobre bem-estar mental

### Subgrafo de Tutoria
1. **Classificador de Matéria/Tópico**: Identifica o assunto específico da dúvida
2. **Gerador de Explicações**: Cria explicações personalizadas sobre o tópico
3. **Gerador de Exemplos**: Fornece exemplos práticos e exercícios

### Subgrafo de Planejamento Acadêmico
1. **Analisador de Objetivos**: Identifica os objetivos de planejamento do estudante
2. **Gerador de Tarefas**: Cria um plano de estudo com tarefas específicas
3. **Recomendador de Recursos**: Sugere ferramentas e técnicas de planejamento

### Componentes Comuns
1. **Agente RAG**: Recupera informações de documentos PDF
2. **Agente Tavily**: Busca informações na web
3. **Agente de Resposta Aumentada**: Combina informações de várias fontes
4. **Agente de Fallback**: Lida com erros e fornece respostas alternativas
5. **Agente de Logging**: Registra interações para análise e rastreamento

## Fluxo de Processamento

### Fluxo Geral
1. O usuário faz uma pergunta
2. O sistema enriquece o contexto do usuário (RA, curso, período atual)
3. Verifica se há uma resposta em cache
4. Classifica a categoria principal da pergunta (acadêmica, emocional, tutoria, planejamento)
5. Encaminha para o subgrafo especializado apropriado
6. Processa a pergunta no subgrafo especializado
7. Gera uma resposta natural
8. Armazena a resposta em cache para uso futuro
9. Registra a interação para análise

### Exemplo de Fluxo Acadêmico
1. Pergunta: "Quantas faltas tenho em Anatomia?"
2. Classificação: Categoria acadêmica > Intenção "faltas"
3. Recuperação de informações do schema
4. Geração de consulta SQL
5. Validação e otimização da consulta
6. Execução no Supabase
7. Conversão dos resultados em linguagem natural

### Exemplo de Fluxo Emocional
1. Pergunta: "Estou muito ansioso com a prova de amanhã"
2. Classificação: Categoria emocional > Estado "ansiedade"
3. Detecção do problema específico e severidade
4. Geração de estratégias para lidar com ansiedade de provas
5. Recomendação de recursos de apoio
6. Geração de resposta empática e acolhedora

## Configuração

1. Clone o repositório
2. Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```
OPENAI_API_KEY=sua_chave_api_openai
SUPABASE_URL=sua_url_supabase
SUPABASE_KEY=sua_chave_supabase
LANGSMITH_API_KEY=sua_chave_api_langsmith (opcional)
TAVILY_API_KEY=sua_chave_api_tavily
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

## Uso

### Como biblioteca

```python
from src.main import process_query

# Processar uma consulta
result = process_query(
    user_query="Quantas faltas eu tenho em Anatomia?",
    user_id="user_123",
    user_context={
        "periodo_atual": "2023.2",
        "curso_id": "MED2020"
    }
)

# Exibir a resposta
print(result["response"])
```

### Como CLI

```bash
python src/main.py --query "Quantas faltas eu tenho em Anatomia?" --user_id "user_123" --context '{"periodo_atual": "2023.2", "curso_id": "MED2020"}'
```

### Testes

#### Teste Interativo

Execute o script de teste interativo para conversar com o sistema:

```bash
python tests/interactive_test.py
```

Este script permite:
- Fazer perguntas ao sistema
- Configurar o contexto do usuário
- Ver o histórico de conversas

#### Teste com RA Específico

Execute o script de teste com RA específico:

```bash
python tests/test_ra_specific.py
```

Este script testa o sistema com um RA e disciplina específicos, verificando:
- Classificação de intenção
- Geração de SQL
- Processo completo

## Estrutura do Projeto

```
src/
├── agents/              # Agentes especializados
│   ├── cache_agent.py
│   ├── dba_guard_agent.py
│   ├── emotional_support_agent.py
│   ├── executor_agent.py
│   ├── fallback_agent.py
│   ├── logger_agent.py
│   ├── main_router_agent.py
│   ├── planning_agent.py
│   ├── rag_agent.py
│   ├── response_agent.py
│   ├── router_agent.py
│   ├── schema_agent.py
│   ├── sql_generator_agent.py
│   ├── tavily_agent.py
│   ├── tutor_agent.py
│   ├── user_context_agent.py
│   └── validator_agent.py
├── config/              # Configurações
│   └── settings.py
├── database/            # Integração com banco de dados
│   └── supabase_client.py
├── graph/               # Definição do grafo LangGraph
│   └── academic_graph.py
├── models/              # Modelos de dados
│   └── state.py
├── utils/               # Utilitários
│   ├── cache.py
│   └── logging.py
├── interactive_test.py  # Teste interativo
├── simple_test.py      # Teste para agentes especializados
└── main.py              # Ponto de entrada principal

docs/
└── DOCUMENTACAO_SISTEMA.md  # Documentação detalhada do sistema

test_ra_specific.py  # Teste com RA específico
```

## Requisitos do Supabase

Este sistema requer as seguintes funções RPC no Supabase:

1. `get_schema_info()`: Retorna informações sobre o schema do banco de dados
2. `get_user_context(user_id)`: Retorna o contexto do usuário
3. `execute_secured_query(query_text, params, user_id)`: Executa consultas SQL de forma segura

Os scripts SQL para criar essas funções estão disponíveis na [documentação detalhada](docs/DOCUMENTACAO_SISTEMA.md).

## Documentação Detalhada

Para uma documentação completa e detalhada do sistema, incluindo:

- Arquitetura detalhada
- Componentes principais
- Funções RPC do Supabase (com código SQL completo)
- Sistema de cache
- Fluxo de processamento de consultas
- Configuração e implantação

Consulte o arquivo [docs/DOCUMENTACAO_SISTEMA.md](docs/DOCUMENTACAO_SISTEMA.md).

## Contribuição

Contribuições são bem-vindas! Por favor, abra uma issue para discutir mudanças importantes antes de enviar um pull request.

## Licença

Este projeto está licenciado sob a licença MIT.

## Autor

Victor Aarão Lemes - Trabalho de Conclusão de Curso

