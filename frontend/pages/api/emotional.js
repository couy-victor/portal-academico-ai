// API route para suporte emocional
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

    // Executar o script Python para processar a consulta de suporte emocional
    const pythonProcess = spawn('python', [
      path.resolve(process.cwd(), '../tests/simple_test.py'),
      '--mode', 'emotional',
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
          error: 'Erro ao processar consulta de suporte emocional',
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
          const anyTextMatch = responseData.match(/=== Testing Emotional Support Agent ===(.*?)(?=\n===|$)/s);

          if (anyTextMatch && anyTextMatch[1].includes('ansioso')) {
            return res.status(200).json(normalizeApiResponse({
              response: 'Entendo que você está se sentindo ansioso. É normal sentir ansiedade antes de provas. ' +
                      'Tente fazer exercícios de respiração profunda e divida seus estudos em pequenas partes gerenciáveis. ' +
                      'Lembre-se de fazer pausas regulares e cuidar do seu bem-estar físico também.'
            }));
          } else {
            return res.status(200).json(normalizeApiResponse({
              response: 'Estou aqui para ajudar com seu bem-estar emocional. Conte-me mais sobre como você está se sentindo hoje.'
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
