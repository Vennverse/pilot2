"""
AI Automation Flow - Refactored Server
Clean architecture with provider registry pattern, proper scheduler initialization,
and database-backed credential management.
"""

import os
import json
import uuid
import time
import requests
from datetime import datetime
from typing import Tuple, Any, Optional, List, Dict

from flask import Flask, request, jsonify
from flask_cors import CORS
from cryptography.fernet import Fernet

# ============= NEW IMPORTS FROM REFACTORED ARCHITECTURE =============
from execution_engine import execute_step, execute_plan
from scheduler import init_scheduler, schedule_plan, unschedule_plan, list_scheduled_jobs
from provider_registry import registry
from database_manager import DatabaseManager
from agent_engine import agent_engine
from agents import agent_registry

# ============= NEW IMPORTS FOR 10 BREAKTHROUGH FEATURES =============
from advanced_execution_engine import AdvancedExecutionEngine, ExecutionStatus
from pricing_system import QuotaManager, PlanTier, PricingPlans
from team_collaboration import TeamCollaborationManager
from execution_monitoring import ExecutionMonitor, CustomCodeExecutor, CodeBlockStep
from analytics_engine import AnalyticsEngine
from marketplace import MarketplaceManager

# ============= FLASK APP INITIALIZATION =============
app = Flask(__name__)
CORS(app)

# Database Manager - handles all persistence
db_manager = DatabaseManager()

# Initialize feature managers
quota_manager = QuotaManager()
team_manager = TeamCollaborationManager()
execution_monitor = ExecutionMonitor()
analytics_engine = AnalyticsEngine()
code_executor = CustomCodeExecutor()
marketplace = MarketplaceManager()
advanced_engine = AdvancedExecutionEngine()

# ============= INITIALIZATION HOOK =============
@app.before_request
def initialize_app():
    """Initialize app on first request - sets up scheduler and registers providers"""
    if not hasattr(app, '_initialized'):
        # Initialize scheduler with Flask app
        init_scheduler(app)
        print(f"✓ Scheduler initialized and started")
        print(f"✓ Registered {len(registry.providers)} providers")
        app._initialized = True


# ============= HEALTH & DIAGNOSTIC ENDPOINTS =============
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint with timestamp"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0-refactored",
        "scheduler": "active",
        "database": "connected"
    })


@app.route('/api/providers', methods=['GET'])
def list_providers():
    """List all available providers and their actions"""
    providers_info = []
    for provider_name, provider_instance in registry.providers.items():
        providers_info.append({
            "name": provider_name,
            "description": getattr(provider_instance, 'description', 'No description'),
            "actions": getattr(provider_instance, 'actions', [])
        })
    
    return jsonify({
        "total": len(registry.providers),
        "providers": providers_info
    })


