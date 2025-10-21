"""
Metrics and monitoring utilities for the Academic Agent system.
Provides comprehensive monitoring of agent performance and system health.
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import time
import json
import threading
from enum import Enum

from src.utils.logging import logger


class MetricType(Enum):
    """Types of metrics collected."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class MetricData:
    """Data structure for a single metric."""
    name: str
    type: MetricType
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    description: str = ""


@dataclass
class AgentMetrics:
    """Metrics for a single agent."""
    agent_name: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    skipped_executions: int = 0
    total_execution_time: float = 0.0
    min_execution_time: float = float('inf')
    max_execution_time: float = 0.0
    avg_execution_time: float = 0.0
    last_execution: Optional[datetime] = None
    error_rate: float = 0.0
    
    def update_execution(self, execution_time: float, success: bool, skipped: bool = False):
        """Update metrics after an execution."""
        self.total_executions += 1
        self.last_execution = datetime.now()
        
        if skipped:
            self.skipped_executions += 1
            return
        
        if success:
            self.successful_executions += 1
        else:
            self.failed_executions += 1
        
        # Update timing metrics
        self.total_execution_time += execution_time
        self.min_execution_time = min(self.min_execution_time, execution_time)
        self.max_execution_time = max(self.max_execution_time, execution_time)
        
        # Calculate average execution time (excluding skipped)
        executed_count = self.successful_executions + self.failed_executions
        if executed_count > 0:
            self.avg_execution_time = self.total_execution_time / executed_count
        
        # Calculate error rate
        if self.total_executions > 0:
            self.error_rate = self.failed_executions / (self.successful_executions + self.failed_executions)


@dataclass
class SystemMetrics:
    """System-wide metrics."""
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    cached_responses: int = 0
    cache_hit_rate: float = 0.0
    avg_response_time: float = 0.0
    uptime: timedelta = field(default_factory=lambda: timedelta(0))
    start_time: datetime = field(default_factory=datetime.now)
    
    def update_query(self, success: bool, response_time: float, from_cache: bool = False):
        """Update metrics after a query."""
        self.total_queries += 1
        
        if from_cache:
            self.cached_responses += 1
        
        if success:
            self.successful_queries += 1
        else:
            self.failed_queries += 1
        
        # Update cache hit rate
        if self.total_queries > 0:
            self.cache_hit_rate = self.cached_responses / self.total_queries
        
        # Update average response time
        if self.successful_queries > 0:
            total_time = self.avg_response_time * (self.successful_queries - 1) + response_time
            self.avg_response_time = total_time / self.successful_queries
        
        # Update uptime
        self.uptime = datetime.now() - self.start_time


