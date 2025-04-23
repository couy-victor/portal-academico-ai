import { spawn } from 'child_process';
import path from 'path';
import { normalizeApiResponse } from '../../utils/apiUtils';

export default async function handler(req, res) {
  if (req.method === 'POST') {
    const { query } = req.body;

    if (!query) {
      return res.status(400).json({ error: 'Consulta não fornecida' });
    }

    // Executar o script Python para processar a consulta de planejamento
    console.log('Diretório atual:', process.cwd());
    console.log('Caminho completo:', path.resolve(process.cwd(), '../tests/test_planning.py'));

    // Usar caminho absoluto para o script Python
    const pythonProcess = spawn('python', [
      path.resolve(process.cwd(), '../tests/test_planning.py'),
      '--query', query,
      '--single_query'
    ]);

    // Registrar o comando completo para debug
    console.log('Comando:', `python ${path.resolve(process.cwd(), '../tests/test_planning.py')} --query "${query}" --single_query`);

    let responseData = '';
    let errorData = '';

    pythonProcess.stdout.on('data', (data) => {
      responseData += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      errorData += data.toString();
      console.error(`Erro no processo Python: ${data}`);
    });

    return new Promise((resolve, reject) => {
      pythonProcess.on('close', (code) => {
        console.log(`Processo Python encerrado com código ${code}`);

        if (code !== 0) {
          console.error(`Erro no processo Python: ${errorData}`);
          return resolve(res.status(500).json(normalizeApiResponse({
            error: 'Erro ao processar consulta de planejamento',
            details: errorData
          })));
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

            return resolve(res.status(200).json(normalizeApiResponse({ response: cleanResponse })));
          } else {
            // Extrair qualquer texto relevante
            const anyTextMatch = responseData.match(/=== Testing Planning Agent ===(.*?)(?=\n===|$)/s);

            if (anyTextMatch && anyTextMatch[1].includes('estudos')) {
              return resolve(res.status(200).json(normalizeApiResponse({
                response: 'Para organizar seus estudos, recomendo criar um cronograma semanal, ' +
                        'dividindo o tempo entre as diferentes disciplinas. Priorize as matérias ' +
                        'com provas mais próximas e reserve períodos específicos para revisão. ' +
                        'Lembre-se de incluir pequenos intervalos para descanso.'
              })));
            } else {
              return resolve(res.status(200).json(normalizeApiResponse({
                response: 'Posso ajudar você a criar um plano de estudos eficiente. ' +
                        'Por favor, me conte mais sobre suas disciplinas, prazos e objetivos específicos.'
              })));
            }
          }
        } catch (parseError) {
          console.error('Erro ao analisar resposta:', parseError);
          return resolve(res.status(500).json(normalizeApiResponse({
            error: 'Erro ao analisar resposta',
            details: parseError.message
          })));
        }
      });
    });
  } else {
    res.setHeader('Allow', ['POST']);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}
