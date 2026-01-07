import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, Link2, Unlink, Key, Check, Loader2, Search, X, Plus, Settings } from "lucide-react";
import * as LucideIcons from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { supabase } from "@/integrations/supabase/client";
import { useToast } from "@/hooks/use-toast";
import type { Provider, Credential } from "@/types/execution";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { CreateCustomIntegrationModal } from "@/components/dashboard/CreateCustomIntegrationModal";

const Settings = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { toast } = useToast();
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [credentials, setCredentials] = useState<Credential[]>([]);
  const [apiKeyModal, setApiKeyModal] = useState<{ open: boolean; provider: Provider | null }>({
    open: false,
    provider: null,
  });
  const [apiKeyValue, setApiKeyValue] = useState("");
  const [saving, setSaving] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [authFilter, setAuthFilter] = useState<"all" | "oauth" | "api_key">("all");
  const [connectionFilter, setConnectionFilter] = useState<"all" | "connected" | "not_connected">("all");
  const [isCustomIntegrationModalOpen, setIsCustomIntegrationModalOpen] = useState(false);
  const [editingCustomIntegration, setEditingCustomIntegration] = useState<Provider | null>(null);

  const handleOAuthCallback = async (code: string, state: string, providerName: string) => {
    try {
      // In a real implementation, you would exchange the code for tokens on the backend
      // For now, we'll simulate saving the OAuth credential
      const provider = providers.find(p => p.name === providerName);
      if (!provider) {
        throw new Error("Provider not found");
      }

      // Save OAuth credential (in production, this should be done on backend)
      const { error } = await supabase.from("credentials").insert({
        user_id: user?.id,
        provider_id: provider.id,
        type: "oauth",
        encrypted_access_token: code, // In production, exchange code for token on backend
        metadata: { state, provider: providerName },
      });

      if (error) throw error;

      toast({
        title: "Connected!",
        description: `${provider.display_name} has been connected successfully via OAuth.`,
      });

      setSearchParams({});
      fetchCredentials();
    } catch (error) {
      console.error("OAuth callback error:", error);
      toast({
        title: "Connection failed",
        description: "Failed to complete OAuth authentication",
        variant: "destructive",
      });
      setSearchParams({});
    }
  };

  // Handle OAuth callback params
  useEffect(() => {
    if (!user) return;

    const connected = searchParams.get("connected");
    const error = searchParams.get("error");
    const code = searchParams.get("code");
    const state = searchParams.get("state");
    const provider = searchParams.get("provider");

    // Handle OAuth callback with authorization code
    if (code && state && provider && providers.length > 0) {
      handleOAuthCallback(code, state, provider);
      return;
    }

    if (connected) {
      toast({
        title: "Connected!",
        description: `${connected} has been connected successfully.`,
      });
      setSearchParams({});
      fetchCredentials();
    }

    if (error) {
      toast({
        title: "Connection failed",
        description: error === "missing_params" 
          ? "Invalid OAuth callback" 
          : error === "token_exchange_failed"
          ? "Failed to complete authentication"
          : error,
        variant: "destructive",
      });
      setSearchParams({});
    }
  }, [searchParams, user, providers]);

  const isConnected = (providerId: string) => {
    // In this API Key version, we consider it connected if it's in our local dummy credentials list
    return credentials.some((c) => c.provider_id === providerId);
  };

  // Filter providers based on search and filters
  const filteredProviders = providers.filter((provider) => {
    const matchesSearch = provider.display_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      provider.name.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesAuth = authFilter === "all" || provider.auth_type === authFilter;
    
    const isProviderConnected = isConnected(provider.id);
    const matchesConnection = connectionFilter === "all" ||
      (connectionFilter === "connected" && isProviderConnected) ||
      (connectionFilter === "not_connected" && !isProviderConnected);
    
    return matchesSearch && matchesAuth && matchesConnection;
  });

  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event, session) => {
        setUser(session?.user ?? null);
        setLoading(false);
      }
    );

    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
      setLoading(false);
    });

    return () => subscription.unsubscribe();
  }, []);

  useEffect(() => {
    if (!loading && !user) {
      navigate("/auth");
    }
  }, [loading, user, navigate]);

  useEffect(() => {
    if (user) {
      fetchProviders();
      fetchCredentials();
    }
  }, [user]);

  const fetchProviders = async () => {
    try {
      // Load custom integrations from localStorage
      let customIntegrations: Provider[] = [];
      try {
        const stored = localStorage.getItem("custom_integrations");
        if (stored) {
          customIntegrations = JSON.parse(stored);
        }
      } catch (error) {
        console.error("Error loading custom integrations:", error);
        customIntegrations = [];
      }

      // Providers with OAuth support
      const mockProviders: Provider[] = [
      // OAuth Providers
      { 
        id: "slack", 
        name: "slack", 
        display_name: "Slack", 
        icon: "Hash", 
        auth_type: "oauth", 
        oauth_config: {
          authorization_url: "https://slack.com/oauth/v2/authorize",
          client_id: import.meta.env.VITE_SLACK_CLIENT_ID || "",
          scope: "chat:write,channels:read,users:read",
          redirect_uri: `${window.location.origin}/settings?provider=slack`
        },
        actions: [{id: "post_message", name: "Post Message"}]
      },
      { 
        id: "google_mail", 
        name: "google_mail", 
        display_name: "Gmail", 
        icon: "Mail", 
        auth_type: "oauth",
        oauth_config: {
          authorization_url: "https://accounts.google.com/o/oauth2/v2/auth",
          client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID || "",
          scope: "https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/gmail.readonly",
          redirect_uri: `${window.location.origin}/settings?provider=google_mail`
        },
        actions: [{id: "send_email", name: "Send Email"}]
      },
      { 
        id: "google_sheets", 
        name: "google_sheets", 
        display_name: "Google Sheets", 
        icon: "Table", 
        auth_type: "oauth",
        oauth_config: {
          authorization_url: "https://accounts.google.com/o/oauth2/v2/auth",
          client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID || "",
          scope: "https://www.googleapis.com/auth/spreadsheets https://www.googleapis.com/auth/drive.file",
          redirect_uri: `${window.location.origin}/settings?provider=google_sheets`
        },
        actions: [{id: "row", name: "Add Row"}]
      },
      { 
        id: "notion", 
        name: "notion", 
        display_name: "Notion", 
        icon: "BookOpen", 
        auth_type: "oauth",
        oauth_config: {
          authorization_url: "https://api.notion.com/v1/oauth/authorize",
          client_id: import.meta.env.VITE_NOTION_CLIENT_ID || "",
          scope: "read write",
          redirect_uri: `${window.location.origin}/settings?provider=notion`
        },
        actions: [{id: "create_page", name: "Create Page"}]
      },
      { 
        id: "github", 
        name: "github", 
        display_name: "GitHub", 
        icon: "Github", 
        auth_type: "oauth",
        oauth_config: {
          authorization_url: "https://github.com/login/oauth/authorize",
          client_id: import.meta.env.VITE_GITHUB_CLIENT_ID || "",
          scope: "repo issues:write",
          redirect_uri: `${window.location.origin}/settings?provider=github`
        },
        actions: [{id: "issue", name: "Create Issue"}]
      },
      { 
        id: "hubspot", 
        name: "hubspot", 
        display_name: "HubSpot", 
        icon: "Users", 
        auth_type: "oauth",
        oauth_config: {
          authorization_url: "https://app.hubspot.com/oauth/authorize",
          client_id: import.meta.env.VITE_HUBSPOT_CLIENT_ID || "",
          scope: "contacts",
          redirect_uri: `${window.location.origin}/settings?provider=hubspot`
        },
        actions: [{id: "create_contact", name: "Create Contact"}]
      },
      { 
        id: "salesforce", 
        name: "salesforce", 
        display_name: "Salesforce", 
        icon: "Building", 
        auth_type: "oauth",
        oauth_config: {
          authorization_url: "https://login.salesforce.com/services/oauth2/authorize",
          client_id: import.meta.env.VITE_SALESFORCE_CLIENT_ID || "",
          scope: "api refresh_token",
          redirect_uri: `${window.location.origin}/settings?provider=salesforce`
        },
        actions: [{id: "create_lead", name: "Create Lead"}]
      },
      { 
        id: "twitter", 
        name: "twitter", 
        display_name: "X / Twitter", 
        icon: "Twitter", 
        auth_type: "oauth",
        oauth_config: {
          authorization_url: "https://twitter.com/i/oauth2/authorize",
          client_id: import.meta.env.VITE_TWITTER_CLIENT_ID || "",
          scope: "tweet.read tweet.write",
          redirect_uri: `${window.location.origin}/settings?provider=twitter`
        },
        actions: [{id: "tweet", name: "Post Update"}]
      },
      { 
        id: "meta", 
        name: "meta", 
        display_name: "Meta (FB/IG)", 
        icon: "Facebook", 
        auth_type: "oauth",
        oauth_config: {
          authorization_url: "https://www.facebook.com/v18.0/dialog/oauth",
          client_id: import.meta.env.VITE_META_CLIENT_ID || "",
          scope: "pages_manage_posts,instagram_basic,instagram_content_publish",
          redirect_uri: `${window.location.origin}/settings?provider=meta`
        },
        actions: [{id: "post", name: "Post Content"}]
      },
      { 
        id: "zoom", 
        name: "zoom", 
        display_name: "Zoom", 
        icon: "Video", 
        auth_type: "oauth",
        oauth_config: {
          authorization_url: "https://zoom.us/oauth/authorize",
          client_id: import.meta.env.VITE_ZOOM_CLIENT_ID || "",
          scope: "meeting:write",
          redirect_uri: `${window.location.origin}/settings?provider=zoom`
        },
        actions: [{id: "meeting", name: "Create Meeting"}]
      },
      { 
        id: "discord", 
        name: "discord", 
        display_name: "Discord", 
        icon: "Hash", 
        auth_type: "oauth",
        oauth_config: {
          authorization_url: "https://discord.com/api/oauth2/authorize",
          client_id: import.meta.env.VITE_DISCORD_CLIENT_ID || "",
          scope: "webhook.incoming",
          redirect_uri: `${window.location.origin}/settings?provider=discord`
        },
        actions: [{id: "webhook", name: "Post Webhook"}]
      },
      { 
        id: "shopify", 
        name: "shopify", 
        display_name: "Shopify", 
        icon: "ShoppingBag", 
        auth_type: "oauth",
        oauth_config: {
          authorization_url: "https://{shop}.myshopify.com/admin/oauth/authorize",
          client_id: import.meta.env.VITE_SHOPIFY_CLIENT_ID || "",
          scope: "write_products",
          redirect_uri: `${window.location.origin}/settings?provider=shopify`
        },
        actions: [{id: "product", name: "Add Product"}]
      },
      { 
        id: "jira", 
        name: "jira", 
        display_name: "Jira", 
        icon: "Trello", 
        auth_type: "oauth",
        oauth_config: {
          authorization_url: "https://auth.atlassian.com/authorize",
          client_id: import.meta.env.VITE_JIRA_CLIENT_ID || "",
          scope: "write:jira-work",
          redirect_uri: `${window.location.origin}/settings?provider=jira`
        },
        actions: [{id: "ticket", name: "Create Ticket"}]
      },
      
      // API Key Providers (services that require API keys)
      { id: "web_search", name: "web_search", display_name: "Web Search", icon: "Search", auth_type: "api_key", oauth_config: {}, actions: [{id: "search", name: "Search"}] },
      { id: "weather", name: "weather", display_name: "Weather", icon: "CloudSun", auth_type: "api_key", oauth_config: {}, actions: [{id: "get", name: "Get Forecast"}] },
      { id: "mailchimp", name: "mailchimp", display_name: "Mailchimp", icon: "Mail", auth_type: "api_key", oauth_config: {}, actions: [{id: "add_subscriber", name: "Add Subscriber"}] },
      { id: "claude", name: "claude", display_name: "Claude (Anthropic)", icon: "Cpu", auth_type: "api_key", oauth_config: {}, actions: [{id: "chat", name: "Chat"}] },
      { id: "chatgpt", name: "chatgpt", display_name: "ChatGPT (OpenAI)", icon: "Zap", auth_type: "api_key", oauth_config: {}, actions: [{id: "chat", name: "Chat"}] },
      { id: "perplexity", name: "perplexity", display_name: "Perplexity", icon: "Search", auth_type: "api_key", oauth_config: {}, actions: [{id: "search", name: "Search"}] },
      { id: "stripe", name: "stripe", display_name: "Stripe", icon: "CreditCard", auth_type: "api_key", oauth_config: {}, actions: [{id: "pay", name: "Create Customer"}] },
      { id: "twilio", name: "twilio", display_name: "Twilio", icon: "Phone", auth_type: "api_key", oauth_config: {}, actions: [{id: "sms", name: "Send SMS"}] },
      { id: "tiktok", name: "tiktok", display_name: "TikTok", icon: "Video", auth_type: "api_key", oauth_config: {}, actions: [{id: "upload", name: "Upload Video"}] },
      { id: "whatsapp", name: "whatsapp", display_name: "WhatsApp", icon: "MessageSquare", auth_type: "api_key", oauth_config: {}, actions: [{id: "msg", name: "Send Message"}] },
      { id: "woocommerce", name: "woocommerce", display_name: "WooCommerce", icon: "ShoppingBag", auth_type: "api_key", oauth_config: {}, actions: [{id: "order", name: "Create Order"}] },
      { id: "zendesk", name: "zendesk", display_name: "Zendesk", icon: "LifeBuoy", auth_type: "api_key", oauth_config: {}, actions: [{id: "support", name: "Create Ticket"}] },
      { id: "custom_tool", name: "custom_tool", display_name: "Custom Integration (Webhook)", icon: "Link", auth_type: "api_key", oauth_config: {}, actions: [{id: "webhook", name: "Trigger Webhook"}] },
      { id: "custom_api", name: "custom_api", display_name: "Custom API Tool (Auth Required)", icon: "ShieldCheck", auth_type: "api_key", oauth_config: {}, actions: [{id: "call", name: "Call API"}] },
      { id: "ai_marketing", name: "ai_marketing", display_name: "Marketing AI", icon: "Sparkles", auth_type: "api_key", oauth_config: {}, actions: [{id: "copy", name: "Generate Copy"}] },
      { id: "groq", name: "groq", display_name: "Groq", icon: "Cpu", auth_type: "api_key", oauth_config: {}, actions: [{id: "chat", name: "AI Chat"}] },
      
      // Communication
      { 
        id: "telegram", 
        name: "telegram", 
        display_name: "Telegram", 
        icon: "MessageSquare", 
        auth_type: "api_key", 
        oauth_config: {}, 
        actions: [{id: "send_message", name: "Send Message"}] 
      },
      { 
        id: "microsoft_teams", 
        name: "microsoft_teams", 
        display_name: "Microsoft Teams", 
        icon: "Users", 
        auth_type: "api_key", 
        oauth_config: {}, 
        actions: [{id: "post_message", name: "Post Message"}] 
      },
      { 
        id: "reddit", 
        name: "reddit", 
        display_name: "Reddit", 
        icon: "MessageCircle", 
        auth_type: "oauth",
        oauth_config: {
          authorization_url: "https://www.reddit.com/api/v1/authorize",
          client_id: import.meta.env.VITE_REDDIT_CLIENT_ID || "",
          scope: "submit",
          redirect_uri: `${window.location.origin}/settings?provider=reddit`
        },
        actions: [{id: "post_submission", name: "Post to Subreddit"}] 
      },
      
      // Productivity
      { 
        id: "airtable", 
        name: "airtable", 
        display_name: "Airtable", 
        icon: "Table", 
        auth_type: "api_key", 
        oauth_config: {}, 
        actions: [{id: "create_record", name: "Create Record"}] 
      },
      { 
        id: "trello", 
        name: "trello", 
        display_name: "Trello", 
        icon: "Trello", 
        auth_type: "oauth",
        oauth_config: {
          authorization_url: "https://trello.com/1/OAuthAuthorizeToken",
          client_id: import.meta.env.VITE_TRELLO_CLIENT_ID || "",
          scope: "read,write",
          redirect_uri: `${window.location.origin}/settings?provider=trello`
        },
        actions: [{id: "create_card", name: "Create Card"}] 
      },
      { 
        id: "asana", 
        name: "asana", 
        display_name: "Asana", 
        icon: "CheckSquare", 
        auth_type: "oauth",
        oauth_config: {
          authorization_url: "https://app.asana.com/-/oauth_authorize",
          client_id: import.meta.env.VITE_ASANA_CLIENT_ID || "",
          scope: "default",
          redirect_uri: `${window.location.origin}/settings?provider=asana`
        },
        actions: [{id: "create_task", name: "Create Task"}] 
      },
      { 
        id: "monday", 
        name: "monday", 
        display_name: "Monday.com", 
        icon: "Calendar", 
        auth_type: "api_key", 
        oauth_config: {}, 
        actions: [{id: "create_item", name: "Create Item"}] 
      },
      { 
        id: "clickup", 
        name: "clickup", 
        display_name: "ClickUp", 
        icon: "Target", 
        auth_type: "api_key", 
        oauth_config: {}, 
        actions: [{id: "create_task", name: "Create Task"}] 
      },
      
      // Cloud Storage
      { 
        id: "dropbox", 
        name: "dropbox", 
        display_name: "Dropbox", 
        icon: "Cloud", 
        auth_type: "oauth",
        oauth_config: {
          authorization_url: "https://www.dropbox.com/oauth2/authorize",
          client_id: import.meta.env.VITE_DROPBOX_CLIENT_ID || "",
          scope: "files.content.write",
          redirect_uri: `${window.location.origin}/settings?provider=dropbox`
        },
        actions: [{id: "upload_file", name: "Upload File"}] 
      },
      { 
        id: "onedrive", 
        name: "onedrive", 
        display_name: "OneDrive", 
        icon: "Cloud", 
        auth_type: "oauth",
        oauth_config: {
          authorization_url: "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
          client_id: import.meta.env.VITE_ONEDRIVE_CLIENT_ID || "",
          scope: "Files.ReadWrite",
          redirect_uri: `${window.location.origin}/settings?provider=onedrive`
        },
        actions: [{id: "upload_file", name: "Upload File"}] 
      },
      { 
        id: "google_drive", 
        name: "google_drive", 
        display_name: "Google Drive", 
        icon: "HardDrive", 
        auth_type: "oauth",
        oauth_config: {
          authorization_url: "https://accounts.google.com/o/oauth2/v2/auth",
          client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID || "",
          scope: "https://www.googleapis.com/auth/drive.file",
          redirect_uri: `${window.location.origin}/settings?provider=google_drive`
        },
        actions: [{id: "upload_file", name: "Upload File"}] 
      },
      
      // CRM
      { 
        id: "pipedrive", 
        name: "pipedrive", 
        display_name: "Pipedrive", 
        icon: "TrendingUp", 
        auth_type: "api_key", 
        oauth_config: {}, 
        actions: [{id: "create_deal", name: "Create Deal"}] 
      },
      { 
        id: "zoho_crm", 
        name: "zoho_crm", 
        display_name: "Zoho CRM", 
        icon: "Building", 
        auth_type: "oauth",
        oauth_config: {
          authorization_url: "https://accounts.zoho.com/oauth/v2/auth",
          client_id: import.meta.env.VITE_ZOHO_CLIENT_ID || "",
          scope: "ZohoCRM.modules.ALL",
          redirect_uri: `${window.location.origin}/settings?provider=zoho_crm`
        },
        actions: [{id: "create_lead", name: "Create Lead"}] 
      },
      { 
        id: "freshsales", 
        name: "freshsales", 
        display_name: "Freshsales", 
        icon: "Users", 
        auth_type: "api_key", 
        oauth_config: {}, 
        actions: [{id: "create_contact", name: "Create Contact"}] 
      },
      
      // Analytics
      { 
        id: "google_analytics", 
        name: "google_analytics", 
        display_name: "Google Analytics", 
        icon: "BarChart", 
        auth_type: "oauth",
        oauth_config: {
          authorization_url: "https://accounts.google.com/o/oauth2/v2/auth",
          client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID || "",
          scope: "https://www.googleapis.com/auth/analytics.edit",
          redirect_uri: `${window.location.origin}/settings?provider=google_analytics`
        },
        actions: [{id: "track_event", name: "Track Event"}] 
      },
      { 
        id: "mixpanel", 
        name: "mixpanel", 
        display_name: "Mixpanel", 
        icon: "BarChart", 
        auth_type: "api_key", 
        oauth_config: {}, 
        actions: [{id: "track_event", name: "Track Event"}] 
      },
      { 
        id: "amplitude", 
        name: "amplitude", 
        display_name: "Amplitude", 
        icon: "BarChart", 
        auth_type: "api_key", 
        oauth_config: {}, 
        actions: [{id: "track_event", name: "Track Event"}] 
      },
      
      // Development
      { 
        id: "gitlab", 
        name: "gitlab", 
        display_name: "GitLab", 
        icon: "GitBranch", 
        auth_type: "oauth",
        oauth_config: {
          authorization_url: "https://gitlab.com/oauth/authorize",
          client_id: import.meta.env.VITE_GITLAB_CLIENT_ID || "",
          scope: "api",
          redirect_uri: `${window.location.origin}/settings?provider=gitlab`
        },
        actions: [{id: "create_issue", name: "Create Issue"}] 
      },
      { 
        id: "bitbucket", 
        name: "bitbucket", 
        display_name: "Bitbucket", 
        icon: "GitBranch", 
        auth_type: "oauth",
        oauth_config: {
          authorization_url: "https://bitbucket.org/site/oauth2/authorize",
          client_id: import.meta.env.VITE_BITBUCKET_CLIENT_ID || "",
          scope: "repository:write",
          redirect_uri: `${window.location.origin}/settings?provider=bitbucket`
        },
        actions: [{id: "create_issue", name: "Create Issue"}] 
      },
      { 
        id: "linear", 
        name: "linear", 
        display_name: "Linear", 
        icon: "Workflow", 
        auth_type: "api_key", 
        oauth_config: {}, 
        actions: [{id: "create_issue", name: "Create Issue"}] 
      },
      { 
        id: "sentry", 
        name: "sentry", 
        display_name: "Sentry", 
        icon: "AlertTriangle", 
        auth_type: "api_key", 
        oauth_config: {}, 
        actions: [{id: "create_event", name: "Create Event"}] 
      },
      
      // E-commerce
      { 
        id: "bigcommerce", 
        name: "bigcommerce", 
        display_name: "BigCommerce", 
        icon: "ShoppingBag", 
        auth_type: "api_key", 
        oauth_config: {}, 
        actions: [{id: "create_product", name: "Create Product"}] 
      },
      { 
        id: "square", 
        name: "square", 
        display_name: "Square", 
        icon: "CreditCard", 
        auth_type: "api_key", 
        oauth_config: {}, 
        actions: [{id: "create_customer", name: "Create Customer"}] 
      },
      { 
        id: "paypal", 
        name: "paypal", 
        display_name: "PayPal", 
        icon: "CreditCard", 
        auth_type: "api_key", 
        oauth_config: {}, 
        actions: [{id: "create_payment", name: "Create Payment"}] 
      },
      
      // Other
      { 
        id: "calendly", 
        name: "calendly", 
        display_name: "Calendly", 
        icon: "Calendar", 
        auth_type: "api_key", 
        oauth_config: {}, 
        actions: [{id: "create_event", name: "Create Event"}] 
      },
      { 
        id: "typeform", 
        name: "typeform", 
        display_name: "Typeform", 
        icon: "FileText", 
        auth_type: "api_key", 
        oauth_config: {}, 
        actions: [{id: "create_response", name: "Create Response"}] 
      },
      { 
        id: "intercom", 
        name: "intercom", 
        display_name: "Intercom", 
        icon: "MessageCircle", 
        auth_type: "api_key", 
        oauth_config: {}, 
        actions: [{id: "create_conversation", name: "Create Conversation"}] 
      },
      { 
        id: "pagerduty", 
        name: "pagerduty", 
        display_name: "PagerDuty", 
        icon: "Bell", 
        auth_type: "api_key", 
        oauth_config: {}, 
        actions: [{id: "create_incident", name: "Create Incident"}] 
      },
      { 
        id: "sendgrid", 
        name: "sendgrid", 
        display_name: "SendGrid", 
        icon: "Mail", 
        auth_type: "api_key", 
        oauth_config: {}, 
        actions: [{id: "send_email", name: "Send Email"}] 
      },
      { 
        id: "mailgun", 
        name: "mailgun", 
        display_name: "Mailgun", 
        icon: "Mail", 
        auth_type: "api_key", 
        oauth_config: {}, 
        actions: [{id: "send_email", name: "Send Email"}] 
      },
      { 
        id: "aws_s3", 
        name: "aws_s3", 
        display_name: "AWS S3", 
        icon: "Cloud", 
        auth_type: "api_key", 
        oauth_config: {}, 
        actions: [{id: "upload_file", name: "Upload File"}] 
      },
      
      // Email Services
      { id: "postmark", name: "postmark", display_name: "Postmark", icon: "Mail", auth_type: "api_key", oauth_config: {}, actions: [{id: "send_email", name: "Send Email"}] },
      { id: "sparkpost", name: "sparkpost", display_name: "SparkPost", icon: "Mail", auth_type: "api_key", oauth_config: {}, actions: [{id: "send_email", name: "Send Email"}] },
      { id: "ses", name: "ses", display_name: "AWS SES", icon: "Mail", auth_type: "api_key", oauth_config: {}, actions: [{id: "send_email", name: "Send Email"}] },
      { id: "postal", name: "postal", display_name: "Postal", icon: "Mail", auth_type: "api_key", oauth_config: {}, actions: [{id: "send_email", name: "Send Email"}] },
      
      // SMS/Voice
      { id: "vonage", name: "vonage", display_name: "Vonage", icon: "Phone", auth_type: "api_key", oauth_config: {}, actions: [{id: "send_sms", name: "Send SMS"}] },
      { id: "bandwidth", name: "bandwidth", display_name: "Bandwidth", icon: "Phone", auth_type: "api_key", oauth_config: {}, actions: [{id: "send_sms", name: "Send SMS"}] },
      { id: "messagebird", name: "messagebird", display_name: "MessageBird", icon: "Phone", auth_type: "api_key", oauth_config: {}, actions: [{id: "send_sms", name: "Send SMS"}] },
      { id: "plivo", name: "plivo", display_name: "Plivo", icon: "Phone", auth_type: "api_key", oauth_config: {}, actions: [{id: "send_sms", name: "Send SMS"}] },
      
      // Payment Processors
      { id: "braintree", name: "braintree", display_name: "Braintree", icon: "CreditCard", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_transaction", name: "Create Transaction"}] },
      { id: "razorpay", name: "razorpay", display_name: "Razorpay", icon: "CreditCard", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_payment", name: "Create Payment"}] },
      { id: "mollie", name: "mollie", display_name: "Mollie", icon: "CreditCard", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_payment", name: "Create Payment"}] },
      { id: "adyen", name: "adyen", display_name: "Adyen", icon: "CreditCard", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_payment", name: "Create Payment"}] },
      { id: "revolut", name: "revolut", display_name: "Revolut", icon: "CreditCard", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_payment", name: "Create Payment"}] },
      
      // Accounting/Finance
      { id: "quickbooks", name: "quickbooks", display_name: "QuickBooks", icon: "DollarSign", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_invoice", name: "Create Invoice"}] },
      { id: "xero", name: "xero", display_name: "Xero", icon: "DollarSign", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_invoice", name: "Create Invoice"}] },
      { id: "freshbooks", name: "freshbooks", display_name: "FreshBooks", icon: "DollarSign", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_invoice", name: "Create Invoice"}] },
      { id: "wave", name: "wave", display_name: "Wave", icon: "DollarSign", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_invoice", name: "Create Invoice"}] },
      { id: "sage", name: "sage", display_name: "Sage", icon: "DollarSign", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_invoice", name: "Create Invoice"}] },
      
      // Marketing Automation
      { id: "activecampaign", name: "activecampaign", display_name: "ActiveCampaign", icon: "Mail", auth_type: "api_key", oauth_config: {}, actions: [{id: "add_contact", name: "Add Contact"}] },
      { id: "convertkit", name: "convertkit", display_name: "ConvertKit", icon: "Mail", auth_type: "api_key", oauth_config: {}, actions: [{id: "add_subscriber", name: "Add Subscriber"}] },
      { id: "getresponse", name: "getresponse", display_name: "GetResponse", icon: "Mail", auth_type: "api_key", oauth_config: {}, actions: [{id: "add_contact", name: "Add Contact"}] },
      { id: "drip", name: "drip", display_name: "Drip", icon: "Mail", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_subscriber", name: "Create Subscriber"}] },
      { id: "omnisend", name: "omnisend", display_name: "Omnisend", icon: "Mail", auth_type: "api_key", oauth_config: {}, actions: [{id: "add_contact", name: "Add Contact"}] },
      { id: "klaviyo", name: "klaviyo", display_name: "Klaviyo", icon: "Mail", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_profile", name: "Create Profile"}] },
      { id: "brevo", name: "brevo", display_name: "Brevo", icon: "Mail", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_contact", name: "Create Contact"}] },
      { id: "sendinblue", name: "sendinblue", display_name: "SendinBlue", icon: "Mail", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_contact", name: "Create Contact"}] },
      
      // Social Media Management
      { id: "buffer", name: "buffer", display_name: "Buffer", icon: "Share2", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_post", name: "Create Post"}] },
      { id: "hootsuite", name: "hootsuite", display_name: "Hootsuite", icon: "Share2", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_post", name: "Create Post"}] },
      { id: "later", name: "later", display_name: "Later", icon: "Share2", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_post", name: "Create Post"}] },
      { id: "sprout_social", name: "sprout_social", display_name: "Sprout Social", icon: "Share2", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_post", name: "Create Post"}] },
      { id: "co_schedule", name: "co_schedule", display_name: "CoSchedule", icon: "Share2", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_post", name: "Create Post"}] },
      
      // Customer Support
      { id: "freshdesk", name: "freshdesk", display_name: "Freshdesk", icon: "LifeBuoy", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_ticket", name: "Create Ticket"}] },
      { id: "helpscout", name: "helpscout", display_name: "Help Scout", icon: "LifeBuoy", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_conversation", name: "Create Conversation"}] },
      { id: "crisp", name: "crisp", display_name: "Crisp", icon: "MessageCircle", auth_type: "api_key", oauth_config: {}, actions: [{id: "send_message", name: "Send Message"}] },
      { id: "drift", name: "drift", display_name: "Drift", icon: "MessageCircle", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_conversation", name: "Create Conversation"}] },
      { id: "tawk", name: "tawk", display_name: "Tawk.to", icon: "MessageCircle", auth_type: "api_key", oauth_config: {}, actions: [{id: "send_message", name: "Send Message"}] },
      { id: "livechat", name: "livechat", display_name: "LiveChat", icon: "MessageCircle", auth_type: "api_key", oauth_config: {}, actions: [{id: "send_message", name: "Send Message"}] },
      
      // Project Management
      { id: "basecamp", name: "basecamp", display_name: "Basecamp", icon: "Trello", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_todo", name: "Create Todo"}] },
      { id: "wrike", name: "wrike", display_name: "Wrike", icon: "Trello", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_task", name: "Create Task"}] },
      { id: "smartsheet", name: "smartsheet", display_name: "Smartsheet", icon: "Table", auth_type: "api_key", oauth_config: {}, actions: [{id: "add_row", name: "Add Row"}] },
      { id: "notion_api", name: "notion_api", display_name: "Notion API", icon: "BookOpen", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_page", name: "Create Page"}] },
      { id: "coda", name: "coda", display_name: "Coda", icon: "FileText", auth_type: "api_key", oauth_config: {}, actions: [{id: "insert_row", name: "Insert Row"}] },
      
      // Database/Data
      { id: "supabase_db", name: "supabase_db", display_name: "Supabase DB", icon: "Database", auth_type: "api_key", oauth_config: {}, actions: [{id: "insert_row", name: "Insert Row"}] },
      { id: "firebase", name: "firebase", display_name: "Firebase", icon: "Database", auth_type: "api_key", oauth_config: {}, actions: [{id: "write_data", name: "Write Data"}] },
      { id: "mongodb", name: "mongodb", display_name: "MongoDB", icon: "Database", auth_type: "api_key", oauth_config: {}, actions: [{id: "insert_document", name: "Insert Document"}] },
      { id: "airtable_api", name: "airtable_api", display_name: "Airtable API", icon: "Table", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_record", name: "Create Record"}] },
      { id: "dynamodb", name: "dynamodb", display_name: "DynamoDB", icon: "Database", auth_type: "api_key", oauth_config: {}, actions: [{id: "put_item", name: "Put Item"}] },
      
      // Monitoring/Logging
      { id: "datadog", name: "datadog", display_name: "Datadog", icon: "Activity", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_event", name: "Create Event"}] },
      { id: "newrelic", name: "newrelic", display_name: "New Relic", icon: "Activity", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_event", name: "Create Event"}] },
      { id: "loggly", name: "loggly", display_name: "Loggly", icon: "FileText", auth_type: "api_key", oauth_config: {}, actions: [{id: "send_log", name: "Send Log"}] },
      { id: "papertrail", name: "papertrail", display_name: "Papertrail", icon: "FileText", auth_type: "api_key", oauth_config: {}, actions: [{id: "send_log", name: "Send Log"}] },
      { id: "rollbar", name: "rollbar", display_name: "Rollbar", icon: "AlertTriangle", auth_type: "api_key", oauth_config: {}, actions: [{id: "report_error", name: "Report Error"}] },
      { id: "honeybadger", name: "honeybadger", display_name: "Honeybadger", icon: "AlertTriangle", auth_type: "api_key", oauth_config: {}, actions: [{id: "notify", name: "Notify"}] },
      { id: "bugsnag", name: "bugsnag", display_name: "Bugsnag", icon: "AlertTriangle", auth_type: "api_key", oauth_config: {}, actions: [{id: "notify", name: "Notify"}] },
      
      // CI/CD
      { id: "circleci", name: "circleci", display_name: "CircleCI", icon: "GitBranch", auth_type: "api_key", oauth_config: {}, actions: [{id: "trigger_pipeline", name: "Trigger Pipeline"}] },
      { id: "travis_ci", name: "travis_ci", display_name: "Travis CI", icon: "GitBranch", auth_type: "api_key", oauth_config: {}, actions: [{id: "trigger_build", name: "Trigger Build"}] },
      { id: "jenkins", name: "jenkins", display_name: "Jenkins", icon: "GitBranch", auth_type: "api_key", oauth_config: {}, actions: [{id: "trigger_build", name: "Trigger Build"}] },
      { id: "github_actions", name: "github_actions", display_name: "GitHub Actions", icon: "Github", auth_type: "api_key", oauth_config: {}, actions: [{id: "trigger_workflow", name: "Trigger Workflow"}] },
      { id: "gitlab_ci", name: "gitlab_ci", display_name: "GitLab CI", icon: "GitBranch", auth_type: "api_key", oauth_config: {}, actions: [{id: "trigger_pipeline", name: "Trigger Pipeline"}] },
      
      // Content Management
      { id: "contentful", name: "contentful", display_name: "Contentful", icon: "FileText", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_entry", name: "Create Entry"}] },
      { id: "strapi", name: "strapi", display_name: "Strapi", icon: "FileText", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_entry", name: "Create Entry"}] },
      { id: "wordpress", name: "wordpress", display_name: "WordPress", icon: "FileText", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_post", name: "Create Post"}] },
      { id: "ghost", name: "ghost", display_name: "Ghost", icon: "FileText", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_post", name: "Create Post"}] },
      { id: "medium", name: "medium", display_name: "Medium", icon: "FileText", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_post", name: "Create Post"}] },
      { id: "dev_to", name: "dev_to", display_name: "Dev.to", icon: "FileText", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_article", name: "Create Article"}] },
      
      // Forms/Surveys
      { id: "google_forms", name: "google_forms", display_name: "Google Forms", icon: "FileText", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_response", name: "Create Response"}] },
      { id: "jotform", name: "jotform", display_name: "JotForm", icon: "FileText", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_submission", name: "Create Submission"}] },
      { id: "wufoo", name: "wufoo", display_name: "Wufoo", icon: "FileText", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_entry", name: "Create Entry"}] },
      { id: "formspree", name: "formspree", display_name: "Formspree", icon: "FileText", auth_type: "api_key", oauth_config: {}, actions: [{id: "submit_form", name: "Submit Form"}] },
      
      // Video/Media
      { id: "vimeo", name: "vimeo", display_name: "Vimeo", icon: "Video", auth_type: "api_key", oauth_config: {}, actions: [{id: "upload_video", name: "Upload Video"}] },
      { id: "youtube", name: "youtube", display_name: "YouTube", icon: "Video", auth_type: "api_key", oauth_config: {}, actions: [{id: "upload_video", name: "Upload Video"}] },
      { id: "cloudinary", name: "cloudinary", display_name: "Cloudinary", icon: "Image", auth_type: "api_key", oauth_config: {}, actions: [{id: "upload_image", name: "Upload Image"}] },
      { id: "imgur", name: "imgur", display_name: "Imgur", icon: "Image", auth_type: "api_key", oauth_config: {}, actions: [{id: "upload_image", name: "Upload Image"}] },
      
      // Maps/Location
      { id: "google_maps", name: "google_maps", display_name: "Google Maps", icon: "MapPin", auth_type: "api_key", oauth_config: {}, actions: [{id: "geocode", name: "Geocode Address"}] },
      { id: "mapbox", name: "mapbox", display_name: "Mapbox", icon: "MapPin", auth_type: "api_key", oauth_config: {}, actions: [{id: "geocode", name: "Geocode Address"}] },
      { id: "here", name: "here", display_name: "HERE Maps", icon: "MapPin", auth_type: "api_key", oauth_config: {}, actions: [{id: "geocode", name: "Geocode Address"}] },
      
      // Translation
      { id: "deep_l", name: "deep_l", display_name: "DeepL", icon: "Languages", auth_type: "api_key", oauth_config: {}, actions: [{id: "translate", name: "Translate Text"}] },
      { id: "google_translate", name: "google_translate", display_name: "Google Translate", icon: "Languages", auth_type: "api_key", oauth_config: {}, actions: [{id: "translate", name: "Translate Text"}] },
      { id: "microsoft_translator", name: "microsoft_translator", display_name: "Microsoft Translator", icon: "Languages", auth_type: "api_key", oauth_config: {}, actions: [{id: "translate", name: "Translate Text"}] },
      
      // OCR/Image Processing
      { id: "tesseract", name: "tesseract", display_name: "Tesseract OCR", icon: "Scan", auth_type: "api_key", oauth_config: {}, actions: [{id: "extract_text", name: "Extract Text"}] },
      { id: "aws_textract", name: "aws_textract", display_name: "AWS Textract", icon: "Scan", auth_type: "api_key", oauth_config: {}, actions: [{id: "extract_text", name: "Extract Text"}] },
      { id: "google_vision", name: "google_vision", display_name: "Google Vision", icon: "Eye", auth_type: "api_key", oauth_config: {}, actions: [{id: "analyze_image", name: "Analyze Image"}] },
      
      // Webhooks/API
      { id: "zapier", name: "zapier", display_name: "Zapier", icon: "Link", auth_type: "api_key", oauth_config: {}, actions: [{id: "trigger_webhook", name: "Trigger Webhook"}] },
      { id: "make", name: "make", display_name: "Make", icon: "Link", auth_type: "api_key", oauth_config: {}, actions: [{id: "trigger_scenario", name: "Trigger Scenario"}] },
      { id: "n8n", name: "n8n", display_name: "n8n", icon: "Link", auth_type: "api_key", oauth_config: {}, actions: [{id: "trigger_workflow", name: "Trigger Workflow"}] },
      { id: "ifttt", name: "ifttt", display_name: "IFTTT", icon: "Link", auth_type: "api_key", oauth_config: {}, actions: [{id: "trigger_applet", name: "Trigger Applet"}] },
      
      // Time Tracking
      { id: "toggl", name: "toggl", display_name: "Toggl", icon: "Clock", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_time_entry", name: "Create Time Entry"}] },
      { id: "harvest", name: "harvest", display_name: "Harvest", icon: "Clock", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_time_entry", name: "Create Time Entry"}] },
      { id: "clockify", name: "clockify", display_name: "Clockify", icon: "Clock", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_time_entry", name: "Create Time Entry"}] },
      
      // HR/Recruiting
      { id: "bamboohr", name: "bamboohr", display_name: "BambooHR", icon: "Users", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_employee", name: "Create Employee"}] },
      { id: "workday", name: "workday", display_name: "Workday", icon: "Users", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_worker", name: "Create Worker"}] },
      { id: "greenhouse", name: "greenhouse", display_name: "Greenhouse", icon: "Users", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_candidate", name: "Create Candidate"}] },
      
      // Document Management
      { id: "docu_sign", name: "docu_sign", display_name: "DocuSign", icon: "FileText", auth_type: "api_key", oauth_config: {}, actions: [{id: "send_envelope", name: "Send Envelope"}] },
      { id: "hello_sign", name: "hello_sign", display_name: "HelloSign", icon: "FileText", auth_type: "api_key", oauth_config: {}, actions: [{id: "send_signature_request", name: "Send Signature Request"}] },
      { id: "pandadoc", name: "pandadoc", display_name: "PandaDoc", icon: "FileText", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_document", name: "Create Document"}] },
      
      // Shipping/Logistics
      { id: "shipstation", name: "shipstation", display_name: "ShipStation", icon: "Package", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_shipment", name: "Create Shipment"}] },
      { id: "easypost", name: "easypost", display_name: "EasyPost", icon: "Package", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_shipment", name: "Create Shipment"}] },
      { id: "shippo", name: "shippo", display_name: "Shippo", icon: "Package", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_transaction", name: "Create Transaction"}] },
      
      // Real Estate
      { id: "zillow", name: "zillow", display_name: "Zillow", icon: "Home", auth_type: "api_key", oauth_config: {}, actions: [{id: "get_property", name: "Get Property"}] },
      { id: "realtor", name: "realtor", display_name: "Realtor.com", icon: "Home", auth_type: "api_key", oauth_config: {}, actions: [{id: "search_listings", name: "Search Listings"}] },
      
      // Weather/Environment
      { id: "openweather", name: "openweather", display_name: "OpenWeather", icon: "CloudSun", auth_type: "api_key", oauth_config: {}, actions: [{id: "get_weather", name: "Get Weather"}] },
      { id: "weather_api", name: "weather_api", display_name: "Weather API", icon: "CloudSun", auth_type: "api_key", oauth_config: {}, actions: [{id: "get_forecast", name: "Get Forecast"}] },
      
      // News/Content
      { id: "newsapi", name: "newsapi", display_name: "NewsAPI", icon: "Newspaper", auth_type: "api_key", oauth_config: {}, actions: [{id: "get_articles", name: "Get Articles"}] },
      { id: "rss", name: "rss", display_name: "RSS Feed", icon: "Rss", auth_type: "api_key", oauth_config: {}, actions: [{id: "parse_feed", name: "Parse Feed"}] },
      
      // Cryptocurrency
      { id: "coinbase", name: "coinbase", display_name: "Coinbase", icon: "Bitcoin", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_transaction", name: "Create Transaction"}] },
      { id: "binance", name: "binance", display_name: "Binance", icon: "Bitcoin", auth_type: "api_key", oauth_config: {}, actions: [{id: "create_order", name: "Create Order"}] },
      
      // AI/ML Services
      { id: "replicate", name: "replicate", display_name: "Replicate", icon: "Cpu", auth_type: "api_key", oauth_config: {}, actions: [{id: "run_model", name: "Run Model"}] },
      { id: "huggingface", name: "huggingface", display_name: "Hugging Face", icon: "Cpu", auth_type: "api_key", oauth_config: {}, actions: [{id: "run_inference", name: "Run Inference"}] },
      { id: "stability_ai", name: "stability_ai", display_name: "Stability AI", icon: "Image", auth_type: "api_key", oauth_config: {}, actions: [{id: "generate_image", name: "Generate Image"}] },
      { id: "midjourney_api", name: "midjourney_api", display_name: "Midjourney API", icon: "Image", auth_type: "api_key", oauth_config: {}, actions: [{id: "generate_image", name: "Generate Image"}] },
      { id: "elevenlabs", name: "elevenlabs", display_name: "ElevenLabs", icon: "Volume2", auth_type: "api_key", oauth_config: {}, actions: [{id: "text_to_speech", name: "Text to Speech"}] },
      { id: "assemblyai", name: "assemblyai", display_name: "AssemblyAI", icon: "Volume2", auth_type: "api_key", oauth_config: {}, actions: [{id: "transcribe_audio", name: "Transcribe Audio"}] }
    ];
    
    // Combine built-in and custom integrations
    const allProviders = [...mockProviders, ...customIntegrations];
    setProviders(allProviders);
    } catch (error) {
      console.error("Error in fetchProviders:", error);
      // Set empty providers on error to prevent blank screen
      setProviders([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchCredentials = async () => {
    if (!user) return;
    
    try {
      const { data, error } = await supabase
        .from("credentials")
        .select("*")
        .eq("user_id", user.id);

      if (error) {
        console.error("Error fetching credentials:", error);
        // If table doesn't exist, use empty array (for development)
        setCredentials([]);
        return;
      }

      setCredentials(data || []);
    } catch (error) {
      console.error("Error fetching credentials:", error);
      // Fallback to empty array if Supabase call fails
      setCredentials([]);
    }
  };

  const handleConnect = async (provider: Provider) => {
    if (provider.auth_type === "api_key") {
      setApiKeyModal({ open: true, provider });
    } else {
      // OAuth flow - construct authorization URL
      const oauthConfig = provider.oauth_config as {
        authorization_url?: string;
        client_id?: string;
        scope?: string;
        redirect_uri?: string;
      };

      if (!oauthConfig?.authorization_url) {
        toast({
          title: "OAuth not configured",
          description: `OAuth for ${provider.display_name} requires server-side configuration.`,
          variant: "destructive",
        });
        return;
      }

      if (!oauthConfig.client_id) {
        toast({
          title: "OAuth Client ID not configured",
          description: `Please configure the OAuth client ID for ${provider.display_name} in your environment variables.`,
          variant: "destructive",
        });
        return;
      }

      // Build OAuth URL with state for security
      const state = `${user.id}:${provider.name}`;
      const redirectUri = oauthConfig.redirect_uri || 
        `${window.location.origin}/settings`;

      const authUrl = new URL(oauthConfig.authorization_url);
      authUrl.searchParams.set("client_id", oauthConfig.client_id);
      authUrl.searchParams.set("redirect_uri", redirectUri);
      authUrl.searchParams.set("response_type", "code");
      authUrl.searchParams.set("scope", oauthConfig.scope || "");
      authUrl.searchParams.set("state", state);
      authUrl.searchParams.set("access_type", "offline");
      authUrl.searchParams.set("prompt", "consent");

      // Redirect to OAuth provider
      window.location.href = authUrl.toString();
    }
  };

  const handleSaveApiKey = async () => {
    if (!apiKeyModal.provider || !apiKeyValue.trim()) return;

    setSaving(true);

    try {
      const { error } = await supabase.from("credentials").insert({
        user_id: user.id,
        provider_id: apiKeyModal.provider.id,
        type: "api_key",
        encrypted_api_key: apiKeyValue, // In production, encrypt this
        metadata: {},
      });

      if (error) throw error;

      toast({
        title: "Connected!",
        description: `${apiKeyModal.provider.display_name} has been connected.`,
      });

      setApiKeyModal({ open: false, provider: null });
      setApiKeyValue("");
      fetchCredentials();

    } catch (error) {
      console.error("Save API key error:", error);
      toast({
        title: "Error",
        description: "Failed to save API key",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  const handleDisconnect = async (providerId: string) => {
    const credential = credentials.find((c) => c.provider_id === providerId);
    if (!credential) return;

    try {
      const { error } = await supabase
        .from("credentials")
        .delete()
        .eq("id", credential.id);

      if (error) throw error;

      toast({
        title: "Disconnected",
        description: "Provider has been disconnected.",
      });

      fetchCredentials();

    } catch (error) {
      console.error("Disconnect error:", error);
      toast({
        title: "Error",
        description: "Failed to disconnect provider",
        variant: "destructive",
      });
    }
  };

  const getIcon = (iconName: string) => {
    const Icon = (LucideIcons as any)[iconName] || LucideIcons.Puzzle;
    return <Icon className="w-6 h-6" />;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50 w-full">
        <div className="container flex items-center gap-4 h-16 px-4 mx-auto max-w-7xl">
          <Button variant="ghost" size="sm" onClick={() => navigate("/dashboard")}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          <h1 className="text-xl font-semibold">Settings</h1>
        </div>
      </header>

        <main className="container px-4 py-8 max-w-7xl mx-auto w-full">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
            <div className="flex-1 min-w-0">
              <h2 className="text-2xl font-bold mb-2">Integrations</h2>
              <p className="text-muted-foreground">
                Connect your accounts to use them in execution plans.
              </p>
            </div>
            <Button 
              onClick={() => {
                setEditingCustomIntegration(null);
                setIsCustomIntegrationModalOpen(true);
              }}
              className="flex-shrink-0"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Custom Integration
            </Button>
          </div>

          {/* Search and Filters */}
          <div className="space-y-4 mb-8">
            {/* Search Input */}
            <div className="relative w-full">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground z-10" />
              <Input
                placeholder="Search integrations..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 pr-10 w-full"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery("")}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors z-10"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            {/* Filter Badges - Single Row */}
            <div className="flex flex-wrap items-center gap-4 w-full">
              <div className="flex items-center gap-2 flex-shrink-0">
                <span className="text-sm font-medium text-muted-foreground whitespace-nowrap">Type:</span>
                <div className="flex items-center gap-1">
                  <Badge
                    variant={authFilter === "all" ? "default" : "outline"}
                    className="cursor-pointer whitespace-nowrap"
                    onClick={() => setAuthFilter("all")}
                  >
                    All
                  </Badge>
                  <Badge
                    variant={authFilter === "oauth" ? "default" : "outline"}
                    className="cursor-pointer whitespace-nowrap"
                    onClick={() => setAuthFilter("oauth")}
                  >
                    OAuth
                  </Badge>
                  <Badge
                    variant={authFilter === "api_key" ? "default" : "outline"}
                    className="cursor-pointer whitespace-nowrap"
                    onClick={() => setAuthFilter("api_key")}
                  >
                    API Key
                  </Badge>
                </div>
              </div>

              <div className="flex items-center gap-2 flex-shrink-0">
                <span className="text-sm font-medium text-muted-foreground whitespace-nowrap">Status:</span>
                <div className="flex items-center gap-1">
                  <Badge
                    variant={connectionFilter === "all" ? "default" : "outline"}
                    className="cursor-pointer whitespace-nowrap"
                    onClick={() => setConnectionFilter("all")}
                  >
                    All
                  </Badge>
                  <Badge
                    variant={connectionFilter === "connected" ? "default" : "outline"}
                    className="cursor-pointer whitespace-nowrap"
                    onClick={() => setConnectionFilter("connected")}
                  >
                    Connected
                  </Badge>
                  <Badge
                    variant={connectionFilter === "not_connected" ? "default" : "outline"}
                    className="cursor-pointer whitespace-nowrap"
                    onClick={() => setConnectionFilter("not_connected")}
                  >
                    Not Connected
                  </Badge>
                </div>
              </div>

              {/* Results count */}
              <div className="ml-auto flex-shrink-0">
                <p className="text-sm text-muted-foreground whitespace-nowrap">
                  Showing {filteredProviders.length} of {providers.length}
                </p>
              </div>
            </div>
          </div>

          {filteredProviders.length === 0 ? (
            <div className="text-center py-12 glass rounded-xl">
              <p className="text-muted-foreground">No integrations found matching your criteria.</p>
              <Button
                variant="ghost"
                size="sm"
                className="mt-2"
                onClick={() => {
                  setSearchQuery("");
                  setAuthFilter("all");
                  setConnectionFilter("all");
                }}
              >
                Clear filters
              </Button>
            </div>
          ) : (
          <div className="grid gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
            {filteredProviders.map((provider) => {
              const connected = isConnected(provider.id);

              return (
                <motion.div
                  key={provider.id}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  whileHover={{ y: -4 }}
                  transition={{ duration: 0.2 }}
                  className="glass rounded-xl p-6 flex flex-col min-h-[260px] overflow-hidden"

                >
                  <div className="flex items-start justify-between gap-4 mb-6">
                    <div className="flex items-center gap-4 min-w-0 flex-1">
                      <div className="w-14 h-14 rounded-2xl bg-primary/10 flex items-center justify-center text-primary flex-shrink-0 border border-primary/20">
                        {getIcon(provider.icon)}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2 flex-wrap mb-1">
                          <h3 className="font-bold text-lg leading-tight line-clamp-2"></h3>
                          {provider.id.startsWith("custom_") && (
                            <Badge variant="secondary" className="text-[10px] h-4 uppercase font-bold tracking-wider">Custom</Badge>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground/80 font-medium">
                          {provider.auth_type === "oauth" ? "OAuth 2.0" : "API Key Auth"}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-1.5 flex-shrink-0">
                      {provider.id.startsWith("custom_") && (
                        <>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-muted-foreground hover:text-foreground"
                            onClick={() => {
                              setEditingCustomIntegration(provider);
                              setIsCustomIntegrationModalOpen(true);
                            }}
                          >
                            <Settings className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-destructive/70 hover:text-destructive hover:bg-destructive/10"
                            onClick={() => {
                              const customIntegrations: Provider[] = JSON.parse(
                                localStorage.getItem("custom_integrations") || "[]"
                              );
                              const updated = customIntegrations.filter(
                                (p) => p.id !== provider.id
                              );
                              localStorage.setItem(
                                "custom_integrations",
                                JSON.stringify(updated)
                              );
                              fetchProviders();
                              toast({
                                title: "Integration deleted",
                                description: `${provider.display_name} has been removed.`,
                              });
                            }}
                          >
                            <X className="w-4 h-4" />
                          </Button>
                        </>
                      )}
                    </div>
                  </div>

                    <div className="flex-1 flex flex-col gap-4">
                    <div className="flex flex-wrap gap-2">
                      {connected ? (
                        <div className="flex items-center justify-between w-full bg-success/5 border border-success/20 rounded-lg p-3">
                          <span className="text-sm font-semibold text-success flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-success animate-pulse" />
                            Connected
                          </span>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                            onClick={() => handleDisconnect(provider.id)}
                          >
                            <Unlink className="w-4 h-4 mr-2" />
                            Disconnect
                          </Button>
                        </div>
                      ) : (
                        <Button
                          variant="secondary"
                          className="w-full font-semibold shadow-sm hover:shadow-md transition-all h-10"
                          onClick={() => handleConnect(provider)}
                        >
                          {provider.auth_type === "oauth" ? (
                            <Link2 className="w-4 h-4 mr-2" />
                          ) : (
                            <Key className="w-4 h-4 mr-2" />
                          )}
                          Connect {provider.display_name}
                        </Button>
                      )}
                    </div>

                    <div className="pt-4 border-t border-white/5">
                      <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60 mb-3">Capabilities</p>
                      <div className="flex flex-wrap gap-1.5">
                        {(provider.actions as any[])?.slice(0, 4).map((action: any) => (
                          <span
                            key={action.id}
                            className="text-[11px] font-medium px-2.5 py-1 rounded-md bg-white/5 text-muted-foreground border border-white/5"
                          >
                            {action.name}
                          </span>
                        ))}
                        {(provider.actions as any[])?.length > 4 && (
                          <span className="text-[11px] font-bold text-muted-foreground/50 px-1">
                            +{(provider.actions as any[]).length - 4}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
          )}
        </motion.div>
      </main>

      {/* API Key Modal */}
      <Dialog open={apiKeyModal.open} onOpenChange={(open) => setApiKeyModal({ open, provider: open ? apiKeyModal.provider : null })}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Connect {apiKeyModal.provider?.display_name}</DialogTitle>
            <DialogDescription>
              Enter your API key to connect this provider. Your key will be encrypted and stored securely.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Input
              type="password"
              placeholder="Enter API key"
              value={apiKeyValue}
              onChange={(e) => setApiKeyValue(e.target.value)}
            />
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setApiKeyModal({ open: false, provider: null })}>
              Cancel
            </Button>
            <Button onClick={handleSaveApiKey} disabled={!apiKeyValue.trim() || saving}>
              {saving ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                "Save & Connect"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Custom Integration Modal */}
      <CreateCustomIntegrationModal
        isOpen={isCustomIntegrationModalOpen}
        onClose={() => {
          setIsCustomIntegrationModalOpen(false);
          setEditingCustomIntegration(null);
        }}
        editingIntegration={editingCustomIntegration}
        onSave={(integration) => {
          fetchProviders();
          setIsCustomIntegrationModalOpen(false);
          setEditingCustomIntegration(null);
        }}
      />
    </div>
  );
};

export default Settings;
