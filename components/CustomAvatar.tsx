import React from 'react';
import { Avatar, AvatarFallback } from './ui/avatar';
import { cn } from '@/lib/utils';
import Image from 'next/image';

interface CustomAvatarProps {
  role: 'user' | 'bot';
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const CustomAvatar: React.FC<CustomAvatarProps> = ({
  role,
  className,
  size = 'md',
}) => {
  const sizeClasses = {
    sm: 'h-8 w-8',
    md: 'h-10 w-10',
    lg: 'h-12 w-12',
  };

  // Animação para o avatar do bot
  const botAnimation = role === 'bot' ? 'animate-bounce-slow' : '';

  return (
    <div className={cn(
      sizeClasses[size],
      botAnimation,
      className
    )}>
      {role === 'bot' ? (
        <div className="relative h-full w-full">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-400 to-blue-600 rounded-full opacity-20 animate-pulse"></div>
          <div className="relative h-full w-full flex items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-blue-700 text-white overflow-hidden border-2 border-blue-300 shadow-lg">
            <Image 
              src="/images/bosquinho.png" 
              alt="Bosquinho" 
              width={size === 'lg' ? 48 : size === 'md' ? 40 : 32} 
              height={size === 'lg' ? 48 : size === 'md' ? 40 : 32}
              className="object-cover"
              onError={(e) => {
                // Fallback se a imagem não carregar
                const target = e.target as HTMLImageElement;
                target.style.display = 'none';
                const parent = target.parentElement;
                if (parent) {
                  parent.innerHTML = 'B';
                }
              }}
            />
          </div>
          
          {/* Efeito de brilho */}
          <div className="absolute -top-1 -right-1 h-3 w-3 bg-green-400 rounded-full border border-white animate-pulse"></div>
        </div>
      ) : (
        <div className="relative h-full w-full">
          <div className="relative h-full w-full flex items-center justify-center rounded-full bg-gradient-to-br from-purple-500 to-pink-500 text-white overflow-hidden border-2 border-purple-300 shadow-lg">
            <Image 
              src="/images/user.png" 
              alt="Usuário" 
              width={size === 'lg' ? 48 : size === 'md' ? 40 : 32} 
              height={size === 'lg' ? 48 : size === 'md' ? 40 : 32}
              className="object-cover"
              onError={(e) => {
                // Fallback se a imagem não carregar
                const target = e.target as HTMLImageElement;
                target.style.display = 'none';
                const parent = target.parentElement;
                if (parent) {
                  parent.innerHTML = 'U';
                }
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
};
