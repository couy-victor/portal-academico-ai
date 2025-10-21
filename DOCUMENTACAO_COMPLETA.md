# Documentação Completa do Sistema Portal Acadêmico AI

## Sumário

1. [Introdução](#introdução)
2. [Arquitetura do Sistema](#arquitetura-do-sistema)
3. [Agentes Especializados](#agentes-especializados)
   - [Agente Acadêmico](#agente-acadêmico)
   - [Agente de Suporte Emocional](#agente-de-suporte-emocional)
   - [Agente Tutor](#agente-tutor)
   - [Agente de Planejamento Acadêmico](#agente-de-planejamento-acadêmico)
   - [Agente Financeiro](#agente-financeiro)
4. [Componentes Comuns](#componentes-comuns)
   - [Sistema de Cache](#sistema-de-cache)
   - [Integração com Supabase](#integração-com-supabase)
   - [Recuperação de Informações (RAG)](#recuperação-de-informações-rag)
   - [Busca na Web (Tavily)](#busca-na-web-tavily)
5. [Interfaces de Usuário](#interfaces-de-usuário)
   - [Interface Streamlit](#interface-streamlit)
   - [Interface Next.js](#interface-nextjs)
6. [Configuração e Implantação](#configuração-e-implantação)
7. [Testes e Depuração](#testes-e-depuração)
8. [Recursos Adicionais](#recursos-adicionais)

## Introdução

O Portal Acadêmico AI é um sistema multi-agentes desenvolvido para fornecer suporte acadêmico abrangente aos estudantes. Utilizando a arquitetura LangGraph e modelos de linguagem avançados, o sistema oferece diversas funcionalidades:

- **Consultas Acadêmicas**: Acesso a informações sobre notas, faltas, disciplinas e professores
- **Suporte Emocional**: Ajuda com ansiedade, estresse e outros desafios emocionais
- **Tutoria Educacional**: Explicações sobre conteúdos acadêmicos específicos
- **Planejamento Acadêmico**: Assistência na organização de estudos e definição de metas
- **Suporte Financeiro**: Consulta e geração de boletos, informações sobre mensalidades

O sistema utiliza uma arquitetura de agentes especializados que trabalham em conjunto para processar consultas dos usuários e fornecer respostas personalizadas e contextualizadas.

## Arquitetura do Sistema

O Portal Acadêmico AI utiliza uma arquitetura de multi-agentes baseada em LangGraph, organizando os agentes em um grafo de processamento com nós especializados.

### Fluxo Principal

1. **Entrada da Consulta**: O usuário faz uma pergunta através da interface (Streamlit ou Next.js)
2. **Enriquecimento de Contexto**: O sistema recupera informações contextuais do usuário (RA, curso, período)
3. **Verificação de Cache**: Verifica se há uma resposta em cache para a consulta
4. **Roteamento Principal**: Classifica a consulta em uma das categorias principais:
   - Acadêmica (notas, faltas, disciplinas)
   - Emocional (ansiedade, estresse)
   - Tutoria (explicações sobre conteúdos)
   - Planejamento (organização de estudos)
   - Financeira (boletos, mensalidades)
5. **Processamento Especializado**: Encaminha a consulta para o subgrafo especializado apropriado
6. **Geração de Resposta**: Gera uma resposta natural e contextualizada
7. **Armazenamento em Cache**: Armazena a resposta para uso futuro
8. **Registro**: Registra a interação para análise

### Diagrama de Fluxo

```
[Consulta do Usuário] → [Contexto do Usuário] → [Verificação de Cache] → [Roteador Principal]
                                                                            ↓
                      ┌─────────────────┬───────────────────┬──────────────┬───────────────┐
                      ↓                 ↓                   ↓              ↓               ↓
              [Agente Acadêmico] [Agente Emocional] [Agente Tutor] [Agente Planejamento] [Agente Financeiro]
                      ↓                 ↓                   ↓              ↓               ↓
                      └─────────────────┴───────────────────┴──────────────┴───────────────┘
                                                            ↓
                                                [Geração de Resposta] → [Cache] → [Logging]
```

## Agentes Especializados

### Agente Acadêmico

O Agente Acadêmico é responsável por processar consultas relacionadas a informações acadêmicas estruturadas, como notas, faltas, disciplinas e professores.

#### Componentes Principais

1. **Roteador de Intenção**: Classifica a intenção específica da consulta acadêmica
2. **Agente de Schema**: Recupera informações sobre o schema do banco de dados
3. **Gerador de SQL**: Gera consultas SQL com base na intenção e schema
4. **Validador**: Valida as consultas SQL quanto à correção e segurança
5. **DBA Guard**: Otimiza as consultas para performance
6. **Executor**: Executa as consultas no Supabase

#### Fluxo de Processamento

1. Classificação da intenção específica (notas, faltas, disciplinas)
2. Recuperação do schema relevante do banco de dados
3. Geração da consulta SQL apropriada
4. Validação e otimização da consulta
5. Execução no banco de dados
6. Formatação dos resultados em linguagem natural

#### Exemplo de Uso

```
Consulta: "Quantas faltas tenho em Anatomia?"

Fluxo:
1. Classificação: Intenção "faltas"
2. Schema: Tabelas de faltas, disciplinas e alunos
3. SQL: SELECT COUNT(*) FROM faltas WHERE aluno_id = ? AND disciplina_id = (SELECT id FROM disciplinas WHERE nome LIKE '%Anatomia%')
4. Validação e otimização
5. Execução no Supabase
6. Resposta: "Você tem 3 faltas em Anatomia no período atual."
```

### Agente de Suporte Emocional

O Agente de Suporte Emocional é responsável por fornecer apoio a estudantes lidando com desafios emocionais como ansiedade, estresse e burnout acadêmico.

#### Frameworks Metodológicos

1. **CARE AI Framework**:
   - **Controlabilidade**: Garantindo que o usuário mantenha controle sobre a interação
   - **Prestação de contas**: Documentando decisões e recomendações do sistema
   - **Responsabilidade**: Priorizando o bem-estar do usuário
   - **Explicabilidade**: Fornecendo justificativas claras para estratégias recomendadas

2. **Empathy Loop**:
   - **Reconhecer**: Identificação do estado emocional e problema específico
   - **Refletir**: Análise da severidade e geração de estratégias
   - **Responder**: Fornecimento de resposta empática e recursos
   - **Reavaliar**: Verificação contínua da adequação da resposta

3. **HITES (Human-in-the-loop Empathetic System)**:
   - Sistema que garante intervenção humana em casos de alta severidade
   - Recomenda explicitamente contato com profissionais quando necessário
   - Mantém registro de quando intervenção humana foi recomendada
   - Implementa protocolos específicos para situações de crise

#### Componentes Principais

1. **Detector de Estado Emocional**: Identifica o estado emocional e a severidade do problema
2. **Detector de Mensagens de Alto Risco**: Identifica automaticamente mensagens relacionadas a ideação suicida ou automutilação
3. **Gerador de Estratégias**: Sugere técnicas específicas para o problema identificado
4. **Recomendador de Recursos**: Oferece recursos sobre bem-estar mental
5. **Gerador de Resposta Empática**: Cria respostas acolhedoras e empáticas

#### Fluxo de Processamento

1. Detecção do estado emocional e severidade
2. Verificação de mensagens de alto risco
3. Geração de estratégias personalizadas
4. Recomendação de recursos relevantes
5. Geração de resposta empática
6. Recomendação de intervenção humana quando necessário

#### Exemplo de Uso

```
Consulta: "Estou muito ansioso com a prova de amanhã"

Fluxo:
1. Detecção: Estado "ansiedade", Problema "ansiedade relacionada a provas", Severidade "média"
2. Estratégias: Técnicas de respiração, visualização positiva, preparação estruturada
3. Recursos: Aplicativo de meditação, guia de técnicas anti-ansiedade, contato do NAP
4. Resposta: Mensagem empática com estratégias práticas e recursos de apoio
```

### Agente Tutor

O Agente Tutor é responsável por fornecer explicações educacionais sobre conteúdos acadêmicos específicos, adaptando o nível de explicação ao conhecimento prévio do estudante.

#### Componentes Principais

1. **Classificador de Matéria/Tópico**: Identifica o assunto específico da dúvida
2. **Avaliador de Conhecimento Prévio**: Estima o nível de familiaridade do estudante com o tópico
3. **Gerador de Explicações Multinível**: Cria explicações em diferentes níveis de complexidade
4. **Conector de Conhecimentos**: Relaciona o tópico com conceitos que o estudante já conhece
5. **Gerador de Exemplos**: Fornece exemplos práticos e exercícios
6. **Gerador de Perguntas Socráticas**: Cria perguntas que estimulam o pensamento crítico

#### Abordagens Pedagógicas

1. **Tutoria Adaptativa**: Ajusta o nível de explicação ao conhecimento prévio do estudante
2. **Método Socrático**: Utiliza perguntas para guiar o estudante na descoberta do conhecimento
3. **Conexão de Conhecimentos**: Relaciona novos conceitos com conhecimentos prévios
4. **Aprendizagem Ativa**: Fornece exemplos e exercícios práticos para fixação

#### Fluxo de Processamento

1. Classificação do assunto e tópico específico
2. Avaliação do conhecimento prévio do estudante
3. Identificação de conceitos relacionados
4. Criação de mapa conceitual
5. Geração de explicação adaptada ao nível do estudante
6. Geração de exemplos e exercícios práticos
7. Criação de perguntas socráticas para reflexão
8. Geração de resposta tutorial completa

#### Exemplo de Uso

```
Consulta: "O que é uma máquina de Turing?"

Fluxo:
1. Classificação: Matéria "Ciência da Computação", Tópico "Máquina de Turing", Complexidade "intermediário"
2. Conhecimento prévio: Avaliação de familiaridade com conceitos de computação teórica
3. Conceitos relacionados: Autômatos finitos, computabilidade, problema da parada
4. Explicação: Definição adaptada ao nível do estudante, com analogias e exemplos
5. Exemplos: Máquina de Turing para reconhecer palíndromos
6. Exercícios: "Descreva uma máquina de Turing que aceita a linguagem a^nb^n"
7. Perguntas socráticas: "Como a máquina de Turing se relaciona com os computadores modernos?"
```

### Agente de Planejamento Acadêmico

O Agente de Planejamento Acadêmico é responsável por ajudar estudantes a planejar seus estudos, definir metas e gerenciar seu tempo, utilizando métodos baseados em evidências científicas.

#### Métodos de Estudo Implementados

1. **Método Pomodoro**:
   - Divide o tempo de estudo em blocos focados (geralmente 25 minutos)
   - Intercala com pausas curtas (5 minutos) e pausas longas (15-30 minutos)
   - Ajuda a manter o foco e evitar a fadiga mental

2. **Active Recall (Recuperação Ativa)**:
   - Baseado em testar ativamente o conhecimento em vez de apenas revisar
   - Utiliza flashcards, quizzes e auto-questionamento
   - Comprovadamente mais eficaz para retenção de longo prazo

3. **Time Blocking (Blocos de Tempo)**:
   - Aloca blocos específicos de tempo para diferentes tarefas/disciplinas
   - Prioriza conteúdos mais difíceis nos horários de pico cognitivo
   - Melhora a gestão do tempo e reduz a procrastinação

#### Componentes Principais

1. **Analisador de Objetivos**: Identifica o objetivo de planejamento do estudante
2. **Gerador de Tarefas**: Cria um plano de estudo com tarefas específicas
3. **Recomendador de Recursos**: Sugere ferramentas e técnicas de planejamento
4. **Gerador de Visualizações**: Cria representações visuais do plano (timeline, calendário)
5. **Exportador de Plano**: Permite exportar o plano em diferentes formatos (PDF, ICS)

#### Fluxo de Processamento

1. Análise do objetivo de planejamento e período de tempo
2. Identificação do método de estudo mais adequado
3. Geração de tarefas específicas baseadas no método escolhido
4. Recomendação de recursos complementares
5. Geração de resposta formatada em markdown
6. Criação de visualizações e opções de exportação

#### Exemplo de Uso

```
Consulta: "Preciso organizar meus estudos para as provas finais que começam em duas semanas"

Fluxo:
1. Análise: Objetivo "preparação para provas finais", Período "médio prazo (duas semanas)"
2. Método: Pomodoro (25 minutos de foco, 5 minutos de pausa)
3. Tarefas: Cronograma detalhado com sessões de estudo para cada disciplina
4. Recursos: Aplicativo de temporizador Pomodoro, técnicas de revisão espaçada
5. Resposta: Plano de estudos formatado com cronograma, tarefas e dicas
6. Exportação: Opções para baixar como PDF ou importar para calendário
```

### Agente Financeiro

O Agente Financeiro é responsável por processar consultas relacionadas a questões financeiras, como boletos, mensalidades e situação financeira do aluno.

#### Componentes Principais

1. **Classificador de Intenção Financeira**: Identifica o tipo específico de consulta financeira
2. **Gerador de Boletos**: Cria PDFs de boletos para visualização e download
3. **Consultor de Situação Financeira**: Verifica a situação de pagamentos do aluno
4. **Gerador de Respostas Financeiras**: Cria respostas claras sobre questões financeiras

#### Fluxo de Processamento

1. Classificação da intenção financeira espec��fica
2. Consulta ao banco de dados financeiro
3. Geração de documentos financeiros quando necessário
4. Formatação da resposta com informações financeiras
5. Disponibilização de boletos para download quando solicitado

#### Exemplo de Uso

```
Consulta: "Quero ver meus boletos pendentes"

Fluxo:
1. Classificação: Intenção "consulta de boletos pendentes"
2. Consulta: Verificação de boletos pendentes no banco de dados
3. Geração: Criação de PDFs para os boletos pendentes
4. Resposta: Informações sobre os boletos pendentes e opções de download
5. Interface: Exibição de botões para download dos PDFs dos boletos
```

## Componentes Comuns

### Sistema de Cache

O sistema implementa um mecanismo de cache para armazenar respostas a consultas frequentes, reduzindo o tempo de resposta e o consumo de recursos.

#### Características

- **Armazenamento**: Utiliza SQLite para persistência dos dados de cache
- **TTL (Time-to-Live)**: Configurável para definir o tempo de validade das entradas
- **Chave de Cache**: Baseada no hash da consulta e do contexto do usuário
- **Invalidação Seletiva**: Permite limpar entradas específicas ou todo o cache

#### Configuração

```python
# Configurações de cache em settings.py
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "True").lower() == "true"
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # Default: 1 hora
CACHE_DIR = os.getenv("CACHE_DIR", "./cache")
```

### Integração com Supabase

O sistema utiliza o Supabase como banco de dados principal para armazenar e recuperar informações acadêmicas.

#### Funcionalidades

- **Autenticação**: Gerenciamento de usuários e autenticação
- **Armazenamento de Dados**: Informações acadêmicas, financeiras e de usuários
- **Funções RPC**: Execução segura de consultas SQL através de funções RPC
- **Storage**: Armazenamento de documentos e arquivos

#### Funções RPC Principais

1. **get_schema_info()**: Retorna informações sobre o schema do banco de dados
2. **get_user_context(user_id)**: Retorna o contexto do usuário
3. **execute_secured_query(query_text, params, user_id)**: Executa consultas SQL de forma segura

### Recuperação de Informações (RAG)

O sistema implementa Retrieval-Augmented Generation (RAG) para enriquecer as respostas com informações de documentos PDF e outras fontes estruturadas.

#### Componentes

1. **Processador de PDF**: Extrai e processa texto de documentos PDF
2. **Embeddings**: Gera embeddings para chunks de texto usando modelos de linguagem
3. **Índice Vetorial**: Armazena embeddings para busca por similaridade
4. **BM25**: Implementa busca por palavras-chave usando o algoritmo BM25
5. **Busca Híbrida**: Combina busca vetorial e BM25 para melhores resultados

#### Configuração

```python
# Configurações de RAG em settings.py
PDF_STORAGE_DIR = os.getenv("PDF_STORAGE_DIR", "./data/pdfs")
EMBEDDINGS_DIR = os.getenv("EMBEDDINGS_DIR", "./data/embeddings")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
RAG_STORAGE_TYPE = os.getenv("RAG_STORAGE_TYPE", "supabase")  # "local" ou "supabase"

# Configurações de BM25
USE_BM25 = os.getenv("USE_BM25", "True").lower() == "true"
HYBRID_ALPHA = float(os.getenv("HYBRID_ALPHA", "0.5"))  # Peso para embeddings vs BM25
BM25_K1 = float(os.getenv("BM25_K1", "1.5"))  # Parâmetro k1 do BM25
BM25_B = float(os.getenv("BM25_B", "0.75"))  # Parâmetro b do BM25
```

### Busca na Web (Tavily)

O sistema integra a API Tavily para realizar buscas na web e enriquecer as respostas com informações atualizadas.

#### Características

- **Busca Contextual**: Realiza buscas na web com base no contexto da consulta
- **Filtragem de Resultados**: Seleciona as informações mais relevantes
- **Integração com RAG**: Combina resultados da web com informações locais
- **Citação de Fontes**: Inclui referências às fontes consultadas

#### Configuração

```python
# Configurações de Tavily em settings.py
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
TAVILY_MAX_RESULTS = int(os.getenv("TAVILY_MAX_RESULTS", "5"))
TAVILY_SEARCH_DEPTH = os.getenv("TAVILY_SEARCH_DEPTH", "basic")
```

## Interfaces de Usuário

### Interface Streamlit

O sistema oferece uma interface baseada em Streamlit para interação via navegador web.

#### Características

- **Chat Interativo**: Interface de chat para interação com os agentes
- **Seleção de Agente**: Permite escolher o tipo de agente para consulta
- **Configuração de Contexto**: Campos para definir RA e outras informações do usuário
- **Visualização de Documentos**: Exibição de PDFs e outros documentos
- **Exportação de Planos**: Opções para exportar planos de estudo em diferentes formatos

#### Componentes da Interface

1. **Barra Lateral**: Configurações do usuário e seleção de agente
2. **Área de Chat**: Histórico de mensagens e campo de entrada
3. **Área de Visualização**: Exibição de documentos, planos e visualizações
4. **Botões de Exemplo**: Sugestões de consultas para cada tipo de agente

### Interface Next.js

O sistema também oferece uma interface moderna baseada em Next.js e React.

#### Características

- **Design Responsivo**: Adaptação a diferentes tamanhos de tela
- **Tema Claro/Escuro**: Suporte a diferentes temas de interface
- **Componentes Reutilizáveis**: Estrutura modular com componentes React
- **Roteamento Dinâmico**: Navegação entre diferentes seções da aplicação
- **API Routes**: Endpoints para comunicação com o backend

#### Tecnologias Utilizadas

- **Next.js**: Framework React para renderização do lado do servidor
- **Tailwind CSS**: Framework CSS para estilização
- **Radix UI**: Componentes acessíveis e customizáveis
- **TypeScript**: Tipagem estática para maior segurança e produtividade

## Configuração e Implantação

### Requisitos do Sistema

- **Python**: 3.9 ou superior
- **Node.js**: 16.x ou superior (para a interface Next.js)
- **Supabase**: Conta e projeto configurado
- **OpenAI API**: Chave de API válida
- **Tavily API**: Chave de API válida (opcional)

### Variáveis de Ambiente

O sistema utiliza um arquivo `.env` para configuração. Exemplo:

```
OPENAI_API_KEY=sua_chave_api_openai
SUPABASE_URL=sua_url_supabase
SUPABASE_KEY=sua_chave_supabase
LANGSMITH_API_KEY=sua_chave_api_langsmith (opcional)
TAVILY_API_KEY=sua_chave_api_tavily (opcional)
LLM_MODEL=gpt-4o
LLM_TEMPERATURE=0.1
LLM_TEMPERATURE_CREATIVE=0.7
CACHE_ENABLED=True
CACHE_TTL=3600
```

### Instalação

1. Clone o repositório
2. Crie e ative um ambiente virtual Python
3. Instale as dependências Python: `pip install -r requirements.txt`
4. Configure o arquivo `.env` com suas credenciais
5. Para a interface Next.js:
   - Navegue até a pasta `frontend-new`
   - Instale as dependências: `npm install`
   - Execute o servidor de desenvolvimento: `npm run dev`

### Execução

- **Interface Streamlit**: `streamlit run Chatbot.py`
- **Interface Next.js**: `cd frontend-new && npm run dev`
- **CLI**: `python src/main.py --query "Sua consulta" --user_id "user_123" --context '{"periodo_atual": "2023.2"}'`
- **Teste Interativo**: `python tests/interactive_test.py`

## Testes e Depuração

### Scripts de Teste

O sistema inclui diversos scripts para testar diferentes componentes:

- **interactive_test.py**: Teste interativo via linha de comando
- **simple_test.py**: Teste simples para agentes específicos
- **test_academic_query.py**: Teste para consultas acadêmicas
- **test_planning.py**: Teste para o agente de planejamento
- **test_ra_specific.py**: Teste com RA específico
- **test_rag.py**: Teste para o sistema RAG
- **test_tavily.py**: Teste para integração com Tavily

### Depuração

- **Logs**: O sistema utiliza logging estruturado para rastreamento de operações
- **Tracing**: Integração opcional com LangSmith para visualização de traces
- **Modo de Depuração**: Opção para exibir informações detalhadas durante a execução

## Recursos Adicionais

### Geração de Boletos

O sistema inclui funcionalidade para gerar boletos fictícios para demonstração:

- **Gerador de Boletos**: Cria PDFs de boletos com dados fictícios
- **Visualização de Boletos**: Interface para visualizar boletos gerados
- **Download de Boletos**: Opção para baixar boletos em formato PDF

### Exportação de Planos de Estudo

O agente de planejamento oferece opções para exportar planos de estudo:

- **Exportação para PDF**: Gera um documento PDF com o plano de estudos
- **Exportação para ICS**: Cria um arquivo de calendário para importação em aplicativos
- **Visualização de Timeline**: Representação visual do cronograma de estudos

### Integração com Calendário

O sistema permite integrar planos de estudo com aplicativos de calendário:

- **Formato ICS**: Padrão universal para eventos de calendário
- **Google Calendar**: Importação direta para o Google Calendar
- **Outlook**: Compatibilidade com Microsoft Outlook
- **Apple Calendar**: Compatibilidade com calendários Apple

---

## Conclusão

O Portal Acadêmico AI é um sistema abrangente que utiliza inteligência artificial para fornecer suporte acadêmico, emocional, tutorial e de planejamento aos estudantes. Através de sua arquitetura de multi-agentes e integração com diversas tecnologias, o sistema oferece uma experiência personalizada e contextualizada, ajudando os estudantes a terem sucesso em sua jornada acadêmica.

Para mais informações ou suporte, entre em contato com a equipe de desenvolvimento.

---

Documentação criada em: 30/05/2024