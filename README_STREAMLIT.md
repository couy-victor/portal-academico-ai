# Interface Streamlit para o Portal Acadêmico AI

Esta interface Streamlit permite interagir com os diferentes agentes do Portal Acadêmico AI através de uma interface de chat amigável.

## Funcionalidades

- **Campo para RA**: Permite ao aluno inserir seu RA para consultas personalizadas
- **Seleção de Agentes**: Escolha entre diferentes tipos de assistentes:
  - **Acadêmico**: Consultas sobre notas, faltas, disciplinas, etc.
  - **Suporte Emocional**: Ajuda com ansiedade, estresse, etc.
  - **Tutor**: Explicações sobre conteúdos acadêmicos
  - **Planejamento**: Ajuda com organização de estudos
- **Exemplos de Perguntas**: Botões com exemplos de perguntas para cada tipo de agente
- **Histórico de Conversa**: Mantém o histórico da conversa com o agente
- **Depuração**: Informações detalhadas para desenvolvedores

## Como Executar

1. Certifique-se de que todas as dependências estão instaladas:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure as variáveis de ambiente necessárias no arquivo `.env`

3. Execute o Streamlit a partir do diretório raiz do projeto:
   ```bash
   streamlit run Chatbot.py
   ```

4. Acesse a interface no navegador (geralmente em http://localhost:8501)

## Requisitos

- Python 3.8+
- Streamlit
- Todas as dependências listadas em requirements.txt
- Variáveis de ambiente configuradas (API keys, etc.)

## Estrutura de Arquivos

- `Chatbot.py`: Interface principal do Streamlit
- `app_test.py`: Testes automatizados para a interface

## Notas para Desenvolvedores

- A interface usa a função `initialize_agent_state()` para criar o estado inicial do agente
- Cada tipo de agente (acadêmico, suporte emocional, tutor, planejamento) é processado de forma diferente
- Erros são capturados e exibidos de forma amigável para o usuário, com detalhes técnicos disponíveis em expansores
- Os exemplos de perguntas são atualizados dinamicamente com base no tipo de agente selecionado

## Troubleshooting

Se você encontrar problemas ao executar a interface:

1. **Erros de importação**: Certifique-se de executar o Streamlit a partir do diretório raiz do projeto
2. **Erros de API**: Verifique se todas as chaves de API necessárias estão configuradas no arquivo `.env`
3. **Erros de dependência**: Verifique se todas as dependências estão instaladas com as versões corretas

## Próximos Passos

- Implementar autenticação de usuários
- Adicionar mais exemplos de perguntas
- Melhorar a exibição de resultados com formatação avançada
- Adicionar feedback do usuário para melhorar os agentes
