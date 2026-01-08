"""
Agent AI Intelligence Layer - Groq-powered intelligent workflow generation
Top-of-industry LLM integration for truly intelligent automation agents
"""

import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib

from provider_registry import registry
from database import db_manager

logger = logging.getLogger(__name__)


@dataclass
class WorkflowSuggestion:
    """LLM-generated workflow suggestion with confidence scoring"""
    workflow: Dict[str, Any]
    confidence: float  # 0-1 score
    reasoning: str
    alternative_approaches: List[Dict[str, Any]]
    estimated_execution_time: int  # seconds
    success_probability: float  # Based on historical data
    cost_estimate: float  # API calls estimated cost


class AIIntelligenceLayer:
    """
    Core LLM intelligence for agents.
    Handles all Groq-powered workflow generation with context awareness.
    Industry-leading prompt engineering and optimization.
    """
    
    def __init__(self):
        self.logger = logger
        self.groq_model = "mixtral-8x7b-instruct-v0.1"  # Fast, powerful model
        self.cache = {}  # In-memory cache for request deduplication
        self.cache_ttl = 3600  # 1 hour cache TTL
    
    def analyze_request_with_context(
        self,
        user_id: str,
        agent_name: str,
        user_request: str
    ) -> Dict[str, Any]:
        """
        Analyze request with full context awareness:
        - User history (past workflows)
        - Common patterns
        - User preferences
        - Industry best practices
        """
        try:
            # Get user's workflow history
            user_history = db_manager.get_user_execution_plans(user_id, limit=10)
            
            # Build context prompt
            context_data = self._build_context(user_id, user_request, user_history)
            
            # Call Groq for intelligent analysis
            response = registry.execute(
                provider_name="groq",
                action="generate_content",
                parameters={
                    "model": self.groq_model,
                    "prompt": self._build_analysis_prompt(
                        user_request,
                        agent_name,
                        context_data
                    ),
                    "temperature": 0.3,  # Focused, deterministic
                    "max_tokens": 1000
                }
            )
            
            analysis = json.loads(response.get('result', '{}'))
            
            return {
                "intent": analysis.get("intent", "general"),
                "workflow_type": analysis.get("workflow_type"),
                "entities": analysis.get("entities", {}),
                "parameters": analysis.get("parameters", {}),
                "confidence": analysis.get("confidence", 0.8),
                "reasoning": analysis.get("reasoning", ""),
                "similar_past_workflows": analysis.get("similar_workflows", [])
            }
        except Exception as e:
            self.logger.error(f"Error in context analysis: {str(e)}")
            return {
                "intent": "general",
                "confidence": 0.5,
                "error": str(e)
            }
    
    def generate_workflow_intelligently(
        self,
        user_id: str,
        agent_name: str,
        user_request: str,
        analysis: Dict[str, Any],
        available_providers: List[str]
    ) -> WorkflowSuggestion:
        """
        Generate optimal workflow using Groq with multiple approaches.
        Returns best suggestion + alternatives.
        """
        try:
            # Check cache first
            cache_key = self._get_cache_key(user_id, agent_name, user_request)
            if cache_key in self.cache:
                cached = self.cache[cache_key]
                if datetime.now().timestamp() - cached['timestamp'] < self.cache_ttl:
                    self.logger.info(f"Using cached workflow for {cache_key}")
                    return cached['suggestion']
            
            # Get user's workflow history for learning
            user_workflows = db_manager.get_user_execution_plans(user_id, limit=20)
            successful_workflows = [w for w in user_workflows if w.get('status') == 'completed']
            
            # Build sophisticated prompt for workflow generation
            prompt = self._build_generation_prompt(
                user_request,
                agent_name,
                analysis,
                available_providers,
                successful_workflows
            )
            
            # Call Groq for workflow generation
            response = registry.execute(
                provider_name="groq",
                action="generate_content",
                parameters={
                    "model": self.groq_model,
                    "prompt": prompt,
                    "temperature": 0.2,  # Highly deterministic
                    "max_tokens": 2000
                }
            )
            
            result_text = response.get('result', '{}')
            
            # Parse multi-approach response
            suggestion = self._parse_workflow_response(
                result_text,
                user_request,
                available_providers
            )
            
            # Cache the suggestion
            self.cache[cache_key] = {
                'suggestion': suggestion,
                'timestamp': datetime.now().timestamp()
            }
            
            return suggestion
            
        except Exception as e:
            self.logger.error(f"Error generating workflow: {str(e)}")
            raise
    
    def refine_workflow_based_on_feedback(
        self,
        user_id: str,
        workflow: Dict[str, Any],
        execution_result: Dict[str, Any],
        user_feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Use Groq to refine workflow based on execution results and feedback.
        Learns from success/failure patterns.
        """
        try:
            prompt = f"""
            A workflow was executed with the following result:
            
            Workflow:
            {json.dumps(workflow, indent=2)}
            
            Execution Result:
            {json.dumps(execution_result, indent=2)}
            
            User Feedback: {user_feedback or "None"}
            
            Based on this, suggest improvements to make the workflow:
            1. More efficient (fewer steps, faster)
            2. More reliable (error handling, retry logic)
            3. Better results (higher success rate)
            
            Return JSON with:
            - suggested_improvements: list of specific changes
            - optimization_priority: which changes have highest impact
            - success_factors: what worked well
            - failure_points: what failed and why
            - recommended_next_steps: actions to take
            
            Be specific and actionable.
            """
            
            response = registry.execute(
                provider_name="groq",
                action="generate_content",
                parameters={
                    "model": self.groq_model,
                    "prompt": prompt,
                    "temperature": 0.3,
                    "max_tokens": 1500
                }
            )
            
            refinements = json.loads(response.get('result', '{}'))
            return refinements
            
        except Exception as e:
            self.logger.error(f"Error refining workflow: {str(e)}")
            return {}
    
    def predict_workflow_success(
        self,
        user_id: str,
        workflow: Dict[str, Any],
        user_history: List[Dict[str, Any]]
    ) -> Tuple[float, str]:
        """
        Predict success probability using historical patterns and LLM analysis.
        Returns (probability: 0-1, reasoning: str)
        """
        try:
            # Analyze similar past workflows
            similar_workflows = [w for w in user_history 
                               if w.get('agent_name') == workflow.get('agent_name')]
            
            if similar_workflows:
                success_rate = len([w for w in similar_workflows if w.get('status') == 'completed']) / len(similar_workflows)
            else:
                success_rate = 0.7  # Default assumption
            
            # Use Groq for deeper analysis
            prompt = f"""
            Predict the success probability of this workflow:
            {json.dumps(workflow, indent=2)}
            
            Based on:
            - Workflow complexity
            - Number of steps
            - Provider reliability
            - Parameter specificity
            - Historical success rate: {success_rate}
            
            Return JSON:
            - probability: 0-1 (0.1 to 0.99)
            - confidence: how confident in this prediction
            - risk_factors: things that could go wrong
            - mitigation_strategies: how to improve success
            
            Be realistic and honest about failure risks.
            """
            
            response = registry.execute(
                provider_name="groq",
                action="generate_content",
                parameters={
                    "model": self.groq_model,
                    "prompt": prompt,
                    "temperature": 0.3,
                    "max_tokens": 800
                }
            )
            
            analysis = json.loads(response.get('result', '{}'))
            probability = float(analysis.get('probability', success_rate))
            reasoning = analysis.get('reasoning', f'Historical success rate: {success_rate}')
            
            return min(0.99, max(0.1, probability)), reasoning
            
        except Exception as e:
            self.logger.error(f"Error predicting success: {str(e)}")
            return 0.7, "Default prediction due to analysis error"
    
    def suggest_workflow_alternatives(
        self,
        user_request: str,
        agent_name: str,
        primary_workflow: Dict[str, Any],
        available_providers: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Generate alternative workflow approaches for same request.
        Industry best practice: always provide options.
        """
        try:
            prompt = f"""
            The user requested: "{user_request}"
            
            Primary suggested workflow:
            {json.dumps(primary_workflow, indent=2)}
            
            Available providers: {', '.join(available_providers)}
            
            Generate 2-3 ALTERNATIVE approaches to accomplish the same goal.
            Each alternative should:
            1. Use different providers or tool combinations
            2. Have different trade-offs (speed vs accuracy, cost vs features)
            3. Be fully executable
            
            Return JSON array of alternative workflows with:
            - name: alternative approach name
            - description: why someone might prefer this
            - steps: workflow steps
            - pros: advantages over primary
            - cons: disadvantages
            - execution_time_estimate: seconds
            - cost_estimate: API call costs
            
            Make alternatives genuinely different and valuable.
            """
            
            response = registry.execute(
                provider_name="groq",
                action="generate_content",
                parameters={
                    "model": self.groq_model,
                    "prompt": prompt,
                    "temperature": 0.6,  # More creative
                    "max_tokens": 2500
                }
            )
            
            alternatives_text = response.get('result', '[]')
            alternatives = json.loads(alternatives_text)
            
            return alternatives if isinstance(alternatives, list) else []
            
        except Exception as e:
            self.logger.error(f"Error suggesting alternatives: {str(e)}")
            return []
    
    def learn_from_pattern(
        self,
        user_id: str,
        pattern_name: str,
        successful_workflows: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Extract and learn from successful patterns.
        Build reusable best practices.
        """
        try:
            prompt = f"""
            Analyze these successful workflows and extract the key success pattern:
            
            Workflows:
            {json.dumps(successful_workflows, indent=2)}
            
            Identify:
            - common_structure: what steps appear in all
            - success_factors: why these worked
            - key_parameters: critical values that matter
            - generic_pattern: abstract workflow template
            - when_to_use: situations where this pattern works
            - when_not_to_use: limitations
            
            Create a reusable pattern that can be applied to similar requests.
            """
            
            response = registry.execute(
                provider_name="groq",
                action="generate_content",
                parameters={
                    "model": self.groq_model,
                    "prompt": prompt,
                    "temperature": 0.2,
                    "max_tokens": 1200
                }
            )
            
            pattern = json.loads(response.get('result', '{}'))
            
            # Store pattern for reuse
            db_manager.save_workflow_pattern(
                user_id,
                pattern_name,
                pattern
            )
            
            return pattern
            
        except Exception as e:
            self.logger.error(f"Error learning pattern: {str(e)}")
            return {}
    
    # ============= PROMPT ENGINEERING (Industry Best Practices) =============
    
    def _build_analysis_prompt(
        self,
        user_request: str,
        agent_name: str,
        context_data: Dict[str, Any]
    ) -> str:
        """Build sophisticated analysis prompt with context"""
        return f"""
You are an expert automation analyst for {agent_name} workflows.

USER REQUEST: "{user_request}"

CONTEXT:
- User's past workflows: {context_data.get('past_workflows_summary', 'None')}
- Common patterns: {context_data.get('common_patterns', 'None')}
- User preferences: {context_data.get('preferences', 'None')}

TASK: Analyze what the user wants to accomplish.

Return a JSON object with:
{{
    "intent": "primary goal (one of: {context_data.get('valid_intents', 'general')})",
    "workflow_type": "specific workflow type needed",
    "entities": {{"keys": "values"}},
    "parameters": {{"extracted": "parameters"}},
    "confidence": 0.95,
    "reasoning": "why you interpreted it this way",
    "similar_workflows": ["past workflow IDs that are similar"]
}}

Be precise. Learn from the user's history. Understand their domain context.
"""
    
    def _build_generation_prompt(
        self,
        user_request: str,
        agent_name: str,
        analysis: Dict[str, Any],
        available_providers: List[str],
        successful_workflows: List[Dict[str, Any]]
    ) -> str:
        """Build advanced workflow generation prompt"""
        return f"""
You are a world-class automation workflow engineer.

REQUEST: "{user_request}"

INTENT ANALYSIS:
{json.dumps(analysis, indent=2)}

AVAILABLE PROVIDERS: {', '.join(available_providers[:10])}

USER'S SUCCESSFUL PATTERNS:
{json.dumps(successful_workflows[:3], indent=2) if successful_workflows else 'None - use best practices'}

YOUR TASK:
1. Design the OPTIMAL workflow to accomplish this request
2. Use proven patterns from user's history when applicable
3. Choose best providers for speed, reliability, cost
4. Include proper error handling
5. Structure steps logically with dependencies

CONSTRAINTS:
- Each step needs: id, name, provider, action, parameters
- Use depends_on for step chaining
- Minimize steps while maximizing reliability
- Prefer fast providers (Groq, HubSpot) over slow ones

Return VALID JSON:
{{
    "workflow": {{
        "name": "workflow name",
        "description": "what it does",
        "steps": [
            {{"id": "s1", "name": "...", "provider": "...", "action": "...", "parameters": {{...}}}}
        ]
    }},
    "confidence": 0.95,
    "reasoning": "why this approach is best",
    "alternative_approaches": [
        {{"name": "alternative 1", "description": "..."}}
    ],
    "estimated_execution_time": 30,
    "success_probability": 0.92,
    "cost_estimate": 0.10
}}

Optimize for the user's goals and constraints. Think like a senior engineer.
"""
    
    def _build_context(
        self,
        user_id: str,
        user_request: str,
        user_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build rich context for analysis"""
        if not user_history:
            return {"past_workflows_summary": "No history"}
        
        # Extract patterns
        past_workflows = [w.get('workflow', {}) for w in user_history]
        common_providers = {}
        for wf in past_workflows:
            for step in wf.get('steps', []):
                provider = step.get('provider', 'unknown')
                common_providers[provider] = common_providers.get(provider, 0) + 1
        
        return {
            "past_workflows_summary": f"{len(user_history)} workflows executed",
            "common_providers": list(sorted(common_providers.keys(), 
                                           key=lambda x: common_providers[x], 
                                           reverse=True)[:5]),
            "success_rate": len([w for w in user_history if w.get('status') == 'completed']) / len(user_history) if user_history else 0,
            "preferences": "Learn from execution patterns"
        }
    
    def _get_cache_key(self, user_id: str, agent_name: str, request: str) -> str:
        """Generate cache key for request"""
        key_str = f"{user_id}:{agent_name}:{request}"
        return hashlib.sha256(key_str.encode()).hexdigest()[:16]
    
    def _parse_workflow_response(
        self,
        response_text: str,
        user_request: str,
        available_providers: List[str]
    ) -> WorkflowSuggestion:
        """Parse and validate LLM response into WorkflowSuggestion"""
        try:
            parsed = json.loads(response_text)
            
            return WorkflowSuggestion(
                workflow=parsed.get('workflow', {}),
                confidence=float(parsed.get('confidence', 0.8)),
                reasoning=parsed.get('reasoning', ''),
                alternative_approaches=parsed.get('alternative_approaches', []),
                estimated_execution_time=int(parsed.get('estimated_execution_time', 60)),
                success_probability=float(parsed.get('success_probability', 0.8)),
                cost_estimate=float(parsed.get('cost_estimate', 0.0))
            )
        except Exception as e:
            self.logger.error(f"Error parsing workflow response: {str(e)}")
            raise


# Global AI intelligence instance
ai_intelligence = AIIntelligenceLayer()
