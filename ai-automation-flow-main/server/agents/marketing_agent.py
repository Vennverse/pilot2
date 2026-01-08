"""
Marketing Agent - Specialized for campaign management and content automation
Handles email campaigns, social media posting, lead nurturing, and analytics
"""

from agents.base_agent import BaseAgent, AgentTool, AgentResponse
from agents.registry import register_agent
from typing import Dict, Any, List


@register_agent("marketing")
class MarketingAgent(BaseAgent):
    """
    Marketing-focused agent for campaign automation and content distribution.
    Generates workflows for email campaigns, social media, and nurture sequences.
    """
    
    def __init__(self):
        super().__init__(
            agent_name="Marketing Agent",
            description="Automates marketing campaigns, email nurturing, social media posting, and lead scoring"
        )
        self._init_tools()
    
    def _init_tools(self):
        """Initialize tools available to marketing agent"""
        self.tools = [
            AgentTool(
                name="create_campaign",
                provider="mailchimp",
                description="Create and manage email marketing campaigns",
                parameters={"name": "str", "recipients": "list", "template": "str"},
                output_schema={"campaign_id": "str"}
            ),
            AgentTool(
                name="post_social",
                provider="hootsuite",
                description="Schedule and post content to social media",
                parameters={"platforms": "list", "content": "str", "schedule_time": "str"},
                output_schema={"post_id": "str", "platforms": "list"}
            ),
            AgentTool(
                name="score_leads",
                provider="hubspot",
                description="Score and segment leads based on engagement",
                parameters={"leads": "list", "criteria": "dict"},
                output_schema={"scored_leads": "list"}
            ),
            AgentTool(
                name="create_content",
                provider="openai",
                description="Generate marketing content using AI",
                parameters={"topic": "str", "type": "str", "tone": "str"},
                output_schema={"content": "str"}
            ),
            AgentTool(
                name="send_newsletter",
                provider="sendgrid",
                description="Send newsletters to subscriber lists",
                parameters={"list": "str", "subject": "str", "content": "str"},
                output_schema={"sent": "int"}
            ),
            AgentTool(
                name="track_analytics",
                provider="google_analytics",
                description="Get campaign performance metrics",
                parameters={"campaign_id": "str", "date_range": "str"},
                output_schema={"clicks": "int", "conversions": "int", "roi": "float"}
            ),
        ]
    
    def get_system_prompt(self) -> str:
        """Get specialized marketing agent prompt"""
        return """You are a Marketing Agent specializing in campaign automation and content distribution.
Your expertise:
- Email campaign creation and management
- Social media scheduling and posting
- Lead scoring and nurturing
- Content generation and personalization
- Marketing analytics and ROI tracking

When given a marketing task:
1. Understand the campaign goal (awareness, nurture, conversion)
2. Identify target audience
3. Break into workflow steps
4. Use available tools to create comprehensive marketing workflows

Example workflows you can generate:
- Newsletter campaign: Create content → Segment audience → Send via Mailchimp → Track analytics
- Social campaign: Generate content → Post to multiple platforms → Track engagement
- Nurture sequence: Score leads → Send targeted emails → Update CRM → Measure conversion
- Content marketing: Create content via AI → Schedule on social → Track performance

Always consider audience segmentation and personalization for maximum engagement."""
    
    def get_tools(self) -> List[AgentTool]:
        """Return available tools"""
        return self.tools
    
    def analyze_request(self, user_request: str) -> Dict[str, Any]:
        """Analyze marketing request to extract intent and entities"""
        request_lower = user_request.lower()
        
        analysis = {
            "raw_request": user_request,
            "intent": None,
            "entities": {
                "audience": [],
                "channels": [],
                "goals": []
            },
            "workflow_type": None
        }
        
        # Intent detection
        if any(word in request_lower for word in ["email", "newsletter", "campaign"]):
            analysis["intent"] = "email_marketing"
            analysis["workflow_type"] = "email_campaign"
        elif any(word in request_lower for word in ["social", "post", "tweet", "facebook", "linkedin"]):
            analysis["intent"] = "social_media"
            analysis["workflow_type"] = "social_campaign"
        elif any(word in request_lower for word in ["content", "write", "generate", "article"]):
            analysis["intent"] = "content"
            analysis["workflow_type"] = "content_generation"
        elif any(word in request_lower for word in ["lead", "nurture", "score", "segment"]):
            analysis["intent"] = "lead_nurturing"
            analysis["workflow_type"] = "nurture_sequence"
        else:
            analysis["intent"] = "general"
            analysis["workflow_type"] = "email_campaign"
        
        # Channel detection
        if "social" in request_lower:
            analysis["entities"]["channels"].extend(["facebook", "twitter", "linkedin", "instagram"])
        if "email" in request_lower:
            analysis["entities"]["channels"].append("email")
        
        return analysis
    
    def generate_plan(self, user_request: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate marketing workflow plan"""
        workflow_type = analysis.get("workflow_type", "email_campaign")
        
        if workflow_type == "email_campaign":
            return self._generate_email_campaign_workflow(user_request, analysis)
        elif workflow_type == "social_campaign":
            return self._generate_social_campaign_workflow(user_request, analysis)
        elif workflow_type == "content_generation":
            return self._generate_content_workflow(user_request, analysis)
        elif workflow_type == "nurture_sequence":
            return self._generate_nurture_workflow(user_request, analysis)
        else:
            return self._generate_email_campaign_workflow(user_request, analysis)
    
    def _generate_email_campaign_workflow(self, user_request: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate email campaign workflow"""
        steps = [
            self.build_workflow_step(
                step_id="step_1",
                name="Generate email content",
                provider="openai",
                action="generate_content",
                parameters={
                    "topic": user_request,
                    "type": "email_body",
                    "tone": "professional_friendly"
                }
            ),
            self.build_workflow_step(
                step_id="step_2",
                name="Get audience segment",
                provider="hubspot",
                action="get_contacts",
                parameters={
                    "segment": "marketing_engaged",
                    "limit": 1000
                }
            ),
            self.build_workflow_step(
                step_id="step_3",
                name="Create Mailchimp campaign",
                provider="mailchimp",
                action="create_campaign",
                parameters={
                    "name": f"Campaign: {user_request[:50]}",
                    "recipients": "step_2",
                    "content": "step_1"
                },
                depends_on="step_1"
            ),
            self.build_workflow_step(
                step_id="step_4",
                name="Send campaign",
                provider="mailchimp",
                action="send_campaign",
                parameters={
                    "campaign_id": "step_3"
                },
                depends_on="step_3"
            ),
            self.build_workflow_step(
                step_id="step_5",
                name="Track performance",
                provider="google_analytics",
                action="track_campaign",
                parameters={
                    "campaign_id": "step_3",
                    "track_clicks": True,
                    "track_conversions": True
                },
                depends_on="step_4"
            )
        ]
        
        return self.build_workflow(
            name="Email Marketing Campaign",
            description=f"Automated campaign for: {user_request[:100]}",
            steps=steps,
            tags=["marketing", "email", "campaign"],
            metadata={"channel": "email"}
        )
    
    def _generate_social_campaign_workflow(self, user_request: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate social media campaign workflow"""
        steps = [
            self.build_workflow_step(
                step_id="step_1",
                name="Generate social content",
                provider="openai",
                action="generate_content",
                parameters={
                    "topic": user_request,
                    "type": "social_media_posts",
                    "platforms": analysis.get("entities", {}).get("channels", ["twitter", "linkedin"]),
                    "count": 5
                }
            ),
            self.build_workflow_step(
                step_id="step_2",
                name="Schedule on social platforms",
                provider="hootsuite",
                action="schedule_posts",
                parameters={
                    "platforms": analysis.get("entities", {}).get("channels", ["twitter", "linkedin"]),
                    "content": "step_1",
                    "schedule": "optimal_times"
                },
                depends_on="step_1"
            ),
            self.build_workflow_step(
                step_id="step_3",
                name="Track engagement",
                provider="hootsuite",
                action="track_engagement",
                parameters={
                    "posts": "step_2",
                    "metrics": ["likes", "comments", "shares", "clicks"]
                },
                depends_on="step_2"
            )
        ]
        
        return self.build_workflow(
            name="Social Media Campaign",
            description=f"Social campaign for: {user_request[:100]}",
            steps=steps,
            tags=["marketing", "social_media", "campaign"],
            metadata={"channel": "social"}
        )
    
    def _generate_content_workflow(self, user_request: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate content creation workflow"""
        steps = [
            self.build_workflow_step(
                step_id="step_1",
                name="Generate blog/content",
                provider="openai",
                action="generate_long_form_content",
                parameters={
                    "topic": user_request,
                    "type": "blog_post",
                    "length": "1500_words",
                    "tone": "informative"
                }
            ),
            self.build_workflow_step(
                step_id="step_2",
                name="Create social snippets",
                provider="openai",
                action="generate_content",
                parameters={
                    "content": "step_1",
                    "type": "social_snippets",
                    "count": 5
                },
                depends_on="step_1"
            ),
            self.build_workflow_step(
                step_id="step_3",
                name="Schedule social posts",
                provider="hootsuite",
                action="schedule_posts",
                parameters={
                    "platforms": ["twitter", "linkedin"],
                    "content": "step_2"
                },
                depends_on="step_2"
            )
        ]
        
        return self.build_workflow(
            name="Content Marketing Workflow",
            description=f"Create and promote content: {user_request[:100]}",
            steps=steps,
            tags=["marketing", "content"],
            metadata={"content_type": "blog"}
        )
    
    def _generate_nurture_workflow(self, user_request: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate lead nurturing workflow"""
        steps = [
            self.build_workflow_step(
                step_id="step_1",
                name="Score and segment leads",
                provider="hubspot",
                action="score_leads",
                parameters={
                    "criteria": {
                        "engagement": "high",
                        "stage": "considering"
                    }
                }
            ),
            self.build_workflow_step(
                step_id="step_2",
                name="Create nurture sequence",
                provider="mailchimp",
                action="create_automation",
                parameters={
                    "type": "nurture_sequence",
                    "leads": "step_1",
                    "duration_days": 30,
                    "email_count": 5
                },
                depends_on="step_1"
            ),
            self.build_workflow_step(
                step_id="step_3",
                name="Track nurture performance",
                provider="hubspot",
                action="track_nurture",
                parameters={
                    "automation_id": "step_2"
                },
                depends_on="step_2"
            )
        ]
        
        return self.build_workflow(
            name="Lead Nurturing Workflow",
            description=f"Nurture leads for: {user_request[:100]}",
            steps=steps,
            tags=["marketing", "nurturing"],
            metadata={"nurture_type": "sequence"}
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
            agent_name="marketing",
            available_tools=self.get_tools(),
            system_prompt=self.get_system_prompt()
        )
        
        return result
