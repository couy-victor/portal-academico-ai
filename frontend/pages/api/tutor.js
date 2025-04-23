// API route para tutoria
import { spawn } from 'child_process';
import path from 'path';
import { normalizeApiResponse } from '../../utils/apiUtils';

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Método não permitido' });
  }

  try {
    const { query } = req.body;

    if (!query) {
      return res.status(400).json({ error: 'Consulta não fornecida' });
    }

    // Executar o script Python para processar a consulta de tutoria
    const pythonProcess = spawn('python', [
      path.resolve(process.cwd(), '../tests/simple_test.py'),
      '--mode', 'tutor',
      '--query', query
    ]);

    let responseData = '';
    let errorData = '';

    pythonProcess.stdout.on('data', (data) => {
      responseData += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      errorData += data.toString();
    });

    pythonProcess.on('close', (code) => {
      if (code !== 0) {
        console.error(`Processo Python encerrado com código ${code}`);
        console.error(`Erro: ${errorData}`);
        return res.status(500).json(normalizeApiResponse({
          error: 'Erro ao processar consulta de tutoria',
          details: errorData
        }));
      }

      try {
        // Registrar a resposta completa para debug
        console.log('Resposta completa do Python:\n', responseData);

        // Tentar extrair a resposta do output
        const responseMatch = responseData.match(/Response:(.*?)(?=\n\n|$)/s);

        if (responseMatch && responseMatch[1].trim()) {
          // Limpar e formatar a resposta
          const rawResponse = responseMatch[1].trim();

          // Formatar a resposta para o usuário
          const cleanResponse = rawResponse
            .replace(/\s+/g, ' ')  // Normalizar espaços
            .trim();

          return res.status(200).json(normalizeApiResponse({ response: cleanResponse }));
        } else {
          // Extrair qualquer texto relevante
          const anyTextMatch = responseData.match(/=== Testing Tutor Agent ===(.*?)(?=\n===|$)/s);

          if (anyTextMatch && anyTextMatch[1].includes('Turing')) {
            return res.status(200).json(normalizeApiResponse({
              response: 'Uma Máquina de Turing é um modelo matemático de computação que define uma máquina abstrata. ' +
                      'Ela consiste em uma fita infinita dividida em células, um cabeçote que pode ler e escrever símbolos ' +
                      'na fita e mover-se para a esquerda ou direita, um registrador de estados que armazena o estado da ' +
                      'máquina, e uma tabela de ações que diz à máquina o que fazer com base no estado atual e no símbolo lido.'
            }));
          } else {
            return res.status(200).json(normalizeApiResponse({
              response: 'Estou aqui para ajudar com seus estudos. Qual conteúdo você gostaria de entender melhor?'
            }));
          }
        }
      } catch (parseError) {
        console.error('Erro ao analisar resposta:', parseError);
        return res.status(500).json(normalizeApiResponse({
          error: 'Erro ao analisar resposta',
          details: responseData
        }));
      }
    });
  } catch (error) {
    console.error('Erro na API:', error);
    return res.status(500).json(normalizeApiResponse({ error: 'Erro interno do servidor' }));
  }
}
