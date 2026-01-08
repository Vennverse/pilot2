"""
Base Agent Class - Abstract foundation for all specialized agents (v2.0 - LLM-Powered)
Agents translate natural language requests into execution plans (workflows)
All agents generate workflows that use the existing execution_engine.py
Enhanced with Groq LLM for intelligent workflow generation and learning
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentTool:
    """Definition of a tool an agent can use"""
    name: str
    provider: str  # Provider name from provider_registry
    description: str
    parameters: Dict[str, Any]  # Expected input parameters
    output_schema: Dict[str, Any]  # Expected output structure


@dataclass
class AgentResponse:
    """Standard response from agent execution"""
    success: bool
    plan_id: Optional[str] = None
    message: str = ""
    workflow_generated: bool = False
    execution_started: bool = False
    steps: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class BaseAgent(ABC):
    """
    Abstract base class for all specialized agents.
    Each agent translates natural language into structured workflow execution plans.
    
    Key principle: Agents don't execute directly - they generate execution plans
    that use the existing execution_engine.py (ONE ENGINE, TWO INTERFACES)
    """
    
    def __init__(self, agent_name: str, description: str):
        self.agent_name = agent_name
        self.description = description
        self.tools: List[AgentTool] = []
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Build LLM system prompt for this agent"""
        return f"""You are {self.agent_name}, a specialized automation agent.
Your job is to:
1. Understand user requests in natural language
2. Break down requests into discrete workflow steps
3. Generate JSON execution plans that can be executed by the workflow engine

You have access to these tools:
{self._format_tools_for_prompt()}

When the user requests something, analyze it and generate a structured plan.
Always return valid JSON that can be executed as a workflow."""
    
    def _format_tools_for_prompt(self) -> str:
        """Format available tools for LLM prompt"""
        if not self.tools:
            return "None configured yet"
        return "\n".join([
            f"- {tool.name}: {tool.description} (provider: {tool.provider})"
            for tool in self.tools
        ])
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent (can be overridden by subclasses)"""
        return self.system_prompt
    
    @abstractmethod
    def get_tools(self) -> List[AgentTool]:
        """Return list of tools this agent can use"""
        return self.tools
    
    @abstractmethod
    def analyze_request(self, user_request: str) -> Dict[str, Any]:
        """
        Analyze user request and extract intent, entities, and required steps.
        This is called BEFORE LLM to do lightweight analysis.
        """
        pass
    
    @abstractmethod
    def generate_plan(self, user_request: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate execution plan (workflow) from user request.
        This is the core agent logic - converts chat to structured workflow.
        
        Returns a plan dict that can be passed to execution_engine.execute_plan()
        """
        pass
    
    @abstractmethod
    def generate_workflow_json(self, user_request: str) -> Dict[str, Any]:
        """
        Generate the actual workflow JSON structure with all steps.
        This JSON will be passed directly to execution_engine.py
        
        Example structure:
        {
            "name": "Lead Enrichment Workflow",
            "description": "...",
            "steps": [
                {
                    "id": "step_1",
                    "name": "Search Lead Info",
                    "provider": "hubspot",
                    "action": "search_contacts",
                    "parameters": {...}
                },
                {
                    "id": "step_2", 
                    "name": "Send Email",
                    "provider": "sendgrid",
                    "action": "send_email",
                    "parameters": {...}
                }
            ]
        }
        """
        pass
    
    # ============= LLM-POWERED METHODS (v2.0 - INDUSTRY LEADING) =============
    
    def get_available_providers(self) -> List[str]:
        """Get list of providers this agent can access"""
        from provider_registry import registry
        return list(registry.providers.keys())
    
    def generate_workflow_with_intelligence(
        self,
        user_id: str,
        user_request: str
    ) -> Dict[str, Any]:
        """
        LLM-powered workflow generation with context awareness and learning.
        Industry-leading intelligent automation.
        """
        from agent_intelligence import ai_intelligence
        
        try:
            logger.info(f"Generating workflow with AI intelligence for: {user_request}")
            
            # Step 1: Analyze request with user context
            analysis = ai_intelligence.analyze_request_with_context(
                user_id=user_id,
                agent_name=self.agent_name,
                user_request=user_request
            )
            
            # Step 2: Generate workflow intelligently
            suggestion = ai_intelligence.generate_workflow_intelligently(
                user_id=user_id,
                agent_name=self.agent_name,
                user_request=user_request,
                analysis=analysis,
                available_providers=self.get_available_providers()
            )
            
            # Step 3: Validate workflow
            is_valid, msg = self.validate_workflow(suggestion.workflow)
            if not is_valid:
                logger.error(f"Generated invalid workflow: {msg}")
                raise ValueError(f"Generated invalid workflow: {msg}")
            
            logger.info(f"✓ Workflow generated with {suggestion.confidence:.1%} confidence")
            
            return {
                "workflow": suggestion.workflow,
                "confidence": suggestion.confidence,
                "reasoning": suggestion.reasoning,
                "alternatives": suggestion.alternative_approaches,
                "success_probability": suggestion.success_probability,
                "estimated_time": suggestion.estimated_execution_time,
                "cost_estimate": suggestion.cost_estimate
            }
            
        except Exception as e:
            logger.error(f"Error in intelligent workflow generation: {str(e)}")
            # Fallback to rule-based generation
            return self.generate_workflow_json(user_request)
    
    def get_workflow_alternatives(
        self,
        user_request: str
    ) -> List[Dict[str, Any]]:
        """Get alternative workflow approaches"""
        from agent_intelligence import ai_intelligence
        from agents.base_agent import AgentTool
        
        primary_workflow = self.generate_workflow_json(user_request)
        
        alternatives = ai_intelligence.suggest_workflow_alternatives(
            user_request=user_request,
            agent_name=self.agent_name,
            primary_workflow=primary_workflow,
            available_providers=self.get_available_providers()
        )
        
        return alternatives
    
    def predict_success(
        self,
        user_id: str,
        workflow: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Predict workflow success probability"""
        from agent_intelligence import ai_intelligence
        from database import db_manager
        
        user_history = db_manager.get_user_execution_plans(user_id, limit=20)
        probability, reasoning = ai_intelligence.predict_workflow_success(
            user_id=user_id,
            workflow=workflow,
            user_history=user_history
        )
        
        return {
            "probability": probability,
            "reasoning": reasoning,
            "recommended": probability > 0.7
        }
    
    def learn_from_execution(
        self,
        user_id: str,
        workflow: Dict[str, Any],
        execution_result: Dict[str, Any],
        user_feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        """Learn from execution results and improve future workflows"""
        from agent_intelligence import ai_intelligence
        
        refinements = ai_intelligence.refine_workflow_based_on_feedback(
            user_id=user_id,
            workflow=workflow,
            execution_result=execution_result,
            user_feedback=user_feedback
        )
        
        return refinements
    
    def validate_workflow(self, workflow: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate that generated workflow is executable.
        All workflows must have: name, description, steps[] with id/provider/action/parameters
        """
        if not isinstance(workflow, dict):
            return False, "Workflow must be a dictionary"
        
        required_fields = {"name", "description", "steps"}
        if not all(field in workflow for field in required_fields):
            return False, f"Missing required fields: {required_fields - set(workflow.keys())}"
        
        if not isinstance(workflow["steps"], list):
            return False, "Steps must be a list"
        
        if len(workflow["steps"]) == 0:
            return False, "Workflow must have at least one step"
        
        for i, step in enumerate(workflow["steps"]):
            required_step_fields = {"id", "name", "provider", "action", "parameters"}
            if not all(field in step for field in required_step_fields):
                return False, f"Step {i} missing required fields: {required_step_fields - set(step.keys())}"
        
        return True, "Workflow is valid"
    
    def build_workflow_step(
        self,
        step_id: str,
        name: str,
        provider: str,
        action: str,
        parameters: Dict[str, Any],
        depends_on: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Helper to build a single workflow step.
        Standardizes step structure across all agents.
        """
        step = {
            "id": step_id,
            "name": name,
            "provider": provider,
            "action": action,
            "parameters": parameters
        }
        
        if depends_on:
            step["depends_on"] = depends_on
        
        return step
    
    def build_workflow(
        self,
        name: str,
        description: str,
        steps: List[Dict[str, Any]],
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Helper to build complete workflow structure.
        All agent workflows use this standardized format.
        """
        workflow = {
            "name": name,
            "description": description,
            "steps": steps,
            "tags": tags or [self.agent_name.lower()],
            "metadata": metadata or {}
        }
        return workflow
    
    def on_success(self, user_request: str, workflow: Dict[str, Any]) -> None:
        """Hook called after successful plan execution (for logging/analytics)"""
        pass
    
    def on_error(self, user_request: str, error: str) -> None:
        """Hook called when plan generation or execution fails"""
        pass


class AgentContext:
    """Context passed during agent execution (similar to execution_engine context)"""
    
    def __init__(self, user_id: str, agent_name: str, user_request: str):
        self.user_id = user_id
        self.agent_name = agent_name
        self.user_request = user_request
        self.started_at = datetime.utcnow()
        self.previous_results = {}  # Results from previous steps for chaining
    
    def get_previous_result(self, step_id: str) -> Optional[Any]:
        """Get result from a previous step for use in current step"""
        return self.previous_results.get(step_id)
    
    def set_previous_result(self, step_id: str, result: Any) -> None:
        """Store result from a step for potential use in subsequent steps"""
        self.previous_results[step_id] = result
