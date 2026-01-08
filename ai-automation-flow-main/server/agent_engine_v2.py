"""
Agent Execution Engine (v2.0 - AI-Powered) - Core orchestration layer
Translates natural language requests into execution workflows using Groq LLM
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
    Central agent execution engine (v2.0 - LLM-powered).
    
    Flow:
    1. User request comes in (e.g., "send emails to tech companies")
    2. Agent + Groq LLM intelligently generate structured workflow
    3. Agent workflow is executed by existing execution_engine.py
    4. Results are tracked and learned from
    5. System improves over time
    
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
        use_ai: bool = True  # Use Groq for intelligent generation
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Execute an agent request with full LLM intelligence.
        
        Args:
            user_id: User making the request
            agent_name: Which agent to use
            user_request: Natural language request
            auto_execute: Execute immediately
            use_ai: Use Groq for intelligent workflow generation (recommended)
        
        Returns:
            (success, result_dict)
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
                    "traceback": traceback.format_exc()
                }
            
            # Step 3: Validate workflow
            is_valid, validation_msg = agent.validate_workflow(workflow)
            if not is_valid:
                return False, {
                    "error": f"Generated invalid workflow: {validation_msg}"
                }
            
            # Step 4: Get alternative approaches (NEW - multiple options)
            alternatives = []
            try:
                if use_ai:
                    alternatives = agent.get_workflow_alternatives(user_request)
            except Exception as e:
                self.logger.warning(f"Could not generate alternatives: {str(e)}")
            
            # Step 5: Save workflow to database
            plan_id = db_manager.create_execution_plan(
                user_id=user_id,
                name=workflow.get('name'),
                workflow=workflow,
                agent_name=agent_name
            )
            
            if not plan_id:
                return False, {"error": "Failed to save workflow"}
            
            result = {
                "success": True,
                "plan_id": plan_id,
                "workflow_name": workflow.get('name'),
                "agent_name": agent_name,
                "user_request": user_request,
                "ai_powered": use_ai
            }
            
            # Add AI metadata
            if ai_metadata:
                result.update(ai_metadata)
            
            # Add alternatives
            if alternatives:
                result["alternatives"] = alternatives
            
            # Step 6: Execute workflow if requested
            if auto_execute:
                self.logger.info(f"Executing workflow {plan_id}")
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
            
            agent.on_success(user_request, workflow)
            return True, result
            
        except Exception as e:
            self.logger.error(f"Error in execute_agent_request: {str(e)}")
            return False, {
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    def execute_workflow(
        self,
        user_id: str,
        plan_id: str
    ) -> Dict[str, Any]:
        """Execute workflow using existing execution_engine"""
        try:
            workflow = db_manager.get_execution_plan(plan_id)
            if not workflow:
                return {"success": False, "error": f"Workflow {plan_id} not found"}
            
            execution_result = execute_plan(
                plan_id=plan_id,
                workflow=workflow.get('workflow', {}),
                user_id=user_id
            )
            
            return {"success": True, "execution_result": execution_result}
            
        except Exception as e:
            self.logger.error(f"Error executing workflow: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_agent_info(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """Get agent information"""
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
        """Validate agent implementation"""
        return agent_registry.validate_agent(agent_name)
    
    def get_workflow_history(
        self,
        user_id: str,
        agent_name: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get workflow execution history"""
        try:
            workflows = db_manager.get_user_execution_plans(user_id, limit=limit)
            
            if agent_name:
                workflows = [w for w in workflows if w.get('agent_name') == agent_name]
            
            return workflows
        except Exception as e:
            self.logger.error(f"Error getting history: {str(e)}")
            return []
    
    def generate_workflow_without_execution(
        self,
        agent_name: str,
        user_request: str,
        user_id: Optional[str] = None,
        use_ai: bool = True
    ) -> Tuple[bool, Dict[str, Any]]:
        """Generate workflow without executing (preview mode)"""
        try:
            agent = self._get_agent(agent_name)
            if not agent:
                return False, {"error": f"Agent '{agent_name}' not found"}
            
            if use_ai and user_id:
                result = agent.generate_workflow_with_intelligence(user_id, user_request)
                workflow = result.get('workflow', {})
            else:
                workflow = agent.generate_workflow_json(user_request)
            
            is_valid, msg = agent.validate_workflow(workflow)
            if not is_valid:
                return False, {"error": f"Generated invalid workflow: {msg}"}
            
            return True, {
                "workflow": workflow,
                "validated": True,
                "steps_count": len(workflow.get('steps', []))
            }
        except Exception as e:
            return False, {"error": str(e), "traceback": traceback.format_exc()}
    
    def execute_workflow_step_by_step(
        self,
        user_id: str,
        plan_id: str
    ) -> Dict[str, Any]:
        """Execute workflow step-by-step with monitoring"""
        try:
            workflow = db_manager.get_execution_plan(plan_id)
            if not workflow:
                return {"success": False, "error": "Workflow not found"}
            
            steps = workflow.get('workflow', {}).get('steps', [])
            results = []
            
            for i, step in enumerate(steps):
                self.logger.info(f"Step {i+1}/{len(steps)}: {step.get('name')}")
                
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
            return {"success": False, "error": str(e)}
    
    def get_workflow_insights(
        self,
        user_id: str,
        limit_workflows: int = 10
    ) -> Dict[str, Any]:
        """
        Get AI insights about user's workflow patterns (NEW - Analytics)
        """
        try:
            workflows = db_manager.get_user_execution_plans(user_id, limit=limit_workflows)
            
            if not workflows:
                return {"message": "No workflows to analyze"}
            
            # Analyze patterns
            agents_used = {}
            success_rate = 0
            total_steps = 0
            
            for w in workflows:
                agent = w.get('agent_name', 'unknown')
                agents_used[agent] = agents_used.get(agent, 0) + 1
                
                if w.get('status') == 'completed':
                    success_rate += 1
                
                total_steps += len(w.get('workflow', {}).get('steps', []))
            
            success_rate = success_rate / len(workflows) if workflows else 0
            
            return {
                "total_workflows": len(workflows),
                "agents_used": agents_used,
                "success_rate": f"{success_rate:.1%}",
                "avg_steps_per_workflow": total_steps / len(workflows) if workflows else 0,
                "recommendations": [
                    "Workflows are being used most often with: " + 
                    (max(agents_used, key=agents_used.get) if agents_used else "no data")
                ]
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _get_agent(self, agent_name: str):
        """Get agent instance by name"""
        return agent_registry.get_agent(agent_name)


# Global agent engine instance
agent_engine = AgentExecutionEngine()
