/**
 * Normaliza o texto substituindo caracteres especiais e corrigindo problemas de codificação
 * @param {string} text - Texto a ser normalizado
 * @returns {string} - Texto normalizado
 */
export function normalizeText(text) {
  if (!text) return '';

  // Mapa de substituições para caracteres especiais
  const replacements = {
    'á': 'á', 'à': 'à', 'â': 'â', 'ã': 'ã', 'ä': 'ä',
    'é': 'é', 'è': 'è', 'ê': 'ê', 'ë': 'ë',
    'í': 'í', 'ì': 'ì', 'î': 'î', 'ï': 'ï',
    'ó': 'ó', 'ò': 'ò', 'ô': 'ô', 'õ': 'õ', 'ö': 'ö',
    'ú': 'ú', 'ù': 'ù', 'û': 'û', 'ü': 'ü',
    'ç': 'ç',
    'Á': 'Á', 'À': 'À', 'Â': 'Â', 'Ã': 'Ã', 'Ä': 'Ä',
    'É': 'É', 'È': 'È', 'Ê': 'Ê', 'Ë': 'Ë',
    'Í': 'Í', 'Ì': 'Ì', 'Î': 'Î', 'Ï': 'Ï',
    'Ó': 'Ó', 'Ò': 'Ò', 'Ô': 'Ô', 'Õ': 'Õ', 'Ö': 'Ö',
    'Ú': 'Ú', 'Ù': 'Ù', 'Û': 'Û', 'Ü': 'Ü',
    'Ç': 'Ç',
    '�': 'á', // Caracteres problemáticos comuns
    '�': 'é',
    '�': 'í',
    '�': 'ó',
    '�': 'ú',
    '�': 'ã',
    '�': 'õ',
    '�': 'ç',
    '�': 'Á',
    '�': 'É',
    '�': 'Í',
    '�': 'Ó',
    '�': 'Ú',
    '�': 'Ã',
    '�': 'Õ',
    '�': 'Ç'
  };

  // Substituições de palavras e frases comuns com problemas
  const commonPhrases = {
    'Voc�': 'Você',
    'voc�': 'você',
    'est�': 'está',
    'n�o': 'não',
    'informa��o': 'informação',
    'Informa��o': 'Informação',
    'Intelig�ncia': 'Inteligência',
    'intelig�ncia': 'inteligência',
    'Acad�mico': 'Acadêmico',
    'acad�mico': 'acadêmico',
    'Hist�rico': 'Histórico',
    'hist�rico': 'histórico',
    'matr�cula': 'matrícula',
    'Matr�cula': 'Matrícula',
    'c�lculo': 'cálculo',
    'C�lculo': 'Cálculo',
    'poss�vel': 'possível',
    'Poss�vel': 'Possível',
    'Dispon�vel': 'Disponível',
    'dispon�vel': 'disponível',
    'Necess�rio': 'Necessário',
    'necess�rio': 'necessário',
    'Pr�ximo': 'Próximo',
    'pr�ximo': 'próximo',
    'Hor�rio': 'Horário',
    'hor�rio': 'horário',
    'Calend�rio': 'Calendário',
    'calend�rio': 'calendário',
    'Disciplina': 'Disciplina',
    'disciplina': 'disciplina',
    'Teoria da Computa��o': 'Teoria da Computação',
    'teoria da computa��o': 'teoria da computação',
    'Ol�': 'Olá',
    'ol�': 'olá',
    'Ç': 'á',
    'Ç': 'é',
    'Ç': 'í',
    'Ç': 'ó',
    'Ç': 'ú',
    'ÇÇ': 'çã',
    'Çt': 'út',
    'Çv': 'áv',
    'Çc': 'íc',
    'Çl': 'íl',
    'Çm': 'ém',
    'Çs': 'ês',
    'Çr': 'ér',
    'Çg': 'ég',
    'Çf': 'íf',
    'Çd': 'íd',
    'Çp': 'íp',
    'Çq': 'éq',
    'Çn': 'ên'
  };

  // Função para substituir todas as ocorrências
  const replaceAll = (str, mapObj) => {
    const re = new RegExp(Object.keys(mapObj).join("|"), "g");
    return str.replace(re, (matched) => mapObj[matched]);
  };

  // Primeiro, substituir caracteres especiais
  let result = text;
  
  // Substituir caracteres especiais
  for (const [char, replacement] of Object.entries(replacements)) {
    result = result.split(char).join(replacement);
  }
  
  // Substituir frases comuns
  result = replaceAll(result, commonPhrases);
  
  // Substituir caracteres Unicode problemáticos
  result = result
    .replace(/\ufffd/g, 'á')
    .replace(/\u00c3\u00a1/g, 'á')
    .replace(/\u00c3\u00a9/g, 'é')
    .replace(/\u00c3\u00ad/g, 'í')
    .replace(/\u00c3\u00b3/g, 'ó')
    .replace(/\u00c3\u00ba/g, 'ú')
    .replace(/\u00c3\u00a3/g, 'ã')
    .replace(/\u00c3\u00b5/g, 'õ')
    .replace(/\u00c3\u00a7/g, 'ç');

  // Substituições específicas para problemas comuns
  const specificReplacements = [
    { from: 'OlÇ!', to: 'Olá!' },
    { from: 'vocÇ', to: 'você' },
    { from: 'VocÇ', to: 'Você' },
    { from: 'estÇ', to: 'está' },
    { from: 'nÇo', to: 'não' },
    { from: 'Ç completamente', to: 'é completamente' },
    { from: 'sÇo vÇlidos', to: 'são válidos' },
    { from: 'nÇo estÇ', to: 'não está' },
    { from: 'difÇcil', to: 'difícil' },
    { from: 'concentraÇÇo', to: 'concentração' },
    { from: 'hÇ algumas', to: 'há algumas' },
    { from: 'sensaÇÇo', to: 'sensação' },
    { from: 'respiraÇÇo', to: 'respiração' },
    { from: 'meditaÇÇo', to: 'meditação' },
    { from: 'Çtil', to: 'útil' },
    { from: 'gerenciÇveis', to: 'gerenciáveis' },
    { from: 'motivaÇÇo', to: 'motivação' },
    { from: 'alguÇm', to: 'alguém' },
    { from: 'famÇlia', to: 'família' },
    { from: 'preocupaÇÇes', to: 'preocupações' },
    { from: 'Çreas', to: 'áreas' },
    { from: 'PsicÇlogos', to: 'Psicólogos' },
    { from: 'especÇficas', to: 'específicas' },
    { from: 'jÇ superou', to: 'já superou' }
  ];

  // Aplicar substituições específicas
  for (const { from, to } of specificReplacements) {
    result = result.split(from).join(to);
  }

  return result;
}
