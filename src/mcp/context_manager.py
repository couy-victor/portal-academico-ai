"""
MCP Context Manager implementation.
Manages context sharing and lifecycle across agents and models.
"""
from typing import Dict, Any, List, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import threading
import time
from collections import defaultdict

from src.mcp.protocol import MCPProtocol, MCPMessage, MCPResponse, MCPMessageType, MCPStatus
from src.utils.logging import logger


class ContextScope(Enum):
    """Context scope levels."""
    GLOBAL = "global"          # Available to all agents
    SESSION = "session"        # Available within a user session
    AGENT = "agent"           # Available only to specific agent
    TEMPORARY = "temporary"    # Short-lived context


class ContextType(Enum):
    """Types of context data."""
    USER_PROFILE = "user_profile"
    CONVERSATION = "conversation"
    DATABASE_SCHEMA = "database_schema"
    RAG_DOCUMENTS = "rag_documents"
    QUERY_HISTORY = "query_history"
    AGENT_STATE = "agent_state"
    SYSTEM_CONFIG = "system_config"
    METRICS = "metrics"


@dataclass
class ContextEntry:
    """A single context entry."""
    key: str
    context_type: ContextType
    scope: ContextScope
    data: Any
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if context entry is expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def access(self) -> None:
        """Record access to this context entry."""
        self.access_count += 1
        self.last_accessed = datetime.now()


