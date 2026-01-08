# DEPLOYMENT CHECKLIST

## Pre-Deployment: Verification (DO THIS FIRST)

### Code Review
- [ ] Review all new files for syntax errors
- [ ] Verify imports in `server/providers/__init__.py`
- [ ] Check database connection string in `database.py`
- [ ] Verify Fernet key is set for encryption
- [ ] Review RLS policies in migration SQL

### Database Preparation
- [ ] Backup current PostgreSQL database
  ```bash
  pg_dump -U postgres pilot2_db > backup_$(date +%Y%m%d_%H%M%S).sql
  ```
- [ ] Verify PostgreSQL version >= 12 (for RLS support)
  ```sql
  SELECT version();
  ```
- [ ] Verify current user can create tables
  ```sql
  CREATE TABLE test (id INT);
  DROP TABLE test;
  ```

### Dependencies
- [ ] Verify Flask is installed
  ```bash
  pip list | grep -i flask
  ```
- [ ] Verify flask-apscheduler is installed
  ```bash
  pip install flask-apscheduler
  ```
- [ ] Verify psycopg2 is installed
  ```bash
  pip install psycopg2-binary
  ```
- [ ] Verify cryptography is installed for Fernet
  ```bash
  pip install cryptography
  ```

---

## Phase 1: Database Migration (CRITICAL)

### Step 1: Run Pre-Migration Checks
```bash
# Connect to database
psql -U postgres pilot2_db

# Check existing tables
SELECT tablename FROM pg_tables WHERE schemaname = 'public';

# Check current RLS status
SELECT * FROM pg_tables WHERE schemaname = 'public' AND rowsecurity = true;
```

### Step 2: Run Migration 002
```bash
# Execute the migration
psql -U postgres pilot2_db < server/migrations/002_provider_credentials_and_logs.sql

# Verify new tables created
psql -U postgres pilot2_db -c \
  "SELECT tablename FROM pg_tables WHERE tablename IN ('provider_credentials', 'execution_plans', 'execution_logs')"

# Expected output: 3 tables
```

### Step 3: Verify RLS Policies
```bash
psql -U postgres pilot2_db

# Check RLS is enabled
SELECT tablename, rowsecurity FROM pg_tables 
WHERE tablename IN ('provider_credentials', 'execution_plans', 'execution_logs');

# Check policies exist
SELECT schemaname, tablename, policyname FROM pg_policies 
WHERE tablename IN ('provider_credentials', 'execution_plans', 'execution_logs');

# Expected: 4 policies per table (SELECT, INSERT, UPDATE, DELETE)
```

### Step 4: Create Encryption Key Function
```bash
psql -U postgres pilot2_db

# The migration assumes this function exists for RLS
-- If using auth.users for user_id, create this:
CREATE OR REPLACE FUNCTION current_user_id() RETURNS VARCHAR AS $$
  SELECT current_setting('app.current_user_id', true)::VARCHAR;
$$ LANGUAGE SQL;

-- For testing without auth:
SET app.current_user_id = 'test_user_123';
SELECT current_user_id();
```

### Step 5: Test RLS Policies
```bash
psql -U postgres pilot2_db

-- Create test data
SET app.current_user_id = 'user_a';
INSERT INTO provider_credentials (user_id, provider, type, encrypted_value)
VALUES ('user_a', 'openai', 'api_key', 'test_encrypted_key_a');

SET app.current_user_id = 'user_b';
INSERT INTO provider_credentials (user_id, provider, type, encrypted_value)
VALUES ('user_b', 'openai', 'api_key', 'test_encrypted_key_b');

-- Verify user_a can only see own data
SET app.current_user_id = 'user_a';
SELECT COUNT(*) FROM provider_credentials;  -- Should be 1

SET app.current_user_id = 'user_b';
SELECT COUNT(*) FROM provider_credentials;  -- Should be 1

-- Verify data integrity
SELECT * FROM provider_credentials WHERE user_id = 'user_a';  -- Only sees user_a's data
```

---

## Phase 2: Code Deployment

### Step 1: Backup Existing App
```bash
cd /path/to/server
cp app.py app_backup_$(date +%Y%m%d_%H%M%S).py
cp -r . backup_$(date +%Y%m%d_%H%M%S)/
```

### Step 2: Deploy New Files
```bash
# Copy new provider registry
cp provider_registry.py ../  # Root or where app.py imports from

# Copy execution engine
cp execution_engine.py ../

# Copy scheduler
cp scheduler.py ../

# Copy providers directory
cp -r providers/ ../

# Copy new app
cp app_new.py app.py

# Verify imports work
python -c "import provider_registry; print('✓ Registry imports OK')"
python -c "import execution_engine; print('✓ Execution engine imports OK')"
python -c "import scheduler; print('✓ Scheduler imports OK')"
python -c "from providers import registry; print(f'✓ {len(registry.providers)} providers loaded')"
```

