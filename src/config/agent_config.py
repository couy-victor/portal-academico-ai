"""
Agent configuration management for the Academic Agent system.
Provides centralized configuration for all agents.
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import os
from pathlib import Path

from src.config.settings import *


class AgentType(Enum):
    """Types of agents in the system."""
    ROUTER = "router"
    PROCESSOR = "processor"
    VALIDATOR = "validator"
    EXECUTOR = "executor"
    GENERATOR = "generator"
    SUPPORT = "support"


@dataclass
class AgentConfig:
    """Configuration for a single agent."""
    name: str
    type: AgentType
    description: str = ""
    enabled: bool = True
    timeout_seconds: int = 30
    max_retries: int = 3
    model: Optional[str] = None
    temperature: Optional[float] = None
    custom_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphConfig:
    """Configuration for the agent graph."""
    name: str
    description: str = ""
    max_execution_time: int = 300  # 5 minutes
    enable_parallel_execution: bool = False
    enable_fallback: bool = True
    enable_caching: bool = True


class AgentConfigManager:
    """
    Manages configuration for all agents in the system.
    """
    
    def __init__(self):
        """Initialize the configuration manager."""
        self._agent_configs: Dict[str, AgentConfig] = {}
        self._graph_config: Optional[GraphConfig] = None
        self._load_default_configs()
    
    def _load_default_configs(self) -> None:
        """Load default configurations for all agents."""
        
        # Router agents
        self.register_agent(AgentConfig(
            name="main_router",
            type=AgentType.ROUTER,
            description="Routes queries to appropriate specialized agents",
            temperature=0.1,
            timeout_seconds=15
        ))
        
        self.register_agent(AgentConfig(
            name="intent_router",
            type=AgentType.ROUTER,
            description="Routes academic queries based on intent",
            temperature=0.1,
            timeout_seconds=15
        ))
        
        # Processor agents
        self.register_agent(AgentConfig(
            name="user_context",
            type=AgentType.PROCESSOR,
            description="Enriches user context information",
            timeout_seconds=10
        ))
        
        self.register_agent(AgentConfig(
            name="schema_retriever",
            type=AgentType.PROCESSOR,
            description="Retrieves database schema information",
            timeout_seconds=20
        ))
        
        self.register_agent(AgentConfig(
            name="rag_agent",
            type=AgentType.PROCESSOR,
            description="Retrieves relevant documents using RAG",
            timeout_seconds=30
        ))
        
        self.register_agent(AgentConfig(
            name="tavily_search",
            type=AgentType.PROCESSOR,
            description="Searches web using Tavily API",
            timeout_seconds=25
        ))
        
        # Validator agents
        self.register_agent(AgentConfig(
            name="query_validator",
            type=AgentType.VALIDATOR,
            description="Validates SQL queries for safety and correctness",
            temperature=0.0,
            timeout_seconds=15
        ))
        
        self.register_agent(AgentConfig(
            name="dba_guard",
            type=AgentType.VALIDATOR,
            description="Optimizes and secures SQL queries",
            temperature=0.0,
            timeout_seconds=15
        ))
        
        # Executor agents
        self.register_agent(AgentConfig(
            name="executor",
            type=AgentType.EXECUTOR,
            description="Executes SQL queries on the database",
            timeout_seconds=45
        ))
        
        # Generator agents
        self.register_agent(AgentConfig(
            name="sql_generator",
            type=AgentType.GENERATOR,
            description="Generates SQL queries from natural language",
            temperature=0.1,
            timeout_seconds=30
        ))
        
        self.register_agent(AgentConfig(
            name="response_generator",
            type=AgentType.GENERATOR,
            description="Generates natural language responses",
            temperature=0.3,
            timeout_seconds=25
        ))
        
        # Specialized agents
        self.register_agent(AgentConfig(
            name="emotional_support",
            type=AgentType.SUPPORT,
            description="Provides emotional support to students",
            temperature=0.7,
            timeout_seconds=30,
            custom_settings={
                "empathy_level": "high",
                "crisis_detection": True,
                "human_intervention_threshold": "high"
            }
        ))
        
        self.register_agent(AgentConfig(
            name="tutor",
            type=AgentType.SUPPORT,
            description="Provides tutoring and educational support",
            temperature=0.5,
            timeout_seconds=45,
            custom_settings={
                "explanation_depth": "adaptive",
                "include_examples": True,
                "socratic_method": True
            }
        ))
        
        self.register_agent(AgentConfig(
            name="planning",
            type=AgentType.SUPPORT,
            description="Helps with academic planning and organization",
            temperature=0.4,
            timeout_seconds=35,
            custom_settings={
                "planning_methods": ["pomodoro", "time_blocking", "active_recall"],
                "export_formats": ["pdf", "ics", "html"]
            }
        ))
        
        # Support agents
        self.register_agent(AgentConfig(
            name="cache_agent",
            type=AgentType.SUPPORT,
            description="Manages caching of responses",
            timeout_seconds=5
        ))
        
        self.register_agent(AgentConfig(
            name="logger",
            type=AgentType.SUPPORT,
            description="Logs interactions and system events",
            timeout_seconds=5
        ))
        
        self.register_agent(AgentConfig(
            name="fallback_handler",
            type=AgentType.SUPPORT,
            description="Handles errors and provides fallback responses",
            temperature=0.6,
            timeout_seconds=15
        ))
        
        # Graph configuration
        self._graph_config = GraphConfig(
            name="academic_graph",
            description="Main academic agent graph",
            max_execution_time=TIMEOUT_SECONDS * 10,  # 10x individual timeout
            enable_parallel_execution=False,
            enable_fallback=True,
            enable_caching=CACHE_ENABLED
        )
    
    def register_agent(self, config: AgentConfig) -> None:
        """
        Register an agent configuration.
        
        Args:
            config (AgentConfig): Agent configuration to register
        """
        self._agent_configs[config.name] = config
    
    def get_agent_config(self, agent_name: str) -> Optional[AgentConfig]:
        """
        Get configuration for a specific agent.
        
        Args:
            agent_name (str): Name of the agent
            
        Returns:
            Optional[AgentConfig]: Agent configuration or None if not found
        """
        return self._agent_configs.get(agent_name)
    
    def get_graph_config(self) -> GraphConfig:
        """
        Get graph configuration.
        
        Returns:
            GraphConfig: Graph configuration
        """
        return self._graph_config
    
    def get_agents_by_type(self, agent_type: AgentType) -> List[AgentConfig]:
        """
        Get all agents of a specific type.
        
        Args:
            agent_type (AgentType): Type of agents to retrieve
            
        Returns:
            List[AgentConfig]: List of agent configurations
        """
        return [
            config for config in self._agent_configs.values()
            if config.type == agent_type and config.enabled
        ]
    
    def update_agent_config(self, agent_name: str, **kwargs) -> bool:
        """
        Update configuration for a specific agent.
        
        Args:
            agent_name (str): Name of the agent
            **kwargs: Configuration parameters to update
            
        Returns:
            bool: True if updated successfully, False if agent not found
        """
        if agent_name not in self._agent_configs:
            return False
        
        config = self._agent_configs[agent_name]
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        return True
    
    def disable_agent(self, agent_name: str) -> bool:
        """
        Disable a specific agent.
        
        Args:
            agent_name (str): Name of the agent to disable
            
        Returns:
            bool: True if disabled successfully, False if agent not found
        """
        return self.update_agent_config(agent_name, enabled=False)
    
    def enable_agent(self, agent_name: str) -> bool:
        """
        Enable a specific agent.
        
        Args:
            agent_name (str): Name of the agent to enable
            
        Returns:
            bool: True if enabled successfully, False if agent not found
        """
        return self.update_agent_config(agent_name, enabled=True)
    
    def get_enabled_agents(self) -> List[str]:
        """
        Get list of enabled agent names.
        
        Returns:
            List[str]: List of enabled agent names
        """
        return [
            name for name, config in self._agent_configs.items()
            if config.enabled
        ]
    
    def load_from_file(self, config_path: str) -> bool:
        """
        Load configuration from a file.
        
        Args:
            config_path (str): Path to configuration file
            
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        try:
            # Implementation for loading from JSON/YAML file
            # This would parse the file and update configurations
            pass
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            return False
        
        return True
    
    def save_to_file(self, config_path: str) -> bool:
        """
        Save current configuration to a file.
        
        Args:
            config_path (str): Path to save configuration file
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            # Implementation for saving to JSON/YAML file
            # This would serialize current configurations
            pass
        except Exception as e:
            logger.error(f"Failed to save config to {config_path}: {e}")
            return False
        
        return True


# Global configuration manager instance
config_manager = AgentConfigManager()
