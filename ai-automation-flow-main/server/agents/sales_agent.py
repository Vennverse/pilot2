"""
Sales Agent - Specialized for B2B/B2C sales automation
Handles lead enrichment, outreach campaigns, deal tracking, and pipeline management
"""

from agents.base_agent import BaseAgent, AgentTool, AgentResponse
from agents.registry import register_agent
from typing import Dict, Any, List


@register_agent("sales")
class SalesAgent(BaseAgent):
    """
    Sales-focused agent for lead generation, enrichment, and outreach.
    Generates workflows for common sales tasks.
    """
    
    def __init__(self):
        super().__init__(
            agent_name="Sales Agent",
            description="Automates B2B/B2C sales workflows including lead enrichment, email campaigns, and deal tracking"
        )
        self._init_tools()
    
    def _init_tools(self):
        """Initialize tools available to sales agent"""
        self.tools = [
            AgentTool(
                name="search_leads",
                provider="hubspot",
                description="Search for leads/contacts in HubSpot based on criteria",
                parameters={"query": "str", "limit": "int"},
                output_schema={"leads": "list[dict]"}
            ),
            AgentTool(
                name="enrich_lead",
                provider="clearbit",
                description="Enrich lead information with company data and insights",
                parameters={"email": "str", "company": "str"},
                output_schema={"company_info": "dict", "insights": "list"}
            ),
            AgentTool(
                name="send_email",
                provider="sendgrid",
                description="Send personalized emails to leads",
                parameters={"to": "list[str]", "subject": "str", "body": "str"},
                output_schema={"sent": "int", "failed": "int"}
            ),
            AgentTool(
                name="create_task",
                provider="hubspot",
                description="Create follow-up task in CRM",
                parameters={"contact_id": "str", "description": "str", "due_date": "str"},
                output_schema={"task_id": "str"}
            ),
            AgentTool(
                name="web_search",
                provider="google_search",
                description="Search web for company/lead information",
                parameters={"query": "str", "limit": "int"},
                output_schema={"results": "list[dict]"}
            ),
            AgentTool(
                name="send_linkedin_message",
                provider="linkedin",
                description="Send LinkedIn connection requests or messages",
                parameters={"user_id": "str", "message": "str"},
                output_schema={"success": "bool"}
            ),
        ]
    
    def get_system_prompt(self) -> str:
        """Get specialized sales agent prompt"""
        return """You are a Sales Agent specializing in B2B/B2C sales automation.
Your expertise:
- Lead generation and enrichment
- Personalized outreach campaigns
- Deal pipeline management
- CRM automation
- Email and LinkedIn outreach

When given a sales task:
1. Analyze what the user wants to accomplish (e.g., "reach out to tech companies")
2. Break it into workflow steps
3. Use available tools to build a comprehensive sales workflow

Example workflows you can generate:
- Lead enrichment: Search HubSpot → Enrich with Clearbit → Web search for additional info
- Outreach campaign: Find leads → Personalize emails → Send via SendGrid → Create follow-up tasks
- Pipeline management: Search deals → Update status → Send notifications

Always prioritize personalization and relevance over volume."""
    
    def get_tools(self) -> List[AgentTool]:
        """Return available tools"""
        return self.tools
    
    def analyze_request(self, user_request: str) -> Dict[str, Any]:
        """Analyze sales request to extract intent and entities"""
        request_lower = user_request.lower()
        
        analysis = {
            "raw_request": user_request,
            "intent": None,
            "entities": {
                "companies": [],
                "industries": [],
                "job_titles": [],
                "regions": []
            },
            "workflow_type": None
        }
        
        # Simple intent detection
        if any(word in request_lower for word in ["reach out", "contact", "email", "message"]):
            analysis["intent"] = "outreach"
            analysis["workflow_type"] = "email_campaign"
        elif any(word in request_lower for word in ["find", "search", "look for", "prospecting"]):
            analysis["intent"] = "prospecting"
            analysis["workflow_type"] = "lead_search"
        elif any(word in request_lower for word in ["enrich", "research", "learn about"]):
            analysis["intent"] = "research"
            analysis["workflow_type"] = "lead_enrichment"
        else:
            analysis["intent"] = "general"
            analysis["workflow_type"] = "lead_search"
        
        return analysis
    
    def generate_plan(self, user_request: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate sales workflow plan"""
        workflow_type = analysis.get("workflow_type", "lead_search")
        
        if workflow_type == "email_campaign":
            return self._generate_outreach_workflow(user_request, analysis)
        elif workflow_type == "lead_search":
            return self._generate_prospecting_workflow(user_request, analysis)
        elif workflow_type == "lead_enrichment":
            return self._generate_enrichment_workflow(user_request, analysis)
        else:
            return self._generate_prospecting_workflow(user_request, analysis)
    
    def _generate_outreach_workflow(self, user_request: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate email outreach workflow"""
        steps = [
            self.build_workflow_step(
                step_id="step_1",
                name="Search for target companies",
                provider="hubspot",
                action="search_contacts",
                parameters={
                    "query": user_request,
                    "limit": 20
                }
            ),
            self.build_workflow_step(
                step_id="step_2",
                name="Enrich lead information",
                provider="clearbit",
                action="enrich_leads",
                parameters={
                    "leads_from_step": "step_1",
                    "enrich_company": True
                },
                depends_on="step_1"
            ),
            self.build_workflow_step(
                step_id="step_3",
                name="Send personalized emails",
                provider="sendgrid",
                action="send_campaign",
                parameters={
                    "recipients": "step_2",
                    "template": "personalized_outreach",
                    "personalization_fields": ["first_name", "company_name", "role"]
                },
                depends_on="step_2"
            ),
            self.build_workflow_step(
                step_id="step_4",
                name="Create follow-up tasks",
                provider="hubspot",
                action="create_bulk_tasks",
                parameters={
                    "contacts": "step_1",
                    "description": "Follow up on outreach email",
                    "due_days": 3
                },
                depends_on="step_3"
            )
        ]
        
        return self.build_workflow(
            name="Sales Email Outreach Campaign",
            description=f"Automated outreach for: {user_request[:100]}",
            steps=steps,
            tags=["sales", "outreach", "email"],
            metadata={"campaign_type": "cold_outreach"}
        )
    
    def _generate_prospecting_workflow(self, user_request: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate lead prospecting workflow"""
        steps = [
            self.build_workflow_step(
                step_id="step_1",
                name="Search HubSpot database",
                provider="hubspot",
                action="search_contacts",
                parameters={
                    "query": user_request,
                    "limit": 50
                }
            ),
            self.build_workflow_step(
                step_id="step_2",
                name="Web search for additional info",
                provider="google_search",
                action="search",
                parameters={
                    "query": user_request,
                    "limit": 10
                }
            ),
            self.build_workflow_step(
                step_id="step_3",
                name="Create HubSpot list",
                provider="hubspot",
                action="create_list",
                parameters={
                    "list_name": f"Prospects: {user_request[:50]}",
                    "contacts": "step_1"
                },
                depends_on="step_1"
            )
        ]
        
        return self.build_workflow(
            name="Sales Prospecting Workflow",
            description=f"Find prospects for: {user_request[:100]}",
            steps=steps,
            tags=["sales", "prospecting"],
            metadata={"search_query": user_request}
        )
    
    def _generate_enrichment_workflow(self, user_request: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate lead enrichment workflow"""
        steps = [
            self.build_workflow_step(
                step_id="step_1",
                name="Enrich with Clearbit",
                provider="clearbit",
                action="enrich_leads",
                parameters={
                    "query": user_request,
                    "enrich_company": True,
                    "enrich_person": True
                }
            ),
            self.build_workflow_step(
                step_id="step_2",
                name="Get company insights",
                provider="clearbit",
                action="get_company_insights",
                parameters={
                    "companies": "step_1"
                },
                depends_on="step_1"
            )
        ]
        
        return self.build_workflow(
            name="Lead Enrichment Workflow",
            description=f"Enrich leads for: {user_request[:100]}",
            steps=steps,
            tags=["sales", "enrichment"],
            metadata={"enrichment_type": "comprehensive"}
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
        """LLM-powered workflow generation for top-of-industry intelligence"""
        return self.generate_workflow_with_intelligence(user_id, user_request)
