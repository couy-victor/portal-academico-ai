import { useRouter } from 'next/router';
import Head from 'next/head';
import { MainLayout } from '@/components/layout/MainLayout';
import { AgentCard } from '@/components/AgentCard';
import { LayoutGrid, MessageCircle, FileText, Smile, Calendar, CreditCard } from 'lucide-react';

export default function Home() {
  const router = useRouter();
  
  const agents = [
    {
      title: 'Acadêmico',
      description: 'Consulte informações acadêmicas, notas, faltas e disciplinas',
      icon: LayoutGrid,
      path: '/chat?agent=academic'
    },
    {
      title: 'Financeiro',
      description: 'Consulte boletos, mensalidades e informações financeiras',
      icon: CreditCard,
      path: '/chat?agent=financial'
    },
    {
      title: 'Documentos',
      description: 'Pesquise informações em documentos e regulamentos',
      icon: FileText,
      path: '/chat?agent=documents'
    },
    {
      title: 'Suporte Emocional',
      description: 'Receba apoio para lidar com ansiedade e estresse',
      icon: Smile,
      path: '/chat?agent=support'
    },
    {
      title: 'Tutoria',
      description: 'Obtenha explicações sobre conteúdos das disciplinas',
      icon: MessageCircle,
      path: '/chat?agent=tutor'
    },
    {
      title: 'Planejamento',
      description: 'Organize seus estudos e crie cronogramas eficientes',
      icon: Calendar,
      path: '/chat?agent=planning'
    }
  ];

  return (
    <>
      <Head>
        <title>Portal Acadêmico - Bosquinho</title>
        <meta name="description" content="Seu assistente acadêmico inteligente na UNISAL" />
      </Head>
      
      <MainLayout>
        <div className="container mx-auto py-8 px-4">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold mb-2">Bem-vindo ao Portal Acadêmico</h1>
            <p className="text-xl text-muted-foreground">
              Olá! Eu sou o Bosquinho, seu assistente acadêmico na UNISAL.
              <br />Como posso ajudar você hoje?
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {agents.map((agent) => (
              <AgentCard
                key={agent.title}
                title={agent.title}
                description={agent.description}
                icon={agent.icon}
                onClick={() => router.push(agent.path)}
              />
            ))}
          </div>
          
          <div className="mt-12 text-center">
            <p className="text-muted-foreground">
              Selecione um dos assistentes acima para começar uma conversa
              <br />ou acesse diretamente pela barra lateral.
            </p>
          </div>
        </div>
      </MainLayout>
    </>
  );
}
