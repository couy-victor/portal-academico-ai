import React, { useState, useRef, useEffect } from 'react';
import { Button } from './ui/button';
import { cn } from '@/lib/utils';
import { Send, Paperclip, Mic, Smile } from 'lucide-react';
import { motion } from 'framer-motion';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  placeholder?: string;
  disabled?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  placeholder = "Digite sua mensagem...",
  disabled = false
}) => {
  const [message, setMessage] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Ajustar altura do textarea automaticamente
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      inputRef.current.style.height = `${inputRef.current.scrollHeight}px`;
    }
  }, [message]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (message.trim() && !disabled) {
      onSendMessage(message);
      setMessage('');
      
      // Resetar altura do textarea
      if (inputRef.current) {
        inputRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <motion.div 
      className={cn(
        "relative rounded-xl border bg-card p-1",
        isFocused ? "ring-2 ring-primary/50" : "",
        disabled && "opacity-70"
      )}
      initial={{ y: 20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ type: 'spring', stiffness: 500, damping: 30 }}
    >
      <form onSubmit={handleSubmit} className="flex items-end">
        {/* Botões de anexo e emoji (decorativos) */}
        <div className="flex space-x-1 px-2">
          <Button 
            type="button" 
            variant="ghost" 
            size="icon" 
            className="h-8 w-8 rounded-full text-muted-foreground hover:text-foreground"
            disabled={disabled}
          >
            <Paperclip size={18} />
          </Button>
          <Button 
            type="button" 
            variant="ghost" 
            size="icon" 
            className="h-8 w-8 rounded-full text-muted-foreground hover:text-foreground"
            disabled={disabled}
          >
            <Smile size={18} />
          </Button>
        </div>
        
        {/* Textarea para mensagem */}
        <textarea
          ref={inputRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder={placeholder}
          className="flex-1 bg-transparent border-0 focus:ring-0 focus:outline-none resize-none max-h-32 py-3 px-2 text-sm"
          rows={1}
          disabled={disabled}
        />
        
        {/* Botão de envio */}
        <div className="flex items-center pr-2">
          <Button 
            type="submit" 
            size="icon" 
            className={cn(
              "h-10 w-10 rounded-full transition-all duration-200",
              message.trim() ? "bg-unisal text-white scale-100" : "bg-muted text-muted-foreground scale-90"
            )}
            disabled={!message.trim() || disabled}
          >
            <Send size={18} className={message.trim() ? "transform -rotate-45" : ""} />
          </Button>
        </div>
      </form>
    </motion.div>
  );
};
