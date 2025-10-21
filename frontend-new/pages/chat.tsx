import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import { MainLayout } from '@/components/layout/MainLayout';
import { ChatMessage } from '@/components/ChatMessage';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { AgentCard } from '@/components/AgentCard';
import {
  Send,
  LayoutGrid,
  MessageCircle,
  FileText,
  Smile,
  Calendar,
  CreditCard
} from 'lucide-react';

// Tipos
interface Message {
  role: 'user' | 'bot';
  content: string;
  timestamp: string;
  source?: 'web' | 'database';
  loading?: boolean;
  error?: boolean;
}

interface AgentInfo {
  id: string;
  title: string;
  description: string;
  icon: React.ElementType;
  endpoint: string;
}

export default function ChatPage() {
  const router = useRouter();
  const { agent: agentParam } = router.query;

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [selectedAgent, setSelectedAgent] = useState<string>('academic');
  const [studentRA, setStudentRA] = useState<string>('');
  const [showRAModal, setShowRAModal] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Definição dos agentes
  const agents: Record<string, AgentInfo> = {
    academic: {
      id: 'academic',
      title: 'Acadêmico',
      description: 'Consulte informações acadêmicas, notas, faltas e disciplinas',
      icon: LayoutGrid,
      endpoint: '/api/academic'
    },
    financial: {
      id: 'financial',
      title: 'Financeiro',
      description: 'Consulte boletos, mensalidades e informações financeiras',
      icon: CreditCard,
      endpoint: '/api/financial'
    },
    documents: {
      id: 'documents',
      title: 'Documentos',
      description: 'Pesquise informações em documentos e regulamentos',
      icon: FileText,
      endpoint: '/api/rag'
    },
    support: {
      id: 'support',
      title: 'Suporte Emocional',
      description: 'Receba apoio para lidar com ansiedade e estresse',
      icon: Smile,
      endpoint: '/api/emotional'
    },
    tutor: {
      id: 'tutor',
      title: 'Tutoria',
      description: 'Obtenha explicações sobre conteúdos das disciplinas',
      icon: MessageCircle,
      endpoint: '/api/tutor'
    },
    planning: {
      id: 'planning',
      title: 'Planejamento',
      description: 'Organize seus estudos e crie cronogramas eficientes',
      icon: Calendar,
      endpoint: '/api/planning'
    }
  };

  // Efeito para carregar o RA do localStorage
  useEffect(() => {
    const savedRA = localStorage.getItem('studentRA');
    if (savedRA) {
      setStudentRA(savedRA);
    }

    // Adicionar mensagem de boas-vindas
    setMessages([
      {
        role: 'bot',
        content: `👋 Olá! Eu sou o Bosquinho, seu assistente acadêmico na UNISAL! Posso ajudar com consultas acadêmicas, tutoria, suporte emocional e planejamento de estudos. Como posso ajudar você hoje?`,
        timestamp: new Date().toLocaleTimeString()
      }
    ]);
  }, []);

  // Efeito para definir o agente a partir da URL
  useEffect(() => {
    if (agentParam && typeof agentParam === 'string' && agents[agentParam]) {
      setSelectedAgent(agentParam);

      // Atualizar mensagem de boas-vindas quando o agente muda
      setMessages([
        {
          role: 'bot',
          content: `👋 Olá! Eu sou o Bosquinho, seu assistente ${agents[agentParam].title} na UNISAL! ${
            agentParam === 'academic' ? 'Posso consultar suas notas, faltas e informações acadêmicas.' :
            agentParam === 'tutor' ? 'Posso ajudar com explicações sobre conteúdos das disciplinas. Use [socratic] para perguntas no estilo socrático.' :
            agentParam === 'support' ? 'Estou aqui para ajudar com ansiedade, estresse e outras questões emocionais.' :
            agentParam === 'planning' ? 'Posso ajudar a organizar seus estudos e criar cronogramas eficientes.' :
            ''
          } Como posso ajudar você hoje?`,
          timestamp: new Date().toLocaleTimeString()
        }
      ]);
    }
  }, [agentParam]);

  // Efeito para rolar para o final das mensagens
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Função para enviar mensagem
  const sendMessage = async () => {
    if (!input.trim()) return;

    // Verificar se precisa do RA para o agente acadêmico
    if (selectedAgent === 'academic' && !studentRA) {
      setShowRAModal(true);
      return;
    }

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date().toLocaleTimeString()
    };

    // Adicionar mensagem do usuário
    setMessages(prev => [...prev, userMessage]);

    // Limpar input
    setInput('');

    // Adicionar mensagem de carregamento
    const loadingMessage: Message = {
      role: 'bot',
      content: 'Processando sua consulta...',
      timestamp: new Date().toLocaleTimeString(),
      loading: true
    };

    setMessages(prev => [...prev, loadingMessage]);

    try {
      // Determinar endpoint com base no agente selecionado
      const endpoint = agents[selectedAgent].endpoint;

      // Preparar payload
      const payload: Record<string, any> = { query: input };

      // Adicionar RA para agentes que precisam
      if (['academic', 'financial'].includes(selectedAgent)) {
        payload.user_id = studentRA;
      }

      // Fazer requisição
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`Erro na resposta: ${response.status}`);
      }

      const data = await response.json();

      // Obter resposta
      const formattedResponse = data.response || data.resposta || '';

      // Determinar fonte da informação
      const source = data.source || '';

      // Remover mensagem de carregamento e adicionar resposta
      setMessages(prev => [
        ...prev.filter(msg => !msg.loading),
        {
          role: 'bot',
          content: formattedResponse,
          timestamp: new Date().toLocaleTimeString(),
          source: source as 'web' | 'database'
        }
      ]);

    } catch (error) {
      console.error('Erro ao enviar mensagem:', error);

      // Remover mensagem de carregamento e adicionar mensagem de erro
      setMessages(prev => [
        ...prev.filter(msg => !msg.loading),
        {
          role: 'bot',
          content: 'Desculpe, ocorreu um erro ao processar sua consulta. Por favor, tente novamente mais tarde.',
          timestamp: new Date().toLocaleTimeString(),
          error: true
        }
      ]);
    }
  };

  // Função para lidar com o envio do RA
  const handleRASubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const raInput = (document.getElementById('ra-input') as HTMLInputElement).value;

    if (raInput) {
      setStudentRA(raInput);
      localStorage.setItem('studentRA', raInput);
      setShowRAModal(false);

      // Enviar a mensagem após definir o RA
      setTimeout(sendMessage, 100);
    }
  };

  // Função para mudar o agente selecionado
  const changeAgent = (agentId: string) => {
    setSelectedAgent(agentId);
    router.push(`/chat?agent=${agentId}`, undefined, { shallow: true });

    // Atualizar mensagem de boas-vindas
    setMessages([
      {
        role: 'bot',
        content: `👋 Olá! Eu sou o Bosquinho, seu assistente ${agents[agentId].title} na UNISAL! ${
          agentId === 'academic' ? 'Posso consultar suas notas, faltas e informações acadêmicas.' :
          agentId === 'tutor' ? 'Posso ajudar com explicações sobre conteúdos das disciplinas. Use [socratic] para perguntas no estilo socrático.' :
          agentId === 'support' ? 'Estou aqui para ajudar com ansiedade, estresse e outras questões emocionais.' :
          agentId === 'planning' ? 'Posso ajudar a organizar seus estudos e criar cronogramas eficientes.' :
          ''
        } Como posso ajudar você hoje?`,
        timestamp: new Date().toLocaleTimeString()
      }
    ]);
  };

  return (
    <>
      <Head>
        <title>{`Chat ${agents[selectedAgent]?.title || 'Acadêmico'} - Bosquinho`}</title>
        <meta name="description" content="Converse com o Bosquinho, seu assistente acadêmico na UNISAL" />
      </Head>

      <MainLayout>
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="p-4 border-b">
            <h1 className="text-2xl font-bold">Bosquinho - Assistente {agents[selectedAgent]?.title}</h1>
            <p className="text-muted-foreground">{agents[selectedAgent]?.description}</p>

            {/* Mostrar RA quando estiver no chat acadêmico ou financeiro */}
            {['academic', 'financial'].includes(selectedAgent) && (
              <div className="mt-2 flex items-center">
                {studentRA ? (
                  <>
                    <span className="text-sm font-medium">RA: {studentRA}</span>
                    <button
                      className="ml-2 text-xs text-primary underline"
                      onClick={() => setShowRAModal(true)}
                    >
                      Alterar
                    </button>
                  </>
                ) : (
                  <button
                    className="text-sm text-primary underline"
                    onClick={() => setShowRAModal(true)}
                  >
                    Definir RA
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Top Navigation Bar with Model Selection */}
          <div className="border-b bg-[#F5F5F5]">
            <div className="max-w-screen-xl mx-auto px-4 py-2 flex justify-between items-center">
              <div className="flex-1"></div>
              <div className="inline-flex rounded-full border border-gray-200 p-1 bg-white shadow-sm">
                {Object.values(agents).slice(0, 4).map((agent) => {
                  const Icon = agent.icon;
                  return (
                    <button
                      key={agent.id}
                      className={`flex items-center justify-center px-4 py-1.5 rounded-full text-sm font-medium transition-all ${
                        selectedAgent === agent.id
                          ? 'bg-aiva text-white shadow-md'
                          : 'text-gray-700 hover:bg-gray-100'
                      }`}
                      onClick={() => changeAgent(agent.id)}
                    >
                      {agent.title}
                    </button>
                  );
                })}
              </div>
              <div className="flex-1 flex justify-end">
                <div className="flex items-center">
                  <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-gray-700 mr-2">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
                      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2a7.2 7.2 0 0 1-6-3.22c.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08a7.2 7.2 0 0 1-6 3.22z"/>
                    </svg>
                  </div>
                  <div className="w-12 h-6">
                    <div className="w-12 h-6 bg-gray-200 rounded-full flex items-center p-1">
                      <div className="w-4 h-4 bg-white rounded-full transform transition-transform duration-200 translate-x-6"></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-6 bg-[#F9F9F9]">
            <div className="max-w-4xl mx-auto">
              {messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center py-20">
                  <div className="w-24 h-24 bg-[#E8F5E9] rounded-full flex items-center justify-center mb-6 shadow-md">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-12 h-12 text-aiva">
                      <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2M7.5 13A2.5 2.5 0 0 0 5 15.5A2.5 2.5 0 0 0 7.5 18a2.5 2.5 0 0 0 2.5-2.5A2.5 2.5 0 0 0 7.5 13m9 0a2.5 2.5 0 0 0-2.5 2.5a2.5 2.5 0 0 0 2.5 2.5a2.5 2.5 0 0 0 2.5-2.5a2.5 2.5 0 0 0-2.5-2.5Z" />
                    </svg>
                  </div>
                  <h2 className="text-2xl font-bold text-aiva mb-2">Bosquinho</h2>
                  <p className="text-gray-600 max-w-md mb-6">
                    Seu assistente acadêmico na UNISAL. Posso ajudar com consultas acadêmicas, tutoria, suporte emocional e planejamento de estudos.
                  </p>
                  <div className="grid grid-cols-2 gap-3 max-w-md">
                    <div className="bg-white p-3 rounded-2xl border border-gray-200 shadow-sm hover:shadow transition-shadow cursor-pointer">
                      <h3 className="font-medium text-aiva mb-1">Consulta de Notas</h3>
                      <p className="text-sm text-gray-600">Quais são minhas notas neste semestre?</p>
                    </div>
                    <div className="bg-white p-3 rounded-2xl border border-gray-200 shadow-sm hover:shadow transition-shadow cursor-pointer">
                      <h3 className="font-medium text-aiva mb-1">Tutoria</h3>
                      <p className="text-sm text-gray-600">Me explique o conceito de [assunto]</p>
                    </div>
                    <div className="bg-white p-3 rounded-2xl border border-gray-200 shadow-sm hover:shadow transition-shadow cursor-pointer">
                      <h3 className="font-medium text-aiva mb-1">Suporte Emocional</h3>
                      <p className="text-sm text-gray-600">Estou ansioso com as provas</p>
                    </div>
                    <div className="bg-white p-3 rounded-2xl border border-gray-200 shadow-sm hover:shadow transition-shadow cursor-pointer">
                      <h3 className="font-medium text-aiva mb-1">Planejamento</h3>
                      <p className="text-sm text-gray-600">Me ajude a criar um cronograma de estudos</p>
                    </div>
                  </div>
                </div>
              ) : (
                messages.map((message, index) => (
                  <ChatMessage
                    key={index}
                    role={message.role}
                    content={message.content}
                    timestamp={message.timestamp}
                    loading={message.loading}
                    source={message.source}
                    error={message.error}
                  />
                ))
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Input Area */}
          <div className="p-4 border-t bg-white">
            <div className="max-w-4xl mx-auto">
              <div className="flex gap-2 relative">
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Digite sua mensagem..."
                  onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                  className="pr-24 rounded-5xl border-gray-300 shadow-sm focus:border-aiva focus:ring-aiva transition-all"
                />
                <Button
                  onClick={sendMessage}
                  className="absolute right-1 top-1 bottom-1 rounded-full bg-aiva hover:bg-aiva-light transition-colors"
                >
                  <Send size={18} />
                </Button>
              </div>
              <div className="text-xs text-center text-gray-500 mt-2">
                Pressione Enter para enviar, Shift+Enter para nova linha
              </div>
            </div>
          </div>
        </div>
      </MainLayout>

      {/* RA Modal */}
      {showRAModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 backdrop-blur-sm">
          <Card className="w-full max-w-md rounded-3xl shadow-lg overflow-hidden">
            <div className="bg-aiva p-4 text-white">
              <h2 className="text-xl font-bold">Identificação do Aluno</h2>
            </div>
            <CardContent className="pt-6">
              <div className="flex items-center mb-4">
                <div className="w-10 h-10 rounded-full bg-[#E8F5E9] flex items-center justify-center mr-3">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-6 h-6 text-aiva">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2a7.2 7.2 0 0 1-6-3.22c.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08a7.2 7.2 0 0 1-6 3.22z"/>
                  </svg>
                </div>
                <div>
                  <p className="text-gray-700">
                    Para consultar informações acadêmicas como notas e faltas, é necessário informar seu RA (Registro Acadêmico).
                  </p>
                </div>
              </div>
              <form onSubmit={handleRASubmit} className="space-y-4">
                <div>
                  <label htmlFor="ra-input" className="block text-sm font-medium text-gray-700 mb-1">
                    Registro Acadêmico (RA)
                  </label>
                  <Input
                    id="ra-input"
                    type="text"
                    placeholder="Digite seu RA (ex: 123456)"
                    className="rounded-5xl"
                    defaultValue={studentRA}
                  />
                </div>
                <div className="flex justify-end gap-2 pt-2">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setShowRAModal(false)}
                    className="rounded-5xl"
                  >
                    Cancelar
                  </Button>
                  <Button
                    type="submit"
                    className="rounded-5xl bg-aiva hover:bg-aiva-light"
                  >
                    Confirmar
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}
    </>
  );
}
