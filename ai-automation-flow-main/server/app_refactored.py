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

# ============= FLASK APP INITIALIZATION =============
app = Flask(__name__)
CORS(app)

# Database Manager - handles all persistence
db_manager = DatabaseManager()

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