@app.route('/api/scheduler/jobs', methods=['GET'])
def get_scheduled_jobs():
    """List all currently scheduled jobs"""
    try:
        jobs = list_scheduled_jobs()
        return jsonify({
            "total": len(jobs),
            "jobs": jobs
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/execution-logs', methods=['GET'])
def get_execution_logs():
    """Get execution logs for a plan - database-backed"""
    user_id = request.args.get('user_id')
    plan_id = request.args.get('plan_id')
    limit = request.args.get('limit', 100, type=int)
    
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    
    try:
        logs = db_manager.get_execution_logs(user_id, plan_id, limit)
        return jsonify({
            "count": len(logs),
            "logs": logs
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============= AI PLANNER ENDPOINT =============
@app.route('/api/ai-planner', methods=['POST'])
def ai_planner():
    """Generate execution plans using AI with access to provider catalog"""
    data = request.json
    prompt = data.get('prompt')
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400
    
    # Build action catalog from registered providers
    action_catalog = [
        {
            "provider": name,
            "actions": getattr(provider, 'actions', [])
        }
        for name, provider in registry.providers.items()
    ]
    
    system_prompt = f"""Expert automation architect. You have access to {len(action_catalog)} providers.
PROVIDERS: {json.dumps(action_catalog)}

Generate execution plans with:
- action steps (type: 'action')
- conditional branches (type: 'condition')
- loops (type: 'loop')
- error handling

Reference previous step outputs with {{{{step_n.output}}}} syntax.
Output ONLY valid JSON matching the execution plan structure."""
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        return jsonify(json.loads(response.choices[0].message.content))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============= EXECUTION PLAN ENDPOINTS =============
@app.route('/api/execution-plans', methods=['GET', 'POST'])
def handle_plans():
    """Get or create execution plans"""
    user_id = request.args.get('user_id') or (request.json or {}).get('user_id')
    
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    
    if request.method == 'POST':
        try:
            plan_data = request.json or {}
            plan_data['user_id'] = user_id
            plan_data['created_at'] = datetime.now().isoformat()
            
            # Create in database
            plan = db_manager.create_execution_plan(
                user_id=user_id,
                name=plan_data.get('name', 'Untitled Plan'),
                description=plan_data.get('description', ''),
                plan_json=plan_data.get('plan_json', []),
                enabled=plan_data.get('enabled', True)
            )
            return jsonify(plan), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    # GET - list plans
    try:
        plans = db_manager.get_user_plans(user_id)
        return jsonify(plans)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/execution-plans/<plan_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_plan(plan_id):
    """Get, update, or delete a specific execution plan"""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    
    try:
        if request.method == 'GET':
            plan = db_manager.get_plan(plan_id, user_id)
            if not plan:
                return jsonify({"error": "Plan not found"}), 404
            return jsonify(plan)
        
        elif request.method == 'PUT':
            update_data = request.json or {}
            plan = db_manager.update_plan(plan_id, user_id, update_data)
            if not plan:
                return jsonify({"error": "Plan not found"}), 404
            return jsonify(plan)
        
        elif request.method == 'DELETE':
            # Unschedule any jobs for this plan
            unschedule_plan(plan_id)
            
            # Delete from database
            if db_manager.delete_plan(plan_id, user_id):
                return jsonify({"message": "Plan deleted"}), 200
            return jsonify({"error": "Plan not found"}), 404
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/execute-plan', methods=['POST'])
def execute_plan_endpoint():
    """Execute a plan immediately"""
    data = request.json or {}
    plan_id = data.get('execution_plan_id')
    user_id = data.get('user_id')
    trigger_data = data.get('trigger_data')
    
    if not plan_id or not user_id:
        return jsonify({"error": "execution_plan_id and user_id required"}), 400
    
    try:
        plan = db_manager.get_plan(plan_id, user_id)
        if not plan:
            return jsonify({"error": "Plan not found"}), 404
        
        # Execute the plan
        execution = execute_plan(
            plan=plan,
            user_id=user_id,
            trigger_data=trigger_data
        )
        return jsonify(execution)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/execution-plans/<plan_id>/schedule', methods=['POST', 'DELETE'])
def manage_plan_schedule(plan_id):
    """Schedule or unschedule a plan execution"""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    
    try:
        if request.method == 'POST':
            data = request.json or {}
            cron_expression = data.get('cron_expression')
            
            if not cron_expression:
                return jsonify({"error": "cron_expression is required"}), 400
            
            plan = db_manager.get_plan(plan_id, user_id)
            if not plan:
                return jsonify({"error": "Plan not found"}), 404
            
            # Schedule the plan
            job = schedule_plan(plan_id, user_id, cron_expression)
            return jsonify({
                "message": "Plan scheduled",
                "job_id": str(job.id),
                "schedule": cron_expression
            })
        
        elif request.method == 'DELETE':
            unschedule_plan(plan_id)
            return jsonify({"message": "Schedule removed"})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============= WEBHOOK TRIGGER ENDPOINTS =============
@app.route('/api/webhook/<path:webhook_path>', methods=['POST', 'GET', 'PUT', 'PATCH', 'DELETE'])
def webhook_trigger(webhook_path):
    """Webhook endpoint to trigger workflows"""
    try:
        # Look up plan by webhook path
        webhook_record = db_manager.get_webhook_by_path(webhook_path)
        if not webhook_record:
            return jsonify({"error": "Webhook not found"}), 404
        
        plan_id = webhook_record.get('plan_id')
        user_id = webhook_record.get('user_id')
        
        plan = db_manager.get_plan(plan_id, user_id)
        if not plan:
            return jsonify({"error": "Plan not found"}), 404
        
        # Extract webhook data
        trigger_data = {
            "method": request.method,
            "headers": dict(request.headers),
            "body": request.json if request.is_json else request.form.to_dict(),
            "query": request.args.to_dict(),
            "timestamp": datetime.now().isoformat()
        }
        
        # Execute the plan
        execution = execute_plan(
            plan=plan,
            user_id=user_id,
            trigger_data=trigger_data
        )
        return jsonify(execution)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============= MONITORING & ANALYTICS ENDPOINTS =============
@app.route('/api/monitoring/status', methods=['GET'])
def get_monitoring_status():
    """Get execution status for a user"""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    
    try:
        stats = db_manager.get_user_execution_stats(user_id)
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============= CUSTOM INTEGRATION ENDPOINTS =============
@app.route('/api/custom-integrations', methods=['GET', 'POST'])
def manage_custom_integrations():
    """Get or create custom integrations"""
    user_id = request.args.get('user_id') or (request.json or {}).get('user_id')
    
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    
    if request.method == 'GET':
        try:
            integrations = db_manager.get_custom_integrations(user_id)
            for integration in integrations:
                integration['actions'] = db_manager.get_integration_actions(str(integration['id']))
                if isinstance(integration.get('oauth_config'), str):
                    integration['oauth_config'] = json.loads(integration['oauth_config'])
            return jsonify(integrations)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    if request.method == 'POST':
        try:
            data = request.json or {}
            integration = db_manager.create_custom_integration(
                user_id=user_id,
                name=data.get('name'),
                display_name=data.get('display_name'),
                auth_type=data.get('auth_type', 'api_key'),
                base_url=data.get('oauth_config', {}).get('base_url', ''),
                auth_header=data.get('oauth_config', {}).get('auth_header', 'Authorization'),
                auth_prefix=data.get('oauth_config', {}).get('auth_prefix', 'Bearer'),
                description=data.get('description'),
                oauth_config=data.get('oauth_config', {})
            )
            
            # Create actions
            actions = []
            for action in data.get('actions', []):
                created_action = db_manager.create_integration_action(
                    integration_id=str(integration['id']),
                    action_id=action.get('id'),
                    action_name=action.get('name'),
                    http_method=action.get('method', 'POST'),
                    endpoint=action.get('endpoint', ''),
                    description=action.get('description'),
                    parameters=action.get('params', [])
                )
                actions.append(created_action)
            
            integration['actions'] = actions
            return jsonify(integration), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500


@app.route('/api/custom-integrations/<integration_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_single_integration(integration_id):
    """Get, update, or delete a specific custom integration"""
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    
    try:
        if request.method == 'GET':
            integration = db_manager.get_custom_integration(integration_id, user_id)
            if not integration:
                return jsonify({"error": "Integration not found"}), 404
            
            integration['actions'] = db_manager.get_integration_actions(integration_id)
            return jsonify(integration)
        
        elif request.method == 'PUT':
            data = request.json or {}
            updated = db_manager.update_custom_integration(
                integration_id=integration_id,
                user_id=user_id,
                display_name=data.get('display_name'),
                description=data.get('description'),
                auth_type=data.get('auth_type'),
                base_url=data.get('oauth_config', {}).get('base_url'),
                auth_header=data.get('oauth_config', {}).get('auth_header'),
                auth_prefix=data.get('oauth_config', {}).get('auth_prefix'),
                oauth_config=data.get('oauth_config', {})
            )
            
            if not updated:
                return jsonify({"error": "Integration not found"}), 404
            
            updated['actions'] = db_manager.get_integration_actions(integration_id)
            return jsonify(updated)
        
        elif request.method == 'DELETE':
            if db_manager.delete_custom_integration(integration_id, user_id):
                return jsonify({"message": "Integration deleted"}), 200
            return jsonify({"error": "Integration not found"}), 404
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/custom-integrations/<integration_id>/credentials', methods=['POST'])
def store_integration_credential(integration_id):
    """Store credential for a custom integration"""
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    
    try:
        data = request.json or {}
        credential = db_manager.store_credential(
            user_id=user_id,
            integration_id=integration_id,
            credential_type=data.get('type', 'api_key'),
            value=data.get('value'),
            expires_at=data.get('expires_at')
        )
        return jsonify({
            "message": "Credential stored",
            "credential_id": str(credential['id'])
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/custom-integrations/<integration_id>/test', methods=['POST'])
def test_integration(integration_id):
    """Test a custom integration by making a request"""
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    
    try:
        integration = db_manager.get_custom_integration(integration_id, user_id)
        if not integration:
            return jsonify({"error": "Integration not found"}), 404
        
        data = request.json or {}
        api_key = db_manager.get_credential(user_id, integration_id, 'api_key')
        
        # Build request
        base_url = integration.get('base_url', '')
        endpoint = data.get('endpoint', '')
        method = (data.get('method', 'POST')).upper()
        headers = data.get('headers', {})
        body = data.get('body', {})
        
        # Add auth header if API key exists
        if api_key:
            auth_header = integration.get('auth_header', 'Authorization')
            auth_prefix = integration.get('auth_prefix', 'Bearer')
            headers[auth_header] = f"{auth_prefix} {api_key}"
        
        full_url = f"{base_url}{endpoint}" if base_url else endpoint
        
        # Make test request
        if method == 'GET':
            response = requests.get(full_url, headers=headers, params=body, timeout=5)
        elif method == 'POST':
            response = requests.post(full_url, headers=headers, json=body, timeout=5)
        elif method == 'PUT':
            response = requests.put(full_url, headers=headers, json=body, timeout=5)
        elif method == 'PATCH':
            response = requests.patch(full_url, headers=headers, json=body, timeout=5)
        elif method == 'DELETE':
            response = requests.delete(full_url, headers=headers, timeout=5)
        else:
            return jsonify({"error": f"Unsupported HTTP method: {method}"}), 400
        
        response.raise_for_status()
        
        return jsonify({
            "status": "success",
            "status_code": response.status_code,
            "response": response.json() if response.content else {}
        })
    
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "failed", "error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============= AGENT ENDPOINTS =============
@app.route('/api/agents', methods=['GET'])
def list_agents():
    """List all available agents and their capabilities"""
    agents_info = agent_engine.get_agent_info()
    return jsonify({
        "agents": agents_info,
        "total_agents": len(agent_engine.list_agents()),
        "available_agents": agent_engine.list_agents()
    })


@app.route('/api/agents/<agent_name>', methods=['GET'])
def get_agent_info(agent_name):
    """Get detailed information about a specific agent"""
    agent_info = agent_engine.get_agent_info(agent_name)
    if "error" in agent_info:
        return jsonify(agent_info), 404
    
    # Add validation status
    is_valid, validation_msg = agent_engine.validate_agent(agent_name)
    agent_info['validation'] = {
        'is_valid': is_valid,
        'message': validation_msg
    }
    
    return jsonify(agent_info)


@app.route('/api/agents/<agent_name>/execute', methods=['POST'])
def execute_agent(agent_name):
    """
    Execute an agent with a natural language request.
    
    Request body:
    {
        "request": "send emails to tech companies",
        "auto_execute": true  // execute workflow immediately (default: true)
    }
    """
    data = request.get_json()
    user_request = data.get('request', '').strip()
    auto_execute = data.get('auto_execute', True)
    
    if not user_request:
        return jsonify({"error": "Missing 'request' field"}), 400
    
    user_id = request.headers.get('X-User-ID', 'unknown_user')
    
    # Execute agent
    success, result = agent_engine.execute_agent_request(
        user_id=user_id,
        agent_name=agent_name,
        user_request=user_request,
        auto_execute=auto_execute
    )
    
    status_code = 200 if success else 400
    return jsonify(result), status_code


@app.route('/api/agents/<agent_name>/preview', methods=['POST'])
def preview_agent_workflow(agent_name):
    """
    Generate a workflow without executing it.
    Useful for previewing what the agent will do before committing to execution.
    
    Request body:
    {
        "request": "send emails to tech companies"
    }
    """
    data = request.get_json()
    user_request = data.get('request', '').strip()
    
    if not user_request:
        return jsonify({"error": "Missing 'request' field"}), 400
    
    # Generate without executing
    success, result = agent_engine.generate_workflow_without_execution(
        agent_name=agent_name,
        user_request=user_request
    )
    
    status_code = 200 if success else 400
    return jsonify(result), status_code


@app.route('/api/agents/<agent_name>/history', methods=['GET'])
def get_agent_history(agent_name):
    """Get execution history for a specific agent"""
    user_id = request.headers.get('X-User-ID', 'unknown_user')
    limit = request.args.get('limit', 20, type=int)
    
    history = agent_engine.get_workflow_history(
        user_id=user_id,
        agent_name=agent_name,
        limit=limit
    )
    
    return jsonify({
        "agent_name": agent_name,
        "user_id": user_id,
        "executions": history,
        "total": len(history)
    })


@app.route('/api/workflows/<plan_id>/execute-steps', methods=['POST'])
def execute_workflow_step_by_step(plan_id):
    """
    Execute a workflow step-by-step with detailed logging.
    Useful for debugging and monitoring agent-generated workflows.
    """
    user_id = request.headers.get('X-User-ID', 'unknown_user')
    
    result = agent_engine.execute_workflow_step_by_step(
        user_id=user_id,
        plan_id=plan_id
    )
    
    status_code = 200 if result.get('success') else 400
    return jsonify(result), status_code


# ============= NEW AI INTELLIGENCE ENDPOINTS (LLM-POWERED) =============

@app.route('/api/agents/<agent_name>/alternatives', methods=['POST'])
def get_workflow_alternatives(agent_name):
    """
    Get alternative workflow approaches for a request.
    
    Request body:
    {
        "request": "send emails to tech companies"
    }
    
    Response: Multiple workflow options with trade-offs
    """
    data = request.get_json()
    user_request = data.get('request', '').strip()
    
    if not user_request:
        return jsonify({"error": "Missing 'request' field"}), 400
    
    try:
        agent = agent_registry.get_agent(agent_name)
        if not agent:
            return jsonify({"error": f"Agent '{agent_name}' not found"}), 404
        
        alternatives = agent.get_workflow_alternatives(user_request)
        
        return jsonify({
            "agent_name": agent_name,
            "request": user_request,
            "alternatives": alternatives,
            "count": len(alternatives)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/agents/<agent_name>/predict', methods=['POST'])
def predict_workflow_success(agent_name):
    """
    Predict success probability of a workflow approach.
    
    Request body:
    {
        "request": "send emails to tech companies"
    }
    
    Response: Success probability (0-1), reasoning, and risk factors
    """
    data = request.get_json()
    user_request = data.get('request', '').strip()
    
    if not user_request:
        return jsonify({"error": "Missing 'request' field"}), 400
    
    user_id = request.headers.get('X-User-ID', 'unknown_user')
    
    try:
        agent = agent_registry.get_agent(agent_name)
        if not agent:
            return jsonify({"error": f"Agent '{agent_name}' not found"}), 404
        
        prediction = agent.predict_success(user_request, user_id)
        
        return jsonify({
            "agent_name": agent_name,
            "request": user_request,
            "prediction": prediction,
            "success_probability": prediction.get('probability', 0),
            "reasoning": prediction.get('reasoning', ''),
            "risk_factors": prediction.get('risk_factors', [])
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/workflows/<plan_id>/learn', methods=['POST'])
def learn_from_workflow_execution(plan_id):
    """
    Extract insights and learn from a completed workflow execution.
    This improves future workflow generation for similar requests.
    
    Request body:
    {
        "feedback": "workflow worked well but took too long",
        "rating": 4
    }
    
    Response: Learning insights and pattern extraction
    """
    user_id = request.headers.get('X-User-ID', 'unknown_user')
    data = request.get_json() or {}
    feedback = data.get('feedback', '')
    rating = data.get('rating', 0)
    
    try:
        # Get workflow from database
        workflow = db_manager.get_execution_plan(plan_id)
        if not workflow:
            return jsonify({"error": f"Workflow {plan_id} not found"}), 404
        
        agent_name = workflow.get('agent_name')
        agent = agent_registry.get_agent(agent_name)
        if not agent:
            return jsonify({"error": f"Agent '{agent_name}' not found"}), 404
        
        # Get execution results
        execution_result = {
            'plan_id': plan_id,
            'workflow': workflow.get('workflow'),
            'feedback': feedback,
            'rating': rating,
            'timestamp': datetime.now().isoformat()
        }
        
        # Learn from execution
        learning = agent.learn_from_execution(
            user_id=user_id,
            workflow=workflow.get('workflow'),
            execution_result=execution_result
        )
        
        # Store learning in database
        db_manager.store_learning(
            user_id=user_id,
            workflow_id=plan_id,
            learning=learning,
            feedback=feedback,
            rating=rating
        )
        
        return jsonify({
            "plan_id": plan_id,
            "learning": learning,
            "patterns_extracted": learning.get('patterns', []),
            "improvements": learning.get('improvements', []),
            "message": "Learning stored and will improve future workflows"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/workflows/insights', methods=['GET'])
def get_workflow_insights():
    """
    Get AI-powered insights about workflow patterns and recommendations.
    """
    user_id = request.headers.get('X-User-ID', 'unknown_user')
    limit = request.args.get('limit', 10, type=int)
    
    try:
        insights = agent_engine.get_workflow_insights(user_id, limit)
        return jsonify(insights)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============= PRICING & QUOTA ENDPOINTS =============
@app.route('/api/pricing/plans', methods=['GET'])
def get_pricing_plans():
    """Get all available pricing plans"""
    try:
        plans = PricingPlans.get_all_plans()
        return jsonify(plans)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/pricing/quota', methods=['GET'])
def get_user_quota():
    """Get user's current quota and usage"""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    
    try:
        quota = quota_manager.get_user_quota_status(user_id)
        return jsonify(quota)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/pricing/quota/check', methods=['POST'])
def check_quota():
    """Check if user can perform an action (pre-flight check)"""
    data = request.json or {}
    user_id = data.get('user_id')
    action = data.get('action', 'execute_workflow')
    
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    
    try:
        allowed, remaining = quota_manager.check_quota(user_id, action)
        return jsonify({
            "allowed": allowed,
            "remaining": remaining
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/pricing/plan/upgrade', methods=['POST'])
def upgrade_plan():
    """Upgrade user's plan to a higher tier"""
    data = request.json or {}
    user_id = data.get('user_id')
    new_plan = data.get('plan')
    
    if not user_id or not new_plan:
        return jsonify({"error": "user_id and plan are required"}), 400
    
    try:
        quota_manager.upgrade_plan(user_id, new_plan)
        updated_quota = quota_manager.get_user_quota_status(user_id)
        return jsonify({
            "message": f"Upgraded to {new_plan}",
            "quota": updated_quota
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============= TEAM COLLABORATION ENDPOINTS =============
@app.route('/api/team/workspaces', methods=['GET'])
def get_workspaces():
    """Get user's workspaces"""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    
    try:
        workspaces = team_manager.get_user_workspaces(user_id)
        return jsonify(workspaces)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/team/workspaces', methods=['POST'])
def create_workspace():
    """Create a new team workspace"""
    data = request.json or {}
    user_id = data.get('user_id')
    name = data.get('name')
    description = data.get('description', '')
    
    if not user_id or not name:
        return jsonify({"error": "user_id and name are required"}), 400
    
    try:
        workspace = team_manager.create_workspace(name, user_id, description)
        return jsonify(workspace), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/team/workspaces/<workspace_id>/members', methods=['GET'])
def get_workspace_members(workspace_id):
    """Get members of a workspace"""
    try:
        members = team_manager.get_workspace_members(workspace_id)
        return jsonify(members)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/team/workspaces/<workspace_id>/members', methods=['POST'])
def add_member_to_workspace(workspace_id):
    """Add a member to workspace"""
    data = request.json or {}
    user_id = data.get('user_id')
    member_email = data.get('member_email')
    role = data.get('role', 'EDITOR')
    
    if not user_id or not member_email:
        return jsonify({"error": "user_id and member_email are required"}), 400
    
    try:
        # In production, would lookup user by email
        result = team_manager.add_member_to_workspace(workspace_id, member_email, role)
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/team/workspaces/<workspace_id>/invite', methods=['POST'])
def generate_invite_link(workspace_id):
    """Generate shareable invite link for workspace"""
    data = request.json or {}
    user_id = data.get('user_id')
    role = data.get('role', 'EDITOR')
    max_uses = data.get('max_uses', None)
    
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    
    try:
        invite = team_manager.generate_invite_link(workspace_id, role, max_uses)
        return jsonify(invite), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/team/workspaces/invite/<invite_code>', methods=['POST'])
def accept_invite(invite_code):
    """Accept workspace invite via invite code"""
    data = request.json or {}
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    
    try:
        result = team_manager.accept_invite(invite_code, user_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/team/workspaces/<workspace_id>/audit-log', methods=['GET'])
def get_audit_log(workspace_id):
    """Get workspace audit log"""
    limit = request.args.get('limit', 100, type=int)
    
    try:
        logs = team_manager.get_audit_log(workspace_id, limit)
        return jsonify(logs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============= ANALYTICS ENDPOINTS =============
@app.route('/api/analytics/roi', methods=['GET'])
def get_roi_dashboard():
    """Get user's ROI dashboard"""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    
    try:
        roi = analytics_engine.get_user_roi_dashboard(user_id)
        return jsonify(roi)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/analytics/workflow/<workflow_id>', methods=['GET'])
def get_workflow_analytics(workflow_id):
    """Get analytics for specific workflow"""
    try:
        performance = analytics_engine.get_workflow_performance(workflow_id)
        return jsonify(performance)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/analytics/team', methods=['GET'])
def get_team_analytics():
    """Get team-wide analytics"""
    workspace_id = request.args.get('workspace_id')
    if not workspace_id:
        return jsonify({"error": "workspace_id is required"}), 400
    
    try:
        team_stats = analytics_engine.get_team_analytics(workspace_id)
        return jsonify(team_stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/analytics/roi-projection', methods=['GET'])
def get_roi_projection():
    """Get 12-month ROI projection"""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    
    try:
        projection = analytics_engine.calculate_roi_projection(user_id)
        return jsonify(projection)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============= EXECUTION MONITORING ENDPOINTS =============
@app.route('/api/monitoring/stream/<execution_id>', methods=['GET'])
def get_execution_stream(execution_id):
    """Get execution event stream"""
    limit = request.args.get('limit', 50, type=int)
    
    try:
        events = execution_monitor.get_execution_stream(execution_id, limit)
        return jsonify([e.to_dict() if hasattr(e, 'to_dict') else e for e in events])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/monitoring/subscribe', methods=['POST'])
def subscribe_to_execution():
    """Subscribe to execution events (WebSocket would be better, but this is REST)"""
    data = request.json or {}
    execution_id = data.get('execution_id')
    
    if not execution_id:
        return jsonify({"error": "execution_id is required"}), 400
    
    try:
        execution_monitor.start_monitoring(execution_id)
        return jsonify({"message": "Monitoring started", "execution_id": execution_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============= CODE EXECUTION ENDPOINTS =============
@app.route('/api/code/execute', methods=['POST'])
def execute_custom_code():
    """Execute custom code in sandbox"""
    data = request.json or {}
    user_id = data.get('user_id')
    language = data.get('language', 'python')
    code = data.get('code')
    
    if not user_id or not code:
        return jsonify({"error": "user_id and code are required"}), 400
    
    # Check quota
    allowed, _ = quota_manager.check_quota(user_id, 'custom_code')
    if not allowed:
        return jsonify({"error": "Custom code execution quota exceeded"}), 403
    
    try:
        result = None
        if language == 'python':
            result = code_executor.execute_python(code)
        elif language == 'javascript':
            result = code_executor.execute_javascript(code)
        elif language == 'sql':
            result = code_executor.execute_sql_transform(code)
        else:
            return jsonify({"error": f"Unsupported language: {language}"}), 400
        
        # Increment usage
        quota_manager.increment_usage(user_id, 'custom_code')
        
        return jsonify({
            "language": language,
            "result": result,
            "success": True
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "success": False
        }), 500


# ============= MARKETPLACE ENDPOINTS =============
@app.route('/api/marketplace/templates', methods=['GET'])
def get_marketplace_templates():
    """Get templates from marketplace"""
    industry = request.args.get('industry')
    category = request.args.get('category')
    search = request.args.get('search')
    featured_only = request.args.get('featured_only', False, type=bool)
    
    try:
        if featured_only:
            templates = marketplace.get_featured_templates()
        elif industry:
            templates = marketplace.get_templates_by_industry(industry)
        elif category:
            templates = marketplace.get_templates_by_category(category)
        elif search:
            templates = marketplace.search_templates(search)
        else:
            templates = marketplace.get_all_templates()
        
        return jsonify([t.to_dict() if hasattr(t, 'to_dict') else t for t in templates])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/marketplace/templates/<template_id>/download', methods=['POST'])
def download_template(template_id):
    """Download template to user's workspace"""
    data = request.json or {}
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    
    try:
        template = marketplace.download_template(template_id, user_id)
        return jsonify({
            "message": "Template downloaded successfully",
            "template": template.to_dict() if hasattr(template, 'to_dict') else template
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/marketplace/templates/<template_id>/rate', methods=['POST'])
def rate_template(template_id):
    """Rate a template"""
    data = request.json or {}
    user_id = data.get('user_id')
    rating = data.get('rating')
    review = data.get('review', '')
    
    if not user_id or not rating:
        return jsonify({"error": "user_id and rating are required"}), 400
    
    try:
        result = marketplace.rate_template(template_id, user_id, rating, review)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/marketplace/templates/<template_id>', methods=['GET'])
def get_template_details(template_id):
    """Get template details"""
    try:
        template = marketplace.get_template(template_id)
        return jsonify(template.to_dict() if hasattr(template, 'to_dict') else template)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/marketplace/stats', methods=['GET'])
def get_marketplace_stats():
    """Get marketplace statistics"""
    try:
        stats = marketplace.get_marketplace_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============= ADVANCED EXECUTION ENDPOINTS =============
@app.route('/api/execution/advanced/pause', methods=['POST'])
def pause_execution():
    """Pause an execution"""
    data = request.json or {}
    execution_id = data.get('execution_id')
    user_id = data.get('user_id')
    
    if not execution_id or not user_id:
        return jsonify({"error": "execution_id and user_id are required"}), 400
    
    try:
        advanced_engine.pause_execution(execution_id)
        return jsonify({"message": "Execution paused", "execution_id": execution_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/execution/advanced/resume', methods=['POST'])
def resume_execution():
    """Resume a paused execution"""
    data = request.json or {}
    execution_id = data.get('execution_id')
    user_id = data.get('user_id')
    
    if not execution_id or not user_id:
        return jsonify({"error": "execution_id and user_id are required"}), 400
    
    try:
        advanced_engine.resume_execution(execution_id)
        return jsonify({"message": "Execution resumed", "execution_id": execution_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/execution/advanced/status', methods=['GET'])
def get_execution_status():
    """Get execution status"""
    execution_id = request.args.get('execution_id')
    
    if not execution_id:
        return jsonify({"error": "execution_id is required"}), 400
    
    try:
        status = advanced_engine.get_execution_status(execution_id)
        return jsonify({"status": status.value if hasattr(status, 'value') else status})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/execution/advanced/dlq', methods=['GET'])
def get_dead_letter_queue():
    """Get failed executions from dead letter queue"""
    user_id = request.args.get('user_id')
    limit = request.args.get('limit', 50, type=int)
    
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    
    try:
        dlq = advanced_engine.get_dead_letter_queue(user_id, limit)
        return jsonify(dlq)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/execution/advanced/retry-dlq', methods=['POST'])
def retry_dlq():
    """Retry failed execution from DLQ"""
    data = request.json or {}
    execution_id = data.get('execution_id')
    user_id = data.get('user_id')
    
    if not execution_id or not user_id:
        return jsonify({"error": "execution_id and user_id are required"}), 400
    
    try:
        result = advanced_engine.retry_from_dlq(execution_id)
        return jsonify({"message": "Retry initiated", "execution_id": execution_id, "result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============= ERROR HANDLERS =============
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error", "details": str(e)}), 500


# ============= MAIN ENTRY POINT =============
if __name__ == '__main__':
    print("Starting AI Automation Flow Server (v2.0 - Refactored)")
    print(f"Database: {os.environ.get('DATABASE_URL', 'localhost')}")
    print(f"Scheduler: APScheduler (will start on first request)")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5001, debug=False)
