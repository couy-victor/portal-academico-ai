import React from 'react';
import { CustomAvatar } from './CustomAvatar';
import { Button } from './ui/button';
import { cn } from '@/lib/utils';
import { MoreHorizontal, Info, RefreshCw } from 'lucide-react';
import { motion } from 'framer-motion';

interface ChatHeaderProps {
  agentName: string;
  agentDescription: string;
  studentRA?: string;
  onChangeRA?: () => void;
  onRefresh?: () => void;
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({
  agentName,
  agentDescription,
  studentRA,
  onChangeRA,
  onRefresh
}) => {
  return (
    <motion.div 
      className="flex items-center justify-between p-4 border-b bg-card/80 backdrop-blur-sm sticky top-0 z-10"
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ type: 'spring', stiffness: 500, damping: 30 }}
    >
      <div className="flex items-center space-x-3">
        <CustomAvatar role="bot" size="lg" />
        
        <div>
          <div className="flex items-center">
            <h2 className="text-xl font-bold">Bosquinho</h2>
            <div className="ml-2 px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-xs rounded-full">
              Online
            </div>
          </div>
          
          <div className="flex items-center text-sm text-muted-foreground">
            <span>Assistente {agentName}</span>
            <span className="mx-2">•</span>
            <span className="truncate max-w-[200px]">{agentDescription}</span>
          </div>
          
          {studentRA && (
            <div className="flex items-center mt-1 text-xs">
              <span className="font-medium text-blue-600 dark:text-blue-400">RA: {studentRA}</span>
              {onChangeRA && (
                <button
                  onClick={onChangeRA}
                  className="ml-2 text-primary underline text-xs"
                >
                  Alterar
                </button>
              )}
            </div>
          )}
        </div>
      </div>
      
      <div className="flex items-center space-x-1">
        {onRefresh && (
          <Button 
            variant="ghost" 
            size="icon" 
            className="h-9 w-9 rounded-full"
            onClick={onRefresh}
          >
            <RefreshCw size={18} />
          </Button>
        )}
        
        <Button 
          variant="ghost" 
          size="icon" 
          className="h-9 w-9 rounded-full"
        >
          <Info size={18} />
        </Button>
        
        <Button 
          variant="ghost" 
          size="icon" 
          className="h-9 w-9 rounded-full"
        >
          <MoreHorizontal size={18} />
        </Button>
      </div>
    </motion.div>
  );
};
