"""Fixed scheduler and background job initialization for Flask app"""

from flask_apscheduler import APScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import json
from execution_engine import execute_plan
from database import db_manager

# Initialize scheduler (MUST be done at app startup)
scheduler = APScheduler()


def init_scheduler(app):
    """Initialize and start the APScheduler for the Flask app"""
    
    # Configure scheduler
    app.config['SCHEDULER_API_ENABLED'] = True
    app.config['SCHEDULER_TIMEZONE'] = 'UTC'
    
    # Initialize scheduler with app
    scheduler.init_app(app)
    
    # Start scheduler (THIS WAS MISSING!)
    scheduler.start()
    
    print("✓ APScheduler initialized and started")
    
    # Load scheduled plans from database
    try:
        # This would be called after app startup
        load_scheduled_plans(app)
    except Exception as e:
        print(f"Warning: Failed to load scheduled plans: {e}")


def load_scheduled_plans(app):
    """Load all active scheduled execution plans from database"""
    
    try:
        # Get all execution plans with triggers from database
        conn = db_manager.get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, user_id, name, plan_json, trigger
            FROM execution_plans
            WHERE status = 'active' AND trigger IS NOT NULL AND trigger != '{}'::jsonb
        """)
        
        plans = cur.fetchall()
        cur.close()
        conn.close()
        
        for plan_id, user_id, name, plan_json, trigger in plans:
            if trigger and trigger.get('type') == 'cron':
                schedule_plan(app, plan_id, user_id, name, plan_json, trigger)
    
    except Exception as e:
        print(f"Error loading scheduled plans: {e}")


def schedule_plan(app, plan_id: str, user_id: str, plan_name: str,
                  plan_json: dict, trigger: dict):
    """Schedule a plan to run on a cron trigger"""
    
    try:
        cron_expr = trigger.get('cron_expression')
        if not cron_expr:
            return False
        
        # Parse cron expression (minute, hour, day, month, day_of_week)
        parts = cron_expr.split()
        if len(parts) != 5:
            print(f"Invalid cron expression: {cron_expr}")
            return False
        
        # Create job function that captures the plan details
        def job_func():
            try:
                result = execute_plan(plan_id, user_id, plan_json)
                
                # Log the scheduled execution
                db_manager.create_execution_log(
                    plan_id=plan_id,
                    user_id=user_id,
                    plan_name=plan_name,
                    step_number=0,
                    provider="scheduler",
                    action="trigger",
                    status="completed" if result.get("failed_steps", 0) == 0 else "error",
                    message=f"Scheduled execution completed: {result.get('completed_steps')}/{result.get('total_steps')} steps",
                    latency_ms=0
                )
                
                print(f"✓ Scheduled plan '{plan_name}' executed for user {user_id}")
            except Exception as e:
                print(f"✗ Error executing scheduled plan '{plan_name}': {e}")
                db_manager.create_execution_log(
                    plan_id=plan_id,
                    user_id=user_id,
                    plan_name=plan_name,
                    step_number=0,
                    provider="scheduler",
                    action="trigger",
                    status="error",
                    message=f"Scheduled execution failed",
                    error=str(e)
                )
        
        # Add job to scheduler
        scheduler.add_job(
            func=job_func,
            trigger=CronTrigger.from_crontab(cron_expr),
            id=f"plan_{plan_id}",
            name=f"Execute Plan: {plan_name}",
            replace_existing=True,  # Replace if already scheduled
            misfire_grace_time=60
        )
        
        print(f"✓ Scheduled plan '{plan_name}' with cron: {cron_expr}")
        return True
    
    except Exception as e:
        print(f"Error scheduling plan: {e}")
        return False


def unschedule_plan(plan_id: str):
    """Remove a plan from scheduler"""
    try:
        job_id = f"plan_{plan_id}"
        scheduler.remove_job(job_id)
        print(f"✓ Unscheduled plan {plan_id}")
        return True
    except Exception as e:
        print(f"Error unscheduling plan: {e}")
        return False


def list_scheduled_jobs():
    """Get list of all currently scheduled jobs"""
    try:
        jobs = scheduler.get_jobs()
        return [
            {
                "id": job.id,
                "name": job.name,
                "trigger": str(job.trigger),
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None
            }
            for job in jobs
        ]
    except Exception as e:
        print(f"Error listing scheduled jobs: {e}")
        return []
