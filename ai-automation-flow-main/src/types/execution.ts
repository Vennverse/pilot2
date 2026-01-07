export interface Provider {
  id: string;
  name: string;
  display_name: string;
  auth_type: "oauth" | "api_key";
  oauth_config: Record<string, unknown>;
  actions: ProviderAction[];
  icon: string;
  created_at: string;
}

export interface ProviderAction {
  id: string;
  name: string;
  description: string;
  params: string[];
}

export interface Credential {
  id: string;
  user_id: string;
  provider_id: string;
  type: "oauth" | "api_key";
  encrypted_access_token?: string;
  encrypted_refresh_token?: string;
  encrypted_api_key?: string;
  token_expires_at?: string;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  providers?: Provider;
}

export interface PlanStep {
  order: number;
  provider: string;
  action_id: string;
  action_name: string;
  params: Record<string, string>;
  description: string;
  type?: "action" | "condition" | "loop";
  condition?: string;
  else_jump?: number;
  loop_config?: {
    items_source?: string; // Reference to previous step output
    max_iterations?: number;
  };
}

export interface Trigger {
  type: "manual" | "webhook" | "schedule" | "event";
  config?: {
    // Webhook trigger
    webhook_path?: string;
    webhook_secret?: string;
    // Schedule trigger
    cron_expression?: string;
    timezone?: string;
    // Event trigger
    event_source?: string;
    event_type?: string;
  };
}

export interface ExecutionPlan {
  id: string;
  user_id: string;
  name: string;
  original_prompt: string;
  plan_json: PlanStep[];
  plain_english_steps: string[];
  status: "draft" | "approved" | "rejected" | "active" | "paused";
  required_providers: string[];
  missing_auth: string[];
  trigger?: Trigger;
  created_at: string;
  approved_at?: string;
  enabled?: boolean;
}

export interface Execution {
  id: string;
  execution_plan_id: string;
  user_id: string;
  status: "pending" | "running" | "success" | "failed";
  logs: ExecutionLog[];
  started_at?: string;
  finished_at?: string;
  error_message?: string;
}

export interface ExecutionLog {
  step: number;
  provider: string;
  action: string;
  status: "success" | "failed" | "skipped";
  message: string;
  timestamp: string;
  data?: unknown;
}

export interface AIPlannerResponse {
  name?: string;
  steps?: PlanStep[];
  plain_english_steps?: string[];
  required_providers?: string[];
  missing_auth?: string[];
  error?: string;
}
