"""
Migration: Add agents table and agent_name field to track agent executions
Date: 2026-01-08
"""

migration_name = "003_add_agents_table"
migration_version = "1.0"

# SQL migration scripts
up_sql = """
-- Create agents table to track agent executions
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    agent_name VARCHAR(100) NOT NULL,
    agent_type VARCHAR(50) NOT NULL,  -- sales, marketing, finance, support, hr
    status VARCHAR(50) DEFAULT 'active',  -- active, inactive, archived
    configuration JSONB DEFAULT '{}',  -- agent-specific config
    total_executions INT DEFAULT 0,
    successful_executions INT DEFAULT 0,
    failed_executions INT DEFAULT 0,
    last_execution_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT agents_user_agent_unique UNIQUE(user_id, agent_name),
    CONSTRAINT agents_user_fk FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Add index for user lookups
CREATE INDEX IF NOT EXISTS idx_agents_user_id ON agents(user_id);
CREATE INDEX IF NOT EXISTS idx_agents_agent_type ON agents(agent_type);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);

-- Add agent_name field to execution_plans table
ALTER TABLE execution_plans 
ADD COLUMN IF NOT EXISTS agent_name VARCHAR(100),
ADD COLUMN IF NOT EXISTS generated_by_agent BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS agent_configuration JSONB DEFAULT '{}';

-- Create index for agent lookups in execution plans
CREATE INDEX IF NOT EXISTS idx_execution_plans_agent_name ON execution_plans(agent_name);
CREATE INDEX IF NOT EXISTS idx_execution_plans_generated_by_agent ON execution_plans(generated_by_agent);

-- Add agent execution tracking table
CREATE TABLE IF NOT EXISTS agent_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    agent_name VARCHAR(100) NOT NULL,
    plan_id UUID NOT NULL,
    user_request TEXT NOT NULL,
    workflow_json JSONB NOT NULL,
    status VARCHAR(50) NOT NULL,  -- pending, running, completed, failed
    result JSONB,  -- execution result/output
    error_message TEXT,
    execution_time_ms INT,
    steps_executed INT,
    steps_total INT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    
    CONSTRAINT agent_executions_user_fk FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT agent_executions_plan_fk FOREIGN KEY(plan_id) REFERENCES execution_plans(id) ON DELETE CASCADE
);

-- Create indexes for agent executions
CREATE INDEX IF NOT EXISTS idx_agent_executions_user_id ON agent_executions(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_executions_agent_name ON agent_executions(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_executions_plan_id ON agent_executions(plan_id);
CREATE INDEX IF NOT EXISTS idx_agent_executions_status ON agent_executions(status);
CREATE INDEX IF NOT EXISTS idx_agent_executions_started_at ON agent_executions(started_at);

-- Create RLS policy for agents table
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
CREATE POLICY agents_user_isolation ON agents
    USING (user_id = current_user_id());

-- Create RLS policy for agent_executions table
ALTER TABLE agent_executions ENABLE ROW LEVEL SECURITY;
CREATE POLICY agent_executions_user_isolation ON agent_executions
    USING (user_id = current_user_id());

-- Create view for agent execution stats
CREATE OR REPLACE VIEW agent_execution_stats AS
SELECT 
    ae.user_id,
    ae.agent_name,
    COUNT(*) as total_executions,
    SUM(CASE WHEN ae.status = 'completed' THEN 1 ELSE 0 END) as successful_executions,
    SUM(CASE WHEN ae.status = 'failed' THEN 1 ELSE 0 END) as failed_executions,
    AVG(CASE WHEN ae.execution_time_ms > 0 THEN ae.execution_time_ms ELSE NULL END) as avg_execution_time_ms,
    MAX(ae.completed_at) as last_execution_at
FROM agent_executions ae
GROUP BY ae.user_id, ae.agent_name;
"""

down_sql = """
-- Rollback migration
DROP VIEW IF EXISTS agent_execution_stats;
DROP TABLE IF EXISTS agent_executions;
DROP TABLE IF EXISTS agents;

-- Remove columns from execution_plans
ALTER TABLE execution_plans 
DROP COLUMN IF EXISTS agent_name,
DROP COLUMN IF EXISTS generated_by_agent,
DROP COLUMN IF EXISTS agent_configuration;
"""

def apply_migration(connection):
    """Apply migration to database"""
    cursor = connection.cursor()
    try:
        # Execute migration SQL
        cursor.execute(up_sql)
        connection.commit()
        print(f"✓ Migration {migration_name} applied successfully")
        return True
    except Exception as e:
        connection.rollback()
        print(f"✗ Error applying migration {migration_name}: {str(e)}")
        return False


def rollback_migration(connection):
    """Rollback migration"""
    cursor = connection.cursor()
    try:
        cursor.execute(down_sql)
        connection.commit()
        print(f"✓ Migration {migration_name} rolled back successfully")
        return True
    except Exception as e:
        connection.rollback()
        print(f"✗ Error rolling back migration {migration_name}: {str(e)}")
        return False
