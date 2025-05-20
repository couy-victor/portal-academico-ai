import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { X, User, School } from 'lucide-react';

interface RAModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (ra: string) => void;
  defaultRA?: string;
}

export const RAModal: React.FC<RAModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  defaultRA = ''
}) => {
  const [ra, setRa] = useState(defaultRA);
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (ra.trim()) {
      onSubmit(ra);
    }
  };
  
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <motion.div
            className="w-full max-w-md"
            initial={{ scale: 0.9, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.9, y: 20 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            onClick={(e) => e.stopPropagation()}
          >
            <Card className="border-2 border-primary/20 shadow-xl">
              <div className="relative">
                <Button
                  variant="ghost"
                  size="icon"
                  className="absolute right-2 top-2 rounded-full"
                  onClick={onClose}
                >
                  <X size={18} />
                </Button>
                
                <div className="pt-6 pb-2 px-6 text-center">
                  <div className="mx-auto w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mb-4">
                    <School className="h-8 w-8 text-primary" />
                  </div>
                  <h2 className="text-2xl font-bold mb-1">Informe seu RA</h2>
                  <p className="text-muted-foreground text-sm mb-4">
                    Para consultar informações acadêmicas e financeiras, é necessário informar seu Registro Acadêmico.
                  </p>
                </div>
                
                <CardContent>
                  <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                        <User className="h-5 w-5 text-muted-foreground" />
                      </div>
                      <Input
                        type="text"
                        placeholder="Digite seu RA (ex: 123456)"
                        value={ra}
                        onChange={(e) => setRa(e.target.value)}
                        className="pl-10"
                      />
                    </div>
                    
                    <div className="flex justify-end gap-2 pt-2">
                      <Button
                        type="button"
                        variant="outline"
                        onClick={onClose}
                      >
                        Cancelar
                      </Button>
                      <Button 
                        type="submit"
                        disabled={!ra.trim()}
                        className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800"
                      >
                        Confirmar
                      </Button>
                    </div>
                  </form>
                </CardContent>
              </div>
            </Card>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
