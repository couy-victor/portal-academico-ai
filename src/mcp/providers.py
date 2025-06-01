"""
MCP Context Providers implementation.
Provides specialized context providers for different data sources.
"""
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
import json
from datetime import datetime, timedelta

from src.mcp.context_manager import MCPContextManager, ContextType, ContextScope
from src.models.state import AcademicAgentState
from src.utils.logging import logger


class BaseContextProvider(ABC):
    """
    Base class for context providers.
    """
    
    def __init__(self, provider_id: str, context_manager: MCPContextManager):
        """
        Initialize the context provider.
        
        Args:
            provider_id (str): Unique identifier for this provider
            context_manager (MCPContextManager): Context manager instance
        """
        self.provider_id = provider_id
        self.context_manager = context_manager
        self.enabled = True
        
        logger.info(f"Context provider {provider_id} initialized")
    
    @abstractmethod
    def provide_context(self, context_key: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Provide context data for the given key.
        
        Args:
            context_key (str): Context key to provide data for
            **kwargs: Additional parameters
            
        Returns:
            Optional[Dict[str, Any]]: Context data or None if not available
        """
        pass
    
    @abstractmethod
    def get_supported_context_types(self) -> List[ContextType]:
        """
        Get list of context types supported by this provider.
        
        Returns:
            List[ContextType]: Supported context types
        """
        pass
    
    def is_enabled(self) -> bool:
        """Check if provider is enabled."""
        return self.enabled
    
    def enable(self) -> None:
        """Enable the provider."""
        self.enabled = True
        logger.info(f"Context provider {self.provider_id} enabled")
    
    def disable(self) -> None:
        """Disable the provider."""
        self.enabled = False
        logger.info(f"Context provider {self.provider_id} disabled")


class UserContextProvider(BaseContextProvider):
    """
    Provides user-related context data.
    """
    
    def __init__(self, context_manager: MCPContextManager):
        """Initialize the user context provider."""
        super().__init__("user_context_provider", context_manager)
    
    def provide_context(self, context_key: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Provide user context data.
        
        Args:
            context_key (str): User ID or context key
            **kwargs: Additional parameters
            
        Returns:
            Optional[Dict[str, Any]]: User context data
        """
        if not self.enabled:
            return None
        
        try:
            # Extract user_id from context_key or kwargs
            user_id = kwargs.get("user_id", context_key)
            
            # Try to get from context manager first
            cached_context = self.context_manager.get_context(f"user_profile:{user_id}")
            if cached_context:
                return cached_context
            
            # Fetch user context from database or external source
            user_context = self._fetch_user_context(user_id)
            
            if user_context:
                # Cache the context for future use
                self.context_manager.set_context(
                    key=f"user_profile:{user_id}",
                    data=user_context,
                    context_type=ContextType.USER_PROFILE,
                    scope=ContextScope.SESSION,
                    ttl_seconds=3600  # 1 hour
                )
            
            return user_context
            
        except Exception as e:
            logger.error(f"Error providing user context for {context_key}: {str(e)}")
            return None
    
    def get_supported_context_types(self) -> List[ContextType]:
        """Get supported context types."""
        return [ContextType.USER_PROFILE]
    
    def _fetch_user_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch user context from data source.
        
        Args:
            user_id (str): User ID
            
        Returns:
            Optional[Dict[str, Any]]: User context data
        """
        try:
            # In a real implementation, this would query the database
            # For now, return a mock user context
            return {
                "user_id": user_id,
                "name": f"User {user_id}",
                "course": "Computer Science",
                "semester": "2023.2",
                "preferences": {
                    "language": "pt-BR",
                    "notification_enabled": True
                },
                "last_login": datetime.now().isoformat(),
                "session_count": 1
            }
            
        except Exception as e:
            logger.error(f"Error fetching user context for {user_id}: {str(e)}")
            return None


class ConversationContextProvider(BaseContextProvider):
    """
    Provides conversation history and context.
    """
    
    def __init__(self, context_manager: MCPContextManager):
        """Initialize the conversation context provider."""
        super().__init__("conversation_context_provider", context_manager)
        self.max_history_length = 50  # Maximum number of conversation turns to keep
    
    def provide_context(self, context_key: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Provide conversation context data.
        
        Args:
            context_key (str): Conversation ID or session ID
            **kwargs: Additional parameters
            
        Returns:
            Optional[Dict[str, Any]]: Conversation context data
        """
        if not self.enabled:
            return None
        
        try:
            session_id = kwargs.get("session_id", context_key)
            
            # Get conversation history from context manager
            conversation_data = self.context_manager.get_context(f"conversation:{session_id}")
            
            if not conversation_data:
                # Initialize new conversation
                conversation_data = {
                    "session_id": session_id,
                    "started_at": datetime.now().isoformat(),
                    "turns": [],
                    "summary": "",
                    "topics": [],
                    "sentiment": "neutral"
                }
                
                self.context_manager.set_context(
                    key=f"conversation:{session_id}",
                    data=conversation_data,
                    context_type=ContextType.CONVERSATION,
                    scope=ContextScope.SESSION,
                    ttl_seconds=7200  # 2 hours
                )
            
            return conversation_data
            
        except Exception as e:
            logger.error(f"Error providing conversation context for {context_key}: {str(e)}")
            return None
    
    def add_conversation_turn(
        self, 
        session_id: str, 
        user_message: str, 
        agent_response: str,
        intent: str = None,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Add a conversation turn to the history.
        
        Args:
            session_id (str): Session ID
            user_message (str): User's message
            agent_response (str): Agent's response
            intent (str): Detected intent
            metadata (Dict[str, Any]): Additional metadata
            
        Returns:
            bool: True if successful
        """
        try:
            conversation_data = self.provide_context(session_id)
            if not conversation_data:
                return False
            
            # Add new turn
            turn = {
                "timestamp": datetime.now().isoformat(),
                "user_message": user_message,
                "agent_response": agent_response,
                "intent": intent,
                "metadata": metadata or {}
            }
            
            conversation_data["turns"].append(turn)
            
            # Limit history length
            if len(conversation_data["turns"]) > self.max_history_length:
                conversation_data["turns"] = conversation_data["turns"][-self.max_history_length:]
            
            # Update context
            self.context_manager.set_context(
                key=f"conversation:{session_id}",
                data=conversation_data,
                context_type=ContextType.CONVERSATION,
                scope=ContextScope.SESSION,
                ttl_seconds=7200
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding conversation turn for {session_id}: {str(e)}")
            return False
    
    def get_supported_context_types(self) -> List[ContextType]:
        """Get supported context types."""
        return [ContextType.CONVERSATION, ContextType.QUERY_HISTORY]


class DatabaseContextProvider(BaseContextProvider):
    """
    Provides database schema and query context.
    """
    
    def __init__(self, context_manager: MCPContextManager):
        """Initialize the database context provider."""
        super().__init__("database_context_provider", context_manager)
    
    def provide_context(self, context_key: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Provide database context data.
        
        Args:
            context_key (str): Database context key
            **kwargs: Additional parameters
            
        Returns:
            Optional[Dict[str, Any]]: Database context data
        """
        if not self.enabled:
            return None
        
        try:
            if context_key == "schema":
                return self._get_database_schema()
            elif context_key.startswith("table:"):
                table_name = context_key.split(":", 1)[1]
                return self._get_table_info(table_name)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error providing database context for {context_key}: {str(e)}")
            return None
    
    def get_supported_context_types(self) -> List[ContextType]:
        """Get supported context types."""
        return [ContextType.DATABASE_SCHEMA]
    
    def _get_database_schema(self) -> Optional[Dict[str, Any]]:
        """Get database schema information."""
        try:
            # Check cache first
            cached_schema = self.context_manager.get_context("database_schema")
            if cached_schema:
                return cached_schema
            
            # In a real implementation, this would query the database
            # For now, return a mock schema
            schema_data = {
                "tables": [
                    {
                        "name": "students",
                        "columns": [
                            {"name": "id", "type": "integer", "primary_key": True},
                            {"name": "name", "type": "varchar(255)"},
                            {"name": "email", "type": "varchar(255)"},
                            {"name": "course_id", "type": "integer"}
                        ]
                    },
                    {
                        "name": "courses",
                        "columns": [
                            {"name": "id", "type": "integer", "primary_key": True},
                            {"name": "name", "type": "varchar(255)"},
                            {"name": "code", "type": "varchar(10)"}
                        ]
                    }
                ],
                "relationships": [
                    {
                        "from_table": "students",
                        "from_column": "course_id",
                        "to_table": "courses",
                        "to_column": "id"
                    }
                ],
                "last_updated": datetime.now().isoformat()
            }
            
            # Cache the schema
            self.context_manager.set_context(
                key="database_schema",
                data=schema_data,
                context_type=ContextType.DATABASE_SCHEMA,
                scope=ContextScope.GLOBAL,
                ttl_seconds=86400  # 24 hours
            )
            
            return schema_data
            
        except Exception as e:
            logger.error(f"Error getting database schema: {str(e)}")
            return None
    
    def _get_table_info(self, table_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific table."""
        schema = self._get_database_schema()
        if not schema:
            return None
        
        for table in schema.get("tables", []):
            if table["name"] == table_name:
                return table
        
        return None


class RAGContextProvider(BaseContextProvider):
    """
    Provides RAG (Retrieval-Augmented Generation) context.
    """
    
    def __init__(self, context_manager: MCPContextManager):
        """Initialize the RAG context provider."""
        super().__init__("rag_context_provider", context_manager)
    
    def provide_context(self, context_key: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Provide RAG context data.
        
        Args:
            context_key (str): Query or document key
            **kwargs: Additional parameters
            
        Returns:
            Optional[Dict[str, Any]]: RAG context data
        """
        if not self.enabled:
            return None
        
        try:
            query = kwargs.get("query", context_key)
            top_k = kwargs.get("top_k", 5)
            
            # Check cache first
            cache_key = f"rag_documents:{hash(query)}"
            cached_docs = self.context_manager.get_context(cache_key)
            if cached_docs:
                return cached_docs
            
            # Retrieve relevant documents
            documents = self._retrieve_documents(query, top_k)
            
            if documents:
                # Cache the results
                self.context_manager.set_context(
                    key=cache_key,
                    data=documents,
                    context_type=ContextType.RAG_DOCUMENTS,
                    scope=ContextScope.SESSION,
                    ttl_seconds=1800  # 30 minutes
                )
            
            return documents
            
        except Exception as e:
            logger.error(f"Error providing RAG context for {context_key}: {str(e)}")
            return None
    
    def get_supported_context_types(self) -> List[ContextType]:
        """Get supported context types."""
        return [ContextType.RAG_DOCUMENTS]
    
    def _retrieve_documents(self, query: str, top_k: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve relevant documents for the query.
        
        Args:
            query (str): Search query
            top_k (int): Number of documents to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: Retrieved documents
        """
        try:
            # In a real implementation, this would use vector search
            # For now, return mock documents
            return {
                "query": query,
                "documents": [
                    {
                        "id": f"doc_{i}",
                        "title": f"Document {i}",
                        "content": f"This is the content of document {i} related to {query}",
                        "score": 0.9 - (i * 0.1),
                        "metadata": {"source": f"source_{i}"}
                    }
                    for i in range(min(top_k, 3))
                ],
                "retrieved_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error retrieving documents for query '{query}': {str(e)}")
            return None
