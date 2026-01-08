# QUICK START: Using the Refactored System

## For Users: Executing Automations

### 1. Store Your API Keys (First Time Only)

```bash
curl -X POST http://localhost:5000/api/provider-credentials/openai \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "credentials": {
      "api_key": "sk-..."
    }
  }'
```

### 2. Create an Execution Plan

```bash
curl -X POST http://localhost:5000/api/plans \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "name": "Email Newsletter",
    "original_prompt": "Generate a newsletter and send to Gmail",
    "steps": [
      {
        "provider": "openai",
        "action": "chat_completion",
        "params": {
          "prompt": "Write a weekly newsletter about AI trends"
        }
      },
      {
        "provider": "webhook",
        "action": "post_request",
        "params": {
          "url": "https://api.gmail.com/send",
          "payload": {
            "to": "subscriber@example.com",
            "body": "${steps.0.output}"
          }
        }
      }
    ]
  }'
```

### 3. Execute the Plan

```bash
curl -X POST http://localhost:5000/api/execute \
  -H "Content-Type: application/json" \
  -d '{
    "plan_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "user_123"
  }'
```

### 4. Check Execution Logs

```bash
curl "http://localhost:5000/api/execution-logs?plan_id=550e...&user_id=user_123"

# Response:
{
  "logs": [
    {
      "step_number": 0,
      "provider": "openai",
      "action": "chat_completion",
      "status": "success",
      "latency_ms": 1234,
      "output_preview": "Dear subscribers, here are this week's AI trends...",
      "timestamp": "2024-01-15T10:30:00Z"
    },
    {
      "step_number": 1,
      "provider": "webhook",
      "action": "post_request",
      "status": "success",
      "latency_ms": 456,
      "output_preview": "Status 200",
      "timestamp": "2024-01-15T10:30:02Z"
    }
  ]
}
```

### 5. Schedule the Plan to Run Daily

```bash
curl -X POST http://localhost:5000/api/plans/550e.../schedule \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "cron_expression": "0 9 * * *"  # 9 AM daily
  }'
```

---

## For Developers: Adding a New Provider

### Step 1: Create Provider File

Create `server/providers/myservice.py`:

```python
from provider_registry import register_provider, ProviderResult
import requests
from datetime import datetime

@register_provider("myservice")
def myservice_provider(params, user_id, credentials, step_results):
    """
    Execute action in MyService
    
    Params:
        action (str): The action to perform ("create_item", "update_item", etc.)
        data (dict): Action-specific data
        
    Returns:
        ProviderResult with success, output, metadata
    """
    try:
        # Get per-user credentials
        api_key = credentials.get("api_key")
        if not api_key:
            return ProviderResult(
                success=False,
                output=None,
                message="MyService API key not configured",
                error="MISSING_CREDENTIALS"
            )
        
        # Get action and data from params
        action = params.get("action")
        data = params.get("data", {})
        
        if action == "create_item":
            # Make API call
            response = requests.post(
                "https://api.myservice.com/items",
                headers={"Authorization": f"Bearer {api_key}"},
                json=data,
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            
            return ProviderResult(
                success=True,
                output=result,
                message=f"Created item: {result.get('id')}",
                metadata={
                    "provider": "myservice",
                    "action": action,
                    "item_id": result.get('id'),
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        elif action == "list_items":
            response = requests.get(
                "https://api.myservice.com/items",
                headers={"Authorization": f"Bearer {api_key}"},
                params=data,
                timeout=10
            )
            response.raise_for_status()
            items = response.json()
            
            return ProviderResult(
                success=True,
                output=items,
                message=f"Found {len(items)} items",
                metadata={
                    "provider": "myservice",
                    "action": action,
                    "count": len(items),
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        else:
            return ProviderResult(
                success=False,
                output=None,
                message=f"Unknown action: {action}",
                error="UNKNOWN_ACTION"
            )
    
    except requests.exceptions.Timeout:
        return ProviderResult(
            success=False,
            output=None,
            message="Request timed out",
            error="TIMEOUT"
        )
    except requests.exceptions.HTTPError as e:
        return ProviderResult(
            success=False,
            output=None,
            message=f"API error: {e.response.status_code}",
            error=f"HTTP_{e.response.status_code}"
        )
    except Exception as e:
        return ProviderResult(
            success=False,
            output=None,
            message=f"Unexpected error: {str(e)}",
            error=type(e).__name__
        )
```

### Step 2: Register the Provider

Add to `server/providers/__init__.py`:

```python
# Auto-load all provider modules
import providers.ai
import providers.http
import providers.myservice  # <-- Add this line
```

### Step 3: Test the Provider

```python
# In Python shell or test file
from provider_registry import registry
from database import db_manager

# Test the provider
result = registry.execute(
    provider="myservice",
    action="create_item",
    params={
        "action": "create_item",
        "data": {"name": "Test Item"}
    },
    user_id="test_user_123",
    credentials={"api_key": "test_key_abc"},
    step_results={}
)

print(f"Success: {result.success}")
print(f"Output: {result.output}")
print(f"Message: {result.message}")
print(f"Error: {result.error}")
print(f"Metadata: {result.metadata}")
```

### Step 4: Verify in Execution

```bash
curl -X POST http://localhost:5000/api/execute-step \
  -H "Content-Type: application/json" \
  -d '{
    "step": {
      "provider": "myservice",
      "action": "create_item",
      "params": {
        "action": "create_item",
        "data": {"name": "Test Item"}
      }
    },
    "user_id": "test_user_123",
    "step_results": {}
  }'
```

---

## For DevOps: Deploying & Monitoring

