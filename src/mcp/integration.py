"""
MCP Integration utilities for the Academic Agent system.
Provides integration between MCP and existing agents.
"""
from typing import Dict, Any, Optional, List
from functools import wraps

from src.mcp.context_manager import MCPContextManager, ContextType, ContextScope, context_manager
from src.mcp.providers import (
    UserContextProvider,
    ConversationContextProvider,
    DatabaseContextProvider,
    RAGContextProvider
)
from src.models.state import AcademicAgentState
from src.config.settings import MCP_ENABLED, MCP_CONTEXT_TTL
from src.utils.logging import logger


class MCPIntegration:
    """
    Integrates MCP with the Academic Agent system.
    """
    
    def __init__(self):
        """Initialize MCP integration."""
        self.enabled = MCP_ENABLED
        if not self.enabled:
            logger.info("MCP is disabled")
            return

        self.context_manager = context_manager
        self.providers = {}

        # Initialize providers
        self._initialize_providers()

        # Start context manager
        self.context_manager.start()

        logger.info("MCP Integration initialized")
    
    def _initialize_providers(self) -> None:
        """Initialize context providers."""
        if not self.enabled:
            return

        try:
            # User context provider
            self.providers['user'] = UserContextProvider(self.context_manager)

            # Conversation context provider
            self.providers['conversation'] = ConversationContextProvider(self.context_manager)

            # Database context provider
            self.providers['database'] = DatabaseContextProvider(self.context_manager)

            # RAG context provider
            self.providers['rag'] = RAGContextProvider(self.context_manager)

            logger.info("MCP providers initialized")

        except Exception as e:
            logger.error(f"Error initializing MCP providers: {str(e)}")
    
    def enrich_state_with_context(self, state: AcademicAgentState) -> AcademicAgentState:
        """
        Enrich agent state with relevant context from MCP.

        Args:
            state (AcademicAgentState): Current agent state

        Returns:
            AcademicAgentState: Enriched state with context
        """
        if not self.enabled:
            return state

        try:
            user_id = state.get("user_id")
            if not user_id:
                return state
            
            # Get user context
            user_context = self.providers['user'].provide_context(user_id)
            if user_context:
                if "mcp_context" not in state:
                    state["mcp_context"] = {}
                state["mcp_context"]["user"] = user_context
            
            # Get conversation context
            session_id = state.get("session_id", f"session_{user_id}")
            conversation_context = self.providers['conversation'].provide_context(session_id)
            if conversation_context:
                if "mcp_context" not in state:
                    state["mcp_context"] = {}
                state["mcp_context"]["conversation"] = conversation_context
            
            # Get database schema context
            db_context = self.providers['database'].provide_context("schema")
            if db_context:
                if "mcp_context" not in state:
                    state["mcp_context"] = {}
                state["mcp_context"]["database"] = db_context
            
            # Get RAG context if query is present
            if state.get("user_query"):
                rag_context = self.providers['rag'].provide_context(
                    state["user_query"], 
                    query=state["user_query"]
                )
                if rag_context:
                    if "mcp_context" not in state:
                        state["mcp_context"] = {}
                    state["mcp_context"]["rag"] = rag_context
            
            logger.debug(f"Enriched state with MCP context for user {user_id}")
            return state
            
        except Exception as e:
            logger.error(f"Error enriching state with MCP context: {str(e)}")
            return state
    
    def update_conversation_context(
        self, 
        state: AcademicAgentState,
        agent_response: str = None
    ) -> None:
        """
        Update conversation context after agent interaction.
        
        Args:
            state (AcademicAgentState): Current agent state
            agent_response (str): Agent's response
        """
        try:
            user_id = state.get("user_id")
            if not user_id:
                return
            
            session_id = state.get("session_id", f"session_{user_id}")
            user_query = state.get("user_query", "")
            response = agent_response or state.get("natural_response", "")
            intent = state.get("intent", "unknown")
            
            # Add conversation turn
            self.providers['conversation'].add_conversation_turn(
                session_id=session_id,
                user_message=user_query,
                agent_response=response,
                intent=intent,
                metadata={
                    "timestamp": state.get("timestamp"),
                    "confidence": state.get("confidence"),
                    "from_cache": state.get("from_cache", False)
                }
            )
            
            logger.debug(f"Updated conversation context for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error updating conversation context: {str(e)}")
    
    def get_context_for_agent(
        self, 
        agent_name: str, 
        context_types: List[ContextType],
        state: AcademicAgentState
    ) -> Dict[str, Any]:
        """
        Get specific context for an agent.
        
        Args:
            agent_name (str): Name of the agent
            context_types (List[ContextType]): Types of context needed
            state (AcademicAgentState): Current state
            
        Returns:
            Dict[str, Any]: Context data for the agent
        """
        try:
            context_data = {}
            
            for context_type in context_types:
                if context_type == ContextType.USER_PROFILE:
                    user_id = state.get("user_id")
                    if user_id:
                        user_context = self.providers['user'].provide_context(user_id)
                        if user_context:
                            context_data["user_profile"] = user_context
                
                elif context_type == ContextType.CONVERSATION:
                    session_id = state.get("session_id", f"session_{state.get('user_id')}")
                    if session_id:
                        conv_context = self.providers['conversation'].provide_context(session_id)
                        if conv_context:
                            context_data["conversation"] = conv_context
                
                elif context_type == ContextType.DATABASE_SCHEMA:
                    db_context = self.providers['database'].provide_context("schema")
                    if db_context:
                        context_data["database_schema"] = db_context
                
                elif context_type == ContextType.RAG_DOCUMENTS:
                    query = state.get("user_query")
                    if query:
                        rag_context = self.providers['rag'].provide_context(query, query=query)
                        if rag_context:
                            context_data["rag_documents"] = rag_context
            
            return context_data
            
        except Exception as e:
            logger.error(f"Error getting context for agent {agent_name}: {str(e)}")
            return {}
    
    def cache_agent_result(
        self, 
        agent_name: str, 
        state: AcademicAgentState,
        result_data: Any,
        ttl_seconds: int = 3600
    ) -> None:
        """
        Cache agent result for future use.
        
        Args:
            agent_name (str): Name of the agent
            state (AcademicAgentState): Current state
            result_data (Any): Result data to cache
            ttl_seconds (int): Time to live in seconds
        """
        try:
            user_id = state.get("user_id", "anonymous")
            query = state.get("user_query", "")
            
            # Create cache key
            cache_key = f"agent_result:{agent_name}:{user_id}:{hash(query)}"
            
            # Cache the result
            self.context_manager.set_context(
                key=cache_key,
                data={
                    "agent_name": agent_name,
                    "result": result_data,
                    "state_snapshot": {
                        "user_id": user_id,
                        "user_query": query,
                        "intent": state.get("intent"),
                        "confidence": state.get("confidence")
                    }
                },
                context_type=ContextType.AGENT_STATE,
                scope=ContextScope.SESSION,
                ttl_seconds=ttl_seconds
            )
            
            logger.debug(f"Cached result for agent {agent_name}")
            
        except Exception as e:
            logger.error(f"Error caching agent result: {str(e)}")
    
    def get_cached_agent_result(
        self, 
        agent_name: str, 
        state: AcademicAgentState
    ) -> Optional[Any]:
        """
        Get cached agent result.
        
        Args:
            agent_name (str): Name of the agent
            state (AcademicAgentState): Current state
            
        Returns:
            Optional[Any]: Cached result or None
        """
        try:
            user_id = state.get("user_id", "anonymous")
            query = state.get("user_query", "")
            
            # Create cache key
            cache_key = f"agent_result:{agent_name}:{user_id}:{hash(query)}"
            
            # Get cached result
            cached_data = self.context_manager.get_context(cache_key)
            if cached_data:
                return cached_data.get("result")
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached agent result: {str(e)}")
            return None
    
    def shutdown(self) -> None:
        """Shutdown MCP integration."""
        try:
            self.context_manager.stop()
            logger.info("MCP Integration shutdown")
        except Exception as e:
            logger.error(f"Error during MCP shutdown: {str(e)}")


