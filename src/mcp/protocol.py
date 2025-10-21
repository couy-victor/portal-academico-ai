"""
Core MCP Protocol implementation.
Defines the standard protocol for context sharing between agents and models.
"""
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid

from src.utils.logging import logger


class MCPMessageType(Enum):
    """Types of MCP messages."""
    CONTEXT_REQUEST = "context_request"
    CONTEXT_RESPONSE = "context_response"
    CONTEXT_UPDATE = "context_update"
    CONTEXT_INVALIDATE = "context_invalidate"
    HEARTBEAT = "heartbeat"
    ERROR = "error"


class MCPStatus(Enum):
    """MCP operation status."""
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"
    TIMEOUT = "timeout"


@dataclass
class MCPMessage:
    """
    Standard MCP message format.
    """
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_type: MCPMessageType = MCPMessageType.CONTEXT_REQUEST
    sender_id: str = ""
    recipient_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPMessage':
        """Create message from dictionary."""
        return cls(
            message_id=data.get("message_id", str(uuid.uuid4())),
            message_type=MCPMessageType(data.get("message_type", "context_request")),
            sender_id=data.get("sender_id", ""),
            recipient_id=data.get("recipient_id", ""),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
            payload=data.get("payload", {}),
            metadata=data.get("metadata", {})
        )