### Deployment Steps

```bash
# 1. Backup existing database
pg_dump pilot2_db > backup_$(date +%Y%m%d).sql

# 2. Run database migrations
psql -U postgres pilot2_db < server/migrations/002_provider_credentials_and_logs.sql

# 3. Deploy new code
git pull origin main
cp server/app_new.py server/app.py

# 4. Restart Flask
systemctl restart flask-app

# 5. Verify health
curl http://localhost:5000/api/health
curl http://localhost:5000/api/scheduler/jobs
```

### Monitoring Queries

```sql
-- How many plans are running?
SELECT COUNT(*) FROM execution_logs 
WHERE timestamp > NOW() - INTERVAL '1 hour';

-- Which providers are failing?
SELECT provider, status, COUNT(*) 
FROM execution_logs 
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY provider, status;

-- Average execution time by provider
SELECT provider, 
       AVG(latency_ms) as avg_latency,
       MAX(latency_ms) as max_latency,
       COUNT(*) as total_executions
FROM execution_logs
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY provider
ORDER BY avg_latency DESC;

-- Scheduled jobs
SELECT COUNT(*) as total_jobs,
       status,
       COUNT(*) as job_count
FROM execution_logs
WHERE provider = 'scheduler'
GROUP BY status;

-- Find slow steps
SELECT plan_id, step_number, provider, latency_ms
FROM execution_logs
WHERE latency_ms > 5000  -- Slower than 5 seconds
ORDER BY latency_ms DESC
LIMIT 10;
```

### Health Checks

```bash
#!/bin/bash
# check_health.sh

# Check Flask is running
curl -f http://localhost:5000/api/health || {
  echo "CRITICAL: Flask app is down"
  systemctl restart flask-app
  exit 1
}

# Check scheduler has jobs
JOBS=$(curl -s http://localhost:5000/api/scheduler/jobs | jq '.jobs | length')
if [ "$JOBS" -lt 1 ]; then
  echo "WARNING: No scheduled jobs found"
fi

# Check recent executions
RECENT=$(psql -U postgres pilot2_db -t -c \
  "SELECT COUNT(*) FROM execution_logs WHERE timestamp > NOW() - INTERVAL '1 hour'")
if [ "$RECENT" -eq 0 ]; then
  echo "WARNING: No executions in last hour"
fi

echo "OK: All health checks passed"
```

---

## Common Operations

### List All Available Providers

```bash
curl http://localhost:5000/api/providers

# Response: ["openai", "groq", "webhook", "custom_api", "logic", "myservice", ...]
```

### Get Scheduled Jobs

```bash
curl http://localhost:5000/api/scheduler/jobs

# Response:
{
  "jobs": [
    {
      "id": "plan_550e8400-e29b-41d4-a716-446655440000",
      "name": "Execute Plan: Daily Newsletter",
      "trigger": "cron[hour='9', minute='0']",
      "next_run": "2024-01-16T09:00:00+00:00"
    }
  ]
}
```

### Verify User Credentials Are Stored

```bash
curl "http://localhost:5000/api/provider-credentials/openai?user_id=user_123"

# Response:
{
  "provider": "openai",
  "credential_types": ["api_key"]  # Note: actual values never returned
}
```

### Debug a Failed Execution

```bash
# Get the logs
curl "http://localhost:5000/api/execution-logs?plan_id=...&user_id=user_123" | jq '.'

# Look for:
# - status == "error"
# - error field with error message
# - latency_ms to see if timeout
# - output_preview for partial results

# Check database for more details
psql pilot2_db
SELECT * FROM execution_logs 
WHERE plan_id = '550e8400-e29b-41d4-a716-446655440000' 
ORDER BY timestamp DESC LIMIT 10;
```

---

## Troubleshooting

### "Provider not found" error

**Cause:** Provider module not imported in `__init__.py`

**Fix:**
```python
# server/providers/__init__.py
import providers.myservice  # Make sure this line exists
```

### "API key not configured" error

**Cause:** Credentials not stored for that provider

**Fix:**
```bash
curl -X POST http://localhost:5000/api/provider-credentials/openai \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "credentials": {"api_key": "sk-..."}
  }'
```

### Scheduler jobs not running

**Cause:** `scheduler.start()` not called

**Fix:** Check `server/scheduler.py` - verify `init_scheduler()` is called on startup

### Parameter resolution not working

**Cause:** Wrong syntax for step reference

**Fix:** Use correct syntax: `"${steps.0.output"` not `{{step_0.output}}`

```python
# WRONG
"params": {"query": "{{step_0.output}}"}

# RIGHT
"params": {"query": "${steps.0.output}"}
```

---

## API Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Health check |
| `/api/providers` | GET | List all providers |
| `/api/scheduler/jobs` | GET | List scheduled jobs |
| `/api/plans` | GET | Get user's plans |
| `/api/plans` | POST | Create new plan |
| `/api/plans/<id>` | GET | Get specific plan |
| `/api/execute` | POST | Execute a plan |
| `/api/execute-step` | POST | Execute single step |
| `/api/execution-logs` | GET | Get logs for plan |
| `/api/provider-credentials/<provider>` | GET | Get credential types |
| `/api/provider-credentials/<provider>` | POST | Store credentials |
| `/api/plans/<id>/schedule` | POST | Schedule plan |
| `/api/plans/<id>/unschedule` | POST | Remove schedule |
| `/api/custom-integrations` | GET | Get integrations |
| `/api/custom-integrations` | POST | Create integration |

---

For more details, see `server/ARCHITECTURE_REFACTORING.md`
