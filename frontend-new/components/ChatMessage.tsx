import React from 'react';
import { MessageFormatter } from './MessageFormatter';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import { cn } from '@/lib/utils';
import { Globe, Database, Link, FileText, ThumbsUp, ThumbsDown, Edit } from 'lucide-react';
import { Button } from './ui/button';

export interface MessageProps {
  role: 'user' | 'bot';
  content: string;
  timestamp?: string;
  loading?: boolean;
  source?: 'web' | 'database' | string;
  error?: boolean;
  showActions?: boolean;
}

export const ChatMessage: React.FC<MessageProps> = ({
  role,
  content,
  timestamp,
  loading,
  source,
  error,
  showActions = true
}) => {
  return (
    <div className={cn(
      "flex items-start gap-4 mb-6 px-4 max-w-4xl mx-auto",
      role === 'user' ? "justify-end" : "justify-start"
    )}>
      {/* Avatar - Only show for bot messages */}
      {role === 'bot' && (
        <div className="flex-shrink-0 mt-1">
          <Avatar className="h-10 w-10 bg-aiva text-white shadow-md">
            <AvatarFallback>
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-6 h-6">
                <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2M7.5 13A2.5 2.5 0 0 0 5 15.5A2.5 2.5 0 0 0 7.5 18a2.5 2.5 0 0 0 2.5-2.5A2.5 2.5 0 0 0 7.5 13m9 0a2.5 2.5 0 0 0-2.5 2.5a2.5 2.5 0 0 0 2.5 2.5a2.5 2.5 0 0 0 2.5-2.5a2.5 2.5 0 0 0-2.5-2.5Z" />
              </svg>
            </AvatarFallback>
          </Avatar>
        </div>
      )}

      {/* Message Content */}
      <div className={cn(
        "max-w-[85%]",
        role === 'user' ? "bg-white border border-gray-200 rounded-3xl p-4 shadow-sm" : "",
        loading && "animate-pulse",
        error && "bg-destructive/10 border border-destructive"
      )}>
        {/* User message is simpler */}
        {role === 'user' ? (
          <div className="flex items-start gap-3">
            <div className="flex-1">
              <MessageFormatter content={content} />
            </div>
            <Avatar className="h-8 w-8 bg-gray-100 flex-shrink-0 shadow-sm">
              <AvatarFallback>
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 text-gray-600">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2a7.2 7.2 0 0 1-6-3.22c.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08a7.2 7.2 0 0 1-6 3.22z"/>
                </svg>
              </AvatarFallback>
            </Avatar>
          </div>
        ) : (
          // Bot message has more features
          loading ? (
            <div className="typing-indicator p-3">
              <span></span>
              <span></span>
              <span></span>
            </div>
          ) : (
            <div className="bg-white border border-gray-200 rounded-3xl p-4 shadow-sm">
              {/* Bot name */}
              <div className="text-aiva font-medium mb-2 flex items-center">
                <span className="bg-aiva text-white text-xs px-2 py-0.5 rounded-full mr-2">AI</span>
                Bosquinho
              </div>

              {/* Message content */}
              <div className="text-gray-800 leading-relaxed">
                <MessageFormatter content={content} />
              </div>

              {/* Source information */}
              {source && (
                <div className="mt-3 text-sm text-gray-600 flex items-center">
                  {source === 'web' && <Globe size={14} className="mr-1" />}
                  {source === 'database' && <Database size={14} className="mr-1" />}
                  Fonte: {source === 'web' ? 'Web' : 'Banco de Dados'}
                </div>
              )}

              {/* Document links section */}
              {role === 'bot' && showActions && (
                <div className="mt-4 pt-3 border-t border-gray-200">
                  <div className="flex flex-col gap-2">
                    <div className="text-sm text-gray-600 flex items-center">
                      <FileText size={14} className="mr-1.5" />
                      Links para <span className="font-medium mx-1">Documentos</span> e <span className="font-medium mx-1">Websites</span> desta Resposta
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <Button variant="outline" size="sm" className="text-xs flex items-center gap-1 rounded-5xl border-aiva text-aiva hover:bg-aiva/10 transition-colors">
                        <Link size={12} />
                        <span>Link para website</span>
                      </Button>
                      <Button variant="outline" size="sm" className="text-xs flex items-center gap-1 rounded-5xl border-aiva text-aiva hover:bg-aiva/10 transition-colors">
                        <FileText size={12} />
                        <span>Link para documento</span>
                      </Button>
                    </div>
                  </div>
                </div>
              )}

              {/* Action buttons */}
              {role === 'bot' && showActions && (
                <div className="mt-4 flex flex-wrap gap-2">
                  <Button variant="outline" size="sm" className="text-xs bg-aiva text-white hover:bg-aiva-light border-none rounded-5xl px-4 shadow-sm transition-all hover:shadow">
                    Resumir Resposta
                  </Button>
                  <Button variant="outline" size="sm" className="text-xs bg-aiva text-white hover:bg-aiva-light border-none rounded-5xl px-4 shadow-sm transition-all hover:shadow">
                    Explicar com Exemplos
                  </Button>
                  <Button variant="outline" size="sm" className="text-xs bg-aiva text-white hover:bg-aiva-light border-none rounded-5xl px-4 shadow-sm transition-all hover:shadow">
                    Mais Detalhes
                  </Button>
                </div>
              )}

              {/* Feedback buttons */}
              {role === 'bot' && showActions && (
                <div className="mt-4 flex gap-2 border-t border-gray-100 pt-3">
                  <Button variant="ghost" size="sm" className="text-gray-500 hover:text-green-600 transition-colors rounded-full">
                    <ThumbsUp size={16} />
                  </Button>
                  <Button variant="ghost" size="sm" className="text-gray-500 hover:text-red-600 transition-colors rounded-full">
                    <ThumbsDown size={16} />
                  </Button>
                  <div className="flex-1"></div>
                  <Button variant="ghost" size="sm" className="text-gray-500 hover:bg-gray-100 flex items-center gap-1 rounded-full px-3 transition-all">
                    <Edit size={14} />
                    <span className="text-xs">Gerar nova resposta</span>
                  </Button>
                </div>
              )}
            </div>
          )
        )}
      </div>
    </div>
  );
};
