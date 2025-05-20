import React from 'react';
import { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

interface AgentCardProps {
  title: string;
  description: string;
  icon: LucideIcon;
  active?: boolean;
  onClick?: () => void;
}

export const AgentCard: React.FC<AgentCardProps> = ({
  title,
  description,
  icon: Icon,
  active = false,
  onClick
}) => {
  return (
    <div 
      className={cn(
        "agent-card",
        active && "active"
      )}
      onClick={onClick}
    >
      <Icon className="agent-card-icon" />
      <h3 className="agent-card-title">{title}</h3>
      <p className="agent-card-description">{description}</p>
    </div>
  );
};
