import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { LucideIcon } from 'lucide-react';

interface Agent {
  id: string;
  title: string;
  description: string;
  icon: LucideIcon;
}

interface AgentSelectorProps {
  agents: Agent[];
  selectedAgentId: string;
  onSelectAgent: (agentId: string) => void;
}

export const AgentSelector: React.FC<AgentSelectorProps> = ({
  agents,
  selectedAgentId,
  onSelectAgent
}) => {
  return (
    <motion.div 
      className="grid grid-cols-3 md:grid-cols-6 gap-2 p-3 border-b bg-muted/30"
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
    >
      {agents.map((agent) => {
        const Icon = agent.icon;
        const isSelected = selectedAgentId === agent.id;
        
        return (
          <motion.button
            key={agent.id}
            className={cn(
              "relative flex flex-col items-center justify-center p-3 rounded-lg transition-all duration-200",
              isSelected 
                ? "bg-primary/10 text-primary" 
                : "hover:bg-muted text-muted-foreground hover:text-foreground"
            )}
            onClick={() => onSelectAgent(agent.id)}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <div className={cn(
              "flex items-center justify-center w-10 h-10 rounded-full mb-1",
              isSelected ? "bg-primary/20" : "bg-background"
            )}>
              <Icon size={20} />
            </div>
            <span className="text-xs font-medium">{agent.title}</span>
            
            {isSelected && (
              <motion.div 
                className="absolute -bottom-1 left-1/2 w-12 h-1 bg-primary rounded-full"
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: 48 }}
                layoutId="activeIndicator"
                style={{ x: '-50%' }}
              />
            )}
          </motion.button>
        );
      })}
    </motion.div>
  );
};
