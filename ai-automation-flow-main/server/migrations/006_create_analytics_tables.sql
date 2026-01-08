-- Migration 006: Create analytics and monitoring tables

CREATE TABLE IF NOT EXISTS execution_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    workflow_id UUID NOT NULL,
    execution_id UUID NOT NULL UNIQUE,
    status VARCHAR(50) NOT NULL,
    duration_seconds FLOAT NOT NULL,
    success BOOLEAN NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP NOT NULL,
    steps_executed INT DEFAULT 0,
    steps_failed INT DEFAULT 0,
    error_message TEXT,
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS workflow_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    workflow_id UUID NOT NULL UNIQUE,
    total_executions INT DEFAULT 0,
    successful_executions INT DEFAULT 0,
    failed_executions INT DEFAULT 0,
    avg_duration FLOAT DEFAULT 0,
    last_executed_at TIMESTAMP,
    time_saved_hours FLOAT DEFAULT 0,
    cost_saved_dollars FLOAT DEFAULT 0,
    success_rate FLOAT DEFAULT 0,
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_roi_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE,
    total_workflows INT DEFAULT 0,
    total_executions INT DEFAULT 0,
    total_successful INT DEFAULT 0,
    total_time_saved_hours FLOAT DEFAULT 0,
    total_cost_saved_dollars FLOAT DEFAULT 0,
    avg_success_rate FLOAT DEFAULT 0,
    most_used_integrations JSONB,
    first_execution_date TIMESTAMP,
    last_execution_date TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS execution_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    step_id VARCHAR(255),
    step_name VARCHAR(255),
    event_data JSONB,
    error_details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_execution_metrics_user ON execution_metrics(user_id);
CREATE INDEX idx_execution_metrics_workflow ON execution_metrics(workflow_id);
CREATE INDEX idx_execution_metrics_date ON execution_metrics(started_at);
CREATE INDEX idx_workflow_stats_user ON workflow_stats(user_id);
CREATE INDEX idx_user_roi_user ON user_roi_data(user_id);
CREATE INDEX idx_execution_events_execution ON execution_events(execution_id);
CREATE INDEX idx_execution_events_type ON execution_events(event_type);
