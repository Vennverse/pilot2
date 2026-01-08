-- Migration 002: Provider credentials and execution logging infrastructure

-- Built-in provider credentials table (separate from custom integrations)
CREATE TABLE IF NOT EXISTS provider_credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    provider VARCHAR(255) NOT NULL,  -- 'openai', 'groq', 'anthropic', etc.
    type VARCHAR(100) NOT NULL,      -- 'api_key', 'auth_token', 'password', etc.
    encrypted_value TEXT NOT NULL,
    expires_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Only one credential of each type per provider per user
    UNIQUE(user_id, provider, type),
    CONSTRAINT provider_credentials_user_id_fk FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE
);

-- Execution plans table - saves the AI-generated execution plan
CREATE TABLE IF NOT EXISTS execution_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    original_prompt TEXT NOT NULL,
    plan_json JSONB NOT NULL,              -- Array of steps with provider/params/action
    plain_english_steps TEXT[] NOT NULL,   -- Human readable version of each step
    required_providers VARCHAR(255)[] NOT NULL,  -- List of providers needed
    trigger JSONB DEFAULT '{}'::jsonb,     -- Cron schedule, webhook, etc.
    status VARCHAR(50) NOT NULL DEFAULT 'draft', -- draft, active, archived
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT execution_plans_user_id_fk FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE
);

-- Execution logs table - detailed tracking of each step execution
CREATE TABLE IF NOT EXISTS execution_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL REFERENCES execution_plans(id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL,
    plan_name VARCHAR(255) NOT NULL,       -- Denormalized for easy filtering
    step_number INTEGER NOT NULL,
    provider VARCHAR(255) NOT NULL,        -- Which provider executed
    action VARCHAR(100) NOT NULL,          -- The action type (send_email, query_db, etc.)
    status VARCHAR(50) NOT NULL,           -- 'success', 'error', 'retrying', 'timeout'
    message TEXT,                          -- Brief status message
    latency_ms INTEGER DEFAULT 0,          -- How long did it take?
    output_preview TEXT,                   -- First 500 chars of output
    error TEXT,                            -- Full error message if failed
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    
    CONSTRAINT execution_logs_user_id_fk FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE
);

-- Enable RLS on all new tables
ALTER TABLE provider_credentials ENABLE ROW LEVEL SECURITY;
ALTER TABLE execution_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE execution_logs ENABLE ROW LEVEL SECURITY;

-- RLS policies for provider_credentials
CREATE POLICY provider_credentials_select_policy ON provider_credentials
    FOR SELECT USING (user_id = current_user_id());

CREATE POLICY provider_credentials_insert_policy ON provider_credentials
    FOR INSERT WITH CHECK (user_id = current_user_id());

CREATE POLICY provider_credentials_update_policy ON provider_credentials
    FOR UPDATE USING (user_id = current_user_id());

CREATE POLICY provider_credentials_delete_policy ON provider_credentials
    FOR DELETE USING (user_id = current_user_id());

-- RLS policies for execution_plans
CREATE POLICY execution_plans_select_policy ON execution_plans
    FOR SELECT USING (user_id = current_user_id());

CREATE POLICY execution_plans_insert_policy ON execution_plans
    FOR INSERT WITH CHECK (user_id = current_user_id());

CREATE POLICY execution_plans_update_policy ON execution_plans
    FOR UPDATE USING (user_id = current_user_id());

CREATE POLICY execution_plans_delete_policy ON execution_plans
    FOR DELETE USING (user_id = current_user_id());

-- RLS policies for execution_logs
CREATE POLICY execution_logs_select_policy ON execution_logs
    FOR SELECT USING (user_id = current_user_id());

CREATE POLICY execution_logs_insert_policy ON execution_logs
    FOR INSERT WITH CHECK (user_id = current_user_id());

-- Create indexes for common queries
CREATE INDEX idx_provider_credentials_user_id ON provider_credentials(user_id);
CREATE INDEX idx_provider_credentials_provider ON provider_credentials(provider);
CREATE INDEX idx_execution_plans_user_id ON execution_plans(user_id);
CREATE INDEX idx_execution_plans_status ON execution_plans(status);
CREATE INDEX idx_execution_logs_plan_id ON execution_logs(plan_id);
CREATE INDEX idx_execution_logs_user_id ON execution_logs(user_id);
CREATE INDEX idx_execution_logs_timestamp ON execution_logs(timestamp DESC);
CREATE INDEX idx_execution_logs_provider ON execution_logs(provider);
