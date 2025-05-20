import React from 'react';
import { cn } from '@/lib/utils';

interface MessageFormatterProps {
  content: string;
  className?: string;
}

export const MessageFormatter: React.FC<MessageFormatterProps> = ({ content, className }) => {
  if (!content) return null;

  // Função para processar tabelas Markdown
  const processMarkdownTables = (text: string) => {
    // Regex para identificar tabelas Markdown
    const tableRegex = /(\|[^\n]+\|\n)((?:\|:?[-]+:?)+\|)(\n(?:\|[^\n]+\|\n?)+)/g;
    
    return text.replace(tableRegex, (match, headerRow, alignmentRow, bodyRows) => {
      // Processar cabeçalho
      const headers = headerRow
        .trim()
        .split('|')
        .filter(cell => cell.trim() !== '')
        .map(cell => cell.trim());
      
      // Processar alinhamentos
      const alignments = alignmentRow
        .trim()
        .split('|')
        .filter(cell => cell.trim() !== '')
        .map(cell => {
          if (cell.startsWith(':') && cell.endsWith(':')) return 'text-center';
          if (cell.endsWith(':')) return 'text-right';
          return 'text-left';
        });
      
      // Processar linhas do corpo
      const rows = bodyRows
        .trim()
        .split('\n')
        .map(row => 
          row
            .trim()
            .split('|')
            .filter(cell => cell.trim() !== '')
            .map(cell => cell.trim())
        );
      
      // Construir HTML da tabela
      return `
        <div class="overflow-x-auto my-4">
          <table class="min-w-full border-collapse border border-gray-300 dark:border-gray-700">
            <thead>
              <tr class="bg-gray-100 dark:bg-gray-800">
                ${headers.map((header, i) => 
                  `<th class="px-4 py-2 border border-gray-300 dark:border-gray-700 ${alignments[i] || 'text-left'}">${header}</th>`
                ).join('')}
              </tr>
            </thead>
            <tbody>
              ${rows.map(row => 
                `<tr class="border-t border-gray-300 dark:border-gray-700">
                  ${row.map((cell, i) => 
                    `<td class="px-4 py-2 border border-gray-300 dark:border-gray-700 ${alignments[i] || 'text-left'}">${cell}</td>`
                  ).join('')}
                </tr>`
              ).join('')}
            </tbody>
          </table>
        </div>
      `;
    });
  };

  // Processar listas
  const processLists = (text: string) => {
    // Listas não ordenadas
    let processedText = text.replace(/^[\s]*[-*+][\s](.+)$/gm, '<li>$1</li>');
    processedText = processedText.replace(/(<li>.*<\/li>\n)+/g, '<ul class="list-disc pl-5 my-2">$&</ul>');
    
    // Listas ordenadas
    processedText = processedText.replace(/^[\s]*(\d+)\.[\s](.+)$/gm, '<li>$2</li>');
    processedText = processedText.replace(/(<li>.*<\/li>\n)+/g, '<ol class="list-decimal pl-5 my-2">$&</ol>');
    
    return processedText;
  };

  // Processar formatação básica
  const processFormatting = (text: string) => {
    // Negrito
    let processedText = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    processedText = processedText.replace(/__(.*?)__/g, '<strong>$1</strong>');
    
    // Itálico
    processedText = processedText.replace(/\*(.*?)\*/g, '<em>$1</em>');
    processedText = processedText.replace(/_(.*?)_/g, '<em>$1</em>');
    
    // Código inline
    processedText = processedText.replace(/`(.*?)`/g, '<code class="bg-gray-100 dark:bg-gray-800 px-1 rounded">$1</code>');
    
    // Links
    processedText = processedText.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" class="text-blue-500 hover:underline">$1</a>');
    
    // URLs simples
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    processedText = processedText.replace(urlRegex, '<a href="$1" target="_blank" class="text-blue-500 hover:underline">$1</a>');
    
    return processedText;
  };

  // Processar cabeçalhos
  const processHeadings = (text: string) => {
    return text
      .replace(/^# (.*$)/gm, '<h1 class="text-2xl font-bold my-2">$1</h1>')
      .replace(/^## (.*$)/gm, '<h2 class="text-xl font-bold my-2">$1</h2>')
      .replace(/^### (.*$)/gm, '<h3 class="text-lg font-bold my-2">$1</h3>')
      .replace(/^#### (.*$)/gm, '<h4 class="text-base font-bold my-2">$1</h4>');
  };

  // Processar quebras de linha
  const processLineBreaks = (text: string) => {
    return text.replace(/\n/g, '<br />');
  };

  // Aplicar todas as transformações
  let formattedContent = content;
  formattedContent = processMarkdownTables(formattedContent);
  formattedContent = processHeadings(formattedContent);
  formattedContent = processLists(formattedContent);
  formattedContent = processFormatting(formattedContent);
  formattedContent = processLineBreaks(formattedContent);

  return (
    <div 
      className={cn("prose dark:prose-invert max-w-none", className)}
      dangerouslySetInnerHTML={{ __html: formattedContent }}
    />
  );
};
