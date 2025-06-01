"""
Main Router Agent for the Academic Agent system.
Responsible for routing queries to the appropriate specialized agent.
"""
import json
import time
from typing import Dict, Any, List

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.agents.base_agent import LLMAgent
from src.config.agent_config import config_manager
from src.models.state import AcademicAgentState
from src.utils.logging import logger
from src.utils.validation import input_validator
from src.utils.metrics import metrics_collector
from src.utils.error_handling import error_handler_decorator, LLMError

class MainRouterAgent(LLMAgent):
    """
    Main Router Agent that routes queries to appropriate specialized agents.
    """

    def __init__(self):
        """Initialize the Main Router Agent."""
        super().__init__(
            name="main_router",
            description="Routes queries to the appropriate specialized agent",
            temperature=0.1  # Low temperature for consistent classification
        )

        # Get agent configuration
        self.config = config_manager.get_agent_config("main_router")
        if self.config:
            self.timeout_seconds = self.config.timeout_seconds
        else:
            self.timeout_seconds = 15

    def _execute(self, state: AcademicAgentState) -> AcademicAgentState:
        """
        Execute the main routing logic.

        Args:
            state (AcademicAgentState): Current state

        Returns:
            AcademicAgentState: Updated state with routing decision
        """
        # Validate input
        validation_result = input_validator.validate_user_query(state["user_query"])
        if not validation_result.is_valid:
            raise LLMError(f"Invalid query: {', '.join(validation_result.errors)}")

        # Record metrics
        start_time = time.time()

        try:
            # Classify the query
            classification = self._classify_query(state["user_query"])

            # Update state with classification results
            state["main_category"] = classification["category"]
            state["main_confidence"] = classification["confidence"]

            # Store reasoning in metadata
            if "metadata" not in state:
                state["metadata"] = {}
            state["metadata"]["main_routing_reasoning"] = classification.get("reasoning", "")

            # Record successful execution
            execution_time = time.time() - start_time
            metrics_collector.record_agent_execution(
                self.name, execution_time, True, False
            )

            logger.info(f"Routed query to {state['main_category']} with confidence {state['main_confidence']}")

            return state

        except Exception as e:
            execution_time = time.time() - start_time
            metrics_collector.record_agent_execution(
                self.name, execution_time, False, False, str(type(e).__name__)
            )
            raise LLMError(f"Classification failed: {str(e)}")

    def _classify_query(self, query: str) -> Dict[str, Any]:
        """
        Classify the user query into appropriate category.

        Args:
            query (str): User query to classify

        Returns:
            Dict[str, Any]: Classification result
        """
        # Create prompt for main routing
        prompt = ChatPromptTemplate.from_template("""
        Você é um especialista em classificação de consultas acadêmicas, capaz de identificar
        a categoria mais apropriada para cada pergunta.

        Pergunta do usuário: {query}

        Classifique esta pergunta em uma das seguintes categorias:

        1. academic: Consultas sobre informações acadêmicas estruturadas (notas, faltas, disciplinas, professores, horários, etc.)
        2. emotional_support: Pedidos de apoio emocional, ajuda com ansiedade, estresse, burnout, etc.
        3. tutor: Dúvidas sobre conteúdos específicos, pedidos de explicação sobre matérias, conceitos, etc.
        4. planning: Solicitações de ajuda com planejamento de estudos, organização de tempo, preparação para provas, etc.

        Raciocine passo a passo:
        1. Quais são as palavras-chave na pergunta?
        2. Qual é o objetivo principal do usuário?
        3. Que tipo de resposta seria mais útil?
        4. Qual categoria melhor se encaixa nesta pergunta?
        5. Qual o nível de confiança nesta classificação (0.0 a 1.0)?

        Formato da resposta:
        ```json
        {
            "category": "categoria_escolhida",
            "confidence": valor_de_confiança,
            "reasoning": "seu_raciocínio_aqui"
        }
        ```
        """)

        # Get LLM configuration
        llm_config = self._get_llm_config()
        llm = ChatOpenAI(**llm_config)

        try:
            # Prepare inputs
            inputs = {"query": query}

            # Execute the classification
            response = llm.invoke(prompt.format_messages(**inputs))

            # Parse JSON response
            result = self._parse_json_response(response.content)

            return result

        except Exception as e:
            logger.error(f"Error in query classification: {str(e)}")
            # Return default classification
            return {
                "category": "academic",
                "confidence": 0.5,
                "reasoning": f"Classification failed: {str(e)}"
            }


# Create agent instance
main_router_agent_instance = MainRouterAgent()


def main_router_agent(state: AcademicAgentState) -> Dict[str, Any]:
    """
    Legacy function wrapper for the main router agent.

    Args:
        state (AcademicAgentState): Current state

    Returns:
        Dict[str, Any]: Dictionary containing the next node to route to
    """
    # Execute the agent
    updated_state = main_router_agent_instance(state)

    # Extract routing decision from state
    category = updated_state.get("main_category", "academic")

    if category == "emotional_support":
        return {"next": "emotional_support"}
    elif category == "tutor":
        return {"next": "tutor"}
    elif category == "planning":
        return {"next": "planning"}
    else:  # Default to academic
        return {"next": "intent_router"}
