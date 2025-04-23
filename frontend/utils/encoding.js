/**
 * Função para corrigir problemas de codificação em textos
 * @param {string} text - Texto a ser corrigido
 * @returns {string} - Texto com codificação corrigida
 */
export function fixEncoding(text) {
  if (!text) return '';

  // Mapeamento de caracteres especiais
  const charMap = {
    'Computa\u00e7\u00e3o': 'Computação',
    'Computa��o': 'Computação',
    'informa��es': 'informações',
    'disposi��o': 'disposição',
    'á': 'á',
    'é': 'é',
    'í': 'í',
    'ó': 'ó',
    'ú': 'ú',
    'ã': 'ã',
    'õ': 'õ',
    'ç': 'ç',
    'Á': 'Á',
    'É': 'É',
    'Í': 'Í',
    'Ó': 'Ó',
    'Ú': 'Ú',
    'Ã': 'Ã',
    'Õ': 'Õ',
    'Ç': 'Ç',
    '�': 'á',
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
    '�': 'Ç',
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
    'Voc�': 'Você',
    'voc�': 'você',
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
    'Teoria da Computa��o': 'Teoria da Computação',
    'teoria da computa��o': 'teoria da computação',
    'Teoria da Computaááo': 'Teoria da Computação',
    'teoria da computaááo': 'teoria da computação'
  };

  let result = text;

  // Substituir palavras e frases comuns
  for (const [pattern, replacement] of Object.entries(charMap)) {
    result = result.replace(new RegExp(pattern, 'g'), replacement);
  }

  return result;
}
