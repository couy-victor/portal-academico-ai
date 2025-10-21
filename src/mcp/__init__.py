"""
Model Context Protocol (MCP) implementation for the Academic Agent system.
Provides standardized context management and sharing between agents and models.
"""

from .context_manager import MCPContextManager, ContextScope, ContextType
from .protocol import MCPProtocol, MCPMessage, MCPResponse
from .providers import (
    DatabaseContextProvider,
    RAGContextProvider, 
    UserContextProvider,
    ConversationContextProvider
)
from .serializers import JSONContextSerializer, ProtobufContextSerializer

__all__ = [
    'MCPContextManager',
    'MCPProtocol', 
    'MCPMessage',
    'MCPResponse',
    'ContextScope',
    'ContextType',
    'DatabaseContextProvider',
    'RAGContextProvider',
    'UserContextProvider', 
    'ConversationContextProvider',
    'JSONContextSerializer',
    'ProtobufContextSerializer'
]