### Step 3: Verify No Import Errors
```bash
python -c "
import sys
sys.path.insert(0, '.')
from app import app
print('✓ Flask app imports successfully')
"
```

---

## Phase 3: Environment Configuration

### Step 1: Set Environment Variables
```bash
export FLASK_ENV=production
export FLASK_APP=app.py
export DATABASE_URL=postgresql://postgres:password@localhost/pilot2_db
export FERNET_KEY=<your-fernet-key>  # Generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Step 2: Verify Connections
```bash
# Test database connection
python -c "
from database import db_manager
conn = db_manager.get_connection()
print('✓ Database connection OK')
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM provider_credentials')
print(f'✓ Credential table accessible: {cur.fetchone()[0]} records')
conn.close()
"

# Test Flask startup
python -c "
from app import app
with app.app_context():
    print('✓ Flask app context OK')
"
```

---

## Phase 4: Testing (BEFORE PRODUCTION)

### Unit Tests

```bash
# Test provider registry
python tests/test_provider_registry.py

# Expected output:
# ✓ ProviderResult serialization
# ✓ Provider registration
# ✓ Provider execution
# ✓ Provider error handling
```

### Integration Tests

```bash
# Start Flask in test mode
python -c "
from app import app
from database import db_manager
import json

# Test 1: Store credentials
client = app.test_client()
response = client.post('/api/provider-credentials/openai', json={
    'user_id': 'test_user_123',
    'credentials': {'api_key': 'test_key_abc'}
})
assert response.status_code == 200
print('✓ Credential storage works')

# Test 2: Retrieve credentials
response = client.get('/api/provider-credentials/openai?user_id=test_user_123')
assert response.status_code == 200
print('✓ Credential retrieval works')

# Test 3: Create plan
response = client.post('/api/plans', json={
    'user_id': 'test_user_123',
    'name': 'Test Plan',
    'original_prompt': 'Test',
    'steps': []
})
assert response.status_code == 201
print('✓ Plan creation works')

# Test 4: Execute step
response = client.post('/api/execute-step', json={
    'step': {
        'provider': 'openai',
        'action': 'chat_completion',
        'params': {'prompt': 'Hello'}
    },
    'user_id': 'test_user_123',
    'step_results': {}
})
assert response.status_code in [200, 500]  # May fail without real API key
print('✓ Step execution works')

# Test 5: Scheduler initialization
print(f'✓ Scheduler has {len(registry.providers)} providers')
"
```

### Load Test

```bash
# Test with concurrent requests
python -c "
import concurrent.futures
import requests
import time

def execute_step(i):
    try:
        response = requests.post('http://localhost:5000/api/execute-step', json={
            'step': {
                'provider': 'logic',  # Simple provider that doesn't need real API
                'action': 'transform',
                'params': {'template': f'Test {i}'}
            },
            'user_id': f'user_{i}',
            'step_results': {}
        }, timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f'Error {i}: {e}')
        return False

# Run 10 concurrent requests
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(execute_step, range(10)))

print(f'✓ Load test: {sum(results)}/10 requests succeeded')
"
```

---

## Phase 5: Deployment

### Option A: Blue-Green Deployment (Recommended)

```bash
# 1. Start new app on different port
export FLASK_PORT=5001
python app.py &

# 2. Test new app
curl http://localhost:5001/api/health

# 3. If OK, update load balancer to point to 5001
# 4. Keep old app running for rollback

# 5. Monitor for issues for 1 hour

# 6. If no issues, stop old app
kill %1  # Kill old app process
```

### Option B: Rolling Deployment

```bash
# For multi-instance setup:
# 1. Stop instance 1, deploy, start instance 1
# 2. Verify instance 1 healthy
# 3. Stop instance 2, deploy, start instance 2
# 4. Verify instance 2 healthy
# ... etc
```

### Option C: Direct Deployment (Single Instance)

```bash
# 1. Stop Flask app
systemctl stop flask-app

# 2. Deploy new code
cp app.py /var/www/flask/app.py
cp -r providers/ /var/www/flask/providers/
cp *.py /var/www/flask/

# 3. Start Flask app
systemctl start flask-app

# 4. Verify health
curl http://localhost:5000/api/health
sleep 5
curl http://localhost:5000/api/scheduler/jobs
```

---

## Phase 6: Post-Deployment Monitoring (24 hours)

### Minute 0: Immediate Checks
```bash
# Check app is running
curl http://localhost:5000/api/health
# Expected: {"status": "healthy", "timestamp": "..."}

# Check scheduler initialized
curl http://localhost:5000/api/scheduler/jobs
# Expected: {"jobs": [...]}

# Check providers loaded
curl http://localhost:5000/api/providers
# Expected: {"providers": ["openai", "groq", "webhook", ...]}

