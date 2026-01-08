"""Refactored execute_step function using provider registry pattern"""

import json
import time
from typing import Dict, Any, Tuple
from providers import registry
from database import db_manager


def resolve_params(params: Dict[str, Any], step_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Resolve dynamic parameters by replacing references to previous step outputs.
    
    Example:
        params = {"query": "${steps.0.output}", "limit": 10}
        becomes {"query": <output_from_step_0>, "limit": 10}
    """
    resolved = {}
    
    for key, value in params.items():
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            # Parse reference like "${steps.0.output}"
            ref = value[2:-1]  # Remove "${ }"
            
            try:
                if ref.startswith("steps."):
                    step_idx, output_key = ref.replace("steps.", "").split(".", 1)
                    step_output = step_results.get(int(step_idx), {})
                    resolved[key] = step_output.get(output_key)
                else:
                    resolved[key] = value
            except (ValueError, IndexError, KeyError):
                resolved[key] = value
        elif isinstance(value, dict):
            # Recursively resolve nested dicts
            resolved[key] = resolve_params(value, step_results)
        elif isinstance(value, list):
            # Recursively resolve lists
            resolved[key] = [
                resolve_params({"_": item}, step_results)["_"] if isinstance(item, dict)
                else item
                for item in value
            ]
        else:
            resolved[key] = value
    
    return resolved


def execute_step(step: Dict[str, Any], user_id: str, step_results: Dict[str, Any],
                 plan_id: str = None, step_number: int = 0, max_retries: int = 3) -> Tuple[bool, Any, str]:
    """
    Execute a single step using the provider registry.
    
    Args:
        step: Step configuration with provider, action, params
        user_id: User executing the step (for credential isolation)
        step_results: Dict of previous step outputs
        plan_id: ID of the execution plan (for logging)
        step_number: Index of this step
        max_retries: Number of times to retry on failure
        
    Returns:
        Tuple of (success: bool, output: Any, message: str)
    """
    provider = step.get("provider")
    action = step.get("action")
    params = step.get("params", {})
    
    if not provider:
        return (False, None, "No provider specified in step")
    
    # Resolve dynamic parameters
    try:
        resolved_params = resolve_params(params, step_results)
    except Exception as e:
        return (False, None, f"Parameter resolution failed: {str(e)}")
    
    # Get user credentials for this provider
    try:
        credentials = db_manager.get_provider_credentials(user_id, provider)
    except Exception as e:
        return (False, None, f"Failed to retrieve credentials for {provider}: {str(e)}")
    
    # Execute with retry logic
    last_error = None
    for attempt in range(max_retries):
        start_time = time.time()
        
        try:
            # Call provider through registry
            result = registry.execute(
                provider=provider,
                action=action,
                params=resolved_params,
                user_id=user_id,
                credentials=credentials,
                step_results=step_results
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Log execution
            if plan_id:
                output_preview = str(result.output)[:500] if result.output else None
                try:
                    db_manager.create_execution_log(
                        plan_id=plan_id,
                        user_id=user_id,
                        plan_name=step.get("plan_name", "Unknown"),
                        step_number=step_number,
                        provider=provider,
                        action=action,
                        status="success" if result.success else "error",
                        message=result.message,
                        latency_ms=latency_ms,
                        output_preview=output_preview,
                        error=result.error
                    )
                except Exception as log_error:
                    print(f"Warning: Failed to log execution: {log_error}")
            
            return (result.success, result.output, result.message)
            
        except Exception as e:
            last_error = str(e)
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Log failed attempt
            if plan_id:
                try:
                    db_manager.create_execution_log(
                        plan_id=plan_id,
                        user_id=user_id,
                        plan_name=step.get("plan_name", "Unknown"),
                        step_number=step_number,
                        provider=provider,
                        action=action,
                        status="error",
                        message=f"Attempt {attempt + 1}/{max_retries} failed",
                        latency_ms=latency_ms,
                        error=last_error
                    )
                except Exception as log_error:
                    print(f"Warning: Failed to log error: {log_error}")
            
            # Don't retry on last attempt
            if attempt == max_retries - 1:
                break
            
            # Exponential backoff
            wait_time = 2 ** attempt
            print(f"Provider {provider} failed on attempt {attempt + 1}, retrying in {wait_time}s...")
            time.sleep(wait_time)
    
    # All retries exhausted
    return (False, None, f"Provider {provider} failed after {max_retries} attempts: {last_error}")


def execute_plan(plan_id: str, user_id: str, plan_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute all steps in a plan sequentially.
    
    Args:
        plan_id: ID of the execution plan
        user_id: User executing the plan
        plan_data: The plan structure with steps array
        
    Returns:
        Execution results with status, outputs, and logs
    """
    steps = plan_data.get("steps", [])
    step_results = {}
    execution_summary = {
        "plan_id": plan_id,
        "user_id": user_id,
        "total_steps": len(steps),
        "completed_steps": 0,
        "failed_steps": 0,
        "step_outputs": {},
        "errors": []
    }
    
    for idx, step in enumerate(steps):
        success, output, message = execute_step(
            step=step,
            user_id=user_id,
            step_results=step_results,
            plan_id=plan_id,
            step_number=idx,
            max_retries=3
        )
        
        # Store result for next step's parameter resolution
        step_results[idx] = {
            "success": success,
            "output": output,
            "message": message
        }
        
        # Track summary
        execution_summary["step_outputs"][idx] = {
            "provider": step.get("provider"),
            "action": step.get("action"),
            "success": success,
            "output": output,
            "message": message
        }
        
        if success:
            execution_summary["completed_steps"] += 1
        else:
            execution_summary["failed_steps"] += 1
            execution_summary["errors"].append({
                "step": idx,
                "provider": step.get("provider"),
                "error": message
            })
            
            # Stop on first error (can be made configurable)
            break
    
    return execution_summary
