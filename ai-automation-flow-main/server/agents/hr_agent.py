"""
HR Agent - Specialized for human resources automation
Handles recruitment, onboarding, employee records, and compliance
"""

from agents.base_agent import BaseAgent, AgentTool, AgentResponse
from agents.registry import register_agent
from typing import Dict, Any, List


@register_agent("hr")
class HRAgent(BaseAgent):
    """
    HR-focused agent for recruitment, onboarding, and employee management.
    Generates workflows for hiring, records management, and HR processes.
    """
    
    def __init__(self):
        super().__init__(
            agent_name="HR Agent",
            description="Automates HR operations including recruitment, onboarding, employee records, and compliance"
        )
        self._init_tools()
    
    def _init_tools(self):
        """Initialize tools available to HR agent"""
        self.tools = [
            AgentTool(
                name="post_job",
                provider="linkedin",
                description="Post job openings to LinkedIn and other job boards",
                parameters={"title": "str", "description": "str", "location": "str"},
                output_schema={"job_id": "str"}
            ),
            AgentTool(
                name="search_candidates",
                provider="linkedin",
                description="Search for qualified candidates on LinkedIn",
                parameters={"skills": "list", "location": "str", "experience": "str"},
                output_schema={"candidates": "list[dict]"}
            ),
            AgentTool(
                name="send_offer",
                provider="sendgrid",
                description="Send job offer letters to candidates",
                parameters={"candidate": "str", "position": "str", "salary": "float"},
                output_schema={"sent": "bool"}
            ),
            AgentTool(
                name="onboard_employee",
                provider="workday",
                description="Create employee record and initiate onboarding",
                parameters={"name": "str", "position": "str", "start_date": "str"},
                output_schema={"employee_id": "str"}
            ),
            AgentTool(
                name="send_forms",
                provider="docusign",
                description="Send and track HR forms (W-4, benefits enrollment, etc)",
                parameters={"employee_id": "str", "forms": "list"},
                output_schema={"sent": "int", "completed": "int"}
            ),
            AgentTool(
                name="schedule_training",
                provider="google_calendar",
                description="Schedule employee training and orientation sessions",
                parameters={"employee_id": "str", "training_type": "str", "date": "str"},
                output_schema={"event_id": "str"}
            ),
        ]
    
    def get_system_prompt(self) -> str:
        """Get specialized HR agent prompt"""
        return """You are an HR Agent specializing in human resources operations.
Your expertise:
- Job posting and recruitment
- Candidate search and outreach
- Offer management
- Employee onboarding
- HR documentation and compliance
- Benefits administration
- Training and development
- Employee records management

When given an HR task:
1. Understand the HR process (recruiting, onboarding, records, etc)
2. Identify compliance requirements
3. Break into workflow steps
4. Use available tools to create HR automation workflows

Example workflows you can generate:
- Recruitment: Post job → Search candidates → Send offers → Track responses
- Onboarding: Create employee record → Send forms → Schedule training → Assign mentor
- Records: Update employee data → Archive old records → Generate reports
- Compliance: Review compliance items → Generate audit reports → Send to management

Always ensure compliance with employment law and company policies."""
    
    def get_tools(self) -> List[AgentTool]:
        """Return available tools"""
        return self.tools
    
    def analyze_request(self, user_request: str) -> Dict[str, Any]:
        """Analyze HR request to extract intent and entities"""
        request_lower = user_request.lower()
        
        analysis = {
            "raw_request": user_request,
            "intent": None,
            "entities": {
                "positions": [],
                "skills": [],
                "departments": []
            },
            "workflow_type": None
        }
        
        # Intent detection
        if any(word in request_lower for word in ["hire", "recruit", "hiring", "job posting", "opening"]):
            analysis["intent"] = "recruitment"
            analysis["workflow_type"] = "recruitment"
        elif any(word in request_lower for word in ["onboard", "welcome", "new employee", "start date"]):
            analysis["intent"] = "onboarding"
            analysis["workflow_type"] = "onboarding"
        elif any(word in request_lower for word in ["candidate", "interview", "review application"]):
            analysis["intent"] = "candidate_management"
            analysis["workflow_type"] = "candidate_review"
        elif any(word in request_lower for word in ["offer", "accept", "job offer"]):
            analysis["intent"] = "offer_management"
            analysis["workflow_type"] = "offer"
        elif any(word in request_lower for word in ["form", "paperwork", "w-4", "i-9", "benefits"]):
            analysis["intent"] = "documentation"
            analysis["workflow_type"] = "forms_and_docs"
        else:
            analysis["intent"] = "general"
            analysis["workflow_type"] = "recruitment"
        
        return analysis
    
    def generate_plan(self, user_request: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate HR workflow plan"""
        workflow_type = analysis.get("workflow_type", "recruitment")
        
        if workflow_type == "recruitment":
            return self._generate_recruitment_workflow(user_request, analysis)
        elif workflow_type == "onboarding":
            return self._generate_onboarding_workflow(user_request, analysis)
        elif workflow_type == "candidate_review":
            return self._generate_candidate_review_workflow(user_request, analysis)
        elif workflow_type == "offer":
            return self._generate_offer_workflow(user_request, analysis)
        elif workflow_type == "forms_and_docs":
            return self._generate_forms_workflow(user_request, analysis)
        else:
            return self._generate_recruitment_workflow(user_request, analysis)
    
    def _generate_recruitment_workflow(self, user_request: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate recruitment workflow"""
        steps = [
            self.build_workflow_step(
                step_id="step_1",
                name="Post job opening",
                provider="linkedin",
                action="post_job",
                parameters={
                    "title": user_request,
                    "description": f"Position for: {user_request}",
                    "post_to": ["linkedin", "indeed", "glassdoor"]
                }
            ),
            self.build_workflow_step(
                step_id="step_2",
                name="Search qualified candidates",
                provider="linkedin",
                action="search_candidates",
                parameters={
                    "query": user_request,
                    "limit": 50,
                    "sort_by": "relevance"
                }
            ),
            self.build_workflow_step(
                step_id="step_3",
                name="Send candidate outreach",
                provider="sendgrid",
                action="send_bulk_email",
                parameters={
                    "candidates": "step_2",
                    "template": "candidate_outreach",
                    "personalize": True
                },
                depends_on="step_2"
            ),
            self.build_workflow_step(
                step_id="step_4",
                name="Track responses",
                provider="linkedin",
                action="track_responses",
                parameters={
                    "job_id": "step_1"
                },
                depends_on="step_3"
            )
        ]
        
        return self.build_workflow(
            name="Recruitment Workflow",
            description=f"Recruit for position: {user_request[:100]}",
            steps=steps,
            tags=["hr", "recruitment"],
            metadata={"process_type": "recruitment"}
        )
    
    def _generate_onboarding_workflow(self, user_request: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate employee onboarding workflow"""
        steps = [
            self.build_workflow_step(
                step_id="step_1",
                name="Create employee record",
                provider="workday",
                action="create_employee",
                parameters={
                    "name": user_request,
                    "start_date": "today",
                    "auto_notify": True
                }
            ),
            self.build_workflow_step(
                step_id="step_2",
                name="Send onboarding forms",
                provider="docusign",
                action="send_forms",
                parameters={
                    "employee_id": "step_1",
                    "forms": ["W-4", "I-9", "Direct Deposit", "Emergency Contact"]
                },
                depends_on="step_1"
            ),
            self.build_workflow_step(
                step_id="step_3",
                name="Schedule orientation",
                provider="google_calendar",
                action="schedule_event",
                parameters={
                    "employee_id": "step_1",
                    "event_type": "orientation",
                    "duration": "4_hours"
                },
                depends_on="step_1"
            ),
            self.build_workflow_step(
                step_id="step_4",
                name="Assign mentor",
                provider="slack",
                action="send_message",
                parameters={
                    "channel": "onboarding",
                    "message": f"New employee {user_request} has been assigned",
                    "tag_mentors": True
                },
                depends_on="step_1"
            )
        ]
        
        return self.build_workflow(
            name="Employee Onboarding Workflow",
            description=f"Onboard new employee: {user_request[:100]}",
            steps=steps,
            tags=["hr", "onboarding"],
            metadata={"process_type": "onboarding"}
        )
    
    def _generate_candidate_review_workflow(self, user_request: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate candidate review workflow"""
        steps = [
            self.build_workflow_step(
                step_id="step_1",
                name="Extract candidate info",
                provider="openai",
                action="extract_resume_data",
                parameters={
                    "resume": user_request,
                    "extract": ["skills", "experience", "education"]
                }
            ),
            self.build_workflow_step(
                step_id="step_2",
                name="Score candidate",
                provider="openai",
                action="score_candidate",
                parameters={
                    "candidate_data": "step_1",
                    "job_requirements": "generic"
                },
                depends_on="step_1"
            ),
            self.build_workflow_step(
                step_id="step_3",
                name="Schedule interview if qualified",
                provider="google_calendar",
                action="schedule_interview",
                parameters={
                    "candidate": user_request,
                    "score": "step_2"
                },
                depends_on="step_2"
            )
        ]
        
        return self.build_workflow(
            name="Candidate Review Workflow",
            description=f"Review candidate: {user_request[:100]}",
            steps=steps,
            tags=["hr", "recruitment"],
            metadata={"process_type": "candidate_review"}
        )
    
    def _generate_offer_workflow(self, user_request: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate job offer workflow"""
        steps = [
            self.build_workflow_step(
                step_id="step_1",
                name="Create offer letter",
                provider="docusign",
                action="create_offer_letter",
                parameters={
                    "candidate": user_request,
                    "template": "standard_offer"
                }
            ),
            self.build_workflow_step(
                step_id="step_2",
                name="Send offer letter",
                provider="sendgrid",
                action="send_email",
                parameters={
                    "recipient": user_request,
                    "document": "step_1",
                    "subject": "Job Offer"
                },
                depends_on="step_1"
            ),
            self.build_workflow_step(
                step_id="step_3",
                name="Track offer acceptance",
                provider="docusign",
                action="track_signature",
                parameters={
                    "document_id": "step_1"
                },
                depends_on="step_2"
            )
        ]
        
        return self.build_workflow(
            name="Job Offer Workflow",
            description=f"Send job offer to: {user_request[:100]}",
            steps=steps,
            tags=["hr", "offers"],
            metadata={"process_type": "offer"}
        )
    
    def _generate_forms_workflow(self, user_request: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate HR forms and documentation workflow"""
        steps = [
            self.build_workflow_step(
                step_id="step_1",
                name="Identify required forms",
                provider="openai",
                action="identify_forms",
                parameters={
                    "request": user_request,
                    "jurisdiction": "US"
                }
            ),
            self.build_workflow_step(
                step_id="step_2",
                name="Generate/prepare forms",
                provider="docusign",
                action="prepare_forms",
                parameters={
                    "forms": "step_1"
                },
                depends_on="step_1"
            ),
            self.build_workflow_step(
                step_id="step_3",
                name="Send for signature",
                provider="sendgrid",
                action="send_email",
                parameters={
                    "forms": "step_2",
                    "template": "forms_request"
                },
                depends_on="step_2"
            ),
            self.build_workflow_step(
                step_id="step_4",
                name="Track completion",
                provider="docusign",
                action="track_signatures",
                parameters={
                    "forms": "step_2"
                },
                depends_on="step_3"
            )
        ]
        
        return self.build_workflow(
            name="HR Forms and Documentation Workflow",
            description=f"Process HR forms: {user_request[:100]}",
            steps=steps,
            tags=["hr", "forms"],
            metadata={"process_type": "documentation"}
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
            agent_name="hr",
            available_tools=self.get_tools(),
            system_prompt=self.get_system_prompt()
        )
        
        return result
