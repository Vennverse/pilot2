"""Updated Flask app initialization with provider registry integration"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import uuid
from datetime import datetime

# Import the refactored systems
from database import db_manager
from execution_engine import execute_plan, execute_step
from scheduler import init_scheduler, schedule_plan, unschedule_plan, list_scheduled_jobs
from providers import registry

# Initialize Flask app
app = Flask(__name__)
CORS(app)


# ============================================================================
# APP INITIALIZATION (This replaces the broken in-memory db setup)
# ============================================================================

@app.before_request
def setup():
    """One-time setup on first request"""
    if not hasattr(app, '_initialized'):
        try:
            # Initialize scheduler with app
            init_scheduler(app)
            
            # Initialize provider registry
            print(f"✓ Registered {len(registry.providers)} providers")
            
            app._initialized = True
        except Exception as e:
            print(f"ERROR during initialization: {e}")
            raise


# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})


@app.route('/api/providers', methods=['GET'])
def list_providers():
    """Get list of available providers and their actions"""
    return jsonify({"providers": list(registry.providers.keys())})


@app.route('/api/scheduler/jobs', methods=['GET'])
def scheduler_jobs():
    """Get list of currently scheduled jobs"""
    return jsonify({"jobs": list_scheduled_jobs()})


# ============================================================================
# EXECUTION PLAN ENDPOINTS (Database-backed)
# ============================================================================

@app.route('/api/plans', methods=['GET'])
def get_plans():
    """Get user's execution plans"""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id required"}), 400
    
    try:
        plans = db_manager.get_user_execution_plans(user_id)
        return jsonify({"plans": plans})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/plans', methods=['POST'])