class MetricsCollector:
    """
    Collects and manages metrics for the Academic Agent system.
    """
    
    def __init__(self, max_history_size: int = 1000):
        """
        Initialize the metrics collector.
        
        Args:
            max_history_size (int): Maximum number of historical metrics to keep
        """
        self.max_history_size = max_history_size
        self._agent_metrics: Dict[str, AgentMetrics] = {}
        self._system_metrics = SystemMetrics()
        self._metric_history: deque = deque(maxlen=max_history_size)
        self._custom_metrics: Dict[str, List[MetricData]] = defaultdict(list)
        self._lock = threading.Lock()
        
        # Performance tracking
        self._query_times: deque = deque(maxlen=100)  # Last 100 query times
        self._error_counts: Dict[str, int] = defaultdict(int)
        
        logger.info("MetricsCollector initialized")
    
    def record_agent_execution(
        self, 
        agent_name: str, 
        execution_time: float, 
        success: bool, 
        skipped: bool = False,
        error_type: Optional[str] = None
    ) -> None:
        """
        Record an agent execution.
        
        Args:
            agent_name (str): Name of the agent
            execution_time (float): Execution time in seconds
            success (bool): Whether execution was successful
            skipped (bool): Whether execution was skipped
            error_type (Optional[str]): Type of error if failed
        """
        with self._lock:
            if agent_name not in self._agent_metrics:
                self._agent_metrics[agent_name] = AgentMetrics(agent_name=agent_name)
            
            self._agent_metrics[agent_name].update_execution(execution_time, success, skipped)
            
            # Record error type if provided
            if not success and error_type:
                self._error_counts[f"{agent_name}:{error_type}"] += 1
            
            # Add to history
            metric = MetricData(
                name="agent_execution",
                type=MetricType.TIMER,
                value=execution_time,
                timestamp=datetime.now(),
                labels={
                    "agent": agent_name,
                    "success": str(success),
                    "skipped": str(skipped)
                }
            )
            self._metric_history.append(metric)
    
    def record_query(
        self, 
        success: bool, 
        response_time: float, 
        from_cache: bool = False,
        intent: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> None:
        """
        Record a query execution.
        
        Args:
            success (bool): Whether query was successful
            response_time (float): Response time in seconds
            from_cache (bool): Whether response came from cache
            intent (Optional[str]): Detected intent
            user_id (Optional[str]): User ID
        """
        with self._lock:
            self._system_metrics.update_query(success, response_time, from_cache)
            self._query_times.append(response_time)
            
            # Add to history
            metric = MetricData(
                name="query_execution",
                type=MetricType.TIMER,
                value=response_time,
                timestamp=datetime.now(),
                labels={
                    "success": str(success),
                    "from_cache": str(from_cache),
                    "intent": intent or "unknown",
                    "user_id": user_id or "anonymous"
                }
            )
            self._metric_history.append(metric)
    
    def record_custom_metric(
        self, 
        name: str, 
        value: float, 
        metric_type: MetricType = MetricType.GAUGE,
        labels: Optional[Dict[str, str]] = None,
        description: str = ""
    ) -> None:
        """
        Record a custom metric.
        
        Args:
            name (str): Metric name
            value (float): Metric value
            metric_type (MetricType): Type of metric
            labels (Optional[Dict[str, str]]): Metric labels
            description (str): Metric description
        """
        with self._lock:
            metric = MetricData(
                name=name,
                type=metric_type,
                value=value,
                timestamp=datetime.now(),
                labels=labels or {},
                description=description
            )
            
            self._custom_metrics[name].append(metric)
            self._metric_history.append(metric)
            
            # Keep only recent custom metrics
            if len(self._custom_metrics[name]) > self.max_history_size:
                self._custom_metrics[name] = self._custom_metrics[name][-self.max_history_size:]
    
    def get_agent_metrics(self, agent_name: str) -> Optional[AgentMetrics]:
        """
        Get metrics for a specific agent.
        
        Args:
            agent_name (str): Name of the agent
            
        Returns:
            Optional[AgentMetrics]: Agent metrics or None if not found
        """
        return self._agent_metrics.get(agent_name)
    
    def get_system_metrics(self) -> SystemMetrics:
        """
        Get system-wide metrics.
        
        Returns:
            SystemMetrics: System metrics
        """
        return self._system_metrics
    
    def get_all_agent_metrics(self) -> Dict[str, AgentMetrics]:
        """
        Get metrics for all agents.
        
        Returns:
            Dict[str, AgentMetrics]: Dictionary of agent metrics
        """
        return self._agent_metrics.copy()
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get a performance summary of the system.
        
        Returns:
            Dict[str, Any]: Performance summary
        """
        with self._lock:
            # Calculate recent performance metrics
            recent_query_times = list(self._query_times)
            avg_recent_response_time = sum(recent_query_times) / len(recent_query_times) if recent_query_times else 0
            
            # Get top performing agents
            top_agents = sorted(
                self._agent_metrics.values(),
                key=lambda x: x.successful_executions,
                reverse=True
            )[:5]
            
            # Get agents with highest error rates
            problematic_agents = sorted(
                [m for m in self._agent_metrics.values() if m.total_executions > 0],
                key=lambda x: x.error_rate,
                reverse=True
            )[:3]
            
            return {
                "system": {
                    "total_queries": self._system_metrics.total_queries,
                    "success_rate": (
                        self._system_metrics.successful_queries / self._system_metrics.total_queries
                        if self._system_metrics.total_queries > 0 else 0
                    ),
                    "cache_hit_rate": self._system_metrics.cache_hit_rate,
                    "avg_response_time": self._system_metrics.avg_response_time,
                    "recent_avg_response_time": avg_recent_response_time,
                    "uptime": str(self._system_metrics.uptime)
                },
                "agents": {
                    "total_agents": len(self._agent_metrics),
                    "top_performers": [
                        {
                            "name": agent.agent_name,
                            "executions": agent.successful_executions,
                            "avg_time": agent.avg_execution_time
                        }
                        for agent in top_agents
                    ],
                    "problematic": [
                        {
                            "name": agent.agent_name,
                            "error_rate": agent.error_rate,
                            "total_executions": agent.total_executions
                        }
                        for agent in problematic_agents
                    ]
                },
                "errors": dict(self._error_counts)
            }
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get system health status.
        
        Returns:
            Dict[str, Any]: Health status information
        """
        with self._lock:
            # Calculate health indicators
            overall_success_rate = (
                self._system_metrics.successful_queries / self._system_metrics.total_queries
                if self._system_metrics.total_queries > 0 else 1.0
            )
            
            # Check for problematic agents
            high_error_agents = [
                agent.agent_name for agent in self._agent_metrics.values()
                if agent.error_rate > 0.1 and agent.total_executions > 10
            ]
            
            # Determine overall health
            if overall_success_rate >= 0.95 and not high_error_agents:
                health = "healthy"
            elif overall_success_rate >= 0.8:
                health = "warning"
            else:
                health = "critical"
            
            return {
                "status": health,
                "overall_success_rate": overall_success_rate,
                "cache_hit_rate": self._system_metrics.cache_hit_rate,
                "avg_response_time": self._system_metrics.avg_response_time,
                "high_error_agents": high_error_agents,
                "total_queries": self._system_metrics.total_queries,
                "uptime": str(self._system_metrics.uptime),
                "timestamp": datetime.now().isoformat()
            }
    
    def export_metrics(self, format: str = "json") -> str:
        """
        Export metrics in the specified format.
        
        Args:
            format (str): Export format ("json" or "prometheus")
            
        Returns:
            str: Exported metrics
        """
        if format.lower() == "json":
            return self._export_json()
        elif format.lower() == "prometheus":
            return self._export_prometheus()
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_json(self) -> str:
        """Export metrics as JSON."""
        data = {
            "system_metrics": {
                "total_queries": self._system_metrics.total_queries,
                "successful_queries": self._system_metrics.successful_queries,
                "failed_queries": self._system_metrics.failed_queries,
                "cached_responses": self._system_metrics.cached_responses,
                "cache_hit_rate": self._system_metrics.cache_hit_rate,
                "avg_response_time": self._system_metrics.avg_response_time,
                "uptime": str(self._system_metrics.uptime)
            },
            "agent_metrics": {
                name: {
                    "total_executions": metrics.total_executions,
                    "successful_executions": metrics.successful_executions,
                    "failed_executions": metrics.failed_executions,
                    "skipped_executions": metrics.skipped_executions,
                    "avg_execution_time": metrics.avg_execution_time,
                    "error_rate": metrics.error_rate
                }
                for name, metrics in self._agent_metrics.items()
            },
            "timestamp": datetime.now().isoformat()
        }
        return json.dumps(data, indent=2)
    
    def _export_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []
        
        # System metrics
        lines.append(f"# HELP academic_agent_total_queries Total number of queries processed")
        lines.append(f"# TYPE academic_agent_total_queries counter")
        lines.append(f"academic_agent_total_queries {self._system_metrics.total_queries}")
        
        lines.append(f"# HELP academic_agent_cache_hit_rate Cache hit rate")
        lines.append(f"# TYPE academic_agent_cache_hit_rate gauge")
        lines.append(f"academic_agent_cache_hit_rate {self._system_metrics.cache_hit_rate}")
        
        # Agent metrics
        for name, metrics in self._agent_metrics.items():
            lines.append(f"# HELP academic_agent_executions_total Total executions per agent")
            lines.append(f"# TYPE academic_agent_executions_total counter")
            lines.append(f'academic_agent_executions_total{{agent="{name}"}} {metrics.total_executions}')
            
            lines.append(f"# HELP academic_agent_error_rate Error rate per agent")
            lines.append(f"# TYPE academic_agent_error_rate gauge")
            lines.append(f'academic_agent_error_rate{{agent="{name}"}} {metrics.error_rate}')
        
        return "\n".join(lines)


# Global metrics collector instance
metrics_collector = MetricsCollector()
