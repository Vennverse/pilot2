"""
Support Agent - Specialized for customer support automation
Handles ticket routing, knowledge base searches, customer responses, and escalations
"""

from agents.base_agent import BaseAgent, AgentTool, AgentResponse
from agents.registry import register_agent
from typing import Dict, Any, List


@register_agent("support")
class SupportAgent(BaseAgent):
    """
    Support-focused agent for customer support automation and ticket management.
    Generates workflows for ticket routing, knowledge base integration, and escalations.
    """
    
    def __init__(self):
        super().__init__(
            agent_name="Support Agent",
            description="Automates customer support with ticket routing, knowledge base search, and smart escalations"
        )
        self._init_tools()
    
    def _init_tools(self):
        """Initialize tools available to support agent"""
        self.tools = [
            AgentTool(
                name="search_knowledge_base",
                provider="zendesk",
                description="Search knowledge base articles for solutions",
                parameters={"query": "str", "limit": "int"},
                output_schema={"articles": "list[dict]"}
            ),
            AgentTool(
                name="create_ticket",
                provider="zendesk",
                description="Create and assign support tickets",
                parameters={"subject": "str", "description": "str", "priority": "str"},
                output_schema={"ticket_id": "str"}
            ),
            AgentTool(
                name="send_response",
                provider="sendgrid",
                description="Send customer responses and updates",
                parameters={"customer": "str", "message": "str", "ticket_id": "str"},
                output_schema={"sent": "bool"}
            ),
            AgentTool(
                name="classify_issue",
                provider="openai",
                description="Automatically classify support tickets by type",
                parameters={"description": "str", "categories": "list"},
                output_schema={"category": "str", "confidence": "float"}
            ),
            AgentTool(
                name="escalate_ticket",
                provider="zendesk",
                description="Escalate tickets to human agents",
                parameters={"ticket_id": "str", "reason": "str", "priority": "str"},
                output_schema={"escalated": "bool"}
            ),
            AgentTool(
                name="track_resolution_time",
                provider="zendesk",
                description="Track and measure resolution metrics",
                parameters={"ticket_id": "str"},
                output_schema={"resolution_time": "int", "satisfaction": "float"}
            ),
        ]
    
    def get_system_prompt(self) -> str:
        """Get specialized support agent prompt"""
        return """You are a Support Agent specializing in customer support automation.
Your expertise:
- Support ticket creation and routing
- Knowledge base search and integration
- Issue classification and categorization
- Automated responses for common issues
- Ticket escalation to human agents
- Customer satisfaction tracking
- Resolution time optimization

When given a support task:
1. Understand the customer issue or support process
2. Determine if it's automatable or needs human attention
3. Break into workflow steps
4. Use available tools to create support workflows

Example workflows you can generate:
- Automatic response: Receive ticket → Search knowledge base → If solution found, send response; else escalate
- Ticket routing: Receive ticket → Classify issue → Route to appropriate team → Send acknowledgment
- Resolution tracking: Track ticket status → Measure resolution time → Send satisfaction survey
- Bulk escalation: Find high-priority tickets → Escalate to senior agents → Notify management

Always prioritize customer satisfaction and quick resolution."""
    
    def get_tools(self) -> List[AgentTool]:
        """Return available tools"""
        return self.tools
    
    def analyze_request(self, user_request: str) -> Dict[str, Any]:
        """Analyze support request to extract intent and entities"""
        request_lower = user_request.lower()
        
        analysis = {
            "raw_request": user_request,
            "intent": None,
            "entities": {
                "issue_types": [],
                "priority_level": "medium",
                "requires_human": False
            },
            "workflow_type": None
        }
        
        # Intent detection
        if any(word in request_lower for word in ["ticket", "issue", "problem", "bug"]):
            analysis["intent"] = "ticket_creation"
            analysis["workflow_type"] = "ticket_routing"
        elif any(word in request_lower for word in ["faq", "help", "how to", "guide", "documentation"]):
            analysis["intent"] = "knowledge_search"
            analysis["workflow_type"] = "knowledge_base"
        elif any(word in request_lower for word in ["escalate", "urgent", "critical", "immediate"]):
            analysis["intent"] = "escalation"
            analysis["workflow_type"] = "escalation"
            analysis["entities"]["priority_level"] = "high"
            analysis["entities"]["requires_human"] = True
        elif any(word in request_lower for word in ["response", "reply", "answer", "customer"]):
            analysis["intent"] = "customer_response"
            analysis["workflow_type"] = "response"
        else:
            analysis["intent"] = "general"
            analysis["workflow_type"] = "ticket_routing"
        
        # Priority detection
        if any(word in request_lower for word in ["urgent", "critical", "asap", "emergency"]):
            analysis["entities"]["priority_level"] = "high"
        elif any(word in request_lower for word in ["low", "minor", "when possible"]):
            analysis["entities"]["priority_level"] = "low"
        
        return analysis
    
    def generate_plan(self, user_request: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate support workflow plan"""
        workflow_type = analysis.get("workflow_type", "ticket_routing")
        
        if workflow_type == "ticket_routing":
            return self._generate_ticket_routing_workflow(user_request, analysis)
        elif workflow_type == "knowledge_base":
            return self._generate_knowledge_search_workflow(user_request, analysis)
        elif workflow_type == "escalation":
            return self._generate_escalation_workflow(user_request, analysis)
        elif workflow_type == "response":
            return self._generate_response_workflow(user_request, analysis)
        else:
            return self._generate_ticket_routing_workflow(user_request, analysis)
    
    def _generate_ticket_routing_workflow(self, user_request: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate ticket routing workflow"""
        steps = [
            self.build_workflow_step(
                step_id="step_1",
                name="Classify support issue",
                provider="openai",
                action="classify_issue",
                parameters={
                    "description": user_request,
                    "categories": ["billing", "technical", "feature_request", "account", "other"]
                }
            ),
            self.build_workflow_step(
                step_id="step_2",
                name="Create support ticket",
                provider="zendesk",
                action="create_ticket",
                parameters={
                    "subject": user_request[:100],
                    "description": user_request,
                    "category": "step_1",
                    "priority": analysis.get("entities", {}).get("priority_level", "medium")
                },
                depends_on="step_1"
            ),
            self.build_workflow_step(
                step_id="step_3",
                name="Send customer acknowledgment",
                provider="sendgrid",
                action="send_email",
                parameters={
                    "template": "ticket_received",
                    "ticket_id": "step_2"
                },
                depends_on="step_2"
            )
        ]
        
        return self.build_workflow(
            name="Support Ticket Routing",
            description=f"Route and create ticket for: {user_request[:100]}",
            steps=steps,
            tags=["support", "tickets"],
            metadata={"workflow_type": "routing"}
        )
    
    def _generate_knowledge_search_workflow(self, user_request: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate knowledge base search workflow"""
        steps = [
            self.build_workflow_step(
                step_id="step_1",
                name="Search knowledge base",
                provider="zendesk",
                action="search_knowledge_base",
                parameters={
                    "query": user_request,
                    "limit": 5
                }
            ),
            self.build_workflow_step(
                step_id="step_2",
                name="Format and send solution",
                provider="sendgrid",
                action="send_solution",
                parameters={
                    "articles": "step_1",
                    "template": "self_service_solution"
                },
                depends_on="step_1"
            ),
            self.build_workflow_step(
                step_id="step_3",
                name="Track solution helpfulness",
                provider="zendesk",
                action="track_feedback",
                parameters={
                    "articles": "step_1"
                },
                depends_on="step_2"
            )
        ]
        
        return self.build_workflow(
            name="Knowledge Base Search Workflow",
            description=f"Find solution for: {user_request[:100]}",
            steps=steps,
            tags=["support", "knowledge_base"],
            metadata={"workflow_type": "self_service"}
        )
    
    def _generate_escalation_workflow(self, user_request: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate escalation workflow"""
        steps = [
            self.build_workflow_step(
                step_id="step_1",
                name="Create priority ticket",
                provider="zendesk",
                action="create_ticket",
                parameters={
                    "subject": f"ESCALATED: {user_request[:80]}",
                    "description": user_request,
                    "priority": "high"
                }
            ),
            self.build_workflow_step(
                step_id="step_2",
                name="Escalate to senior agent",
                provider="zendesk",
                action="escalate_ticket",
                parameters={
                    "ticket_id": "step_1",
                    "reason": "High priority/escalated by customer",
                    "assign_to": "senior_support"
                },
                depends_on="step_1"
            ),
            self.build_workflow_step(
                step_id="step_3",
                name="Notify management",
                provider="sendgrid",
                action="send_email",
                parameters={
                    "recipients": ["support_manager@company.com"],
                    "subject": "High Priority Support Escalation",
                    "ticket_id": "step_1"
                },
                depends_on="step_2"
            )
        ]
        
        return self.build_workflow(
            name="Support Escalation Workflow",
            description=f"Escalate critical issue: {user_request[:100]}",
            steps=steps,
            tags=["support", "escalation"],
            metadata={"workflow_type": "escalation", "priority": "high"}
        )
    
    def _generate_response_workflow(self, user_request: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate customer response workflow"""
        steps = [
            self.build_workflow_step(
                step_id="step_1",
                name="Compose support response",
                provider="openai",
                action="generate_response",
                parameters={
                    "customer_message": user_request,
                    "tone": "professional_helpful",
                    "include_next_steps": True
                }
            ),
            self.build_workflow_step(
                step_id="step_2",
                name="Send customer response",
                provider="sendgrid",
                action="send_email",
                parameters={
                    "message": "step_1",
                    "personalize": True
                },
                depends_on="step_1"
            ),
            self.build_workflow_step(
                step_id="step_3",
                name="Log interaction",
                provider="zendesk",
                action="log_interaction",
                parameters={
                    "response": "step_1",
                    "timestamp": "now"
                },
                depends_on="step_2"
            )
        ]
        
        return self.build_workflow(
            name="Customer Response Workflow",
            description=f"Respond to customer: {user_request[:100]}",
            steps=steps,
            tags=["support", "response"],
            metadata={"workflow_type": "response"}
        )
    
    def generate_workflow_json(self, user_request: str) -> Dict[str, Any]:
        """Generate complete workflow JSON from user request"""
        analysis = self.analyze_request(user_request)
        plan = self.generate_plan(user_request, analysis)
        
        # Validate
        is_valid, msg = self.validate_workflow(plan)
        if not is_valid:
            raise ValueError(f"Generated invalid workflow: {msg}")
        
        return plan
    
    def generate_workflow_json_with_ai(self, user_id: str, user_request: str) -> Dict[str, Any]:
        """Generate workflow using Groq LLM for intelligent analysis"""
        from agent_intelligence import ai_intelligence
        
        result = ai_intelligence.generate_workflow_intelligently(
            user_id=user_id,
            request=user_request,
            agent_name="support",
            available_tools=self.get_tools(),
            system_prompt=self.get_system_prompt()
        )
        
        return result