class MCPContextManager:
    """
    Manages context sharing and lifecycle across agents and models.
    Implements the Model Context Protocol for standardized context management.
    """
    
    def __init__(self, cleanup_interval: int = 300):  # 5 minutes
        """
        Initialize the MCP Context Manager.
        
        Args:
            cleanup_interval (int): Interval in seconds for cleanup operations
        """
        self.protocol = MCPProtocol("context_manager")
        self.contexts: Dict[str, ContextEntry] = {}
        self.context_subscribers: Dict[str, Set[str]] = defaultdict(set)
        self.cleanup_interval = cleanup_interval
        self.lock = threading.RLock()
        self.running = False
        self.cleanup_thread: Optional[threading.Thread] = None
        
        # Register custom handlers
        self.protocol.register_handler(MCPMessageType.CONTEXT_REQUEST, self._handle_context_request)
        self.protocol.register_handler(MCPMessageType.CONTEXT_UPDATE, self._handle_context_update)
        
        logger.info("MCP Context Manager initialized")
    
    def start(self) -> None:
        """Start the context manager."""
        if self.running:
            return
        
        self.running = True
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        
        logger.info("MCP Context Manager started")
    
    def stop(self) -> None:
        """Stop the context manager."""
        self.running = False
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)
        
        logger.info("MCP Context Manager stopped")
    
    def set_context(
        self,
        key: str,
        data: Any,
        context_type: ContextType,
        scope: ContextScope = ContextScope.SESSION,
        ttl_seconds: Optional[int] = None,
        tags: Optional[Set[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Set context data.
        
        Args:
            key (str): Context key
            data (Any): Context data
            context_type (ContextType): Type of context
            scope (ContextScope): Context scope
            ttl_seconds (Optional[int]): Time to live in seconds
            tags (Optional[Set[str]]): Context tags
            metadata (Optional[Dict[str, Any]]): Additional metadata
            
        Returns:
            bool: True if successful
        """
        try:
            with self.lock:
                expires_at = None
                if ttl_seconds:
                    expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
                
                # Update existing or create new context entry
                if key in self.contexts:
                    entry = self.contexts[key]
                    entry.data = data
                    entry.updated_at = datetime.now()
                    entry.expires_at = expires_at
                    if tags:
                        entry.tags.update(tags)
                    if metadata:
                        entry.metadata.update(metadata)
                else:
                    entry = ContextEntry(
                        key=key,
                        context_type=context_type,
                        scope=scope,
                        data=data,
                        expires_at=expires_at,
                        tags=tags or set(),
                        metadata=metadata or {}
                    )
                    self.contexts[key] = entry
                
                # Notify subscribers
                self._notify_subscribers(key, "update", entry)
                
                logger.debug(f"Set context: {key} (type: {context_type.value}, scope: {scope.value})")
                return True
                
        except Exception as e:
            logger.error(f"Error setting context {key}: {str(e)}")
            return False
    
    def get_context(self, key: str, requester_id: str = None) -> Optional[Any]:
        """
        Get context data.
        
        Args:
            key (str): Context key
            requester_id (str): ID of the requesting agent
            
        Returns:
            Optional[Any]: Context data or None if not found
        """
        try:
            with self.lock:
                if key not in self.contexts:
                    return None
                
                entry = self.contexts[key]
                
                # Check if expired
                if entry.is_expired():
                    del self.contexts[key]
                    return None
                
                # Check scope permissions (simplified)
                if entry.scope == ContextScope.AGENT and requester_id:
                    # In a real implementation, you'd check if requester has access
                    pass
                
                # Record access
                entry.access()
                
                logger.debug(f"Retrieved context: {key} (accessed {entry.access_count} times)")
                return entry.data
                
        except Exception as e:
            logger.error(f"Error getting context {key}: {str(e)}")
            return None
    
    def delete_context(self, key: str) -> bool:
        """
        Delete context data.
        
        Args:
            key (str): Context key
            
        Returns:
            bool: True if successful
        """
        try:
            with self.lock:
                if key in self.contexts:
                    entry = self.contexts[key]
                    del self.contexts[key]
                    
                    # Notify subscribers
                    self._notify_subscribers(key, "delete", entry)
                    
                    logger.debug(f"Deleted context: {key}")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Error deleting context {key}: {str(e)}")
            return False
    
    def list_contexts(
        self,
        context_type: Optional[ContextType] = None,
        scope: Optional[ContextScope] = None,
        tags: Optional[Set[str]] = None
    ) -> List[str]:
        """
        List context keys matching criteria.
        
        Args:
            context_type (Optional[ContextType]): Filter by context type
            scope (Optional[ContextScope]): Filter by scope
            tags (Optional[Set[str]]): Filter by tags
            
        Returns:
            List[str]: List of matching context keys
        """
        try:
            with self.lock:
                matching_keys = []
                
                for key, entry in self.contexts.items():
                    # Skip expired entries
                    if entry.is_expired():
                        continue
                    
                    # Apply filters
                    if context_type and entry.context_type != context_type:
                        continue
                    if scope and entry.scope != scope:
                        continue
                    if tags and not tags.issubset(entry.tags):
                        continue
                    
                    matching_keys.append(key)
                
                return matching_keys
                
        except Exception as e:
            logger.error(f"Error listing contexts: {str(e)}")
            return []
    
    def subscribe_to_context(self, key: str, subscriber_id: str) -> bool:
        """
        Subscribe to context updates.
        
        Args:
            key (str): Context key to subscribe to
            subscriber_id (str): ID of the subscriber
            
        Returns:
            bool: True if successful
        """
        try:
            with self.lock:
                self.context_subscribers[key].add(subscriber_id)
                logger.debug(f"Agent {subscriber_id} subscribed to context {key}")
                return True
                
        except Exception as e:
            logger.error(f"Error subscribing to context {key}: {str(e)}")
            return False
    
    def unsubscribe_from_context(self, key: str, subscriber_id: str) -> bool:
        """
        Unsubscribe from context updates.
        
        Args:
            key (str): Context key to unsubscribe from
            subscriber_id (str): ID of the subscriber
            
        Returns:
            bool: True if successful
        """
        try:
            with self.lock:
                if key in self.context_subscribers:
                    self.context_subscribers[key].discard(subscriber_id)
                    logger.debug(f"Agent {subscriber_id} unsubscribed from context {key}")
                return True
                
        except Exception as e:
            logger.error(f"Error unsubscribing from context {key}: {str(e)}")
            return False
    
    def get_context_info(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get context metadata and statistics.
        
        Args:
            key (str): Context key
            
        Returns:
            Optional[Dict[str, Any]]: Context information
        """
        try:
            with self.lock:
                if key not in self.contexts:
                    return None
                
                entry = self.contexts[key]
                
                return {
                    "key": entry.key,
                    "context_type": entry.context_type.value,
                    "scope": entry.scope.value,
                    "created_at": entry.created_at.isoformat(),
                    "updated_at": entry.updated_at.isoformat(),
                    "expires_at": entry.expires_at.isoformat() if entry.expires_at else None,
                    "access_count": entry.access_count,
                    "last_accessed": entry.last_accessed.isoformat() if entry.last_accessed else None,
                    "tags": list(entry.tags),
                    "metadata": entry.metadata,
                    "is_expired": entry.is_expired(),
                    "data_size": len(str(entry.data)) if entry.data else 0
                }
                
        except Exception as e:
            logger.error(f"Error getting context info {key}: {str(e)}")
            return None
    
    def cleanup_expired_contexts(self) -> int:
        """
        Clean up expired contexts.
        
        Returns:
            int: Number of contexts cleaned up
        """
        try:
            with self.lock:
                expired_keys = []
                
                for key, entry in self.contexts.items():
                    if entry.is_expired():
                        expired_keys.append(key)
                
                for key in expired_keys:
                    entry = self.contexts[key]
                    del self.contexts[key]
                    self._notify_subscribers(key, "expire", entry)
                
                if expired_keys:
                    logger.info(f"Cleaned up {len(expired_keys)} expired contexts")
                
                return len(expired_keys)
                
        except Exception as e:
            logger.error(f"Error during context cleanup: {str(e)}")
            return 0
    
    def _notify_subscribers(self, key: str, action: str, entry: ContextEntry) -> None:
        """Notify subscribers of context changes."""
        if key not in self.context_subscribers:
            return
        
        for subscriber_id in self.context_subscribers[key]:
            try:
                # In a real implementation, you'd send actual notifications
                logger.debug(f"Notifying {subscriber_id} of {action} on context {key}")
            except Exception as e:
                logger.error(f"Error notifying subscriber {subscriber_id}: {str(e)}")
    
    def _cleanup_loop(self) -> None:
        """Background cleanup loop."""
        while self.running:
            try:
                self.cleanup_expired_contexts()
                time.sleep(self.cleanup_interval)
            except Exception as e:
                logger.error(f"Error in cleanup loop: {str(e)}")
                time.sleep(60)  # Wait a minute before retrying
    
    def _handle_context_request(self, message: MCPMessage) -> MCPResponse:
        """Handle context request from MCP protocol."""
        context_key = message.payload.get("context_key")
        requester_id = message.payload.get("requester_id")
        
        if not context_key:
            return MCPResponse(
                request_id=message.message_id,
                status=MCPStatus.ERROR,
                error_message="Missing context_key in request"
            )
        
        context_data = self.get_context(context_key, requester_id)
        
        if context_data is None:
            return MCPResponse(
                request_id=message.message_id,
                status=MCPStatus.ERROR,
                error_message="Context not found"
            )
        
        return MCPResponse(
            request_id=message.message_id,
            status=MCPStatus.SUCCESS,
            data={
                "context_key": context_key,
                "context_data": context_data
            }
        )
    
    def _handle_context_update(self, message: MCPMessage) -> MCPResponse:
        """Handle context update from MCP protocol."""
        context_key = message.payload.get("context_key")
        context_data = message.payload.get("context_data")
        context_type_str = message.payload.get("context_type", "agent_state")
        
        if not context_key or context_data is None:
            return MCPResponse(
                request_id=message.message_id,
                status=MCPStatus.ERROR,
                error_message="Missing context_key or context_data in update"
            )
        
        try:
            context_type = ContextType(context_type_str)
        except ValueError:
            context_type = ContextType.AGENT_STATE
        
        success = self.set_context(
            key=context_key,
            data=context_data,
            context_type=context_type,
            scope=ContextScope.SESSION
        )
        
        if success:
            return MCPResponse(
                request_id=message.message_id,
                status=MCPStatus.SUCCESS
            )
        else:
            return MCPResponse(
                request_id=message.message_id,
                status=MCPStatus.ERROR,
                error_message="Failed to update context"
            )


# Global context manager instance
context_manager = MCPContextManager()