# Global MCP integration instance
mcp_integration = MCPIntegration()


def with_mcp_context(context_types: List[ContextType] = None):
    """
    Decorator to automatically enrich agent functions with MCP context.
    
    Args:
        context_types (List[ContextType]): Specific context types to include
    """
    def decorator(func):
        @wraps(func)
        def wrapper(state: AcademicAgentState, *args, **kwargs):
            try:
                # Enrich state with context
                enriched_state = mcp_integration.enrich_state_with_context(state)
                
                # Get specific context if requested
                if context_types:
                    agent_context = mcp_integration.get_context_for_agent(
                        func.__name__, context_types, enriched_state
                    )
                    enriched_state["agent_context"] = agent_context
                
                # Execute the original function
                result = func(enriched_state, *args, **kwargs)
                
                # Update conversation context if this was a user-facing interaction
                if enriched_state.get("natural_response"):
                    mcp_integration.update_conversation_context(
                        enriched_state, 
                        enriched_state.get("natural_response")
                    )
                
                return result
                
            except Exception as e:
                logger.error(f"Error in MCP context decorator for {func.__name__}: {str(e)}")
                # Fall back to original function without MCP context
                return func(state, *args, **kwargs)
        
        return wrapper
    return decorator


def mcp_cache_result(ttl_seconds: int = 3600):
    """
    Decorator to automatically cache agent results using MCP.
    
    Args:
        ttl_seconds (int): Time to live for cached results
    """
    def decorator(func):
        @wraps(func)
        def wrapper(state: AcademicAgentState, *args, **kwargs):
            try:
                # Check for cached result first
                cached_result = mcp_integration.get_cached_agent_result(func.__name__, state)
                if cached_result:
                    logger.debug(f"Using cached result for {func.__name__}")
                    # Update state with cached result
                    if isinstance(cached_result, dict):
                        state.update(cached_result)
                    return state
                
                # Execute function
                result = func(state, *args, **kwargs)
                
                # Cache the result
                mcp_integration.cache_agent_result(
                    func.__name__, 
                    state, 
                    result, 
                    ttl_seconds
                )
                
                return result
                
            except Exception as e:
                logger.error(f"Error in MCP cache decorator for {func.__name__}: {str(e)}")
                return func(state, *args, **kwargs)
        
        return wrapper
    return decorator
