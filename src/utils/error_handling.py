"""
Error handling utilities for the Academic Agent system.
Provides comprehensive error handling, recovery strategies, and user-friendly error messages.
"""
import traceback
import sys
from typing import Dict, Any, Optional, List, Callable, Type
from dataclasses import dataclass
from enum import Enum
from functools import wraps
import time

from src.models.state import AcademicAgentState
from src.utils.logging import logger


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories."""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATABASE = "database"
    EXTERNAL_API = "external_api"
    LLM = "llm"
    NETWORK = "network"
    CONFIGURATION = "configuration"
    BUSINESS_LOGIC = "business_logic"
    SYSTEM = "system"
    UNKNOWN = "unknown"


@dataclass
class ErrorInfo:
    """Information about an error."""
    error_type: str
    message: str
    category: ErrorCategory
    severity: ErrorSeverity
    user_message: str
    recovery_suggestions: List[str]
    technical_details: Optional[str] = None
    timestamp: Optional[float] = None
    agent_name: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class AcademicAgentError(Exception):
    """Base exception for Academic Agent system."""
    
    def __init__(
        self, 
        message: str, 
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        user_message: str = None,
        recovery_suggestions: List[str] = None,
        technical_details: str = None
    ):
        """
        Initialize Academic Agent error.
        
        Args:
            message (str): Error message
            category (ErrorCategory): Error category
            severity (ErrorSeverity): Error severity
            user_message (str): User-friendly error message
            recovery_suggestions (List[str]): Suggestions for recovery
            technical_details (str): Technical details for debugging
        """
        super().__init__(message)
        self.category = category
        self.severity = severity
        self.user_message = user_message or self._generate_user_message()
        self.recovery_suggestions = recovery_suggestions or []
        self.technical_details = technical_details
    
    def _generate_user_message(self) -> str:
        """Generate a user-friendly error message."""
        if self.category == ErrorCategory.DATABASE:
            return "Houve um problema ao acessar os dados. Tente novamente em alguns instantes."
        elif self.category == ErrorCategory.LLM:
            return "Estou tendo dificuldades para processar sua solicitação. Pode reformular sua pergunta?"
        elif self.category == ErrorCategory.NETWORK:
            return "Problemas de conectividade detectados. Verifique sua conexão e tente novamente."
        elif self.category == ErrorCategory.VALIDATION:
            return "Há algo incorreto com os dados fornecidos. Verifique e tente novamente."
        else:
            return "Ocorreu um erro inesperado. Nossa equipe foi notificada e está trabalhando na solução."


class ValidationError(AcademicAgentError):
    """Error for validation failures."""
    
    def __init__(self, message: str, field: str = None, **kwargs):
        super().__init__(
            message, 
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            **kwargs
        )
        self.field = field


class DatabaseError(AcademicAgentError):
    """Error for database operations."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )


class LLMError(AcademicAgentError):
    """Error for LLM operations."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.LLM,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )


class ExternalAPIError(AcademicAgentError):
    """Error for external API calls."""
    
    def __init__(self, message: str, api_name: str = None, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.EXTERNAL_API,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )
        self.api_name = api_name


class ErrorHandler:
    """
    Handles errors in the Academic Agent system.
    """
    
    def __init__(self):
        """Initialize the error handler."""
        self.error_registry: Dict[Type[Exception], ErrorInfo] = {}
        self.recovery_strategies: Dict[ErrorCategory, List[Callable]] = {}
        self._register_default_errors()
        self._register_default_recovery_strategies()
    
    def _register_default_errors(self) -> None:
        """Register default error mappings."""
        # Database errors
        self.register_error(
            ConnectionError,
            ErrorInfo(
                error_type="ConnectionError",
                message="Database connection failed",
                category=ErrorCategory.DATABASE,
                severity=ErrorSeverity.HIGH,
                user_message="Não foi possível conectar ao banco de dados. Tente novamente em alguns instantes.",
                recovery_suggestions=[
                    "Verificar conexão com a internet",
                    "Tentar novamente em alguns minutos",
                    "Contatar suporte se o problema persistir"
                ]
            )
        )
        
        # LLM errors
        self.register_error(
            TimeoutError,
            ErrorInfo(
                error_type="TimeoutError",
                message="Operation timed out",
                category=ErrorCategory.LLM,
                severity=ErrorSeverity.MEDIUM,
                user_message="A operação demorou mais que o esperado. Tente reformular sua pergunta.",
                recovery_suggestions=[
                    "Simplificar a pergunta",
                    "Dividir consultas complexas em partes menores",
                    "Tentar novamente"
                ]
            )
        )
        
        # Validation errors
        self.register_error(
            ValueError,
            ErrorInfo(
                error_type="ValueError",
                message="Invalid value provided",
                category=ErrorCategory.VALIDATION,
                severity=ErrorSeverity.LOW,
                user_message="Os dados fornecidos não são válidos. Verifique e tente novamente.",
                recovery_suggestions=[
                    "Verificar formato dos dados",
                    "Consultar documentação",
                    "Usar exemplos válidos"
                ]
            )
        )
    
    def _register_default_recovery_strategies(self) -> None:
        """Register default recovery strategies."""
        # Database recovery strategies
        self.recovery_strategies[ErrorCategory.DATABASE] = [
            self._retry_with_backoff,
            self._use_cache_fallback,
            self._use_minimal_response
        ]
        
        # LLM recovery strategies
        self.recovery_strategies[ErrorCategory.LLM] = [
            self._retry_with_simpler_prompt,
            self._use_fallback_model,
            self._use_template_response
        ]
        
        # External API recovery strategies
        self.recovery_strategies[ErrorCategory.EXTERNAL_API] = [
            self._retry_with_backoff,
            self._skip_external_data,
            self._use_cached_data
        ]
    
    def register_error(self, exception_type: Type[Exception], error_info: ErrorInfo) -> None:
        """
        Register an error type with its information.
        
        Args:
            exception_type (Type[Exception]): Exception type
            error_info (ErrorInfo): Error information
        """
        self.error_registry[exception_type] = error_info
    
    def handle_error(
        self, 
        error: Exception, 
        state: AcademicAgentState,
        agent_name: str = None,
        attempt_recovery: bool = True
    ) -> AcademicAgentState:
        """
        Handle an error and update the state accordingly.
        
        Args:
            error (Exception): The error that occurred
            state (AcademicAgentState): Current state
            agent_name (str): Name of the agent where error occurred
            attempt_recovery (bool): Whether to attempt recovery
            
        Returns:
            AcademicAgentState: Updated state with error information
        """
        # Get error information
        error_info = self._get_error_info(error, agent_name)
        
        # Log the error
        self._log_error(error, error_info, state, agent_name)
        
        # Update state with error information
        state["error"] = error_info.message
        state["error_category"] = error_info.category.value
        state["error_severity"] = error_info.severity.value
        state["user_message"] = error_info.user_message
        
        # Add error metadata
        if "metadata" not in state:
            state["metadata"] = {}
        
        state["metadata"]["error_info"] = {
            "type": error_info.error_type,
            "category": error_info.category.value,
            "severity": error_info.severity.value,
            "timestamp": error_info.timestamp,
            "agent_name": agent_name,
            "recovery_suggestions": error_info.recovery_suggestions,
            "technical_details": error_info.technical_details
        }
        
        # Attempt recovery if enabled
        if attempt_recovery and error_info.severity != ErrorSeverity.CRITICAL:
            recovery_state = self._attempt_recovery(error_info, state, agent_name)
            if recovery_state:
                return recovery_state
        
        # Generate fallback response
        state["natural_response"] = self._generate_fallback_response(error_info, state)
        
        return state
    
    def _get_error_info(self, error: Exception, agent_name: str = None) -> ErrorInfo:
        """
        Get error information for an exception.
        
        Args:
            error (Exception): The exception
            agent_name (str): Name of the agent where error occurred
            
        Returns:
            ErrorInfo: Error information
        """
        # Check if it's a custom Academic Agent error
        if isinstance(error, AcademicAgentError):
            return ErrorInfo(
                error_type=type(error).__name__,
                message=str(error),
                category=error.category,
                severity=error.severity,
                user_message=error.user_message,
                recovery_suggestions=error.recovery_suggestions,
                technical_details=error.technical_details,
                agent_name=agent_name
            )
        
        # Check registered errors
        error_type = type(error)
        if error_type in self.error_registry:
            registered_info = self.error_registry[error_type]
            return ErrorInfo(
                error_type=registered_info.error_type,
                message=str(error),
                category=registered_info.category,
                severity=registered_info.severity,
                user_message=registered_info.user_message,
                recovery_suggestions=registered_info.recovery_suggestions,
                technical_details=traceback.format_exc(),
                agent_name=agent_name
            )
        
        # Default error info for unknown errors
        return ErrorInfo(
            error_type=type(error).__name__,
            message=str(error),
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.MEDIUM,
            user_message="Ocorreu um erro inesperado. Nossa equipe foi notificada.",
            recovery_suggestions=["Tentar novamente", "Contatar suporte"],
            technical_details=traceback.format_exc(),
            agent_name=agent_name
        )
    
    def _log_error(
        self, 
        error: Exception, 
        error_info: ErrorInfo, 
        state: AcademicAgentState,
        agent_name: str = None
    ) -> None:
        """Log error information."""
        log_data = {
            "error_type": error_info.error_type,
            "category": error_info.category.value,
            "severity": error_info.severity.value,
            "agent_name": agent_name,
            "user_id": state.get("user_id", "unknown"),
            "user_query": state.get("user_query", ""),
            "message": error_info.message
        }
        
        if error_info.severity == ErrorSeverity.CRITICAL:
            logger.critical(f"Critical error: {log_data}")
        elif error_info.severity == ErrorSeverity.HIGH:
            logger.error(f"High severity error: {log_data}")
        elif error_info.severity == ErrorSeverity.MEDIUM:
            logger.warning(f"Medium severity error: {log_data}")
        else:
            logger.info(f"Low severity error: {log_data}")
    
    def _attempt_recovery(
        self, 
        error_info: ErrorInfo, 
        state: AcademicAgentState,
        agent_name: str = None
    ) -> Optional[AcademicAgentState]:
        """
        Attempt to recover from an error.
        
        Args:
            error_info (ErrorInfo): Error information
            state (AcademicAgentState): Current state
            agent_name (str): Name of the agent where error occurred
            
        Returns:
            Optional[AcademicAgentState]: Recovered state or None if recovery failed
        """
        recovery_strategies = self.recovery_strategies.get(error_info.category, [])
        
        for strategy in recovery_strategies:
            try:
                logger.info(f"Attempting recovery strategy: {strategy.__name__}")
                recovered_state = strategy(error_info, state, agent_name)
                if recovered_state:
                    logger.info(f"Recovery successful using: {strategy.__name__}")
                    return recovered_state
            except Exception as recovery_error:
                logger.warning(f"Recovery strategy {strategy.__name__} failed: {recovery_error}")
        
        logger.warning("All recovery strategies failed")
        return None
    
    def _generate_fallback_response(self, error_info: ErrorInfo, state: AcademicAgentState) -> str:
        """
        Generate a fallback response for the user.
        
        Args:
            error_info (ErrorInfo): Error information
            state (AcademicAgentState): Current state
            
        Returns:
            str: Fallback response
        """
        base_message = error_info.user_message
        
        if error_info.recovery_suggestions:
            suggestions = "\n\nSugestões:\n" + "\n".join(f"• {suggestion}" for suggestion in error_info.recovery_suggestions)
            return base_message + suggestions
        
        return base_message
    
    # Recovery strategy implementations
    def _retry_with_backoff(self, error_info: ErrorInfo, state: AcademicAgentState, agent_name: str) -> Optional[AcademicAgentState]:
        """Retry operation with exponential backoff."""
        # Implementation would depend on the specific operation
        return None
    
    def _use_cache_fallback(self, error_info: ErrorInfo, state: AcademicAgentState, agent_name: str) -> Optional[AcademicAgentState]:
        """Use cached data as fallback."""
        # Implementation would check cache for similar queries
        return None
    
    def _use_minimal_response(self, error_info: ErrorInfo, state: AcademicAgentState, agent_name: str) -> Optional[AcademicAgentState]:
        """Provide a minimal response when full processing fails."""
        state["natural_response"] = "Não foi possível processar completamente sua solicitação, mas posso ajudá-lo de outras formas. Pode reformular sua pergunta?"
        return state
    
    def _retry_with_simpler_prompt(self, error_info: ErrorInfo, state: AcademicAgentState, agent_name: str) -> Optional[AcademicAgentState]:
        """Retry with a simpler prompt."""
        # Implementation would simplify the prompt and retry
        return None
    
    def _use_fallback_model(self, error_info: ErrorInfo, state: AcademicAgentState, agent_name: str) -> Optional[AcademicAgentState]:
        """Use a fallback LLM model."""
        # Implementation would switch to a different model
        return None
    
    def _use_template_response(self, error_info: ErrorInfo, state: AcademicAgentState, agent_name: str) -> Optional[AcademicAgentState]:
        """Use a template response."""
        templates = {
            "academic": "Não consegui processar sua consulta acadêmica no momento. Tente reformular sua pergunta ou consulte diretamente o sistema acadêmico.",
            "emotional": "Entendo que você pode estar passando por um momento difícil. Embora eu não possa ajudar completamente agora, recomendo conversar com um profissional ou procurar o apoio estudantil.",
            "tutor": "Não consegui explicar esse tópico no momento. Recomendo consultar materiais de estudo ou procurar ajuda de um professor.",
            "planning": "Não foi possível criar um plano de estudos agora. Tente organizar suas atividades manualmente ou use ferramentas de planejamento."
        }
        
        category = state.get("main_category", "academic")
        template = templates.get(category, templates["academic"])
        
        state["natural_response"] = template
        return state
    
    def _skip_external_data(self, error_info: ErrorInfo, state: AcademicAgentState, agent_name: str) -> Optional[AcademicAgentState]:
        """Skip external data and continue with available data."""
        # Mark that external data was skipped
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"]["external_data_skipped"] = True
        return state
    
    def _use_cached_data(self, error_info: ErrorInfo, state: AcademicAgentState, agent_name: str) -> Optional[AcademicAgentState]:
        """Use cached data instead of fresh data."""
        # Implementation would retrieve cached data
        return None


def error_handler_decorator(error_handler: ErrorHandler, agent_name: str = None):
    """
    Decorator for automatic error handling in agent functions.
    
    Args:
        error_handler (ErrorHandler): Error handler instance
        agent_name (str): Name of the agent
    """
    def decorator(func):
        @wraps(func)
        def wrapper(state: AcademicAgentState, *args, **kwargs):
            try:
                return func(state, *args, **kwargs)
            except Exception as e:
                return error_handler.handle_error(e, state, agent_name or func.__name__)
        return wrapper
    return decorator


# Global error handler instance
error_handler = ErrorHandler()