@dataclass
class MCPResponse:
    """
    Standard MCP response format.
    """
    request_id: str
    status: MCPStatus
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {
            "request_id": self.request_id,
            "status": self.status.value,
            "data": self.data,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPResponse':
        """Create response from dictionary."""
        return cls(
            request_id=data["request_id"],
            status=MCPStatus(data["status"]),
            data=data.get("data"),
            error_message=data.get("error_message"),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
            metadata=data.get("metadata", {})
        )


class MCPProtocol:
    """
    Core MCP Protocol implementation.
    Handles message routing, validation, and processing.
    """
    
    def __init__(self, agent_id: str):
        """
        Initialize MCP Protocol.
        
        Args:
            agent_id (str): Unique identifier for this agent
        """
        self.agent_id = agent_id
        self.message_handlers: Dict[MCPMessageType, callable] = {}
        self.pending_requests: Dict[str, MCPMessage] = {}
        self.context_cache: Dict[str, Any] = {}
        
        # Register default handlers
        self._register_default_handlers()
        
        logger.info(f"MCP Protocol initialized for agent: {agent_id}")
    
    def _register_default_handlers(self) -> None:
        """Register default message handlers."""
        self.register_handler(MCPMessageType.CONTEXT_REQUEST, self._handle_context_request)
        self.register_handler(MCPMessageType.CONTEXT_RESPONSE, self._handle_context_response)
        self.register_handler(MCPMessageType.CONTEXT_UPDATE, self._handle_context_update)
        self.register_handler(MCPMessageType.CONTEXT_INVALIDATE, self._handle_context_invalidate)
        self.register_handler(MCPMessageType.HEARTBEAT, self._handle_heartbeat)
        self.register_handler(MCPMessageType.ERROR, self._handle_error)
    
    def register_handler(self, message_type: MCPMessageType, handler: callable) -> None:
        """
        Register a message handler.
        
        Args:
            message_type (MCPMessageType): Type of message to handle
            handler (callable): Handler function
        """
        self.message_handlers[message_type] = handler
        logger.debug(f"Registered handler for {message_type.value}")
    
    def send_message(self, message: MCPMessage) -> MCPResponse:
        """
        Send an MCP message.
        
        Args:
            message (MCPMessage): Message to send
            
        Returns:
            MCPResponse: Response from recipient
        """
        try:
            # Set sender ID
            message.sender_id = self.agent_id
            
            # Validate message
            if not self._validate_message(message):
                return MCPResponse(
                    request_id=message.message_id,
                    status=MCPStatus.ERROR,
                    error_message="Invalid message format"
                )
            
            # Store pending request
            if message.message_type == MCPMessageType.CONTEXT_REQUEST:
                self.pending_requests[message.message_id] = message
            
            # Process message (in a real implementation, this would route to the recipient)
            response = self._process_message(message)
            
            logger.debug(f"Sent message {message.message_id} to {message.recipient_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return MCPResponse(
                request_id=message.message_id,
                status=MCPStatus.ERROR,
                error_message=str(e)
            )
    
    def receive_message(self, message: MCPMessage) -> MCPResponse:
        """
        Receive and process an MCP message.
        
        Args:
            message (MCPMessage): Received message
            
        Returns:
            MCPResponse: Response to the message
        """
        try:
            # Validate message
            if not self._validate_message(message):
                return MCPResponse(
                    request_id=message.message_id,
                    status=MCPStatus.ERROR,
                    error_message="Invalid message format"
                )
            
            # Get handler for message type
            handler = self.message_handlers.get(message.message_type)
            if not handler:
                return MCPResponse(
                    request_id=message.message_id,
                    status=MCPStatus.ERROR,
                    error_message=f"No handler for message type: {message.message_type.value}"
                )
            
            # Process message
            response = handler(message)
            
            logger.debug(f"Processed message {message.message_id} from {message.sender_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return MCPResponse(
                request_id=message.message_id,
                status=MCPStatus.ERROR,
                error_message=str(e)
            )
    
    def request_context(
        self, 
        context_type: str, 
        context_key: str, 
        recipient_id: str = "context_manager"
    ) -> MCPResponse:
        """
        Request context from another agent or context provider.
        
        Args:
            context_type (str): Type of context requested
            context_key (str): Key identifying the context
            recipient_id (str): ID of the context provider
            
        Returns:
            MCPResponse: Context response
        """
        message = MCPMessage(
            message_type=MCPMessageType.CONTEXT_REQUEST,
            recipient_id=recipient_id,
            payload={
                "context_type": context_type,
                "context_key": context_key,
                "requester_id": self.agent_id
            }
        )
        
        return self.send_message(message)
    
    def update_context(
        self, 
        context_type: str, 
        context_key: str, 
        context_data: Dict[str, Any],
        recipient_id: str = "context_manager"
    ) -> MCPResponse:
        """
        Update context in the system.
        
        Args:
            context_type (str): Type of context to update
            context_key (str): Key identifying the context
            context_data (Dict[str, Any]): Context data to update
            recipient_id (str): ID of the context manager
            
        Returns:
            MCPResponse: Update response
        """
        message = MCPMessage(
            message_type=MCPMessageType.CONTEXT_UPDATE,
            recipient_id=recipient_id,
            payload={
                "context_type": context_type,
                "context_key": context_key,
                "context_data": context_data,
                "updater_id": self.agent_id
            }
        )
        
        return self.send_message(message)
    
    def _validate_message(self, message: MCPMessage) -> bool:
        """Validate MCP message format."""
        if not message.message_id:
            return False
        if not message.message_type:
            return False
        if not isinstance(message.payload, dict):
            return False
        return True
    
    def _process_message(self, message: MCPMessage) -> MCPResponse:
        """Process a message (placeholder for routing logic)."""
        # In a real implementation, this would route the message to the appropriate recipient
        # For now, we'll just return a success response
        return MCPResponse(
            request_id=message.message_id,
            status=MCPStatus.SUCCESS,
            data={"message": "Message processed successfully"}
        )
    
    # Default message handlers
    def _handle_context_request(self, message: MCPMessage) -> MCPResponse:
        """Handle context request message."""
        context_type = message.payload.get("context_type")
        context_key = message.payload.get("context_key")
        
        # Check cache first
        cache_key = f"{context_type}:{context_key}"
        if cache_key in self.context_cache:
            return MCPResponse(
                request_id=message.message_id,
                status=MCPStatus.SUCCESS,
                data={"context": self.context_cache[cache_key]}
            )
        
        # Context not found
        return MCPResponse(
            request_id=message.message_id,
            status=MCPStatus.ERROR,
            error_message="Context not found"
        )
    
    def _handle_context_response(self, message: MCPMessage) -> MCPResponse:
        """Handle context response message."""
        # Update local cache with received context
        context_data = message.payload.get("context")
        if context_data:
            context_type = message.payload.get("context_type")
            context_key = message.payload.get("context_key")
            cache_key = f"{context_type}:{context_key}"
            self.context_cache[cache_key] = context_data
        
        return MCPResponse(
            request_id=message.message_id,
            status=MCPStatus.SUCCESS
        )
    
    def _handle_context_update(self, message: MCPMessage) -> MCPResponse:
        """Handle context update message."""
        context_type = message.payload.get("context_type")
        context_key = message.payload.get("context_key")
        context_data = message.payload.get("context_data")
        
        # Update cache
        cache_key = f"{context_type}:{context_key}"
        self.context_cache[cache_key] = context_data
        
        return MCPResponse(
            request_id=message.message_id,
            status=MCPStatus.SUCCESS
        )
    
    def _handle_context_invalidate(self, message: MCPMessage) -> MCPResponse:
        """Handle context invalidation message."""
        context_type = message.payload.get("context_type")
        context_key = message.payload.get("context_key")
        
        # Remove from cache
        cache_key = f"{context_type}:{context_key}"
        if cache_key in self.context_cache:
            del self.context_cache[cache_key]
        
        return MCPResponse(
            request_id=message.message_id,
            status=MCPStatus.SUCCESS
        )
    
    def _handle_heartbeat(self, message: MCPMessage) -> MCPResponse:
        """Handle heartbeat message."""
        return MCPResponse(
            request_id=message.message_id,
            status=MCPStatus.SUCCESS,
            data={"agent_id": self.agent_id, "status": "alive"}
        )
    
    def _handle_error(self, message: MCPMessage) -> MCPResponse:
        """Handle error message."""
        error_msg = message.payload.get("error_message", "Unknown error")
        logger.error(f"Received error message: {error_msg}")
        
        return MCPResponse(
            request_id=message.message_id,
            status=MCPStatus.SUCCESS
        )
