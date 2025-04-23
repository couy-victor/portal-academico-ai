// API route para consultas RAG (Retrieval Augmented Generation)
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

    // Executar o script Python para processar a consulta RAG
    console.log('Diretório atual:', process.cwd());
    console.log('Caminho completo:', path.resolve(process.cwd(), '../tests/test_rag.py'));

    // Usar caminho absoluto para o script Python
    const pythonProcess = spawn('python', [
      path.resolve(process.cwd(), '../tests/test_rag.py'),
      '--query', query,
      '--single_query'
    ]);

    // Registrar o comando completo para debug
    console.log('Comando:', `python ${path.resolve(process.cwd(), '../tests/test_rag.py')} --query "${query}" --single_query`);

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
          error: 'Erro ao processar consulta RAG',
          details: errorData
        }));
      }

      try {
        // Registrar a resposta completa para debug
        console.log('Resposta completa do Python:\n', responseData);

        // Tentar extrair o contexto do output
        const contextMatch = responseData.match(/Extracted Context:(.*?)(?=\n-{10,}|$)/s);

        if (contextMatch && contextMatch[1].trim()) {
          console.log('Contexto encontrado');

          // Extrair apenas a parte relevante e formatar a resposta
          let rawContext = contextMatch[1].trim();

          // Remover informações técnicas e de fonte
          rawContext = rawContext.replace(/\(Fonte:.*?\)/g, '');

          // Extrair apenas a primeira parte substantiva da resposta
          const mainPointMatch = rawContext.match(/1\. \*\*.*?\*\*:(.*?)(?=2\. |$)/s);

          if (mainPointMatch) {
            // Formatar uma resposta limpa e objetiva
            const cleanResponse = `O cálculo de nota das avaliações é feito da seguinte forma:\n\n${mainPointMatch[1].trim()}`;

            // Limpar e normalizar a resposta
            const cleanedResponse = cleanResponse
                .replace(/\*\*/g, '') // Remover marcadores markdown
                .replace(/\s+/g, ' ')  // Normalizar espaços
                .trim();

            return res.status(200).json(normalizeApiResponse({
              response: cleanedResponse
            }));
          } else {
            // Usar o contexto completo, mas limpo
            // Limpar e normalizar a resposta
            const rawResponseText = `O cálculo de nota das avaliações: ${rawContext.substring(0, 200).trim()}...`
                .replace(/\*\*/g, '') // Remover marcadores markdown
                .replace(/\s+/g, ' ')  // Normalizar espaços
                .trim();

            return res.status(200).json(normalizeApiResponse({
              response: rawResponseText
            }));
          }
        } else {
          // Tentar encontrar qualquer texto relevante
          const relevantTextMatch = responseData.match(/\[1\].*?Source:.*?Text:(.*?)\.\.\./s);

          if (relevantTextMatch && relevantTextMatch[1].trim()) {
            console.log('Texto relevante encontrado');
            const cleanText = relevantTextMatch[1].trim()
              .replace(/\s+/g, ' ')  // Normalizar espaços
              .trim();

            const responseText = `O cálculo de nota é baseado em avaliações online e presenciais. ${cleanText}`;
            return res.status(200).json(normalizeApiResponse({
              response: responseText
            }));
          } else {
            console.log('Nenhuma informação relevante encontrada');
            return res.status(200).json(normalizeApiResponse({
              response: 'Não encontrei informações específicas sobre o cálculo de notas nos documentos disponíveis. Por favor, consulte o professor ou coordenador do curso.'
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
