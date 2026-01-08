"""
Agent Registry - Central management of all specialized agents
Uses decorator pattern for clean agent registration, similar to provider_registry.py
"""

from typing import Dict, Type, Optional, Callable, List
from agents.base_agent import BaseAgent, AgentTool
import inspect


class AgentRegistry:
    """
    Central registry for all agents in the system.
    Provides O(1) agent lookup and dynamic agent discovery.
    """
    
    def __init__(self):
        self._agents: Dict[str, Type[BaseAgent]] = {}
        self._instances: Dict[str, BaseAgent] = {}
    
    def register(self, agent_name: Optional[str] = None) -> Callable:
        """
        Decorator to register an agent.
        
        Usage:
            @registry.register("sales")
            class SalesAgent(BaseAgent):
                ...
        
        Or with auto-naming:
            @registry.register()
            class SalesAgent(BaseAgent):
                ...  # will be registered as "sales_agent"
        """
        def decorator(agent_class: Type[BaseAgent]) -> Type[BaseAgent]:
            name = agent_name or agent_class.__name__.lower().replace("agent", "").strip("_")
            
            if name in self._agents:
                raise ValueError(f"Agent '{name}' is already registered")
            
            self._agents[name] = agent_class
            return agent_class
        
        return decorator
    
    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """
        Get an agent instance by name.
        Lazily instantiates agents on first access.
        """
        agent_name = agent_name.lower()
        
        if agent_name not in self._agents:
            return None
        
        if agent_name not in self._instances:
            agent_class = self._agents[agent_name]
            self._instances[agent_name] = agent_class()
        
        return self._instances[agent_name]
    
    def list_agents(self) -> List[str]:
        """List all registered agent names"""
        return sorted(list(self._agents.keys()))
    
    def agent_exists(self, agent_name: str) -> bool:
        """Check if an agent is registered"""
        return agent_name.lower() in self._agents
    
    def get_agent_info(self, agent_name: str) -> Optional[Dict]:
        """Get metadata about an agent"""
        agent = self.get_agent(agent_name)
        if not agent:
            return None
        
        return {
            "name": agent.agent_name,
            "description": agent.description,
            "tools": [
                {
                    "name": tool.name,
                    "provider": tool.provider,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
                for tool in agent.get_tools()
            ],
            "system_prompt": agent.get_system_prompt()
        }
    
    def get_all_agents_info(self) -> Dict[str, Dict]:
        """Get metadata about all agents"""
        result = {}
        for agent_name in self.list_agents():
            result[agent_name] = self.get_agent_info(agent_name)
        return result
    
    def validate_agent(self, agent_name: str) -> tuple[bool, str]:
        """
        Validate that an agent is properly implemented.
        Checks that all abstract methods are implemented.
        """
        if not self.agent_exists(agent_name):
            return False, f"Agent '{agent_name}' not found"
        
        agent_class = self._agents[agent_name]
        
        # Check that all abstract methods are implemented
        abstract_methods = [
            name for name, method in inspect.getmembers(BaseAgent, predicate=inspect.ismethod)
            if getattr(method, '__isabstractmethod__', False)
        ]
        
        # This is a basic check; detailed validation would require more inspection
        try:
            instance = agent_class()
            required_methods = ['analyze_request', 'generate_plan', 'generate_workflow_json']
            for method_name in required_methods:
                if not hasattr(instance, method_name):
                    return False, f"Agent missing required method: {method_name}"
            return True, "Agent is valid"
        except Exception as e:
            return False, f"Error validating agent: {str(e)}"


# Global registry instance
agent_registry = AgentRegistry()


def register_agent(agent_name: Optional[str] = None) -> Callable:
    """
    Convenience decorator - use this to register agents globally.
    
    Usage:
        @register_agent("sales")
        class SalesAgent(BaseAgent):
            ...
    """
    return agent_registry.register(agent_name)
