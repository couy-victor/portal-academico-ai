# Portal Acadêmico - Frontend Moderno

Este é o frontend moderno para o Portal Acadêmico AI, desenvolvido com React, Next.js, TypeScript, Tailwind CSS e Radix UI.

## Tecnologias Utilizadas

- **React**: Biblioteca JavaScript para construção de interfaces
- **Next.js**: Framework React para aplicações web
- **TypeScript**: Superset tipado de JavaScript
- **Tailwind CSS**: Framework CSS utilitário
- **Radix UI**: Biblioteca de componentes acessíveis e sem estilo
- **Lucide React**: Biblioteca de ícones

## Estrutura do Projeto

```
frontend-new/
├── components/       # Componentes React
│   ├── layout/       # Componentes de layout
│   └── ui/           # Componentes de UI
├── lib/              # Funções utilitárias
├── pages/            # Páginas da aplicação
│   └── api/          # Rotas de API
├── public/           # Arquivos estáticos
├── styles/           # Estilos globais
└── types/            # Definições de tipos TypeScript
```

## Funcionalidades

- **Chat Interativo**: Interface de chat para interagir com o assistente Bosquinho
- **Múltiplos Agentes**: Suporte para diferentes tipos de assistentes (Acadêmico, Financeiro, etc.)
- **Formatação de Mensagens**: Suporte para formatação rica nas mensagens (tabelas, listas, etc.)
- **Tema Claro/Escuro**: Alternância entre temas claro e escuro
- **Layout Responsivo**: Interface adaptável para diferentes tamanhos de tela

## Instalação e Execução

1. Instale as dependências:
   ```bash
   npm install
   ```

2. Execute o servidor de desenvolvimento:
   ```bash
   npm run dev
   ```

3. Acesse a aplicação em [http://localhost:3000](http://localhost:3000)

## Construção para Produção

```bash
npm run build
npm run start
```

## Integração com o Backend

O frontend se comunica com o backend através de chamadas API. As rotas estão configuradas no arquivo `next.config.js` para fazer proxy para o servidor backend.

## Personalização

- **Cores**: As cores podem ser personalizadas no arquivo `tailwind.config.js`
- **Componentes**: Os componentes UI podem ser estendidos ou modificados na pasta `components/ui`
- **Temas**: A configuração de temas está no arquivo `_app.tsx` usando o `next-themes`
