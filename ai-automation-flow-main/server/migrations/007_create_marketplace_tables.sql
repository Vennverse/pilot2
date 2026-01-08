-- Migration 007: Create marketplace and templates tables

CREATE TABLE IF NOT EXISTS workflow_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL,
    industry VARCHAR(100) NOT NULL,
    workflow_definition JSONB NOT NULL,
    downloads_count INT DEFAULT 0,
    rating FLOAT DEFAULT 0,
    review_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    featured BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS template_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL,
    user_id UUID NOT NULL,
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    review_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(template_id, user_id),
    CONSTRAINT fk_template FOREIGN KEY (template_id) REFERENCES workflow_templates(id) ON DELETE CASCADE,
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS template_downloads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL,
    user_id UUID NOT NULL,
    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_template FOREIGN KEY (template_id) REFERENCES workflow_templates(id) ON DELETE CASCADE,
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS shared_workflows_marketplace (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL,
    user_id UUID NOT NULL,
    shared_name VARCHAR(255) NOT NULL,
    shared_description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    downloads_count INT DEFAULT 0,
    rating FLOAT DEFAULT 0,
    shared_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE
);

-- Create indexes
CREATE INDEX idx_templates_category ON workflow_templates(category);
CREATE INDEX idx_templates_industry ON workflow_templates(industry);
CREATE INDEX idx_templates_featured ON workflow_templates(featured);
CREATE INDEX idx_template_downloads_user ON template_downloads(user_id);
CREATE INDEX idx_template_downloads_template ON template_downloads(template_id);
CREATE INDEX idx_template_reviews_template ON template_reviews(template_id);
CREATE INDEX idx_shared_workflows_user ON shared_workflows_marketplace(user_id);
