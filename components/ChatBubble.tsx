import React from 'react';
import { MessageFormatter } from './MessageFormatter';
import { cn } from '@/lib/utils';
import { Globe, Database, Clock, AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';

interface ChatBubbleProps {
  content: string;
  timestamp?: string;
  loading?: boolean;
  source?: 'web' | 'database' | string;
  error?: boolean;
  isUser: boolean;
}

export const ChatBubble: React.FC<ChatBubbleProps> = ({
  content,
  timestamp,
  loading,
  source,
  error,
  isUser
}) => {
  // Variantes para animação
  const variants = {
    hidden: { 
      opacity: 0, 
      y: 20,
      x: isUser ? 20 : -20 
    },
    visible: { 
      opacity: 1, 
      y: 0,
      x: 0,
      transition: { 
        type: 'spring',
        stiffness: 500,
        damping: 30
      }
    }
  };

  // Cores e estilos baseados no tipo de mensagem
  const bubbleStyles = cn(
    "relative p-4 rounded-2xl shadow-md max-w-[85%] backdrop-blur-sm",
    isUser 
      ? "bg-gradient-to-br from-purple-500 to-pink-600 text-white ml-auto rounded-tr-none" 
      : "bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/40 dark:to-blue-800/40 text-foreground rounded-tl-none border border-blue-200 dark:border-blue-700",
    loading && "animate-pulse",
    error && "bg-red-100 dark:bg-red-900/30 border-red-300 dark:border-red-700"
  );

  // Indicador de digitação
  if (loading) {
    return (
      <motion.div
        className={bubbleStyles}
        initial="hidden"
        animate="visible"
        variants={variants}
      >
        <div className="flex items-center space-x-2">
          <div className="text-sm font-medium">Digitando</div>
          <div className="flex space-x-1">
            <div className="w-2 h-2 rounded-full bg-current animate-bounce" style={{ animationDelay: '0ms' }}></div>
            <div className="w-2 h-2 rounded-full bg-current animate-bounce" style={{ animationDelay: '150ms' }}></div>
            <div className="w-2 h-2 rounded-full bg-current animate-bounce" style={{ animationDelay: '300ms' }}></div>
          </div>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      className={bubbleStyles}
      initial="hidden"
      animate="visible"
      variants={variants}
    >
      {/* Conteúdo da mensagem */}
      <MessageFormatter content={content} />
      
      {/* Metadados (timestamp, fonte) */}
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
            source === 'web' ? "text-blue-500 dark:text-blue-400" : "text-green-500 dark:text-green-400"
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
    </motion.div>
  );
};
