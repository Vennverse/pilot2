-- Migration 005: Create user quotas and pricing tables

CREATE TABLE IF NOT EXISTS user_quotas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE,
    plan_tier VARCHAR(50) NOT NULL DEFAULT 'FREE' CHECK (plan_tier IN ('FREE', 'PRO', 'BUSINESS', 'ENTERPRISE')),
    workflows_limit INT NOT NULL DEFAULT 3,
    workflows_created INT DEFAULT 0,
    executions_limit INT NOT NULL DEFAULT 50,
    executions_run INT DEFAULT 0,
    integrations_limit INT NOT NULL DEFAULT 10,
    team_members_limit INT NOT NULL DEFAULT 1,
    team_members_added INT DEFAULT 0,
    custom_code_enabled BOOLEAN DEFAULT FALSE,
    api_access_enabled BOOLEAN DEFAULT FALSE,
    sso_enabled BOOLEAN DEFAULT FALSE,
    audit_logs_enabled BOOLEAN DEFAULT FALSE,
    cycle_start_date DATE NOT NULL DEFAULT CURRENT_DATE,
    subscription_start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS usage_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    metadata JSONB,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS plan_upgrades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    from_plan VARCHAR(50) NOT NULL,
    to_plan VARCHAR(50) NOT NULL,
    upgraded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    billing_period_start DATE NOT NULL,
    billing_period_end DATE NOT NULL,
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE
);

-- Create indexes
CREATE INDEX idx_user_quotas_user ON user_quotas(user_id);
CREATE INDEX idx_user_quotas_plan ON user_quotas(plan_tier);
CREATE INDEX idx_usage_tracking_user ON usage_tracking(user_id);
CREATE INDEX idx_usage_tracking_date ON usage_tracking(recorded_at);
CREATE INDEX idx_plan_upgrades_user ON plan_upgrades(user_id);