def create_plan():
    """Create a new execution plan"""
    data = request.json
    user_id = data.get('user_id')
    name = data.get('name')
    prompt = data.get('original_prompt')
    steps = data.get('steps', [])
    
    if not all([user_id, name, prompt]):
        return jsonify({"error": "user_id, name, and original_prompt required"}), 400
    
    try:
        result = db_manager.save_execution_plan(
            user_id=user_id,
            name=name,
            original_prompt=prompt,
            plan_json=steps,
            plain_english_steps=data.get('plain_english_steps', []),
            required_providers=data.get('required_providers', []),
            trigger=data.get('trigger')
        )
        return jsonify({"plan": result}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/plans/<plan_id>', methods=['GET'])
def get_plan(plan_id):
    """Get a specific execution plan"""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id required"}), 400
    
    try:
        plans = db_manager.get_user_execution_plans(user_id)
        plan = next((p for p in plans if p['id'] == plan_id), None)
        
        if not plan:
            return jsonify({"error": "Plan not found"}), 404
        
        return jsonify({"plan": plan})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# EXECUTION ENDPOINTS (Uses new execution engine)
# ============================================================================

@app.route('/api/execute', methods=['POST'])
def execute():
    """Execute a plan"""
    data = request.json
    plan_id = data.get('plan_id')
    user_id = data.get('user_id')
    
    if not all([plan_id, user_id]):
        return jsonify({"error": "plan_id and user_id required"}), 400
    
    try:
        # Get the plan
        plans = db_manager.get_user_execution_plans(user_id)
        plan = next((p for p in plans if p['id'] == plan_id), None)
        
        if not plan:
            return jsonify({"error": "Plan not found"}), 404
        
        # Execute the plan
        result = execute_plan(plan_id, user_id, plan['plan_json'])
        
        return jsonify({
            "execution": result,
            "success": result.get('failed_steps', 0) == 0
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/execute-step', methods=['POST'])
def execute_step_endpoint():
    """Execute a single step (for testing/manual execution)"""
    data = request.json
    step = data.get('step')
    user_id = data.get('user_id')
    plan_id = data.get('plan_id')
    step_number = data.get('step_number', 0)
    
    if not all([step, user_id]):
        return jsonify({"error": "step and user_id required"}), 400
    
    try:
        success, output, message = execute_step(
            step=step,
            user_id=user_id,
            step_results=data.get('step_results', {}),
            plan_id=plan_id,
            step_number=step_number,
            max_retries=3
        )
        
        return jsonify({
            "success": success,
            "output": output,
            "message": message
        })
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500


# ============================================================================
# EXECUTION LOGS ENDPOINTS
# ============================================================================

@app.route('/api/execution-logs', methods=['GET'])
def get_logs():
    """Get execution logs for a plan"""
    plan_id = request.args.get('plan_id')
    user_id = request.args.get('user_id')
    
    if not all([plan_id, user_id]):
        return jsonify({"error": "plan_id and user_id required"}), 400
    
    try:
        logs = db_manager.get_execution_logs(plan_id, user_id)
        return jsonify({"logs": logs})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# PROVIDER CREDENTIALS ENDPOINTS
# ============================================================================

@app.route('/api/provider-credentials/<provider>', methods=['GET'])
def get_provider_creds(provider):
    """Get stored credentials for a provider"""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id required"}), 400
    
    try:
        credentials = db_manager.get_provider_credentials(user_id, provider)
        # Don't return actual values, just the types stored
        return jsonify({
            "provider": provider,
            "credential_types": list(credentials.keys())
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/provider-credentials/<provider>', methods=['POST'])
def store_provider_creds(provider):
    """Store credentials for a provider"""
    data = request.json
    user_id = data.get('user_id')
    credentials = data.get('credentials', {})
    
    if not user_id:
        return jsonify({"error": "user_id required"}), 400
    
    try:
        for cred_type, value in credentials.items():
            db_manager.store_provider_credential(
                user_id=user_id,
                provider=provider,
                credential_type=cred_type,
                value=value,
                expires_at=data.get('expires_at')
            )
        
        return jsonify({"success": True, "provider": provider})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# SCHEDULER ENDPOINTS
# ============================================================================

@app.route('/api/plans/<plan_id>/schedule', methods=['POST'])
def schedule_execution(plan_id):
    """Schedule a plan to run on a cron schedule"""
    data = request.json
    user_id = data.get('user_id')
    cron_expression = data.get('cron_expression')
    
    if not all([user_id, cron_expression]):
        return jsonify({"error": "user_id and cron_expression required"}), 400
    
    try:
        # Get the plan
        plans = db_manager.get_user_execution_plans(user_id)
        plan = next((p for p in plans if p['id'] == plan_id), None)
        
        if not plan:
            return jsonify({"error": "Plan not found"}), 404
        
        # Schedule it
        trigger = {"type": "cron", "cron_expression": cron_expression}
        success = schedule_plan(
            app,
            plan_id,
            user_id,
            plan['name'],
            plan['plan_json'],
            trigger
        )
        
        if success:
            # Update plan status
            # db_manager.update_plan_status(plan_id, 'active', trigger)
            return jsonify({"success": True, "plan_id": plan_id})
        else:
            return jsonify({"error": "Failed to schedule plan"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/plans/<plan_id>/unschedule', methods=['POST'])
def unschedule_execution(plan_id):
    """Remove a plan from scheduler"""
    data = request.json
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({"error": "user_id required"}), 400
    
    try:
        unschedule_plan(plan_id)
        
        # Update plan status
        # db_manager.update_plan_status(plan_id, 'draft', None)
        
        return jsonify({"success": True, "plan_id": plan_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# CUSTOM INTEGRATIONS (from previous migration)
# ============================================================================

@app.route('/api/custom-integrations', methods=['GET'])
def get_custom_integrations():
    """Get user's custom integrations"""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id required"}), 400
    
    try:
        integrations = db_manager.get_custom_integrations(user_id)
        return jsonify({"integrations": integrations})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/custom-integrations', methods=['POST'])
def create_custom_integration():
    """Create a new custom integration"""
    data = request.json
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({"error": "user_id required"}), 400
    
    try:
        integration = db_manager.create_custom_integration(
            user_id=user_id,
            name=data.get('name'),
            auth_type=data.get('auth_type'),
            base_url=data.get('base_url'),
            oauth_config=data.get('oauth_config'),
            api_key=data.get('api_key'),
            extra_config=data.get('extra_config')
        )
        return jsonify({"integration": integration}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
