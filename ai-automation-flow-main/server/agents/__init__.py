"""
Agents Package - AI-powered automation agents for various business functions
Each agent specializes in a domain and generates executable workflows.
"""

# Import all agents to auto-register them
from agents.base_agent import BaseAgent, AgentResponse, AgentContext, AgentTool
from agents.registry import agent_registry, register_agent
from agents.sales_agent import SalesAgent
from agents.marketing_agent import MarketingAgent
from agents.finance_agent import FinanceAgent
from agents.support_agent import SupportAgent
from agents.hr_agent import HRAgent

__all__ = [
    "BaseAgent",
    "AgentResponse",
    "AgentContext",
    "AgentTool",
    "agent_registry",
    "register_agent",
    "SalesAgent",
    "MarketingAgent",
    "FinanceAgent",
    "SupportAgent",
    "HRAgent",
]
