"""
Agent Execution Engine - Core orchestration layer
Translates natural language requests into execution workflows
ONE ENGINE, TWO INTERFACES: agents use existing execution_engine.py
"""

from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from datetime import datetime
import logging
import traceback
import json

from agents.registry import agent_registry
from agents.base_agent import AgentResponse, AgentContext
from execution_engine import execute_plan, execute_step
from database import db_manager
from provider_registry import provider_registry
from agent_intelligence import ai_intelligence

logger = logging.getLogger(__name__)


@dataclass
class ExecutedWorkflow:
    """Result of executing an agent-generated workflow"""
    workflow_id: str
    workflow_name: str
    agent_name: str
    user_request: str
    status: str  # "running", "success", "failed", "partial"
    steps_executed: int
    steps_total: int
    execution_results: List[Dict[str, Any]]
    error_message: Optional[str] = None
    started_at: str = ""
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None


class AgentExecutionEngine:
    """
    Central agent execution engine.
    
    Flow:
    1. User request comes in (e.g., "send emails to tech companies")
    2. Agent.generate_workflow_json() creates structured workflow
    3. Agent workflow is executed by existing execution_engine.py
    4. Results are tracked and returned to user
    
    Key principle: NO CODE DUPLICATION
    Agents generate workflows → execution_engine executes them
    Same engine powers both interfaces (visual workflows + agents)
    """
    
    def __init__(self):
        self.logger = logger
    
    def execute_agent_request(
        self,
        user_id: str,
        agent_name: str,
        user_request: str,
        auto_execute: bool = True,
        use_ai: bool = True
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Execute an agent request with full LLM intelligence.
        
        Args:
            user_id: User making the request
            agent_name: Which agent to use (sales, marketing, finance, support, hr)
            user_request: Natural language request
            auto_execute: If True, execute the generated workflow immediately
            use_ai: Use Groq for intelligent workflow generation (recommended)
        
        Returns:
            (success: bool, result: dict)
        """
        try:
            # Step 1: Get agent
            agent = self._get_agent(agent_name)
            if not agent:
                return False, {
                    "error": f"Agent '{agent_name}' not found",
                    "available_agents": agent_registry.list_agents()
                }
            
            # Step 2: Generate workflow with AI intelligence
            self.logger.info(f"Generating workflow with AI: {user_request}")
            try:
                if use_ai:
                    # LLM-powered intelligent generation
                    result = agent.generate_workflow_with_intelligence(user_id, user_request)
                    workflow = result.get('workflow', {})
                    ai_metadata = {
                        "ai_confidence": result.get('confidence'),
                        "ai_reasoning": result.get('reasoning'),
                        "success_probability": result.get('success_probability', 0.8),
                        "alternatives": result.get('alternatives', []),
                        "estimated_time": result.get('estimated_time', 60)
                    }
                else:
                    # Fallback to basic generation
                    workflow = agent.generate_workflow_json(user_request)
                    ai_metadata = {}
            except Exception as e:
                self.logger.error(f"Workflow generation failed: {str(e)}")
                return False, {
                    "error": f"Failed to generate workflow: {str(e)}",
                    "user_request": user_request,
                    "traceback": traceback.format_exc()
                }
            
            # Step 3: Validate workflow
            is_valid, validation_msg = agent.validate_workflow(workflow)
            if not is_valid:
                return False, {
                    "error": f"Generated invalid workflow: {validation_msg}",
                    "workflow": workflow
                }
            
            # Step 4: Get alternative approaches (NEW - multiple options)
            alternatives = []
            try:
                if use_ai:
                    alternatives = agent.get_workflow_alternatives(user_request)
            except Exception as e:
                self.logger.warning(f"Could not generate alternatives: {str(e)}")
            
            # Step 5: Save workflow to database
            self.logger.info(f"Saving workflow: {workflow.get('name')}")
            plan_id = db_manager.create_execution_plan(
                user_id=user_id,
                name=workflow.get('name'),
                workflow=workflow,
                agent_name=agent_name
            )
            
            if not plan_id:
                return False, {
                    "error": "Failed to save workflow to database"
                }
            
            result = {
                "success": True,
                "plan_id": plan_id,
                "workflow_name": workflow.get('name'),
                "agent_name": agent_name,
                "user_request": user_request,
                "ai_powered": use_ai,
                "workflow_summary": {
                    "steps": len(workflow.get('steps', [])),
                    "description": workflow.get('description'),
                    "tags": workflow.get('tags', [])
                }
            }
            
            # Add AI metadata
            if ai_metadata:
                result.update(ai_metadata)
            
            # Add alternatives
            if alternatives:
                result["alternatives"] = alternatives
            
            # Step 6: Execute workflow if requested
            if auto_execute:
                self.logger.info(f"Auto-executing workflow {plan_id}")
                execution_result = self.execute_workflow(user_id, plan_id)
                result["execution_result"] = execution_result
                result["execution_started"] = True
                
                # Step 7: Learn from execution (NEW - continuous improvement)
                if execution_result.get('success') and use_ai:
                    try:
                        self.logger.info("Learning from successful execution")
                        learning = agent.learn_from_execution(
                            user_id=user_id,
                            workflow=workflow,
                            execution_result=execution_result
                        )
                        result["learning"] = learning
                    except Exception as e:
                        self.logger.warning(f"Learning failed (non-critical): {str(e)}")
            
            # Step 8: Call agent success hook
            agent.on_success(user_request, workflow)
            
            return True, result
            
        except Exception as e:
            self.logger.error(f"Error in execute_agent_request: {str(e)}")
            agent.on_error(user_request, str(e))
            return False, {
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    def execute_workflow(
        self,
        user_id: str,
        plan_id: str
    ) -> Dict[str, Any]:
        """
        Execute a generated workflow using the existing execution_engine.
        
        This is the KEY INTEGRATION POINT:
        Agent-generated workflows are executed by the same engine that
        executes manually-created workflows. NO DUPLICATION.
        """
        try:
            # Get workflow from database
            workflow = db_manager.get_execution_plan(plan_id)
            if not workflow:
                return {
                    "success": False,
                    "error": f"Workflow {plan_id} not found"
                }
            
            # Execute using existing execution_engine
            self.logger.info(f"Executing workflow {plan_id}")
            execution_result = execute_plan(
                plan_id=plan_id,
                workflow=workflow.get('workflow', {}),
                user_id=user_id
            )
            
            return {
                "success": True,
                "plan_id": plan_id,
                "execution_result": execution_result
            }
            
        except Exception as e:
            self.logger.error(f"Error executing workflow: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "plan_id": plan_id
            }
    
    def get_agent_info(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """Get information about available agents and their capabilities"""
        if agent_name:
            agent = self._get_agent(agent_name)
            if not agent:
                return {"error": f"Agent '{agent_name}' not found"}
            return agent_registry.get_agent_info(agent_name)
        else:
            return agent_registry.get_all_agents_info()
    
    def list_agents(self) -> List[str]:
        """List all available agents"""
        return agent_registry.list_agents()
    
    def validate_agent(self, agent_name: str) -> Tuple[bool, str]:
        """Validate that an agent is properly implemented"""
        return agent_registry.validate_agent(agent_name)
    
    def _get_agent(self, agent_name: str):
        """Get an agent instance by name"""
        return agent_registry.get_agent(agent_name)
    
    def get_workflow_history(
        self,
        user_id: str,
        agent_name: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get history of agent-generated and executed workflows
        """
        try:
            # Query database for workflows
            workflows = db_manager.get_user_execution_plans(
                user_id,
                limit=limit
            )
            
            # Filter by agent if specified
            if agent_name:
                workflows = [
                    w for w in workflows
                    if w.get('agent_name') == agent_name
                ]
            
            return workflows
        except Exception as e:
            self.logger.error(f"Error getting workflow history: {str(e)}")
            return []
    
    def generate_workflow_without_execution(
        self,
        agent_name: str,
        user_request: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Generate a workflow without executing it.
        Useful for preview/review before execution.
        """
        try:
            agent = self._get_agent(agent_name)
            if not agent:
                return False, {
                    "error": f"Agent '{agent_name}' not found",
                    "available_agents": agent_registry.list_agents()
                }
            
            workflow = agent.generate_workflow_json(user_request)
            
            # Validate
            is_valid, msg = agent.validate_workflow(workflow)
            if not is_valid:
                return False, {
                    "error": f"Generated invalid workflow: {msg}"
                }
            
            return True, {
                "workflow": workflow,
                "validated": True,
                "steps_count": len(workflow.get('steps', []))
            }
        except Exception as e:
            return False, {
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    def execute_workflow_step_by_step(
        self,
        user_id: str,
        plan_id: str
    ) -> Dict[str, Any]:
        """
        Execute workflow step-by-step with detailed logging.
        Useful for debugging and monitoring.
        """
        try:
            workflow = db_manager.get_execution_plan(plan_id)
            if not workflow:
                return {"success": False, "error": "Workflow not found"}
            
            steps = workflow.get('workflow', {}).get('steps', [])
            results = []
            
            for i, step in enumerate(steps):
                self.logger.info(f"Executing step {i+1}/{len(steps)}: {step.get('name')}")
                
                # Execute single step
                step_result = execute_step(
                    step=step,
                    user_id=user_id,
                    execution_id=plan_id,
                    previous_results={r['step_id']: r['result'] for r in results}
                )
                
                results.append({
                    "step_id": step.get('id'),
                    "step_number": i + 1,
                    "name": step.get('name'),
                    "provider": step.get('provider'),
                    "status": step_result.get('status'),
                    "result": step_result.get('result'),
                    "error": step_result.get('error')
                })
            
            return {
                "success": True,
                "plan_id": plan_id,
                "steps_executed": len(results),
                "results": results
            }
        except Exception as e:
            self.logger.error(f"Error in step-by-step execution: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "plan_id": plan_id
            }


# Global agent engine instance
agent_engine = AgentExecutionEngine()
