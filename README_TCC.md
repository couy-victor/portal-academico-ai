# Sistema Multi-Agentes para Portal Acadêmico com LangGraph

## Visão Geral

Este projeto implementa um sistema multi-agentes utilizando LangGraph para criar um assistente acadêmico inteligente capaz de responder consultas sobre dados acadêmicos, fornecer suporte emocional, tutoria e planejamento acadêmico. O sistema integra múltiplas fontes de informação, incluindo banco de dados Supabase, documentos institucionais (via RAG - Retrieval Augmented Generation) e informações da web (via Tavily Search API).

## Arquitetura do Sistema

O sistema é construído com uma arquitetura de agentes especializados organizados em um grafo de fluxo de trabalho, onde cada agente é responsável por uma tarefa específica. Esta abordagem modular permite:

1. **Especialização**: Cada agente é otimizado para uma função específica
2. **Flexibilidade**: Novos agentes podem ser adicionados ou modificados sem afetar o sistema como um todo
3. **Robustez**: Falhas em um agente não comprometem todo o sistema
4. **Manutenibilidade**: Componentes podem ser testados e atualizados independentemente

### Diagrama de Fluxo Principal

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                                 Fluxo Principal                                    │
│                                                                                    │
│  ┌─────────────┐    ┌─────────────┐    ┌──────────────┐                           │
│  │   Contexto  │    │    Cache    │    │   Roteador   │                           │
│  │  do Usuário │───▶│    Check    │───▶│   Principal  │                           │
│  └─────────────┘    └─────────────┘    └──────────────┘                           │
│                                                │                                   │
│                                                ▼                                   │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                                                                             │  │
│  │  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐     │  │
│  │  │   Agente    │   │   Agente    │   │   Agente    │   │  Roteador   │     │  │
│  │  │  Emocional  │   │  de Tutoria │   │    de       │   │ de Intenção │     │  │
│  │  │             │   │             │   │ Planejamento│   │ Acadêmica   │     │  │
│  │  └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘     │  │
│  │        │                 │                 │                  │            │  │
│  │        │                 │                 │                  ▼            │  │
│  │        │                 │                 │           ┌─────────────┐     │  │
│  │        │                 │                 │           │  Validador  │     │  │
│  │        │                 │                 │           │     SQL     │     │  │
│  │        │                 │                 │           └─────────────┘     │  │
│  │        │                 │                 │                  │            │  │
│  │        │                 │                 │                  ▼            │  │
│  │        │                 │                 │           ┌─────────────┐     │  │
│  │        │                 │                 │           │  Executor   │     │  │
│  │        │                 │                 │           │     SQL     │     │  │
│  │        │                 │                 │           └─────────────┘     │  │
│  │        │                 │                 │                  │            │  │
│  │        ▼                 ▼                 ▼                  ▼            │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                        │                                           │
│                                        ▼                                           │
│  ┌─────────────┐    ┌─────────────┐    ┌──────────────┐                           │
│  │    Cache    │    │   Logger    │    │  Resposta    │                           │
│  │   Update    │◀───│             │◀───│   Final      │                           │
│  └─────────────┘    └─────────────┘    └──────────────┘                           │
│                                                                                    │
└───────────────────────────────────────────────────────────────────────────────────┘
```

## Componentes Principais

### 1. Agentes Especializados

#### Agentes de Roteamento e Contexto

- **Agente de Contexto do Usuário**: Recupera informações do usuário (RA, curso, período) do Supabase
- **Agente de Cache**: Verifica se a consulta já foi respondida anteriormente
- **Roteador Principal**: Analisa a consulta e direciona para o agente especializado apropriado (acadêmico, tutoria, suporte emocional, planejamento)
- **Agente de Roteamento Acadêmico**: Classifica a intenção da consulta acadêmica (notas, faltas, disciplinas, etc.)
- **Agente NL2SQL**: Converte consultas em linguagem natural para SQL usando um subgrafo de agentes:
  - **Search Engineer**: Recupera e formata o esquema do banco de dados
  - **SQL Writer**: Gera consultas SQL com base na intenção e esquema
  - **QA Engineer**: Valida as consultas SQL quanto à correção e segurança
  - **Chief DBA**: Otimiza as consultas para performance
- **Agente Executor**: Executa consultas SQL no Supabase de forma segura
- **Agente de Resposta Aumentada**: Gera respostas em linguagem natural combinando resultados do banco de dados, RAG e busca web

#### Agentes de Recuperação de Informações

- **Agente RAG (Retrieval Augmented Generation)**: Recupera informações relevantes de documentos institucionais
  - Utiliza embeddings e BM25 para busca híbrida
  - Suporta armazenamento local ou no Supabase
- **Agente Tavily**: Realiza buscas na web para complementar informações
  - Extrai consultas otimizadas para busca
  - Processa resultados para extrair informações relevantes

#### Agentes de Suporte Emocional

- **Detector de Estado Emocional**: Identifica o estado emocional e necessidade do aluno
- **Gerador de Estratégias**: Sugere técnicas específicas para o problema identificado
- **Recomendador de Recursos**: Oferece recursos sobre bem-estar mental

#### Agentes de Tutoria Acadêmica

- **Identificador de Matéria**: Detecta a disciplina e tópico específico da dúvida
- **Gerador de Explicações**: Cria explicações personalizadas sobre o conteúdo
- **Criador de Exemplos**: Fornece exemplos práticos e exercícios relacionados
- **Avaliador de Compreensão**: Avalia o nível de entendimento do aluno e adapta as explicações

#### Agentes de Planejamento Acadêmico

- **Analisador de Objetivos**: Identifica os objetivos acadêmicos do aluno
- **Criador de Cronogramas**: Desenvolve planos de estudo personalizados
- **Recomendador de Recursos**: Sugere materiais e ferramentas para otimizar os estudos
- **Monitor de Progresso**: Acompanha o progresso do aluno em relação aos objetivos

### 2. Integração com Banco de Dados (Supabase)

O sistema utiliza o Supabase como banco de dados principal, com funções RPC personalizadas para:

- **Recuperação de Esquema**: Obtém automaticamente o esquema do banco de dados
- **Execução Segura de SQL**: Executa consultas com proteção contra SQL injection
- **Armazenamento de Vetores**: Suporta armazenamento de embeddings para RAG

### 3. Sistema de RAG (Retrieval Augmented Generation)

O sistema implementa RAG para enriquecer respostas com informações de documentos institucionais:

- **Indexação de Documentos**: Processa PDFs e outros documentos em chunks
- **Busca Híbrida**: Combina embeddings semânticos com BM25 para melhor precisão
- **Extração de Contexto**: Utiliza LLM para extrair informações relevantes dos documentos recuperados

### 4. Integração com Busca Web (Tavily)

Para informações não disponíveis no banco de dados ou documentos, o sistema utiliza a API Tavily:

- **Detecção de Consultas Externas**: Identifica quando a informação precisa ser buscada externamente
- **Geração de Consultas Otimizadas**: Cria consultas de busca eficientes
- **Processamento de Resultados**: Extrai e formata informações relevantes dos resultados

## Tecnologias Utilizadas

- **LangGraph**: Framework para construção de sistemas multi-agentes
- **LangChain**: Biblioteca para construção de aplicações com LLMs
- **OpenAI API**: Modelos de linguagem para geração de texto e embeddings
- **Supabase**: Banco de dados PostgreSQL com funcionalidades adicionais
- **Tavily API**: API de busca na web otimizada para IA
- **FAISS/BM25**: Bibliotecas para busca vetorial e textual
- **Streamlit**: Interface de usuário para demonstração e testes

## Fluxo de Processamento de Consultas

1. **Recebimento da Consulta**:
   - O usuário envia uma pergunta através da interface
   - O sistema identifica o usuário e recupera seu contexto (RA, curso, etc.)
   - Verifica se a consulta já foi respondida anteriormente (cache)

2. **Roteamento Principal**:
   - O roteador principal analisa a consulta para determinar sua natureza
   - Classifica a consulta em uma das categorias: acadêmica, tutoria, suporte emocional ou planejamento
   - Direciona a consulta para o agente especializado apropriado

3. **Processamento por Agentes Especializados**:

   **Para Consultas Acadêmicas**:
   - Classifica a intenção específica (notas, faltas, disciplinas, etc.)
   - Recupera o esquema do banco de dados
   - Gera uma consulta SQL apropriada usando o agente NL2SQL
   - Valida e otimiza a consulta SQL
   - Executa a consulta no Supabase

   **Para Consultas de Tutoria**:
   - Identifica o assunto e tópico específico
   - Avalia o nível de conhecimento do aluno
   - Gera explicações adaptativas em múltiplos níveis
   - Cria mapas conceituais e conexões com conhecimento prévio
   - Fornece exemplos e exercícios personalizados

   **Para Consultas de Suporte Emocional**:
   - Identifica o estado emocional e a questão específica
   - Gera estratégias personalizadas para lidar com o desafio
   - Recomenda recursos relevantes
   - Cria uma resposta empática e acolhedora

   **Para Consultas de Planejamento**:
   - Analisa os objetivos acadêmicos do aluno
   - Desenvolve um plano de estudos personalizado
   - Sugere técnicas de estudo e recursos específicos
   - Cria um sistema de acompanhamento de progresso

4. **Enriquecimento de Informações**:
   - Recupera informações adicionais de documentos via RAG
   - Busca informações complementares na web via Tavily
   - Combina todas as fontes de informação

5. **Geração de Resposta Final**:
   - Gera uma resposta em linguagem natural
   - Formata a resposta de acordo com o tipo de consulta e agente
   - Armazena a resposta em cache para consultas futuras
   - Registra a interação para análise e melhoria contínua

## Implementação de RAG (Retrieval Augmented Generation)

O sistema implementa RAG para enriquecer respostas com informações de documentos institucionais:

1. **Processamento de Documentos**:
   - Documentos PDF são divididos em chunks de tamanho apropriado
   - Cada chunk é convertido em embedding usando OpenAI Embeddings
   - Os embeddings são armazenados em um índice FAISS ou no Supabase

2. **Busca Híbrida**:
   - Quando uma consulta é recebida, seu embedding é calculado
   - O sistema realiza uma busca por similaridade de embeddings
   - Paralelamente, realiza uma busca BM25 baseada em palavras-chave
   - Os resultados são combinados usando um algoritmo de fusão

3. **Extração de Contexto**:
   - Os chunks mais relevantes são processados por um LLM
   - O LLM extrai as informações mais pertinentes à consulta
   - O contexto extraído é usado para enriquecer a resposta final

## Implementação de NL2SQL (Natural Language to SQL)

O sistema utiliza uma abordagem multi-agente para converter consultas em linguagem natural para SQL:

1. **Recuperação de Esquema**:
   - O esquema do banco de dados é recuperado do Supabase
   - Amostras de valores de colunas importantes são obtidas para melhor compreensão

2. **Geração de SQL**:
   - Um LLM especializado gera uma consulta SQL inicial
   - A consulta é validada por outro LLM especializado em QA
   - Um terceiro LLM otimiza a consulta para performance

3. **Execução Segura**:
   - A consulta é parametrizada para evitar SQL injection
   - Parâmetros como RA do aluno são substituídos de forma segura
   - A execução é limitada a permissões específicas no banco de dados

## Implementação do Agente de Tutoria

O agente de tutoria é projetado para fornecer explicações personalizadas sobre conteúdos acadêmicos, utilizando técnicas avançadas de ensino e adaptação ao perfil do aluno:

### Funcionalidades Principais

1. **Identificação do Tópico**:
   - Analisa a consulta para identificar a disciplina e o tópico específico
   - Utiliza um classificador especializado para categorizar a dúvida
   - Determina o nível de complexidade da pergunta

2. **Níveis Adaptativos de Explicação**:
   - Avalia o conhecimento prévio do aluno com base na consulta e histórico de interações
   - Gera explicações em três níveis de complexidade (básico, intermediário, avançado)
   - Seleciona automaticamente o nível mais adequado para o aluno
   - Permite que o aluno solicite explicações mais simples ou mais detalhadas

3. **Abordagem Socrática**:
   - Gera perguntas estratégicas que estimulam o pensamento crítico
   - Cria diálogos socráticos simulados que demonstram o processo de descoberta
   - Guia o aluno a desenvolver seu próprio raciocínio em vez de apenas fornecer respostas
   - Pode ser ativada explicitamente adicionando "[socratic]" no início da pergunta

4. **Conexão com Conhecimento Prévio**:
   - Identifica conceitos relacionados que o aluno provavelmente já conhece
   - Cria mapas conceituais que conectam o novo tópico com conhecimentos existentes
   - Utiliza analogias cotidianas para tornar conceitos abstratos mais acessíveis
   - Constrói pontes entre diferentes disciplinas para mostrar conexões interdisciplinares

5. **Criação de Exemplos e Exercícios**:
   - Gera exemplos práticos relacionados ao tópico
   - Fornece exercícios com diferentes níveis de dificuldade
   - Inclui dicas e passos para resolução
   - Adapta os exemplos ao contexto e interesses do aluno

6. **Avaliação de Compreensão**:
   - Analisa perguntas de acompanhamento para avaliar entendimento
   - Identifica lacunas de conhecimento e oferece explicações adicionais
   - Adapta o estilo de explicação com base no feedback do aluno

### Como Utilizar o Agente de Tutoria

O agente de tutoria pode ser acessado através da interface principal do sistema. Aqui estão algumas dicas para aproveitar ao máximo suas funcionalidades:

1. **Consultas Básicas**:
   - Faça perguntas diretas sobre conceitos ou tópicos: "O que é programação orientada a objetos?"
   - Solicite explicações sobre processos: "Como funciona a fotossíntese?"
   - Peça esclarecimentos sobre teorias: "Explique a teoria da relatividade de Einstein"

2. **Ativando a Abordagem Socrática**:
   - Adicione "[socratic]" no início da sua pergunta: "[socratic] O que é inteligência artificial?"
   - Esta abordagem é ideal para desenvolver pensamento crítico e aprofundar a compreensão
   - Em vez de respostas diretas, você receberá perguntas guiadas e um diálogo que estimula a reflexão

3. **Explorando Conexões Interdisciplinares**:
   - Faça perguntas que conectem diferentes áreas: "Como a matemática se relaciona com a música?"
   - Solicite explicações sobre aplicações práticas: "Como a física é aplicada na medicina?"
   - Explore fundamentos compartilhados: "Quais conceitos da biologia são usados na computação?"

4. **Ajustando o Nível de Complexidade**:
   - Para explicações mais simples: "Explique de forma básica o que é um algoritmo"
   - Para explicações mais avançadas: "Quero uma explicação avançada sobre redes neurais"
   - O sistema também detecta automaticamente seu nível de conhecimento e adapta as explicações

5. **Exemplos de Consultas Eficazes**:
   - **Ciências Exatas**: "O que é cálculo diferencial?", "Explique o teorema de Pitágoras"
   - **Computação**: "O que são estruturas de dados?", "Explique o conceito de recursão"
   - **Biologia**: "Como funciona a divisão celular?", "O que é DNA e como ele funciona?"
   - **Humanidades**: "O que foi o Iluminismo?", "Explique o conceito de existencialismo"

### Fluxo de Processamento do Agente de Tutoria

1. **Classificação do Assunto e Tópico**:
   - O sistema identifica a disciplina e o tópico específico da consulta

2. **Avaliação do Conhecimento Prévio**:
   - Analisa a consulta e o histórico de interações para determinar o nível de conhecimento

3. **Identificação de Conceitos Relacionados**:
   - Mapeia conceitos que se conectam ao tópico da consulta

4. **Criação de Mapa Conceitual**:
   - Desenvolve uma representação das relações entre os conceitos

5. **Geração de Explicações Multinível**:
   - Cria explicações em diferentes níveis de complexidade

6. **Elaboração de Explicação Conectiva**:
   - Constrói uma explicação que conecta o novo conhecimento com o que o aluno já sabe

7. **Geração de Perguntas Socráticas**:
   - Cria perguntas estratégicas para estimular o pensamento crítico

8. **Criação de Diálogo Socrático**:
   - Desenvolve um diálogo simulado que demonstra o processo de descoberta

9. **Geração de Exemplos e Exercícios**:
   - Cria exemplos práticos e exercícios relacionados ao tópico

10. **Composição da Resposta Final**:
    - Integra todos os elementos em uma resposta coesa e personalizada

## Implementação do Agente de Planejamento Acadêmico

O agente de planejamento acadêmico ajuda os alunos a organizarem seus estudos de forma eficiente:

### Funcionalidades Principais

1. **Análise de Objetivos**:
   - Identifica objetivos de curto, médio e longo prazo
   - Avalia prioridades e prazos acadêmicos
   - Considera o perfil de aprendizagem do aluno

2. **Desenvolvimento de Planos de Estudo**:
   - Cria cronogramas personalizados com base na carga acadêmica
   - Distribui o tempo de estudo de forma equilibrada entre disciplinas
   - Incorpora técnicas de estudo eficientes (Pomodoro, espaçamento, etc.)

3. **Recomendação de Recursos**:
   - Sugere materiais complementares para cada disciplina
   - Recomenda ferramentas e aplicativos para organização
   - Indica estratégias específicas para diferentes tipos de conteúdo

4. **Acompanhamento de Progresso**:
   - Estabelece marcos e indicadores de progresso
   - Propõe ajustes ao plano com base no desempenho
   - Oferece estratégias motivacionais para manter o engajamento

### Como Utilizar o Agente de Planejamento Acadêmico

O agente de planejamento acadêmico pode ser acessado através da interface principal do sistema. Aqui estão algumas dicas para aproveitar ao máximo suas funcionalidades:

1. **Definição de Objetivos**:
   - Seja específico sobre seus objetivos: "Quero melhorar meu desempenho em Cálculo I"
   - Estabeleça prazos: "Preciso me preparar para as provas finais em 3 semanas"
   - Indique suas prioridades: "Quero focar nas disciplinas com maior dificuldade"

2. **Solicitação de Planos de Estudo**:
   - Peça um plano completo: "Crie um plano de estudos para o semestre"
   - Solicite planos específicos: "Como devo organizar meus estudos para a prova de Física?"
   - Especifique restrições: "Tenho apenas 2 horas por dia para estudar, como devo organizá-las?"

3. **Busca por Técnicas de Estudo**:
   - Solicite técnicas gerais: "Quais são as melhores técnicas de estudo para memorização?"
   - Peça técnicas específicas: "Como aplicar a técnica Pomodoro para estudar programação?"
   - Busque estratégias para desafios específicos: "Como manter o foco durante longos períodos de estudo?"

4. **Acompanhamento e Ajustes**:
   - Relate seu progresso: "Completei 70% do plano, mas estou com dificuldades em Álgebra"
   - Solicite ajustes: "Preciso adaptar meu plano de estudos devido a um novo projeto"
   - Peça feedback: "Como posso avaliar se meu método de estudo está sendo eficaz?"

5. **Exemplos de Consultas Eficazes**:
   - "Crie um plano de estudos semanal para as disciplinas de Engenharia"
   - "Quais técnicas de estudo são mais eficazes para aprender programação?"
   - "Como devo distribuir meu tempo entre teoria e exercícios práticos?"
   - "Preciso de um plano para recuperar o conteúdo atrasado de Química"
   - "Quais são as melhores estratégias para estudar para concursos enquanto faço faculdade?"

## Implementação do Agente de Suporte Emocional

O agente de suporte emocional é projetado para ajudar estudantes a lidar com desafios emocionais e psicológicos relacionados à vida acadêmica:

### Funcionalidades Principais

1. **Detecção de Estado Emocional**:
   - Identifica sinais de ansiedade, estresse, desmotivação ou sobrecarga
   - Avalia a severidade do problema emocional
   - Reconhece padrões de pensamento negativos ou limitantes

2. **Geração de Estratégias Personalizadas**:
   - Oferece técnicas de gerenciamento de estresse e ansiedade
   - Sugere abordagens para lidar com procrastinação e bloqueios
   - Propõe métodos para melhorar a motivação e o bem-estar

3. **Recomendação de Recursos**:
   - Indica livros, aplicativos e ferramentas sobre bem-estar mental
   - Sugere práticas de autocuidado e mindfulness
   - Fornece informações sobre serviços de apoio disponíveis na instituição

4. **Suporte Empático**:
   - Oferece escuta ativa e validação emocional
   - Utiliza linguagem acolhedora e não-julgadora
   - Promove a normalização de dificuldades emocionais na vida acadêmica

### Como Utilizar o Agente de Suporte Emocional

O agente de suporte emocional pode ser acessado através da interface principal do sistema. Aqui estão algumas dicas para aproveitar ao máximo suas funcionalidades:

1. **Expressão de Sentimentos**:
   - Compartilhe como está se sentindo: "Estou muito ansioso com as provas finais"
   - Descreva situações específicas: "Tenho dificuldade para dormir antes de apresentações"
   - Seja honesto sobre suas preocupações: "Sinto que não vou conseguir acompanhar o curso"

2. **Busca por Estratégias**:
   - Solicite técnicas específicas: "Como lidar com a ansiedade antes de provas?"
   - Peça ajuda com desafios comuns: "Tenho procrastinado muito, o que posso fazer?"
   - Busque abordagens para situações específicas: "Como manter a motivação em disciplinas difíceis?"

3. **Desenvolvimento de Autoconsciência**:
   - Explore padrões: "Por que sempre me sinto sobrecarregado no final do semestre?"
   - Busque compreensão: "Como identificar sinais de esgotamento antes que seja tarde?"
   - Solicite reflexões guiadas: "Ajude-me a entender por que tenho medo de falhar"

4. **Busca por Recursos**:
   - Peça recomendações: "Quais aplicativos podem me ajudar com meditação?"
   - Solicite informações: "Existem grupos de apoio para estudantes com ansiedade?"
   - Busque práticas: "Quais exercícios de respiração posso fazer antes de uma prova?"

5. **Exemplos de Consultas Eficazes**:
   - "Estou me sentindo sobrecarregado com tantas tarefas, como posso lidar com isso?"
   - "Tenho medo de fazer perguntas em sala de aula, o que posso fazer?"
   - "Como lidar com a pressão dos pais para ter boas notas?"
   - "Perdi a motivação para estudar, como posso recuperá-la?"
   - "Quais técnicas de relaxamento são rápidas e eficazes para momentos de estresse?"

## Interface do Usuário e Guia de Utilização

O sistema utiliza Streamlit para fornecer uma interface simples e intuitiva que permite aos usuários interagir com os diferentes agentes especializados.

### Componentes da Interface

- **Seleção de Agente**: Menu dropdown para escolher entre diferentes tipos de assistentes
- **Entrada de RA**: Campo para informar o RA (Registro Acadêmico) do aluno
- **Chat**: Interface de chat para interação com o sistema
- **Feedback Visual**: Indicadores de processamento e status
- **Histórico de Mensagens**: Visualização das interações anteriores

### Guia Passo a Passo para Utilização

1. **Iniciar o Sistema**:
   - Execute o aplicativo Streamlit através do comando `streamlit run app.py`
   - Aguarde o carregamento da interface no navegador

2. **Configuração Inicial**:
   - Insira seu RA (Registro Acadêmico) no campo apropriado
   - Selecione o tipo de agente que deseja utilizar no menu dropdown:
     - **Agente Acadêmico**: Para consultas sobre notas, faltas, disciplinas e informações acadêmicas
     - **Agente de Tutoria**: Para explicações sobre conteúdos e conceitos acadêmicos
     - **Agente de Suporte Emocional**: Para apoio em questões emocionais e de bem-estar
     - **Agente de Planejamento**: Para ajuda na organização de estudos e planejamento acadêmico

3. **Interação com os Agentes**:
   - Digite sua pergunta ou solicitação na caixa de texto na parte inferior da interface
   - Pressione Enter ou clique no botão de envio para submeter sua mensagem
   - Aguarde enquanto o sistema processa sua solicitação (um indicador visual mostrará o progresso)
   - Leia a resposta gerada pelo agente selecionado

4. **Utilização de Comandos Especiais**:
   - **[socratic]**: Adicione este prefixo antes de perguntas para ativar o modo socrático no agente de tutoria
   - **[detalhado]**: Use este prefixo para solicitar respostas mais detalhadas
   - **[simples]**: Use este prefixo para solicitar explicações mais simples e diretas

5. **Navegação entre Agentes**:
   - Você pode alternar entre diferentes agentes a qualquer momento usando o menu dropdown
   - O histórico de conversas é mantido separadamente para cada tipo de agente
   - Ao mudar de agente, o sistema mantém o contexto do seu RA e informações acadêmicas

6. **Exemplos de Uso por Tipo de Agente**:

   **Agente Acadêmico**:
   ```
   Quais disciplinas estou matriculado neste semestre?
   Qual minha nota na disciplina de Cálculo I?
   Quantas faltas tenho em Programação?
   Quando é a próxima prova de Física?
   ```

   **Agente de Tutoria**:
   ```
   O que é programação orientada a objetos?
   [socratic] Explique o conceito de derivadas em cálculo.
   Como funciona o processo de fotossíntese?
   Quais são os principais eventos da Segunda Guerra Mundial?
   ```

   **Agente de Suporte Emocional**:
   ```
   Estou muito ansioso com as provas finais, o que posso fazer?
   Tenho dificuldade para me concentrar nos estudos.
   Como lidar com o estresse do TCC?
   Sinto que não estou conseguindo acompanhar o ritmo da turma.
   ```

   **Agente de Planejamento**:
   ```
   Preciso criar um plano de estudos para as próximas duas semanas.
   Como organizar meu tempo entre trabalho e faculdade?
   Quais técnicas posso usar para estudar mais eficientemente?
   Ajude-me a preparar um cronograma para o TCC.
   ```

7. **Feedback e Iteração**:
   - Se a resposta não for satisfatória, você pode refinar sua pergunta
   - Faça perguntas de acompanhamento para obter mais detalhes
   - O sistema aprende com suas interações e melhora com o tempo

8. **Encerramento**:
   - Suas conversas são salvas automaticamente
   - Você pode fechar o navegador quando terminar
   - Na próxima vez que acessar, poderá continuar de onde parou

## Conclusão

Este sistema multi-agentes representa uma abordagem avançada para assistentes acadêmicos, combinando:

1. **Inteligência Artificial**: Uso de LLMs para compreensão e geração de linguagem natural
2. **Engenharia de Prompts**: Técnicas avançadas para direcionar o comportamento dos LLMs
3. **Arquitetura Multi-Agentes**: Especialização e modularidade para maior eficiência
4. **Integração de Múltiplas Fontes**: Combinação de banco de dados, documentos e web
5. **Segurança e Privacidade**: Execução segura de consultas e proteção de dados sensíveis

O resultado é um assistente acadêmico capaz de responder a uma ampla gama de consultas de forma precisa, contextualizada e natural, melhorando significativamente a experiência do usuário no ambiente acadêmico.
