-- Create custom_integrations table
CREATE TABLE IF NOT EXISTS custom_integrations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  name VARCHAR(255) NOT NULL,
  display_name VARCHAR(255) NOT NULL,
  description TEXT,
  auth_type VARCHAR(50) NOT NULL CHECK (auth_type IN ('api_key', 'oauth')),
  base_url VARCHAR(2048),
  auth_header VARCHAR(255) DEFAULT 'Authorization',
  auth_prefix VARCHAR(255) DEFAULT 'Bearer',
  oauth_config JSONB,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  created_by VARCHAR(255),
  updated_by VARCHAR(255),
  UNIQUE(user_id, name)
);

-- Create custom_integration_actions table
CREATE TABLE IF NOT EXISTS custom_integration_actions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  integration_id UUID NOT NULL REFERENCES custom_integrations(id) ON DELETE CASCADE,
  action_id VARCHAR(255) NOT NULL,
  action_name VARCHAR(255) NOT NULL,
  description TEXT,
  http_method VARCHAR(10) NOT NULL CHECK (http_method IN ('GET', 'POST', 'PUT', 'PATCH', 'DELETE')),
  endpoint VARCHAR(2048) NOT NULL,
  parameters JSONB DEFAULT '[]'::jsonb,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(integration_id, action_id)
);

-- Create custom_integration_credentials table
CREATE TABLE IF NOT EXISTS custom_integration_credentials (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  integration_id UUID NOT NULL REFERENCES custom_integrations(id) ON DELETE CASCADE,
  credential_type VARCHAR(50) NOT NULL CHECK (credential_type IN ('api_key', 'oauth_token', 'oauth_refresh_token')),
  encrypted_value TEXT NOT NULL,
  token_expires_at TIMESTAMP WITH TIME ZONE,
  is_valid BOOLEAN DEFAULT true,
  last_validated_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(user_id, integration_id, credential_type)
);

-- Create indexes for better query performance
CREATE INDEX idx_custom_integrations_user_id ON custom_integrations(user_id);
CREATE INDEX idx_custom_integrations_user_active ON custom_integrations(user_id, is_active);
CREATE INDEX idx_custom_integration_actions_integration ON custom_integration_actions(integration_id);
CREATE INDEX idx_custom_integration_credentials_user_integration ON custom_integration_credentials(user_id, integration_id);

-- Enable Row Level Security
ALTER TABLE custom_integrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE custom_integration_actions ENABLE ROW LEVEL SECURITY;
ALTER TABLE custom_integration_credentials ENABLE ROW LEVEL SECURITY;

-- RLS Policies for custom_integrations
CREATE POLICY "Users can view their own integrations" ON custom_integrations
  FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can create integrations" ON custom_integrations
  FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

CREATE POLICY "Users can update their own integrations" ON custom_integrations
  FOR UPDATE USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can delete their own integrations" ON custom_integrations
  FOR DELETE USING (auth.uid()::text = user_id::text);

-- RLS Policies for custom_integration_actions
CREATE POLICY "Users can view actions for their integrations" ON custom_integration_actions
  FOR SELECT USING (
    integration_id IN (
      SELECT id FROM custom_integrations 
      WHERE auth.uid()::text = user_id::text
    )
  );

CREATE POLICY "Users can manage actions for their integrations" ON custom_integration_actions
  FOR ALL USING (
    integration_id IN (
      SELECT id FROM custom_integrations 
      WHERE auth.uid()::text = user_id::text
    )
  );

-- RLS Policies for custom_integration_credentials
CREATE POLICY "Users can view their own credentials" ON custom_integration_credentials
  FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can manage their own credentials" ON custom_integration_credentials
  FOR ALL USING (auth.uid()::text = user_id::text);
