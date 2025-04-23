/**
 * Utilitários para as APIs do frontend
 */
import { normalizeText } from './normalizeText';

/**
 * Normaliza a resposta da API antes de enviá-la ao cliente
 * @param {Object} response - Objeto de resposta da API
 * @returns {Object} - Objeto de resposta normalizado
 */
export function normalizeApiResponse(response) {
  if (!response) return response;
  
  // Se a resposta tiver um campo 'response', normaliza-o
  if (response.response) {
    response.response = normalizeText(response.response);
  }
  
  // Se a resposta tiver um campo 'resposta', normaliza-o
  if (response.resposta) {
    response.resposta = normalizeText(response.resposta);
  }
  
  // Se a resposta tiver um campo 'error', normaliza-o
  if (response.error) {
    response.error = normalizeText(response.error);
  }
  
  return response;
}
