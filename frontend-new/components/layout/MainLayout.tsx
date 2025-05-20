import React, { ReactNode } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import {
  MessageCircle,
  FileText,
  Smile,
  Calendar,
  LayoutGrid,
  Moon,
  Sun,
  Plus,
  Link as LinkIcon
} from 'lucide-react';
import { useTheme } from 'next-themes';
import { Avatar, AvatarFallback, AvatarImage } from '../ui/avatar';
import { Button } from '../ui/button';

interface MainLayoutProps {
  children: ReactNode;
  showRightPanel?: boolean;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children, showRightPanel = true }) => {
  const router = useRouter();
  const { theme, setTheme } = useTheme();
  const { agent: agentParam } = router.query;

  const isActive = (path: string) => router.pathname === path;
  const isActiveAgent = (agent: string) => agentParam === agent;

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  };

  return (
    <div className="flex h-screen bg-background">
      {/* Left Sidebar */}
      <div className="w-64 bg-aiva-sidebar text-white flex flex-col">
        {/* Logo/Brand */}
        <div className="p-4 border-b border-aiva-light/30 flex items-center">
          <h1 className="text-xl font-bold">BOSQUINHO AI</h1>
        </div>

        {/* New Chat Button */}
        <div className="p-4">
          <Button
            variant="outline"
            className="w-full bg-transparent border-white/20 text-white hover:bg-aiva-light flex items-center justify-center rounded-5xl shadow-sm"
            onClick={() => router.push('/chat')}
          >
            <Plus size={18} className="mr-2" />
            Nova Conversa
          </Button>
        </div>

        {/* Chat History */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          <div className="text-sm text-white/60 mb-2">CONVERSAS RECENTES</div>

          <Link href="/chat?history=1" passHref>
            <div className={`p-2 rounded-xl hover:bg-aiva-light ${isActive('/chat') && router.query.history === '1' ? 'bg-aiva-light' : ''}`}>
              <div className="flex items-center">
                <LayoutGrid size={16} className="mr-2" />
                <span className="text-sm">Consulta de notas</span>
              </div>
            </div>
          </Link>

          <Link href="/chat?history=2" passHref>
            <div className={`p-2 rounded-xl hover:bg-aiva-light ${isActive('/chat') && router.query.history === '2' ? 'bg-aiva-light' : ''}`}>
              <div className="flex items-center">
                <MessageCircle size={16} className="mr-2" />
                <span className="text-sm">Dúvida sobre cálculo</span>
              </div>
            </div>
          </Link>

          <Link href="/chat?history=3" passHref>
            <div className={`p-2 rounded-xl hover:bg-aiva-light ${isActive('/chat') && router.query.history === '3' ? 'bg-aiva-light' : ''}`}>
              <div className="flex items-center">
                <Calendar size={16} className="mr-2" />
                <span className="text-sm">Planejamento de estudos</span>
              </div>
            </div>
          </Link>

          <Link href="/chat?history=4" passHref>
            <div className={`p-2 rounded-xl hover:bg-aiva-light ${isActive('/chat') && router.query.history === '4' ? 'bg-aiva-light' : ''}`}>
              <div className="flex items-center">
                <Smile size={16} className="mr-2" />
                <span className="text-sm">Ajuda com ansiedade</span>
              </div>
            </div>
          </Link>

          <div className="text-sm text-white/60 mt-4 mb-2">SEMANA PASSADA</div>

          <Link href="/chat?history=5" passHref>
            <div className={`p-2 rounded-xl hover:bg-aiva-light ${isActive('/chat') && router.query.history === '5' ? 'bg-aiva-light' : ''}`}>
              <div className="flex items-center">
                <FileText size={16} className="mr-2" />
                <span className="text-sm">Informações sobre bolsas</span>
              </div>
            </div>
          </Link>

          <Link href="/chat?history=6" passHref>
            <div className={`p-2 rounded-xl hover:bg-aiva-light ${isActive('/chat') && router.query.history === '6' ? 'bg-aiva-light' : ''}`}>
              <div className="flex items-center">
                <MessageCircle size={16} className="mr-2" />
                <span className="text-sm">Dúvida sobre TCC</span>
              </div>
            </div>
          </Link>
        </div>

        {/* Theme Toggle */}
        <div className="p-4 border-t border-aiva-light/30 flex justify-center">
          <Button
            variant="ghost"
            size="icon"
            className="text-white hover:bg-aiva-light rounded-full"
            onClick={toggleTheme}
          >
            {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        <div className={`flex-1 overflow-hidden ${showRightPanel ? 'border-r border-gray-200' : ''}`}>
          {children}
        </div>

        {/* Right Panel for Links and Documents (conditionally rendered) */}
        {showRightPanel && (
          <div className="w-80 bg-[#F8FBF8] p-6 overflow-y-auto border-l border-gray-100">
            <div className="mb-6">
              <h2 className="text-lg font-medium text-aiva mb-2">Links Gerados</h2>
              <div className="flex items-center text-gray-600">
                <span className="text-aiva font-medium mr-1">Websites</span>
                <span>e</span>
                <span className="text-aiva font-medium ml-1">Documentos</span>
              </div>
              <p className="text-gray-500 text-sm mt-2">aparecerão aqui</p>
            </div>

            <div className="opacity-30">
              <div className="bg-white rounded-2xl p-4 mb-3 border border-gray-200 shadow-sm">
                <div className="flex items-center mb-2">
                  <div className="w-8 h-8 rounded-full bg-[#E8F5E9] flex items-center justify-center mr-2">
                    <LinkIcon size={16} className="text-aiva" />
                  </div>
                  <div>
                    <h3 className="text-sm font-medium">Website UNISAL</h3>
                    <p className="text-xs text-gray-500">unisal.br</p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-2xl p-4 border border-gray-200 shadow-sm">
                <div className="flex items-center mb-2">
                  <div className="w-8 h-8 rounded-full bg-[#E8F5E9] flex items-center justify-center mr-2">
                    <FileText size={16} className="text-aiva" />
                  </div>
                  <div>
                    <h3 className="text-sm font-medium">Manual do Aluno</h3>
                    <p className="text-xs text-gray-500">PDF - 2.4MB</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
