import React from 'react';
import { MessageFormatter } from './MessageFormatter';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import { cn } from '@/lib/utils';
import { Globe, Database, Clock, AlertCircle } from 'lucide-react';

export interface MessageProps {
  role: 'user' | 'bot';
  content: string;
  timestamp?: string;
  loading?: boolean;
  source?: 'web' | 'database' | string;
  error?: boolean;
}

export const ChatMessage: React.FC<MessageProps> = ({
  role,
  content,
  timestamp,
  loading,
  source,
  error
}) => {
  const isUser = role === 'user';

  return (
    <div className={cn(
      "flex items-start gap-3 mb-6 animate-in fade-in slide-in-from-bottom-5 duration-300",
      isUser ? "flex-row-reverse" : "flex-row"
    )}>
      {/* Avatar - Robô ou Menina */}
      <div className={cn(
        "relative",
        isUser ? "ml-2" : "mr-2"
      )}>
        <Avatar className={cn(
          "h-10 w-10 border-2",
          isUser
            ? "bg-gradient-to-br from-purple-500 to-pink-500 border-purple-300"
            : "bg-gradient-to-br from-blue-500 to-blue-700 border-blue-300",
          !isUser && "animate-bounce-slow"
        )}>
          {isUser ? (
            <AvatarImage src="/images/user.svg" alt="Usuário" />
          ) : (
            <AvatarImage src="/images/bosquinho.svg" alt="Bosquinho" />
          )}
          <AvatarFallback className={cn(
            isUser ? "bg-purple-500 text-white" : "bg-blue-600 text-white"
          )}>
            {isUser ? 'U' : 'B'}
          </AvatarFallback>
        </Avatar>

        {/* Indicador de online para o bot */}
        {!isUser && (
          <div className="absolute -top-1 -right-1 h-3 w-3 bg-green-400 rounded-full border border-white animate-pulse"></div>
        )}
      </div>

      {/* Message Content */}
      <div className={cn(
        "relative max-w-[85%] rounded-2xl p-4 shadow-md backdrop-blur-sm",
        isUser
          ? "bg-gradient-to-br from-purple-500 to-pink-600 text-white ml-auto rounded-tr-none"
          : "bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/40 dark:to-blue-800/40 text-foreground rounded-tl-none border border-blue-200 dark:border-blue-700",
        loading && "animate-pulse",
        error && "bg-red-100 dark:bg-red-900/30 border-red-300 dark:border-red-700"
      )}>
        {/* Decoração triangular para bolha de chat */}
        <div className={cn(
          "absolute top-0 w-4 h-4 overflow-hidden",
          isUser ? "right-0 transform translate-x-1/2 -translate-y-1/2" : "left-0 transform -translate-x-1/2 -translate-y-1/2"
        )}>
          <div className={cn(
            "absolute transform rotate-45 w-4 h-4",
            isUser
              ? "bg-purple-500"
              : "bg-blue-50 dark:bg-blue-900/40 border border-blue-200 dark:border-blue-700",
            error && "bg-red-100 dark:bg-red-900/30 border-red-300 dark:border-red-700"
          )}></div>
        </div>

        {loading ? (
          <div className="flex items-center space-x-2">
            <div className="text-sm font-medium">Digitando</div>
            <div className="flex space-x-1">
              <div className="w-2 h-2 rounded-full bg-current animate-bounce" style={{ animationDelay: '0ms' }}></div>
              <div className="w-2 h-2 rounded-full bg-current animate-bounce" style={{ animationDelay: '150ms' }}></div>
              <div className="w-2 h-2 rounded-full bg-current animate-bounce" style={{ animationDelay: '300ms' }}></div>
            </div>
          </div>
        ) : (
          <>
            <MessageFormatter content={content} />

            <div className="flex justify-between items-center mt-2 text-xs opacity-70">
              {timestamp && (
                <div className="flex items-center space-x-1">
                  <Clock size={12} />
                  <span>{timestamp}</span>
                </div>
              )}

              {source && (
                <div className={cn(
                  "flex items-center space-x-1",
                  source === 'web'
                    ? "text-blue-500 dark:text-blue-400"
                    : "text-green-500 dark:text-green-400"
                )}>
                  {source === 'web' ? <Globe size={12} /> : <Database size={12} />}
                  <span>Fonte: {source === 'web' ? 'Web' : 'Banco de Dados'}</span>
                </div>
              )}

              {error && (
                <div className="flex items-center space-x-1 text-red-500">
                  <AlertCircle size={12} />
                  <span>Erro</span>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
};
