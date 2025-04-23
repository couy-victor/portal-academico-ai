// API route para consultas acadêmicas
import { spawn } from 'child_process';
import path from 'path';
import { normalizeApiResponse } from '../../utils/apiUtils';

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Método não permitido' });
  }

  // Definir um timeout para garantir que a API sempre responda
  const TIMEOUT_MS = 30000; // 30 segundos
  let isResponseSent = false;

  const timeoutId = setTimeout(() => {
    if (!isResponseSent) {
      isResponseSent = true;
      console.error('Timeout atingido. Enviando resposta de fallback.');
      return res.status(500).json(normalizeApiResponse({
        error: 'Timeout atingido',
        response: 'Desculpe, a consulta demorou muito para ser processada. Por favor, tente novamente mais tarde.'
      }));
    }
  }, TIMEOUT_MS);

  try {
    const { query, user_id } = req.body;

    if (!query) {
      clearTimeout(timeoutId);
      isResponseSent = true;
      return res.status(400).json({ error: 'Consulta não fornecida' });
    }

    // Executar o script Python para processar a consulta
    console.log(`[${new Date().toISOString()}] Processando consulta acadêmica com RA: ${user_id}`);

    const pythonPath = path.resolve(process.cwd(), '../tests/interactive_test.py');
    console.log(`[${new Date().toISOString()}] Caminho do script Python: ${pythonPath}`);

    const pythonProcess = spawn('python', [
      pythonPath,
      '--query', query,
      '--user_id', user_id || 'interactive_user',
      '--mode', 'academic'
    ]);

    // Registrar o comando completo para debug
    console.log(`[${new Date().toISOString()}] Comando: python ${pythonPath} --query "${query}" --user_id "${user_id}" --mode academic`);

    // Registrar o PID do processo para debug
    console.log(`[${new Date().toISOString()}] PID do processo Python: ${pythonProcess.pid}`);

    let responseData = '';
    let errorData = '';

    pythonProcess.stdout.on('data', (data) => {
      const chunk = data.toString();
      console.log(`[${new Date().toISOString()}] Recebendo dados do stdout: ${chunk.length} bytes`);
      responseData += chunk;
    });

    pythonProcess.stderr.on('data', (data) => {
      const chunk = data.toString();
      console.log(`[${new Date().toISOString()}] Recebendo dados do stderr: ${chunk.length} bytes`);
      console.log(`[${new Date().toISOString()}] Erro: ${chunk}`);
      errorData += chunk;
    });

    // Adicionar handler para eventos de erro
    pythonProcess.on('error', (error) => {
      console.error(`[${new Date().toISOString()}] Erro no processo Python: ${error.message}`);
      if (!isResponseSent) {
        clearTimeout(timeoutId);
        isResponseSent = true;
        return res.status(500).json(normalizeApiResponse({
          error: `Erro ao iniciar o processo Python: ${error.message}`,
          response: 'Desculpe, ocorreu um erro ao processar sua consulta. Por favor, tente novamente mais tarde.'
        }));
      }
    });

    pythonProcess.on('close', (code) => {
      console.log(`[${new Date().toISOString()}] Processo Python encerrado com código ${code}`);

      if (code !== 0) {
        console.error(`[${new Date().toISOString()}] Processo Python encerrado com erro, código ${code}`);
        console.error(`[${new Date().toISOString()}] Erro: ${errorData}`);

        if (!isResponseSent) {
          clearTimeout(timeoutId);
          isResponseSent = true;
          return res.status(500).json(normalizeApiResponse({
            error: `Erro ao processar consulta (código ${code})`,
            details: errorData
          }));
        }
      }

      console.log(`[${new Date().toISOString()}] Processo Python concluído com sucesso`);

      try {
        // Registrar a resposta completa para debug
        console.log(`[${new Date().toISOString()}] Resposta completa do Python (${responseData.length} bytes)`);
        console.log(responseData);

        // Tentar extrair a resposta do output
        console.log(`[${new Date().toISOString()}] Tentando extrair resposta do output...`);
        const responseMatch = responseData.match(/Resposta:(.*?)(?=\n\n|$)/s);

        if (responseMatch && responseMatch[1].trim()) {
          console.log(`[${new Date().toISOString()}] Resposta encontrada no output`);
          // Limpar e formatar a resposta
          const rawResponse = responseMatch[1].trim();
          console.log(`[${new Date().toISOString()}] Resposta bruta: ${rawResponse}`);

          // Formatar a resposta para o usuário
          const cleanResponse = rawResponse
            .replace(/\s+/g, ' ')  // Normalizar espaços
            .replace(/�/g, 'á') // Corrigir á
            .replace(/�/g, 'é') // Corrigir é
            .replace(/�/g, 'í') // Corrigir í
            .replace(/�/g, 'ó') // Corrigir ó
            .replace(/�/g, 'ú') // Corrigir ú
            .replace(/�/g, 'ã') // Corrigir ã
            .replace(/�/g, 'õ') // Corrigir õ
            .replace(/�/g, 'ç') // Corrigir ç
            .replace(/�/g, 'Á') // Corrigir Á
            .replace(/�/g, 'É') // Corrigir É
            .replace(/�/g, 'Í') // Corrigir Í
            .replace(/�/g, 'Ó') // Corrigir Ó
            .replace(/�/g, 'Ú') // Corrigir Ú
            .replace(/�/g, 'Ã') // Corrigir Ã
            .replace(/�/g, 'Õ') // Corrigir Õ
            .replace(/�/g, 'Ç') // Corrigir Ç
            .trim();

          // Verificar se a resposta menciona busca na web
          const webSearchMention = responseData.includes("web_search_context") ||
                                 responseData.includes("Informações da web") ||
                                 responseData.includes("Tavily");

          // Normalizar a resposta antes de enviar
          console.log(`[${new Date().toISOString()}] Normalizando resposta para envio...`);
          const normalizedResponse = normalizeApiResponse({
            response: cleanResponse,
            source: webSearchMention ? "web" : "database"
          });

          console.log(`[${new Date().toISOString()}] Enviando resposta normalizada: ${JSON.stringify(normalizedResponse)}`);
          clearTimeout(timeoutId);
          isResponseSent = true;
          return res.status(200).json(normalizedResponse);
        } else {
          console.log(`[${new Date().toISOString()}] Nenhuma resposta encontrada no formato esperado`);
          // Tentar extrair qualquer informação útil
          const intentMatch = responseData.match(/Intent:\s*([\w_]+)/i);
          const intent = intentMatch ? intentMatch[1].toLowerCase() : '';
          console.log(`[${new Date().toISOString()}] Intent detectada: ${intent || 'nenhuma'}`);

          // Gerar uma resposta genérica baseada na intenção detectada
          let genericResponse = 'Não foi possível processar sua consulta. Por favor, tente novamente.';

          if (intent.includes('falta')) {
            genericResponse = 'Não consegui obter informações específicas sobre suas faltas. Por favor, verifique no portal acadêmico ou consulte a secretaria.';
          } else if (intent.includes('nota')) {
            genericResponse = 'Não consegui obter informações específicas sobre suas notas. Por favor, verifique no portal acadêmico ou consulte a secretaria.';
          } else if (intent.includes('disciplina')) {
            genericResponse = 'Não consegui obter informações específicas sobre suas disciplinas. Por favor, verifique no portal acadêmico ou consulte a secretaria.';
          }

          // Normalizar a resposta genérica antes de enviar
          console.log(`[${new Date().toISOString()}] Gerando resposta genérica: ${genericResponse}`);
          const normalizedResponse = normalizeApiResponse({
            response: genericResponse
          });

          console.log(`[${new Date().toISOString()}] Enviando resposta genérica normalizada`);
          clearTimeout(timeoutId);
          isResponseSent = true;
          return res.status(200).json(normalizedResponse);
        }
      } catch (parseError) {
        console.error(`[${new Date().toISOString()}] Erro ao analisar resposta:`, parseError);
        // Normalizar a resposta de erro antes de enviar
        console.log(`[${new Date().toISOString()}] Gerando resposta de erro para erro de análise`);
        const normalizedResponse = normalizeApiResponse({
          error: 'Erro ao analisar resposta',
          details: responseData
        });

        console.log(`[${new Date().toISOString()}] Enviando resposta de erro`);
        clearTimeout(timeoutId);
        isResponseSent = true;
        return res.status(500).json(normalizedResponse);
      }
    });
  } catch (error) {
    console.error(`[${new Date().toISOString()}] Erro geral na API:`, error);
    // Normalizar a resposta de erro antes de enviar
    console.log(`[${new Date().toISOString()}] Gerando resposta para erro geral`);
    const normalizedResponse = normalizeApiResponse({
      error: 'Erro interno do servidor',
      details: error.message
    });

    console.log(`[${new Date().toISOString()}] Enviando resposta de erro geral`);
    clearTimeout(timeoutId);
    isResponseSent = true;
    return res.status(500).json(normalizedResponse);
  }
}
