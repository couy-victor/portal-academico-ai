// API route para testar a execução do Python
import { spawn } from 'child_process';
import path from 'path';

export default async function handler(req, res) {
  // Definir um timeout para garantir que a API sempre responda
  const TIMEOUT_MS = 10000; // 10 segundos
  let isResponseSent = false;
  
  const timeoutId = setTimeout(() => {
    if (!isResponseSent) {
      isResponseSent = true;
      console.error('Timeout atingido. Enviando resposta de fallback.');
      return res.status(500).json({
        error: 'Timeout atingido',
        response: 'Desculpe, o teste demorou muito para ser processado.'
      });
    }
  }, TIMEOUT_MS);

  try {
    // Executar um script Python simples
    console.log(`[${new Date().toISOString()}] Testando execução do Python`);
    
    // Criar um script Python simples que apenas imprime uma mensagem
    const pythonScript = `
import sys
import os
import time

print("Python está funcionando!")
print(f"Versão do Python: {sys.version}")
print(f"Diretório atual: {os.getcwd()}")
print(f"Argumentos: {sys.argv}")
print("Teste concluído com sucesso!")
`;

    // Salvar o script em um arquivo temporário
    const fs = require('fs');
    const tempScriptPath = path.resolve(process.cwd(), 'temp_test.py');
    fs.writeFileSync(tempScriptPath, pythonScript);
    
    console.log(`[${new Date().toISOString()}] Script de teste salvo em: ${tempScriptPath}`);
    
    // Executar o script Python
    const pythonProcess = spawn('python', [tempScriptPath, 'arg1', 'arg2']);
    
    let responseData = '';
    let errorData = '';
    
    pythonProcess.stdout.on('data', (data) => {
      const chunk = data.toString();
      console.log(`[${new Date().toISOString()}] Saída do Python: ${chunk}`);
      responseData += chunk;
    });
    
    pythonProcess.stderr.on('data', (data) => {
      const chunk = data.toString();
      console.error(`[${new Date().toISOString()}] Erro do Python: ${chunk}`);
      errorData += chunk;
    });
    
    pythonProcess.on('error', (error) => {
      console.error(`[${new Date().toISOString()}] Erro ao executar Python: ${error.message}`);
      if (!isResponseSent) {
        clearTimeout(timeoutId);
        isResponseSent = true;
        
        // Limpar o arquivo temporário
        try {
          fs.unlinkSync(tempScriptPath);
        } catch (e) {
          console.error(`Erro ao remover arquivo temporário: ${e.message}`);
        }
        
        return res.status(500).json({
          error: `Erro ao executar Python: ${error.message}`
        });
      }
    });
    
    pythonProcess.on('close', (code) => {
      console.log(`[${new Date().toISOString()}] Processo Python encerrado com código ${code}`);
      
      // Limpar o arquivo temporário
      try {
        fs.unlinkSync(tempScriptPath);
      } catch (e) {
        console.error(`Erro ao remover arquivo temporário: ${e.message}`);
      }
      
      if (code !== 0) {
        if (!isResponseSent) {
          clearTimeout(timeoutId);
          isResponseSent = true;
          return res.status(500).json({
            error: `Processo Python encerrado com código ${code}`,
            stderr: errorData,
            stdout: responseData
          });
        }
      } else {
        if (!isResponseSent) {
          clearTimeout(timeoutId);
          isResponseSent = true;
          return res.status(200).json({
            success: true,
            message: 'Python está funcionando corretamente!',
            output: responseData
          });
        }
      }
    });
    
  } catch (error) {
    console.error(`[${new Date().toISOString()}] Erro ao testar Python:`, error);
    
    if (!isResponseSent) {
      clearTimeout(timeoutId);
      isResponseSent = true;
      return res.status(500).json({
        error: 'Erro ao testar Python',
        message: error.message
      });
    }
  }
}