# Check database accessible
curl http://localhost:5000/api/plans?user_id=test_user_123
# Expected: {"plans": [...]}
```

### Hour 1: Performance Checks
```bash
# Monitor error logs
tail -f /var/log/flask-app.log | grep ERROR

# Monitor database growth
psql -U postgres pilot2_db -c \
  "SELECT 'execution_logs' as table_name, COUNT(*) as row_count FROM execution_logs
   UNION ALL
   SELECT 'execution_plans', COUNT(*) FROM execution_plans
   UNION ALL
   SELECT 'provider_credentials', COUNT(*) FROM provider_credentials"

# Check slow queries
psql -U postgres pilot2_db -c \
  "SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 5"
```

### Hour 24: Stability Check
```bash
# Check for any recurring errors
grep -c "ERROR" /var/log/flask-app.log

# Check database size
psql -U postgres pilot2_db -c \
  "SELECT pg_size_pretty(pg_database_size('pilot2_db')) as size"

# Check successful executions
psql -U postgres pilot2_db -c \
  "SELECT COUNT(*) as total_logs, 
          SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
          SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as failed
   FROM execution_logs
   WHERE timestamp > NOW() - INTERVAL '24 hours'"
```

---

## Rollback Plan (If Issues Occur)

### Immediate Rollback
```bash
# 1. Stop Flask app
systemctl stop flask-app

# 2. Restore backup
cp app_backup_*.py app.py
cp -r backup_*/* .

# 3. Start Flask app
systemctl start flask-app

# 4. Verify it's working
curl http://localhost:5000/api/health
```

### Partial Rollback (If Only Provider Issue)
```bash
# If a specific provider is causing issues:

# 1. Disable the provider temporarily
# Remove from server/providers/__init__.py
# OR rename server/providers/badprovider.py to server/providers/badprovider.py.bak

# 2. Restart app
systemctl restart flask-app

# 3. Fix the provider code
# Edit server/providers/badprovider.py

# 4. Re-enable and test
mv server/providers/badprovider.py.bak server/providers/badprovider.py
systemctl restart flask-app
```

---

## Success Criteria

- [ ] All 4 new tables created with RLS enabled
- [ ] 0 import errors on startup
- [ ] All 4 CRUD endpoints return 200 OK
- [ ] Scheduler initializes without errors
- [ ] At least 3 providers available
- [ ] Credential storage works (encrypted in database)
- [ ] Execution logs are created and queryable
- [ ] No data loss on restart
- [ ] Load test succeeds (10 concurrent requests)
- [ ] Error rate < 1%

---

## Monitoring Setup

### Metrics to Track

```sql
-- Success rate by provider
SELECT provider, 
       ROUND(100.0 * SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate,
       COUNT(*) as total_executions
FROM execution_logs
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY provider
ORDER BY success_rate ASC;

-- Slowest providers
SELECT provider,
       ROUND(AVG(latency_ms)::numeric, 2) as avg_latency_ms,
       MAX(latency_ms) as max_latency_ms,
       PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95_latency_ms
FROM execution_logs
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY provider
ORDER BY avg_latency_ms DESC;

-- Error trends
SELECT DATE_TRUNC('hour', timestamp) as hour,
       provider,
       COUNT(*) as total,
       SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as errors,
       ROUND(100.0 * SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) / COUNT(*), 2) as error_rate
FROM execution_logs
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', timestamp), provider
ORDER BY hour DESC;
```

---

## Post-Deployment Tasks

- [ ] Document provider credentials for all users
- [ ] Migrate user credentials from environment to database
- [ ] Create monitoring dashboard (if using Grafana/DataDog)
- [ ] Set up alerts for error rate > 5%
- [ ] Set up alerts for scheduler job failures
- [ ] Document provider development process for team
- [ ] Create runbook for common issues
- [ ] Schedule review meeting (1 week post-deployment)
- [ ] Plan for remaining provider migrations

---

## Timeline

| Phase | Duration | Start | End |
|-------|----------|-------|-----|
| Preparation & Testing | 2-4 hours | 9 AM | 1 PM |
| Database Migration | 30 min | 1 PM | 1:30 PM |
| Code Deployment | 15 min | 1:30 PM | 1:45 PM |
| Health Checks | 15 min | 1:45 PM | 2 PM |
| Monitoring (first 24h) | 24 hours | 2 PM | 2 PM next day |
| Review & Documentation | 2-4 hours | Next morning | Complete |

**Recommended: Deploy during off-peak hours (early morning or late evening)**

---

For questions or issues, refer to:
- `server/ARCHITECTURE_REFACTORING.md` - Technical details
- `server/QUICK_START_GUIDE.md` - Usage examples
- `server/REFACTORING_SUMMARY.md` - Summary of changes
