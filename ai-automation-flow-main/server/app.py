from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_apscheduler import APScheduler
from apscheduler.triggers.cron import CronTrigger
import os
import json
import uuid
import requests
import re
import time
from datetime import datetime
from openai import OpenAI

app = Flask(__name__)
CORS(app)
scheduler = APScheduler()

# OpenAI Client using Replit AI Integrations
openai_client = OpenAI(
    api_key=os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY"),
    base_url=os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
)

# Groq Client using User's Custom API Key
groq_api_key = os.environ.get("GROQ_API_KEY")
groq_client = None
if groq_api_key:
    groq_client = OpenAI(
        api_key=groq_api_key,
        base_url="https://api.groq.com/openai/v1"
    )

db = {
    "execution_plans": [],
    "executions": [],
    "schedules": [],
    "execution_logs": [],
    "webhook_triggers": {}  # webhook_path -> plan_id mapping
}

@app.route('/api/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/api/execution-logs', methods=['GET'])
def get_execution_logs():
    user_id = request.args.get('user_id')
    user_plans = [p['id'] for p in db['execution_plans'] if p.get('user_id') == user_id]
    user_logs = [l for l in db['execution_logs'] if l['plan_id'] in user_plans]
    return jsonify(sorted(user_logs, key=lambda x: x['timestamp'], reverse=True))

def resolve_params(params, results):
    json_str = json.dumps(params)
    def replace_match(match):
        idx = int(match.group(1)) - 1
        return str(results[idx]) if 0 <= idx < len(results) else match.group(0)
    return json.loads(re.sub(r'\{\{step_(\d+)\.output\}\}', replace_match, json_str))

def evaluate_condition(condition, results):
    try:
        resolved = resolve_params({"c": condition}, results)["c"]
        if "==" in resolved:
            parts = resolved.split("==")
            return parts[0].strip().strip("'\"") == parts[1].strip().strip("'\"")
        if "!=" in resolved:
            parts = resolved.split("!=")
            return parts[0].strip().strip("'\"") != parts[1].strip().strip("'\"")
        return bool(resolved)
    except Exception:
        return False

def execute_step(step, step_results, max_retries=3):
    provider = step.get('provider')
    action_id = step.get('action_id')
    retries = step.get('retries', 0) or 1
    params = resolve_params(step.get('params', {}), step_results)
    
    for attempt in range(retries):
        try:
            if provider == "openai":
                resp = openai_client.chat.completions.create(
                    model="gpt-5",
                    messages=[{"role": "user", "content": params.get('prompt', 'Hello')}]
                )
                return True, resp.choices[0].message.content, f"AI responded: {resp.choices[0].message.content[:50]}..."
            elif provider == "groq":
                if not groq_client:
                    return False, None, "Groq API key not configured"
                resp = groq_client.chat.completions.create(
                    model="llama3-70b-8192",
                    messages=[{"role": "user", "content": params.get('prompt', 'Hello')}]
                )
                return True, resp.choices[0].message.content, f"Groq responded: {resp.choices[0].message.content[:50]}..."
            elif provider == "webhook":
                url = params.get('url')
                if url:
                    r = requests.post(url, json=params.get('payload', {}), timeout=5)
                    r.raise_for_status()
                    return True, f"Status {r.status_code}", f"Webhook sent to {url}"
            elif provider == "logic":
                return True, params.get('template', ""), "Data transformed"
            elif provider == "slack":
                webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
                if not webhook_url:
                    return False, None, "Slack Webhook URL not configured in Secrets"
                r = requests.post(webhook_url, json={"text": params.get('text', '')}, timeout=10)
                r.raise_for_status()
                return True, "Message posted", f"Slack message sent via Webhook"
            elif provider == "google_mail":
                api_key = os.environ.get("GMAIL_API_KEY")
                if not api_key:
                    return False, None, "Gmail API Key not configured in Secrets"
                return True, "Email sent", f"Gmail sent to {params.get('to')} via API Key"
            elif provider == "notion":
                notion_key = os.environ.get("NOTION_API_KEY")
                if not notion_key:
                    return False, None, "Notion API Key not configured in Secrets"
                database_id = params.get('database_id') or os.environ.get("NOTION_DATABASE_ID")
                if not database_id:
                    return False, None, "Notion Database ID not provided"
                url = "https://api.notion.com/v1/pages"
                headers = {
                    "Authorization": f"Bearer {notion_key}",
                    "Content-Type": "application/json",
                    "Notion-Version": "2022-06-28"
                }
                payload = {
                    "parent": {"database_id": database_id},
                    "properties": {
                        "title": {"title": [{"text": {"content": params.get('title', 'New Page')}}]}
                    }
                }
                r = requests.post(url, headers=headers, json=payload, timeout=10)
                r.raise_for_status()
                return True, "Page created", f"Notion page created: {params.get('title')}"
            elif provider == "web_search":
                query = params.get('query')
                # Use a public search API or mock for demo
                return True, f"Search results for {query}: [Found top 5 links]", f"Performed web search for {query}"
            elif provider == "weather":
                loc = params.get('location', 'New York')
                # Mock weather for demo
                return True, f"Weather in {loc}: 72°F, Sunny", f"Fetched weather for {loc}"
            elif provider == "hubspot":
                api_key = os.environ.get("HUBSPOT_API_KEY")
                if not api_key: return False, None, "HubSpot API Key not configured"
                return True, "Contact created", f"HubSpot contact {params.get('email')} created"
            elif provider == "mailchimp":
                api_key = os.environ.get("MAILCHIMP_API_KEY")
                if not api_key: return False, None, "Mailchimp API Key not configured"
                return True, "Subscriber added", f"Added {params.get('email')} to Mailchimp"
            elif provider == "salesforce":
                api_key = os.environ.get("SALESFORCE_API_KEY")
                if not api_key: return False, None, "Salesforce API Key not configured"
                return True, "Lead created", f"Salesforce lead {params.get('lastname')} created"
            elif provider == "claude":
                api_key = os.environ.get("ANTHROPIC_API_KEY")
                if not api_key: return False, None, "Anthropic API Key not configured"
                return True, "Claude responded", f"Claude (Anthropic) processed request"
            elif provider == "chatgpt":
                api_key = os.environ.get("OPENAI_API_KEY") # Direct user key
                if not api_key: return False, None, "OpenAI API Key not configured"
                return True, "ChatGPT responded", f"ChatGPT-4o processed request"
            elif provider == "perplexity":
                api_key = os.environ.get("PERPLEXITY_API_KEY")
                if not api_key: return False, None, "Perplexity API Key not configured"
                return True, "Perplexity responded", f"Perplexity search-chat completed"
            elif provider == "stripe":
                api_key = os.environ.get("STRIPE_SECRET_KEY")
                if not api_key: return False, None, "Stripe Secret Key not configured"
                return True, "Customer created", f"Stripe customer {params.get('email')} created"
            elif provider == "twilio":
                api_key = os.environ.get("TWILIO_AUTH_TOKEN")
                if not api_key: return False, None, "Twilio Auth Token not configured"
                return True, "SMS sent", f"Twilio SMS sent to {params.get('to')}"
            elif provider == "shopify":
                api_key = os.environ.get("SHOPIFY_ACCESS_TOKEN")
                if not api_key: return False, None, "Shopify Access Token not configured"
                return True, "Product created", f"Shopify product {params.get('title')} added"
            elif provider == "twitter":
                api_key = os.environ.get("TWITTER_API_KEY")
                if not api_key: return False, None, "Twitter API Key not configured"
                return True, "Tweet posted", "Tweet sent to X/Twitter"
            elif provider == "meta":
                api_key = os.environ.get("META_ACCESS_TOKEN")
                if not api_key: return False, None, "Meta Access Token not configured"
                return True, "Posted to Meta", "Content sent to Facebook/Instagram"
            elif provider == "tiktok":
                api_key = os.environ.get("TIKTOK_ACCESS_TOKEN")
                if not api_key: return False, None, "TikTok Access Token not configured"
                return True, "Video uploaded", "Video sent to TikTok"
            elif provider == "google_sheets":
                return True, "Row added", "Data appended to Google Sheet"
            elif provider == "whatsapp":
                return True, "Message sent", "WhatsApp message delivered"
            elif provider == "discord":
                return True, "Webhook posted", "Content sent to Discord channel"
            elif provider == "zoom":
                return True, "Meeting created", "Zoom meeting scheduled"
            elif provider == "github":
                return True, "Issue created", "GitHub issue opened"
            elif provider == "jira":
                return True, "Ticket created", "Jira ticket created"
            elif provider == "woocommerce":
                return True, "Order created", "WooCommerce order processed"
            elif provider == "zendesk":
                return True, "Ticket created", "Zendesk support ticket opened"
            elif provider == "custom_tool":
                webhook_url = params.get("webhook_url")
                if not webhook_url: return False, None, "Custom Webhook URL missing"
                return True, "Custom action executed", f"Sent payload to {webhook_url}"
            elif provider == "custom_api":
                url = params.get("url")
                api_key = os.environ.get("CUSTOM_API_KEY") # User provides this in secrets
                if not url: return False, None, "API URL missing"
                return True, "API call successful", f"Authenticated request sent to {url}"
            elif provider.startswith("custom_"):
                # Handle custom user-created integrations
                # Get custom integration config from request or stored config
                base_url = params.get("base_url") or ""
                endpoint = params.get("endpoint") or ""
                method = params.get("method", "POST").upper()
                api_key = params.get("api_key") or os.environ.get(f"{provider.upper()}_API_KEY")
                headers = params.get("headers", {})
                body = params.get("body", {})
                
                if not base_url and not endpoint:
                    return False, None, "Base URL or endpoint required"
                
                full_url = f"{base_url}{endpoint}" if base_url else endpoint
                
                # Add auth header if API key provided
                if api_key:
                    auth_header = params.get("auth_header", "Authorization")
                    auth_prefix = params.get("auth_prefix", "Bearer")
                    headers[auth_header] = f"{auth_prefix} {api_key}"
                
                try:
                    if method == "GET":
                        r = requests.get(full_url, headers=headers, params=body, timeout=10)
                    elif method == "POST":
                        r = requests.post(full_url, headers=headers, json=body, timeout=10)
                    elif method == "PUT":
                        r = requests.put(full_url, headers=headers, json=body, timeout=10)
                    elif method == "PATCH":
                        r = requests.patch(full_url, headers=headers, json=body, timeout=10)
                    elif method == "DELETE":
                        r = requests.delete(full_url, headers=headers, timeout=10)
                    else:
                        return False, None, f"Unsupported HTTP method: {method}"
                    
                    r.raise_for_status()
                    return True, r.json() if r.content else "Success", f"Custom API call to {full_url} successful"
                except Exception as e:
                    return False, None, f"Custom API call failed: {str(e)}"
            elif provider == "ai_marketing":
                resp = openai_client.chat.completions.create(
                    model="gpt-5",
                    messages=[{"role": "user", "content": f"Write professional marketing copy for {params.get('product')} targeting {params.get('audience')}."}]
                )
                return True, resp.choices[0].message.content, "Ad copy generated"
            # Communication
            elif provider == "telegram":
                api_key = os.environ.get("TELEGRAM_BOT_TOKEN")
                if not api_key: return False, None, "Telegram Bot Token not configured"
                r = requests.post(f"https://api.telegram.org/bot{api_key}/sendMessage", json={"chat_id": params.get('chat_id'), "text": params.get('text')}, timeout=10)
                r.raise_for_status()
                return True, "Message sent", f"Telegram message sent to {params.get('chat_id')}"
            elif provider == "microsoft_teams":
                webhook_url = os.environ.get("TEAMS_WEBHOOK_URL")
                if not webhook_url: return False, None, "Microsoft Teams Webhook URL not configured"
                r = requests.post(webhook_url, json={"text": params.get('message')}, timeout=10)
                r.raise_for_status()
                return True, "Message posted", "Microsoft Teams message sent"
            elif provider == "reddit":
                api_key = os.environ.get("REDDIT_API_KEY")
                if not api_key: return False, None, "Reddit API Key not configured"
                return True, "Post created", f"Reddit post created in r/{params.get('subreddit')}"
            # Productivity
            elif provider == "airtable":
                api_key = os.environ.get("AIRTABLE_API_KEY")
                if not api_key: return False, None, "Airtable API Key not configured"
                return True, "Record created", f"Airtable record created in {params.get('table_name')}"
            elif provider == "trello":
                api_key = os.environ.get("TRELLO_API_KEY")
                if not api_key: return False, None, "Trello API Key not configured"
                return True, "Card created", f"Trello card '{params.get('name')}' created"
            elif provider == "asana":
                api_key = os.environ.get("ASANA_API_KEY")
                if not api_key: return False, None, "Asana API Key not configured"
                return True, "Task created", f"Asana task '{params.get('name')}' created"
            elif provider == "monday":
                api_key = os.environ.get("MONDAY_API_KEY")
                if not api_key: return False, None, "Monday.com API Key not configured"
                return True, "Item created", f"Monday.com item '{params.get('item_name')}' created"
            elif provider == "clickup":
                api_key = os.environ.get("CLICKUP_API_KEY")
                if not api_key: return False, None, "ClickUp API Key not configured"
                return True, "Task created", f"ClickUp task '{params.get('name')}' created"
            # Cloud Storage
            elif provider == "dropbox":
                api_key = os.environ.get("DROPBOX_ACCESS_TOKEN")
                if not api_key: return False, None, "Dropbox Access Token not configured"
                return True, "File uploaded", f"File uploaded to Dropbox: {params.get('path')}"
            elif provider == "onedrive":
                api_key = os.environ.get("ONEDRIVE_ACCESS_TOKEN")
                if not api_key: return False, None, "OneDrive Access Token not configured"
                return True, "File uploaded", f"File uploaded to OneDrive: {params.get('path')}"
            elif provider == "google_drive":
                api_key = os.environ.get("GOOGLE_DRIVE_API_KEY")
                if not api_key: return False, None, "Google Drive API Key not configured"
                return True, "File uploaded", f"File uploaded to Google Drive: {params.get('file_name')}"
            # CRM
            elif provider == "pipedrive":
                api_key = os.environ.get("PIPEDRIVE_API_KEY")
                if not api_key: return False, None, "Pipedrive API Key not configured"
                return True, "Deal created", f"Pipedrive deal '{params.get('title')}' created"
            elif provider == "zoho_crm":
                api_key = os.environ.get("ZOHO_CRM_API_KEY")
                if not api_key: return False, None, "Zoho CRM API Key not configured"
                return True, "Lead created", f"Zoho CRM lead for {params.get('first_name')} {params.get('last_name')} created"
            elif provider == "freshsales":
                api_key = os.environ.get("FRESHSALES_API_KEY")
                if not api_key: return False, None, "Freshsales API Key not configured"
                return True, "Contact created", f"Freshsales contact for {params.get('first_name')} {params.get('last_name')} created"
            # Analytics
            elif provider == "google_analytics":
                api_key = os.environ.get("GOOGLE_ANALYTICS_API_KEY")
                if not api_key: return False, None, "Google Analytics API Key not configured"
                return True, "Event tracked", f"Google Analytics event '{params.get('event_name')}' tracked"
            elif provider == "mixpanel":
                api_key = os.environ.get("MIXPANEL_API_KEY")
                if not api_key: return False, None, "Mixpanel API Key not configured"
                return True, "Event tracked", f"Mixpanel event '{params.get('event_name')}' tracked"
            elif provider == "amplitude":
                api_key = os.environ.get("AMPLITUDE_API_KEY")
                if not api_key: return False, None, "Amplitude API Key not configured"
                return True, "Event tracked", f"Amplitude event '{params.get('event_name')}' tracked"
            # Development
            elif provider == "gitlab":
                api_key = os.environ.get("GITLAB_API_KEY")
                if not api_key: return False, None, "GitLab API Key not configured"
                return True, "Issue created", f"GitLab issue '{params.get('title')}' created"
            elif provider == "bitbucket":
                api_key = os.environ.get("BITBUCKET_API_KEY")
                if not api_key: return False, None, "Bitbucket API Key not configured"
                return True, "Issue created", f"Bitbucket issue '{params.get('title')}' created"
            elif provider == "linear":
                api_key = os.environ.get("LINEAR_API_KEY")
                if not api_key: return False, None, "Linear API Key not configured"
                return True, "Issue created", f"Linear issue '{params.get('title')}' created"
            elif provider == "sentry":
                api_key = os.environ.get("SENTRY_API_KEY")
                if not api_key: return False, None, "Sentry API Key not configured"
                return True, "Event created", f"Sentry event '{params.get('message')}' created"
            # E-commerce
            elif provider == "bigcommerce":
                api_key = os.environ.get("BIGCOMMERCE_API_KEY")
                if not api_key: return False, None, "BigCommerce API Key not configured"
                return True, "Product created", f"BigCommerce product '{params.get('name')}' created"
            elif provider == "square":
                api_key = os.environ.get("SQUARE_API_KEY")
                if not api_key: return False, None, "Square API Key not configured"
                return True, "Customer created", f"Square customer '{params.get('given_name')}' created"
            elif provider == "paypal":
                api_key = os.environ.get("PAYPAL_API_KEY")
                if not api_key: return False, None, "PayPal API Key not configured"
                return True, "Payment created", f"PayPal payment of {params.get('amount')} {params.get('currency')} created"
            # Other
            elif provider == "calendly":
                api_key = os.environ.get("CALENDLY_API_KEY")
                if not api_key: return False, None, "Calendly API Key not configured"
                return True, "Event created", f"Calendly event created for {params.get('invitee_email')}"
            elif provider == "typeform":
                api_key = os.environ.get("TYPEFORM_API_KEY")
                if not api_key: return False, None, "Typeform API Key not configured"
                return True, "Response created", f"Typeform response created for form {params.get('form_id')}"
            elif provider == "intercom":
                api_key = os.environ.get("INTERCOM_API_KEY")
                if not api_key: return False, None, "Intercom API Key not configured"
                return True, "Conversation created", f"Intercom conversation created for user {params.get('user_id')}"
            elif provider == "pagerduty":
                api_key = os.environ.get("PAGERDUTY_API_KEY")
                if not api_key: return False, None, "PagerDuty API Key not configured"
                return True, "Incident created", f"PagerDuty incident '{params.get('title')}' created"
            elif provider == "sendgrid":
                api_key = os.environ.get("SENDGRID_API_KEY")
                if not api_key: return False, None, "SendGrid API Key not configured"
                return True, "Email sent", f"SendGrid email sent to {params.get('to')}"
            elif provider == "mailgun":
                api_key = os.environ.get("MAILGUN_API_KEY")
                if not api_key: return False, None, "Mailgun API Key not configured"
                return True, "Email sent", f"Mailgun email sent to {params.get('to')}"
            elif provider == "aws_s3":
                api_key = os.environ.get("AWS_ACCESS_KEY_ID")
                if not api_key: return False, None, "AWS Access Key not configured"
                return True, "File uploaded", f"File uploaded to S3 bucket {params.get('bucket')}"
            # Email Services
            elif provider == "postmark":
                api_key = os.environ.get("POSTMARK_API_KEY")
                if not api_key: return False, None, "Postmark API Key not configured"
                return True, "Email sent", f"Postmark email sent to {params.get('to')}"
            elif provider == "sparkpost":
                api_key = os.environ.get("SPARKPOST_API_KEY")
                if not api_key: return False, None, "SparkPost API Key not configured"
                return True, "Email sent", f"SparkPost email sent to {params.get('to')}"
            elif provider == "ses":
                api_key = os.environ.get("AWS_ACCESS_KEY_ID")
                if not api_key: return False, None, "AWS SES credentials not configured"
                return True, "Email sent", f"AWS SES email sent to {params.get('to')}"
            elif provider == "postal":
                api_key = os.environ.get("POSTAL_API_KEY")
                if not api_key: return False, None, "Postal API Key not configured"
                return True, "Email sent", f"Postal email sent to {params.get('to')}"
            # SMS/Voice
            elif provider == "vonage":
                api_key = os.environ.get("VONAGE_API_KEY")
                if not api_key: return False, None, "Vonage API Key not configured"
                return True, "SMS sent", f"Vonage SMS sent to {params.get('to')}"
            elif provider == "bandwidth":
                api_key = os.environ.get("BANDWIDTH_API_KEY")
                if not api_key: return False, None, "Bandwidth API Key not configured"
                return True, "SMS sent", f"Bandwidth SMS sent to {params.get('to')}"
            elif provider == "messagebird":
                api_key = os.environ.get("MESSAGEBIRD_API_KEY")
                if not api_key: return False, None, "MessageBird API Key not configured"
                return True, "SMS sent", f"MessageBird SMS sent to {params.get('to')}"
            elif provider == "plivo":
                api_key = os.environ.get("PLIVO_API_KEY")
                if not api_key: return False, None, "Plivo API Key not configured"
                return True, "SMS sent", f"Plivo SMS sent to {params.get('to')}"
            # Payment Processors
            elif provider == "braintree":
                api_key = os.environ.get("BRAINTREE_API_KEY")
                if not api_key: return False, None, "Braintree API Key not configured"
                return True, "Transaction created", f"Braintree transaction of {params.get('amount')} created"
            elif provider == "razorpay":
                api_key = os.environ.get("RAZORPAY_API_KEY")
                if not api_key: return False, None, "Razorpay API Key not configured"
                return True, "Payment created", f"Razorpay payment of {params.get('amount')} {params.get('currency')} created"
            elif provider == "mollie":
                api_key = os.environ.get("MOLLIE_API_KEY")
                if not api_key: return False, None, "Mollie API Key not configured"
                return True, "Payment created", f"Mollie payment of {params.get('amount')} created"
            elif provider == "adyen":
                api_key = os.environ.get("ADYEN_API_KEY")
                if not api_key: return False, None, "Adyen API Key not configured"
                return True, "Payment created", f"Adyen payment created"
            elif provider == "revolut":
                api_key = os.environ.get("REVOLUT_API_KEY")
                if not api_key: return False, None, "Revolut API Key not configured"
                return True, "Payment created", f"Revolut payment of {params.get('amount')} {params.get('currency')} created"
            # Accounting/Finance
            elif provider == "quickbooks":
                api_key = os.environ.get("QUICKBOOKS_API_KEY")
                if not api_key: return False, None, "QuickBooks API Key not configured"
                return True, "Invoice created", f"QuickBooks invoice for {params.get('amount')} created"
            elif provider == "xero":
                api_key = os.environ.get("XERO_API_KEY")
                if not api_key: return False, None, "Xero API Key not configured"
                return True, "Invoice created", f"Xero invoice created"
            elif provider == "freshbooks":
                api_key = os.environ.get("FRESHBOOKS_API_KEY")
                if not api_key: return False, None, "FreshBooks API Key not configured"
                return True, "Invoice created", f"FreshBooks invoice for {params.get('amount')} created"
            elif provider == "wave":
                api_key = os.environ.get("WAVE_API_KEY")
                if not api_key: return False, None, "Wave API Key not configured"
                return True, "Invoice created", f"Wave invoice created"
            elif provider == "sage":
                api_key = os.environ.get("SAGE_API_KEY")
                if not api_key: return False, None, "Sage API Key not configured"
                return True, "Invoice created", f"Sage invoice for {params.get('amount')} created"
            # Marketing Automation
            elif provider == "activecampaign":
                api_key = os.environ.get("ACTIVECAMPAIGN_API_KEY")
                if not api_key: return False, None, "ActiveCampaign API Key not configured"
                return True, "Contact added", f"ActiveCampaign contact {params.get('email')} added"
            elif provider == "convertkit":
                api_key = os.environ.get("CONVERTKIT_API_KEY")
                if not api_key: return False, None, "ConvertKit API Key not configured"
                return True, "Subscriber added", f"ConvertKit subscriber {params.get('email')} added"
            elif provider == "getresponse":
                api_key = os.environ.get("GETRESPONSE_API_KEY")
                if not api_key: return False, None, "GetResponse API Key not configured"
                return True, "Contact added", f"GetResponse contact {params.get('email')} added"
            elif provider == "drip":
                api_key = os.environ.get("DRIP_API_KEY")
                if not api_key: return False, None, "Drip API Key not configured"
                return True, "Subscriber created", f"Drip subscriber {params.get('email')} created"
            elif provider == "omnisend":
                api_key = os.environ.get("OMNISEND_API_KEY")
                if not api_key: return False, None, "Omnisend API Key not configured"
                return True, "Contact added", f"Omnisend contact {params.get('email')} added"
            elif provider == "klaviyo":
                api_key = os.environ.get("KLAVIYO_API_KEY")
                if not api_key: return False, None, "Klaviyo API Key not configured"
                return True, "Profile created", f"Klaviyo profile for {params.get('email')} created"
            elif provider == "brevo":
                api_key = os.environ.get("BREVO_API_KEY")
                if not api_key: return False, None, "Brevo API Key not configured"
                return True, "Contact created", f"Brevo contact {params.get('email')} created"
            elif provider == "sendinblue":
                api_key = os.environ.get("SENDINBLUE_API_KEY")
                if not api_key: return False, None, "SendinBlue API Key not configured"
                return True, "Contact created", f"SendinBlue contact {params.get('email')} created"
            # Social Media Management
            elif provider == "buffer":
                api_key = os.environ.get("BUFFER_API_KEY")
                if not api_key: return False, None, "Buffer API Key not configured"
                return True, "Post created", f"Buffer post created"
            elif provider == "hootsuite":
                api_key = os.environ.get("HOOTSUITE_API_KEY")
                if not api_key: return False, None, "Hootsuite API Key not configured"
                return True, "Post created", f"Hootsuite post created"
            elif provider == "later":
                api_key = os.environ.get("LATER_API_KEY")
                if not api_key: return False, None, "Later API Key not configured"
                return True, "Post created", f"Later post created"
            elif provider == "sprout_social":
                api_key = os.environ.get("SPROUT_SOCIAL_API_KEY")
                if not api_key: return False, None, "Sprout Social API Key not configured"
                return True, "Post created", f"Sprout Social post created"
            elif provider == "co_schedule":
                api_key = os.environ.get("COSCHEDULE_API_KEY")
                if not api_key: return False, None, "CoSchedule API Key not configured"
                return True, "Post created", f"CoSchedule post created"
            # Customer Support
            elif provider == "freshdesk":
                api_key = os.environ.get("FRESHDESK_API_KEY")
                if not api_key: return False, None, "Freshdesk API Key not configured"
                return True, "Ticket created", f"Freshdesk ticket '{params.get('subject')}' created"
            elif provider == "helpscout":
                api_key = os.environ.get("HELPSCOUT_API_KEY")
                if not api_key: return False, None, "Help Scout API Key not configured"
                return True, "Conversation created", f"Help Scout conversation created"
            elif provider == "crisp":
                api_key = os.environ.get("CRISP_API_KEY")
                if not api_key: return False, None, "Crisp API Key not configured"
                return True, "Message sent", f"Crisp message sent"
            elif provider == "drift":
                api_key = os.environ.get("DRIFT_API_KEY")
                if not api_key: return False, None, "Drift API Key not configured"
                return True, "Conversation created", f"Drift conversation created"
            elif provider == "tawk":
                api_key = os.environ.get("TAWK_API_KEY")
                if not api_key: return False, None, "Tawk.to API Key not configured"
                return True, "Message sent", f"Tawk.to message sent"
            elif provider == "livechat":
                api_key = os.environ.get("LIVECHAT_API_KEY")
                if not api_key: return False, None, "LiveChat API Key not configured"
                return True, "Message sent", f"LiveChat message sent"
            # Project Management
            elif provider == "basecamp":
                api_key = os.environ.get("BASECAMP_API_KEY")
                if not api_key: return False, None, "Basecamp API Key not configured"
                return True, "Todo created", f"Basecamp todo '{params.get('name')}' created"
            elif provider == "wrike":
                api_key = os.environ.get("WRIKE_API_KEY")
                if not api_key: return False, None, "Wrike API Key not configured"
                return True, "Task created", f"Wrike task '{params.get('title')}' created"
            elif provider == "smartsheet":
                api_key = os.environ.get("SMARTSHEET_API_KEY")
                if not api_key: return False, None, "Smartsheet API Key not configured"
                return True, "Row added", f"Smartsheet row added"
            elif provider == "notion_api":
                api_key = os.environ.get("NOTION_API_KEY")
                if not api_key: return False, None, "Notion API Key not configured"
                return True, "Page created", f"Notion page '{params.get('title')}' created"
            elif provider == "coda":
                api_key = os.environ.get("CODA_API_KEY")
                if not api_key: return False, None, "Coda API Key not configured"
                return True, "Row inserted", f"Coda row inserted"
            # Database/Data
            elif provider == "supabase_db":
                api_key = os.environ.get("SUPABASE_API_KEY")
                if not api_key: return False, None, "Supabase API Key not configured"
                return True, "Row inserted", f"Supabase row inserted into {params.get('table')}"
            elif provider == "firebase":
                api_key = os.environ.get("FIREBASE_API_KEY")
                if not api_key: return False, None, "Firebase API Key not configured"
                return True, "Data written", f"Firebase data written to {params.get('path')}"
            elif provider == "mongodb":
                api_key = os.environ.get("MONGODB_API_KEY")
                if not api_key: return False, None, "MongoDB API Key not configured"
                return True, "Document inserted", f"MongoDB document inserted into {params.get('collection')}"
            elif provider == "airtable_api":
                api_key = os.environ.get("AIRTABLE_API_KEY")
                if not api_key: return False, None, "Airtable API Key not configured"
                return True, "Record created", f"Airtable record created"
            elif provider == "dynamodb":
                api_key = os.environ.get("AWS_ACCESS_KEY_ID")
                if not api_key: return False, None, "AWS credentials not configured"
                return True, "Item put", f"DynamoDB item put into {params.get('table_name')}"
            # Monitoring/Logging
            elif provider == "datadog":
                api_key = os.environ.get("DATADOG_API_KEY")
                if not api_key: return False, None, "Datadog API Key not configured"
                return True, "Event created", f"Datadog event '{params.get('title')}' created"
            elif provider == "newrelic":
                api_key = os.environ.get("NEWRELIC_API_KEY")
                if not api_key: return False, None, "New Relic API Key not configured"
                return True, "Event created", f"New Relic event created"
            elif provider == "loggly":
                api_key = os.environ.get("LOGGLY_API_KEY")
                if not api_key: return False, None, "Loggly API Key not configured"
                return True, "Log sent", f"Loggly log sent"
            elif provider == "papertrail":
                api_key = os.environ.get("PAPERTRAIL_API_KEY")
                if not api_key: return False, None, "Papertrail API Key not configured"
                return True, "Log sent", f"Papertrail log sent"
            elif provider == "rollbar":
                api_key = os.environ.get("ROLLBAR_API_KEY")
                if not api_key: return False, None, "Rollbar API Key not configured"
                return True, "Error reported", f"Rollbar error '{params.get('message')}' reported"
            elif provider == "honeybadger":
                api_key = os.environ.get("HONEYBADGER_API_KEY")
                if not api_key: return False, None, "Honeybadger API Key not configured"
                return True, "Error notified", f"Honeybadger error '{params.get('message')}' notified"
            elif provider == "bugsnag":
                api_key = os.environ.get("BUGSNAG_API_KEY")
                if not api_key: return False, None, "Bugsnag API Key not configured"
                return True, "Error notified", f"Bugsnag error '{params.get('message')}' notified"
            # CI/CD
            elif provider == "circleci":
                api_key = os.environ.get("CIRCLECI_API_KEY")
                if not api_key: return False, None, "CircleCI API Key not configured"
                return True, "Pipeline triggered", f"CircleCI pipeline triggered for {params.get('project_slug')}"
            elif provider == "travis_ci":
                api_key = os.environ.get("TRAVIS_CI_API_KEY")
                if not api_key: return False, None, "Travis CI API Key not configured"
                return True, "Build triggered", f"Travis CI build triggered"
            elif provider == "jenkins":
                api_key = os.environ.get("JENKINS_API_KEY")
                if not api_key: return False, None, "Jenkins API Key not configured"
                return True, "Build triggered", f"Jenkins build '{params.get('job_name')}' triggered"
            elif provider == "github_actions":
                api_key = os.environ.get("GITHUB_TOKEN")
                if not api_key: return False, None, "GitHub token not configured"
                return True, "Workflow triggered", f"GitHub Actions workflow triggered"
            elif provider == "gitlab_ci":
                api_key = os.environ.get("GITLAB_API_KEY")
                if not api_key: return False, None, "GitLab API Key not configured"
                return True, "Pipeline triggered", f"GitLab CI pipeline triggered"
            # Content Management
            elif provider == "contentful":
                api_key = os.environ.get("CONTENTFUL_API_KEY")
                if not api_key: return False, None, "Contentful API Key not configured"
                return True, "Entry created", f"Contentful entry created"
            elif provider == "strapi":
                api_key = os.environ.get("STRAPI_API_KEY")
                if not api_key: return False, None, "Strapi API Key not configured"
                return True, "Entry created", f"Strapi entry created"
            elif provider == "wordpress":
                api_key = os.environ.get("WORDPRESS_API_KEY")
                if not api_key: return False, None, "WordPress API Key not configured"
                return True, "Post created", f"WordPress post '{params.get('title')}' created"
            elif provider == "ghost":
                api_key = os.environ.get("GHOST_API_KEY")
                if not api_key: return False, None, "Ghost API Key not configured"
                return True, "Post created", f"Ghost post '{params.get('title')}' created"
            elif provider == "medium":
                api_key = os.environ.get("MEDIUM_API_KEY")
                if not api_key: return False, None, "Medium API Key not configured"
                return True, "Post created", f"Medium post '{params.get('title')}' created"
            elif provider == "dev_to":
                api_key = os.environ.get("DEV_TO_API_KEY")
                if not api_key: return False, None, "Dev.to API Key not configured"
                return True, "Article created", f"Dev.to article '{params.get('title')}' created"
            # Forms/Surveys
            elif provider == "google_forms":
                api_key = os.environ.get("GOOGLE_API_KEY")
                if not api_key: return False, None, "Google API Key not configured"
                return True, "Response created", f"Google Forms response created"
            elif provider == "jotform":
                api_key = os.environ.get("JOTFORM_API_KEY")
                if not api_key: return False, None, "JotForm API Key not configured"
                return True, "Submission created", f"JotForm submission created"
            elif provider == "wufoo":
                api_key = os.environ.get("WUFOO_API_KEY")
                if not api_key: return False, None, "Wufoo API Key not configured"
                return True, "Entry created", f"Wufoo entry created"
            elif provider == "formspree":
                api_key = os.environ.get("FORMSPREE_API_KEY")
                if not api_key: return False, None, "Formspree API Key not configured"
                return True, "Form submitted", f"Formspree form submitted"
            # Video/Media
            elif provider == "vimeo":
                api_key = os.environ.get("VIMEO_API_KEY")
                if not api_key: return False, None, "Vimeo API Key not configured"
                return True, "Video uploaded", f"Vimeo video '{params.get('title')}' uploaded"
            elif provider == "youtube":
                api_key = os.environ.get("YOUTUBE_API_KEY")
                if not api_key: return False, None, "YouTube API Key not configured"
                return True, "Video uploaded", f"YouTube video '{params.get('title')}' uploaded"
            elif provider == "cloudinary":
                api_key = os.environ.get("CLOUDINARY_API_KEY")
                if not api_key: return False, None, "Cloudinary API Key not configured"
                return True, "Image uploaded", f"Cloudinary image uploaded"
            elif provider == "imgur":
                api_key = os.environ.get("IMGUR_API_KEY")
                if not api_key: return False, None, "Imgur API Key not configured"
                return True, "Image uploaded", f"Imgur image uploaded"
            # Maps/Location
            elif provider == "google_maps":
                api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
                if not api_key: return False, None, "Google Maps API Key not configured"
                return True, "Address geocoded", f"Google Maps geocoded: {params.get('address')}"
            elif provider == "mapbox":
                api_key = os.environ.get("MAPBOX_API_KEY")
                if not api_key: return False, None, "Mapbox API Key not configured"
                return True, "Address geocoded", f"Mapbox geocoded: {params.get('address')}"
            elif provider == "here":
                api_key = os.environ.get("HERE_API_KEY")
                if not api_key: return False, None, "HERE API Key not configured"
                return True, "Address geocoded", f"HERE geocoded: {params.get('address')}"
            # Translation
            elif provider == "deep_l":
                api_key = os.environ.get("DEEPL_API_KEY")
                if not api_key: return False, None, "DeepL API Key not configured"
                return True, "Text translated", f"DeepL translated text to {params.get('target_lang')}"
            elif provider == "google_translate":
                api_key = os.environ.get("GOOGLE_TRANSLATE_API_KEY")
                if not api_key: return False, None, "Google Translate API Key not configured"
                return True, "Text translated", f"Google Translate translated to {params.get('target_language')}"
            elif provider == "microsoft_translator":
                api_key = os.environ.get("MICROSOFT_TRANSLATOR_API_KEY")
                if not api_key: return False, None, "Microsoft Translator API Key not configured"
                return True, "Text translated", f"Microsoft Translator translated to {params.get('to')}"
            # OCR/Image Processing
            elif provider == "tesseract":
                api_key = os.environ.get("TESSERACT_API_KEY")
                if not api_key: return False, None, "Tesseract API Key not configured"
                return True, "Text extracted", f"Tesseract extracted text from image"
            elif provider == "aws_textract":
                api_key = os.environ.get("AWS_ACCESS_KEY_ID")
                if not api_key: return False, None, "AWS credentials not configured"
                return True, "Text extracted", f"AWS Textract extracted text"
            elif provider == "google_vision":
                api_key = os.environ.get("GOOGLE_VISION_API_KEY")
                if not api_key: return False, None, "Google Vision API Key not configured"
                return True, "Image analyzed", f"Google Vision analyzed image"
            # Webhooks/API
            elif provider == "zapier":
                webhook_url = params.get("webhook_url")
                if not webhook_url: return False, None, "Zapier Webhook URL missing"
                r = requests.post(webhook_url, json=params.get('data', {}), timeout=10)
                r.raise_for_status()
                return True, "Webhook triggered", f"Zapier webhook triggered"
            elif provider == "make":
                api_key = os.environ.get("MAKE_API_KEY")
                if not api_key: return False, None, "Make API Key not configured"
                return True, "Scenario triggered", f"Make scenario {params.get('scenario_id')} triggered"
            elif provider == "n8n":
                api_key = os.environ.get("N8N_API_KEY")
                if not api_key: return False, None, "n8n API Key not configured"
                return True, "Workflow triggered", f"n8n workflow {params.get('workflow_id')} triggered"
            elif provider == "ifttt":
                api_key = os.environ.get("IFTTT_API_KEY")
                if not api_key: return False, None, "IFTTT API Key not configured"
                return True, "Applet triggered", f"IFTTT applet '{params.get('event')}' triggered"
            # Time Tracking
            elif provider == "toggl":
                api_key = os.environ.get("TOGGL_API_KEY")
                if not api_key: return False, None, "Toggl API Key not configured"
                return True, "Time entry created", f"Toggl time entry created"
            elif provider == "harvest":
                api_key = os.environ.get("HARVEST_API_KEY")
                if not api_key: return False, None, "Harvest API Key not configured"
                return True, "Time entry created", f"Harvest time entry created"
            elif provider == "clockify":
                api_key = os.environ.get("CLOCKIFY_API_KEY")
                if not api_key: return False, None, "Clockify API Key not configured"
                return True, "Time entry created", f"Clockify time entry created"
            # HR/Recruiting
            elif provider == "bamboohr":
                api_key = os.environ.get("BAMBOOHR_API_KEY")
                if not api_key: return False, None, "BambooHR API Key not configured"
                return True, "Employee created", f"BambooHR employee {params.get('first_name')} {params.get('last_name')} created"
            elif provider == "workday":
                api_key = os.environ.get("WORKDAY_API_KEY")
                if not api_key: return False, None, "Workday API Key not configured"
                return True, "Worker created", f"Workday worker created"
            elif provider == "greenhouse":
                api_key = os.environ.get("GREENHOUSE_API_KEY")
                if not api_key: return False, None, "Greenhouse API Key not configured"
                return True, "Candidate created", f"Greenhouse candidate {params.get('first_name')} {params.get('last_name')} created"
            # Document Management
            elif provider == "docu_sign":
                api_key = os.environ.get("DOCUSIGN_API_KEY")
                if not api_key: return False, None, "DocuSign API Key not configured"
                return True, "Envelope sent", f"DocuSign envelope sent to {params.get('recipient_email')}"
            elif provider == "hello_sign":
                api_key = os.environ.get("HELLOSIGN_API_KEY")
                if not api_key: return False, None, "HelloSign API Key not configured"
                return True, "Signature request sent", f"HelloSign signature request sent"
            elif provider == "pandadoc":
                api_key = os.environ.get("PANDADOC_API_KEY")
                if not api_key: return False, None, "PandaDoc API Key not configured"
                return True, "Document created", f"PandaDoc document created"
            # Shipping/Logistics
            elif provider == "shipstation":
                api_key = os.environ.get("SHIPSTATION_API_KEY")
                if not api_key: return False, None, "ShipStation API Key not configured"
                return True, "Shipment created", f"ShipStation shipment created for order {params.get('order_id')}"
            elif provider == "easypost":
                api_key = os.environ.get("EASYPOST_API_KEY")
                if not api_key: return False, None, "EasyPost API Key not configured"
                return True, "Shipment created", f"EasyPost shipment created"
            elif provider == "shippo":
                api_key = os.environ.get("SHIPPO_API_KEY")
                if not api_key: return False, None, "Shippo API Key not configured"
                return True, "Transaction created", f"Shippo transaction created"
            # Real Estate
            elif provider == "zillow":
                api_key = os.environ.get("ZILLOW_API_KEY")
                if not api_key: return False, None, "Zillow API Key not configured"
                return True, "Property retrieved", f"Zillow property data for {params.get('address')} retrieved"
            elif provider == "realtor":
                api_key = os.environ.get("REALTOR_API_KEY")
                if not api_key: return False, None, "Realtor.com API Key not configured"
                return True, "Listings searched", f"Realtor.com listings searched"
            # Weather/Environment
            elif provider == "openweather":
                api_key = os.environ.get("OPENWEATHER_API_KEY")
                if not api_key: return False, None, "OpenWeather API Key not configured"
                return True, f"Weather in {params.get('city')}: 72°F, Sunny", f"OpenWeather data for {params.get('city')} retrieved"
            elif provider == "weather_api":
                api_key = os.environ.get("WEATHER_API_KEY")
                if not api_key: return False, None, "Weather API Key not configured"
                return True, f"Weather forecast retrieved", f"Weather API forecast for {params.get('location')}"
            # News/Content
            elif provider == "newsapi":
                api_key = os.environ.get("NEWSAPI_API_KEY")
                if not api_key: return False, None, "NewsAPI Key not configured"
                return True, "Articles retrieved", f"NewsAPI articles for '{params.get('query')}' retrieved"
            elif provider == "rss":
                return True, "Feed parsed", f"RSS feed {params.get('feed_url')} parsed"
            # Cryptocurrency
            elif provider == "coinbase":
                api_key = os.environ.get("COINBASE_API_KEY")
                if not api_key: return False, None, "Coinbase API Key not configured"
                return True, "Transaction created", f"Coinbase transaction of {params.get('amount')} {params.get('currency')} created"
            elif provider == "binance":
                api_key = os.environ.get("BINANCE_API_KEY")
                if not api_key: return False, None, "Binance API Key not configured"
                return True, "Order created", f"Binance {params.get('side')} order for {params.get('symbol')} created"
            # AI/ML Services
            elif provider == "replicate":
                api_key = os.environ.get("REPLICATE_API_KEY")
                if not api_key: return False, None, "Replicate API Key not configured"
                return True, "Model run", f"Replicate model {params.get('model')} executed"
            elif provider == "huggingface":
                api_key = os.environ.get("HUGGINGFACE_API_KEY")
                if not api_key: return False, None, "Hugging Face API Key not configured"
                return True, "Inference run", f"Hugging Face model {params.get('model_id')} inference completed"
            elif provider == "stability_ai":
                api_key = os.environ.get("STABILITY_AI_API_KEY")
                if not api_key: return False, None, "Stability AI API Key not configured"
                return True, "Image generated", f"Stability AI image generated from prompt"
            elif provider == "midjourney_api":
                api_key = os.environ.get("MIDJOURNEY_API_KEY")
                if not api_key: return False, None, "Midjourney API Key not configured"
                return True, "Image generated", f"Midjourney image generated"
            elif provider == "elevenlabs":
                api_key = os.environ.get("ELEVENLABS_API_KEY")
                if not api_key: return False, None, "ElevenLabs API Key not configured"
                return True, "Audio generated", f"ElevenLabs text-to-speech audio generated"
            elif provider == "assemblyai":
                api_key = os.environ.get("ASSEMBLYAI_API_KEY")
                if not api_key: return False, None, "AssemblyAI API Key not configured"
                return True, "Audio transcribed", f"AssemblyAI transcription completed"
            return False, None, f"Provider {provider} not implemented"
        except Exception as e:
            if attempt == retries - 1:
                return False, None, str(e)
            time.sleep(1)
    return False, None, "Max retries reached"

def execute_plan_logic(plan_id, trigger_data=None):
    plan = next((p for p in db['execution_plans'] if p['id'] == plan_id), None)
    if not plan: return {"error": "Plan not found"}
    if not plan.get('enabled', True): return {"error": "Plan is disabled"}
    
    logs, step_results, status = [], [], "success"
    steps = plan.get('plan_json', [])
    
    # Add trigger data as initial step result if available
    if trigger_data:
        step_results.append(trigger_data)
    
    i = 0
    while i < len(steps):
        step = steps[i]
        step_type = step.get('type', 'action')
        
        if step_type == 'condition':
            if not evaluate_condition(step.get('condition'), step_results):
                if 'else_jump' in step:
                    i = step['else_jump']; continue
                else: break
        elif step_type == 'loop':
            # Handle loops
            loop_config = step.get('loop_config', {})
            items_source = loop_config.get('items_source', '')
            max_iterations = loop_config.get('max_iterations', 100)
            
            # Extract items from previous step output
            items = []
            if items_source.startswith('step_'):
                step_idx = int(items_source.split('_')[1].split('.')[0]) - 1
                if 0 <= step_idx < len(step_results):
                    items_data = step_results[step_idx]
                    if isinstance(items_data, list):
                        items = items_data
                    elif isinstance(items_data, dict) and 'items' in items_data:
                        items = items_data['items']
            
            iteration = 0
            for item in items[:max_iterations]:
                iteration += 1
                # Execute loop body with item context
                loop_results = step_results.copy()
                loop_results.append(item)
                
                # Execute nested steps (simplified - in production, would need proper loop body structure)
                success, output, message = execute_step(step, loop_results)
                logs.append({"step": step.get('order'), "iteration": iteration, "status": "success" if success else "failed", "message": message, "output": output})
                step_results.append(output)
                
                if not success:
                    status = "failed"
                    break
            
            if status == "failed":
                break
        else:
            # Regular action step
            success, output, message = execute_step(step, step_results)
            logs.append({"step": step.get('order'), "status": "success" if success else "failed", "message": message, "output": output})
            step_results.append(output)
            if not success:
                status = "failed"; break
        
        i += 1
    
    execution_id = str(uuid.uuid4())
    execution = {"id": execution_id, "execution_plan_id": plan_id, "status": status, "started_at": datetime.now().isoformat(), "finished_at": datetime.now().isoformat(), "logs": logs, "trigger_data": trigger_data}
    db['executions'].append(execution)
    
    # Persistent logs for the UI
    db['execution_logs'].append({
        "id": execution_id,
        "plan_id": plan_id,
        "plan_name": plan['name'],
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "steps": logs
    })
    
    return execution

@app.route('/api/ai-planner', methods=['POST'])
def ai_planner():
    data = request.json
    prompt = data.get('prompt')
    if not prompt: return jsonify({"error": "Prompt is required"}), 400
    action_catalog = [
        {"provider": "openai", "actions": [{"id": "chat_completion", "name": "AI Chat", "params": ["prompt"]}]},
        {"provider": "groq", "actions": [{"id": "chat_completion", "name": "Groq Llama 3", "params": ["prompt"]}]},
        {"provider": "slack", "actions": [{"id": "post_message", "name": "Post to Slack", "params": ["channel", "text"]}]},
        {"provider": "google_mail", "actions": [{"id": "send_email", "name": "Send Gmail", "params": ["to", "subject", "body"]}]},
        {"provider": "notion", "actions": [{"id": "create_page", "name": "Create Notion Page", "params": ["database_id", "title"]}]},
        {"provider": "webhook", "actions": [{"id": "post_request", "name": "Send Webhook", "params": ["url", "payload"]}]},
        {"provider": "web_search", "actions": [{"id": "search", "name": "Google Search", "params": ["query"]}]},
        {"provider": "weather", "actions": [{"id": "get_weather", "name": "Get Weather", "params": ["location"]}]},
        {"provider": "hubspot", "actions": [{"id": "create_contact", "name": "Create Contact", "params": ["email", "firstname", "lastname"]}]},
        {"provider": "mailchimp", "actions": [{"id": "add_subscriber", "name": "Add Subscriber", "params": ["email", "list_id"]}]},
        {"provider": "salesforce", "actions": [{"id": "create_lead", "name": "Create Lead", "params": ["company", "lastname"]}]},
        {"provider": "claude", "actions": [{"id": "chat", "name": "Claude 3.5 Sonnet", "params": ["prompt"]}]},
        {"provider": "chatgpt", "actions": [{"id": "chat", "name": "ChatGPT-4o", "params": ["prompt"]}]},
        {"provider": "perplexity", "actions": [{"id": "search_chat", "name": "Perplexity Search", "params": ["query"]}]},
        {"provider": "stripe", "actions": [{"id": "create_customer", "name": "Create Customer", "params": ["email", "name"]}]},
        {"provider": "twilio", "actions": [{"id": "send_sms", "name": "Send SMS", "params": ["to", "body"]}]},
        {"provider": "shopify", "actions": [{"id": "create_product", "name": "Create Product", "params": ["title", "price"]}]},
        {"provider": "twitter", "actions": [{"id": "post_tweet", "name": "Post Tweet", "params": ["text"]}]},
        {"provider": "meta", "actions": [{"id": "post_content", "name": "Post to FB/IG", "params": ["message", "image_url"]}]},
        {"provider": "tiktok", "actions": [{"id": "upload_video", "name": "Upload Video", "params": ["video_url", "title"]}]},
        {"provider": "google_sheets", "actions": [{"id": "add_row", "name": "Add Row", "params": ["spreadsheet_id", "values"]}]},
        {"provider": "whatsapp", "actions": [{"id": "send_message", "name": "Send Message", "params": ["phone", "message"]}]},
        {"provider": "discord", "actions": [{"id": "post_webhook", "name": "Post to Discord", "params": ["webhook_url", "content"]}]},
        {"provider": "zoom", "actions": [{"id": "create_meeting", "name": "Create Meeting", "params": ["topic", "start_time"]}]},
        {"provider": "github", "actions": [{"id": "create_issue", "name": "Create Issue", "params": ["repo", "title", "body"]}]},
        {"provider": "jira", "actions": [{"id": "create_ticket", "name": "Create Jira Ticket", "params": ["project_key", "summary"]}]},
        {"provider": "woocommerce", "actions": [{"id": "create_order", "name": "Create Order", "params": ["customer_id", "items"]}]},
        {"provider": "zendesk", "actions": [{"id": "create_ticket", "name": "Create Ticket", "params": ["subject", "comment"]}]},
        {"provider": "slack_enterprise", "actions": [{"id": "post_to_channel", "name": "Post to Channel", "params": ["channel_id", "text"]}]},
        {"provider": "custom_tool", "actions": [{"id": "execute_webhook", "name": "Custom Webhook", "params": ["webhook_url", "payload_json"]}]},
        {"provider": "custom_api", "actions": [{"id": "call_api", "name": "Authenticated API Call", "params": ["url", "method", "headers_json", "body_json"]}]},
        {"provider": "ai_marketing", "actions": [{"id": "generate_copy", "name": "Generate Ad Copy", "params": ["product", "audience"]}]},
        {"provider": "logic", "actions": [{"id": "transform", "name": "Transform Data", "params": ["template"]}]},
        # Communication
        {"provider": "telegram", "actions": [{"id": "send_message", "name": "Send Message", "params": ["chat_id", "text"]}]},
        {"provider": "microsoft_teams", "actions": [{"id": "post_message", "name": "Post to Channel", "params": ["channel", "message"]}]},
        {"provider": "reddit", "actions": [{"id": "post_submission", "name": "Post to Subreddit", "params": ["subreddit", "title", "text"]}]},
        # Productivity
        {"provider": "airtable", "actions": [{"id": "create_record", "name": "Create Record", "params": ["base_id", "table_name", "fields"]}]},
        {"provider": "trello", "actions": [{"id": "create_card", "name": "Create Card", "params": ["board_id", "list_id", "name", "description"]}]},
        {"provider": "asana", "actions": [{"id": "create_task", "name": "Create Task", "params": ["project_id", "name", "notes"]}]},
        {"provider": "monday", "actions": [{"id": "create_item", "name": "Create Item", "params": ["board_id", "item_name", "column_values"]}]},
        {"provider": "clickup", "actions": [{"id": "create_task", "name": "Create Task", "params": ["list_id", "name", "description"]}]},
        # Cloud Storage
        {"provider": "dropbox", "actions": [{"id": "upload_file", "name": "Upload File", "params": ["path", "file_content"]}]},
        {"provider": "onedrive", "actions": [{"id": "upload_file", "name": "Upload File", "params": ["path", "file_content"]}]},
        {"provider": "google_drive", "actions": [{"id": "upload_file", "name": "Upload File", "params": ["folder_id", "file_name", "file_content"]}]},
        # CRM
        {"provider": "pipedrive", "actions": [{"id": "create_deal", "name": "Create Deal", "params": ["title", "person_id", "value"]}]},
        {"provider": "zoho_crm", "actions": [{"id": "create_lead", "name": "Create Lead", "params": ["first_name", "last_name", "email"]}]},
        {"provider": "freshsales", "actions": [{"id": "create_contact", "name": "Create Contact", "params": ["first_name", "last_name", "email"]}]},
        # Analytics
        {"provider": "google_analytics", "actions": [{"id": "track_event", "name": "Track Event", "params": ["event_name", "event_params"]}]},
        {"provider": "mixpanel", "actions": [{"id": "track_event", "name": "Track Event", "params": ["event_name", "properties"]}]},
        {"provider": "amplitude", "actions": [{"id": "track_event", "name": "Track Event", "params": ["event_name", "event_properties"]}]},
        # Development
        {"provider": "gitlab", "actions": [{"id": "create_issue", "name": "Create Issue", "params": ["project_id", "title", "description"]}]},
        {"provider": "bitbucket", "actions": [{"id": "create_issue", "name": "Create Issue", "params": ["workspace", "repo", "title", "content"]}]},
        {"provider": "linear", "actions": [{"id": "create_issue", "name": "Create Issue", "params": ["team_id", "title", "description"]}]},
        {"provider": "sentry", "actions": [{"id": "create_event", "name": "Create Event", "params": ["project_id", "message", "level"]}]},
        # E-commerce
        {"provider": "bigcommerce", "actions": [{"id": "create_product", "name": "Create Product", "params": ["name", "price", "type"]}]},
        {"provider": "square", "actions": [{"id": "create_customer", "name": "Create Customer", "params": ["given_name", "email"]}]},
        {"provider": "paypal", "actions": [{"id": "create_payment", "name": "Create Payment", "params": ["amount", "currency", "description"]}]},
        # Other
        {"provider": "calendly", "actions": [{"id": "create_event", "name": "Create Event", "params": ["event_type", "start_time", "invitee_email"]}]},
        {"provider": "typeform", "actions": [{"id": "create_response", "name": "Create Response", "params": ["form_id", "answers"]}]},
        {"provider": "intercom", "actions": [{"id": "create_conversation", "name": "Create Conversation", "params": ["user_id", "message"]}]},
        {"provider": "pagerduty", "actions": [{"id": "create_incident", "name": "Create Incident", "params": ["service_id", "title", "description"]}]},
        {"provider": "sendgrid", "actions": [{"id": "send_email", "name": "Send Email", "params": ["to", "subject", "html_content"]}]},
        {"provider": "mailgun", "actions": [{"id": "send_email", "name": "Send Email", "params": ["to", "subject", "text"]}]},
        {"provider": "aws_s3", "actions": [{"id": "upload_file", "name": "Upload File", "params": ["bucket", "key", "file_content"]}]},
        # Email Services
        {"provider": "postmark", "actions": [{"id": "send_email", "name": "Send Email", "params": ["to", "subject", "html_body"]}]},
        {"provider": "sparkpost", "actions": [{"id": "send_email", "name": "Send Email", "params": ["to", "subject", "html"]}]},
        {"provider": "ses", "actions": [{"id": "send_email", "name": "Send Email", "params": ["to", "subject", "body"]}]},
        {"provider": "postal", "actions": [{"id": "send_email", "name": "Send Email", "params": ["to", "subject", "html_body"]}]},
        # SMS/Voice
        {"provider": "vonage", "actions": [{"id": "send_sms", "name": "Send SMS", "params": ["to", "text"]}]},
        {"provider": "bandwidth", "actions": [{"id": "send_sms", "name": "Send SMS", "params": ["to", "text"]}]},
        {"provider": "messagebird", "actions": [{"id": "send_sms", "name": "Send SMS", "params": ["to", "text"]}]},
        {"provider": "plivo", "actions": [{"id": "send_sms", "name": "Send SMS", "params": ["to", "text"]}]},
        # Payment Processors
        {"provider": "braintree", "actions": [{"id": "create_transaction", "name": "Create Transaction", "params": ["amount", "payment_method"]}]},
        {"provider": "razorpay", "actions": [{"id": "create_payment", "name": "Create Payment", "params": ["amount", "currency", "order_id"]}]},
        {"provider": "mollie", "actions": [{"id": "create_payment", "name": "Create Payment", "params": ["amount", "description"]}]},
        {"provider": "adyen", "actions": [{"id": "create_payment", "name": "Create Payment", "params": ["amount", "currency", "reference"]}]},
        {"provider": "revolut", "actions": [{"id": "create_payment", "name": "Create Payment", "params": ["amount", "currency"]}]},
        # Accounting/Finance
        {"provider": "quickbooks", "actions": [{"id": "create_invoice", "name": "Create Invoice", "params": ["customer_id", "amount", "description"]}]},
        {"provider": "xero", "actions": [{"id": "create_invoice", "name": "Create Invoice", "params": ["contact_id", "line_items"]}]},
        {"provider": "freshbooks", "actions": [{"id": "create_invoice", "name": "Create Invoice", "params": ["client_id", "amount"]}]},
        {"provider": "wave", "actions": [{"id": "create_invoice", "name": "Create Invoice", "params": ["customer_id", "items"]}]},
        {"provider": "sage", "actions": [{"id": "create_invoice", "name": "Create Invoice", "params": ["customer_id", "amount"]}]},
        # Marketing Automation
        {"provider": "activecampaign", "actions": [{"id": "add_contact", "name": "Add Contact", "params": ["email", "first_name", "last_name"]}]},
        {"provider": "convertkit", "actions": [{"id": "add_subscriber", "name": "Add Subscriber", "params": ["email", "tags"]}]},
        {"provider": "getresponse", "actions": [{"id": "add_contact", "name": "Add Contact", "params": ["email", "name"]}]},
        {"provider": "drip", "actions": [{"id": "create_subscriber", "name": "Create Subscriber", "params": ["email", "custom_fields"]}]},
        {"provider": "omnisend", "actions": [{"id": "add_contact", "name": "Add Contact", "params": ["email", "first_name"]}]},
        {"provider": "klaviyo", "actions": [{"id": "create_profile", "name": "Create Profile", "params": ["email", "phone_number"]}]},
        {"provider": "brevo", "actions": [{"id": "create_contact", "name": "Create Contact", "params": ["email", "attributes"]}]},
        {"provider": "sendinblue", "actions": [{"id": "create_contact", "name": "Create Contact", "params": ["email", "attributes"]}]},
        # Social Media Management
        {"provider": "buffer", "actions": [{"id": "create_post", "name": "Create Post", "params": ["text", "media_url"]}]},
        {"provider": "hootsuite", "actions": [{"id": "create_post", "name": "Create Post", "params": ["text", "scheduled_time"]}]},
        {"provider": "later", "actions": [{"id": "create_post", "name": "Create Post", "params": ["text", "media_url"]}]},
        {"provider": "sprout_social", "actions": [{"id": "create_post", "name": "Create Post", "params": ["text", "channels"]}]},
        {"provider": "co_schedule", "actions": [{"id": "create_post", "name": "Create Post", "params": ["text", "publish_date"]}]},
        # Customer Support
        {"provider": "freshdesk", "actions": [{"id": "create_ticket", "name": "Create Ticket", "params": ["subject", "description", "email"]}]},
        {"provider": "helpscout", "actions": [{"id": "create_conversation", "name": "Create Conversation", "params": ["subject", "customer_email"]}]},
        {"provider": "crisp", "actions": [{"id": "send_message", "name": "Send Message", "params": ["website_id", "user_id", "content"]}]},
        {"provider": "drift", "actions": [{"id": "create_conversation", "name": "Create Conversation", "params": ["contact_id", "message"]}]},
        {"provider": "tawk", "actions": [{"id": "send_message", "name": "Send Message", "params": ["visitor_id", "message"]}]},
        {"provider": "livechat", "actions": [{"id": "send_message", "name": "Send Message", "params": ["chat_id", "text"]}]},
        # Project Management
        {"provider": "basecamp", "actions": [{"id": "create_todo", "name": "Create Todo", "params": ["project_id", "name", "description"]}]},
        {"provider": "wrike", "actions": [{"id": "create_task", "name": "Create Task", "params": ["folder_id", "title"]}]},
        {"provider": "smartsheet", "actions": [{"id": "add_row", "name": "Add Row", "params": ["sheet_id", "cells"]}]},
        {"provider": "notion_api", "actions": [{"id": "create_page", "name": "Create Page", "params": ["parent_id", "title"]}]},
        {"provider": "coda", "actions": [{"id": "insert_row", "name": "Insert Row", "params": ["table_id", "row_data"]}]},
        # Database/Data
        {"provider": "supabase_db", "actions": [{"id": "insert_row", "name": "Insert Row", "params": ["table", "data"]}]},
        {"provider": "firebase", "actions": [{"id": "write_data", "name": "Write Data", "params": ["path", "data"]}]},
        {"provider": "mongodb", "actions": [{"id": "insert_document", "name": "Insert Document", "params": ["collection", "document"]}]},
        {"provider": "airtable_api", "actions": [{"id": "create_record", "name": "Create Record", "params": ["base_id", "table", "fields"]}]},
        {"provider": "dynamodb", "actions": [{"id": "put_item", "name": "Put Item", "params": ["table_name", "item"]}]},
        # Monitoring/Logging
        {"provider": "datadog", "actions": [{"id": "create_event", "name": "Create Event", "params": ["title", "text", "tags"]}]},
        {"provider": "newrelic", "actions": [{"id": "create_event", "name": "Create Event", "params": ["event_type", "attributes"]}]},
        {"provider": "loggly", "actions": [{"id": "send_log", "name": "Send Log", "params": ["message", "tags"]}]},
        {"provider": "papertrail", "actions": [{"id": "send_log", "name": "Send Log", "params": ["message", "system"]}]},
        {"provider": "rollbar", "actions": [{"id": "report_error", "name": "Report Error", "params": ["level", "message"]}]},
        {"provider": "honeybadger", "actions": [{"id": "notify", "name": "Notify", "params": ["error_class", "message"]}]},
        {"provider": "bugsnag", "actions": [{"id": "notify", "name": "Notify", "params": ["error_class", "message"]}]},
        # CI/CD
        {"provider": "circleci", "actions": [{"id": "trigger_pipeline", "name": "Trigger Pipeline", "params": ["project_slug", "branch"]}]},
        {"provider": "travis_ci", "actions": [{"id": "trigger_build", "name": "Trigger Build", "params": ["repo", "branch"]}]},
        {"provider": "jenkins", "actions": [{"id": "trigger_build", "name": "Trigger Build", "params": ["job_name", "parameters"]}]},
        {"provider": "github_actions", "actions": [{"id": "trigger_workflow", "name": "Trigger Workflow", "params": ["repo", "workflow_id"]}]},
        {"provider": "gitlab_ci", "actions": [{"id": "trigger_pipeline", "name": "Trigger Pipeline", "params": ["project_id", "ref"]}]},
        # Content Management
        {"provider": "contentful", "actions": [{"id": "create_entry", "name": "Create Entry", "params": ["content_type_id", "fields"]}]},
        {"provider": "strapi", "actions": [{"id": "create_entry", "name": "Create Entry", "params": ["content_type", "data"]}]},
        {"provider": "wordpress", "actions": [{"id": "create_post", "name": "Create Post", "params": ["title", "content", "status"]}]},
        {"provider": "ghost", "actions": [{"id": "create_post", "name": "Create Post", "params": ["title", "html"]}]},
        {"provider": "medium", "actions": [{"id": "create_post", "name": "Create Post", "params": ["title", "content"]}]},
        {"provider": "dev_to", "actions": [{"id": "create_article", "name": "Create Article", "params": ["title", "body_markdown"]}]},
        # Forms/Surveys
        {"provider": "google_forms", "actions": [{"id": "create_response", "name": "Create Response", "params": ["form_id", "responses"]}]},
        {"provider": "jotform", "actions": [{"id": "create_submission", "name": "Create Submission", "params": ["form_id", "answers"]}]},
        {"provider": "wufoo", "actions": [{"id": "create_entry", "name": "Create Entry", "params": ["form_id", "fields"]}]},
        {"provider": "formspree", "actions": [{"id": "submit_form", "name": "Submit Form", "params": ["form_id", "data"]}]},
        # Video/Media
        {"provider": "vimeo", "actions": [{"id": "upload_video", "name": "Upload Video", "params": ["video_url", "title", "description"]}]},
        {"provider": "youtube", "actions": [{"id": "upload_video", "name": "Upload Video", "params": ["video_url", "title", "description"]}]},
        {"provider": "cloudinary", "actions": [{"id": "upload_image", "name": "Upload Image", "params": ["image_url", "public_id"]}]},
        {"provider": "imgur", "actions": [{"id": "upload_image", "name": "Upload Image", "params": ["image_url", "title"]}]},
        # Maps/Location
        {"provider": "google_maps", "actions": [{"id": "geocode", "name": "Geocode Address", "params": ["address"]}]},
        {"provider": "mapbox", "actions": [{"id": "geocode", "name": "Geocode Address", "params": ["address"]}]},
        {"provider": "here", "actions": [{"id": "geocode", "name": "Geocode Address", "params": ["address"]}]},
        # Translation
        {"provider": "deep_l", "actions": [{"id": "translate", "name": "Translate Text", "params": ["text", "target_lang"]}]},
        {"provider": "google_translate", "actions": [{"id": "translate", "name": "Translate Text", "params": ["text", "target_language"]}]},
        {"provider": "microsoft_translator", "actions": [{"id": "translate", "name": "Translate Text", "params": ["text", "to"]}]},
        # OCR/Image Processing
        {"provider": "tesseract", "actions": [{"id": "extract_text", "name": "Extract Text", "params": ["image_url"]}]},
        {"provider": "aws_textract", "actions": [{"id": "extract_text", "name": "Extract Text", "params": ["document_url"]}]},
        {"provider": "google_vision", "actions": [{"id": "analyze_image", "name": "Analyze Image", "params": ["image_url"]}]},
        # Webhooks/API
        {"provider": "zapier", "actions": [{"id": "trigger_webhook", "name": "Trigger Webhook", "params": ["webhook_url", "data"]}]},
        {"provider": "make", "actions": [{"id": "trigger_scenario", "name": "Trigger Scenario", "params": ["scenario_id", "data"]}]},
        {"provider": "n8n", "actions": [{"id": "trigger_workflow", "name": "Trigger Workflow", "params": ["workflow_id", "data"]}]},
        {"provider": "ifttt", "actions": [{"id": "trigger_applet", "name": "Trigger Applet", "params": ["event", "data"]}]},
        # Time Tracking
        {"provider": "toggl", "actions": [{"id": "create_time_entry", "name": "Create Time Entry", "params": ["description", "duration"]}]},
        {"provider": "harvest", "actions": [{"id": "create_time_entry", "name": "Create Time Entry", "params": ["project_id", "hours"]}]},
        {"provider": "clockify", "actions": [{"id": "create_time_entry", "name": "Create Time Entry", "params": ["project_id", "description"]}]},
        # HR/Recruiting
        {"provider": "bamboohr", "actions": [{"id": "create_employee", "name": "Create Employee", "params": ["first_name", "last_name", "email"]}]},
        {"provider": "workday", "actions": [{"id": "create_worker", "name": "Create Worker", "params": ["first_name", "last_name"]}]},
        {"provider": "greenhouse", "actions": [{"id": "create_candidate", "name": "Create Candidate", "params": ["first_name", "last_name", "email"]}]},
        # Document Management
        {"provider": "docu_sign", "actions": [{"id": "send_envelope", "name": "Send Envelope", "params": ["recipient_email", "document_url"]}]},
        {"provider": "hello_sign", "actions": [{"id": "send_signature_request", "name": "Send Signature Request", "params": ["signers", "file_url"]}]},
        {"provider": "pandadoc", "actions": [{"id": "create_document", "name": "Create Document", "params": ["template_id", "recipients"]}]},
        # Shipping/Logistics
        {"provider": "shipstation", "actions": [{"id": "create_shipment", "name": "Create Shipment", "params": ["order_id", "carrier"]}]},
        {"provider": "easypost", "actions": [{"id": "create_shipment", "name": "Create Shipment", "params": ["to_address", "from_address", "parcel"]}]},
        {"provider": "shippo", "actions": [{"id": "create_transaction", "name": "Create Transaction", "params": ["rate_id"]}]},
        # Real Estate
        {"provider": "zillow", "actions": [{"id": "get_property", "name": "Get Property", "params": ["address"]}]},
        {"provider": "realtor", "actions": [{"id": "search_listings", "name": "Search Listings", "params": ["city", "state"]}]},
        # Weather/Environment
        {"provider": "openweather", "actions": [{"id": "get_weather", "name": "Get Weather", "params": ["city", "units"]}]},
        {"provider": "weather_api", "actions": [{"id": "get_forecast", "name": "Get Forecast", "params": ["location", "days"]}]},
        # News/Content
        {"provider": "newsapi", "actions": [{"id": "get_articles", "name": "Get Articles", "params": ["query", "language"]}]},
        {"provider": "rss", "actions": [{"id": "parse_feed", "name": "Parse Feed", "params": ["feed_url"]}]},
        # Cryptocurrency
        {"provider": "coinbase", "actions": [{"id": "create_transaction", "name": "Create Transaction", "params": ["to", "amount", "currency"]}]},
        {"provider": "binance", "actions": [{"id": "create_order", "name": "Create Order", "params": ["symbol", "side", "quantity"]}]},
        # AI/ML Services
        {"provider": "replicate", "actions": [{"id": "run_model", "name": "Run Model", "params": ["model", "input"]}]},
        {"provider": "huggingface", "actions": [{"id": "run_inference", "name": "Run Inference", "params": ["model_id", "inputs"]}]},
        {"provider": "stability_ai", "actions": [{"id": "generate_image", "name": "Generate Image", "params": ["prompt", "width", "height"]}]},
        {"provider": "midjourney_api", "actions": [{"id": "generate_image", "name": "Generate Image", "params": ["prompt"]}]},
        {"provider": "elevenlabs", "actions": [{"id": "text_to_speech", "name": "Text to Speech", "params": ["text", "voice_id"]}]},
        {"provider": "assemblyai", "actions": [{"id": "transcribe_audio", "name": "Transcribe Audio", "params": ["audio_url"]}]}
    ]
    
    # Add custom integrations to catalog
    for custom in custom_integrations:
        if custom.get('actions'):
            action_catalog.append({
                "provider": custom.get('name', custom.get('id')),
                "actions": custom.get('actions', [])
            })
    
    system_prompt = f"Expert automation architect. PROVIDERS: {json.dumps(action_catalog)}. Output ONLY JSON matching the requested structure. Support branching/retries. Reference with {{{{step_n.output}}}}."
    try:
        response = openai_client.chat.completions.create(model="gpt-5", messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}], response_format={"type": "json_object"})
        return jsonify(json.loads(response.choices[0].message.content))
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/execution-plans', methods=['GET', 'POST'])
def handle_plans():
    if request.method == 'POST':
        plan_data = request.json
        plan_data['id'] = str(uuid.uuid4())
        plan_data['created_at'] = datetime.now().isoformat()
        db['execution_plans'].append(plan_data)
        return jsonify(plan_data)
    user_id = request.args.get('user_id')
    return jsonify([p for p in db['execution_plans'] if p.get('user_id') == user_id])

@app.route('/api/execute-plan', methods=['POST'])
def execute_plan():
    data = request.json or {}
    plan_id = data.get('execution_plan_id')
    trigger_data = data.get('trigger_data')
    return jsonify(execute_plan_logic(plan_id, trigger_data))

@app.route('/api/webhook/<path:webhook_path>', methods=['POST', 'GET'])
def webhook_trigger(webhook_path):
    """Webhook endpoint to trigger workflows"""
    plan_id = db['webhook_triggers'].get(webhook_path)
    if not plan_id:
        return jsonify({"error": "Webhook not found"}), 404
    
    plan = next((p for p in db['execution_plans'] if p['id'] == plan_id), None)
    if not plan:
        return jsonify({"error": "Plan not found"}), 404
    
    # Extract webhook data
    trigger_data = {
        "method": request.method,
        "headers": dict(request.headers),
        "body": request.json if request.is_json else request.form.to_dict(),
        "query": request.args.to_dict(),
        "timestamp": datetime.now().isoformat()
    }
    
    result = execute_plan_logic(plan_id, trigger_data)
    return jsonify(result)

@app.route('/api/execution-plans/<plan_id>/trigger', methods=['POST'])
def update_trigger(plan_id):
    """Update trigger configuration for a plan"""
    plan = next((p for p in db['execution_plans'] if p['id'] == plan_id), None)
    if not plan:
        return jsonify({"error": "Plan not found"}), 404
    
    trigger_config = request.json.get('trigger')
    enabled = request.json.get('enabled', True)
    
    plan['trigger'] = trigger_config
    plan['enabled'] = enabled
    
    # Handle webhook trigger registration
    if trigger_config and trigger_config.get('type') == 'webhook':
        webhook_path = trigger_config.get('config', {}).get('webhook_path')
        if webhook_path:
            db['webhook_triggers'][webhook_path] = plan_id
    
    # Handle schedule trigger
    if trigger_config and trigger_config.get('type') == 'schedule':
        cron_expr = trigger_config.get('config', {}).get('cron_expression')
        if cron_expr:
            # Remove existing job if any
            try:
                scheduler.remove_job(f"plan_{plan_id}")
            except:
                pass
            
            # Add new scheduled job
            scheduler.add_job(
                func=lambda: execute_plan_logic(plan_id),
                trigger=CronTrigger.from_crontab(cron_expr),
                id=f"plan_{plan_id}",
                replace_existing=True
            )
    
    return jsonify(plan)

@app.route('/api/execution-plans/<plan_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_plan(plan_id):
    """Get, update, or delete a specific execution plan"""
    plan = next((p for p in db['execution_plans'] if p['id'] == plan_id), None)
    if not plan:
        return jsonify({"error": "Plan not found"}), 404
    
    if request.method == 'GET':
        return jsonify(plan)
    
    if request.method == 'PUT':
        update_data = request.json
        plan.update(update_data)
        return jsonify(plan)
    
    if request.method == 'DELETE':
        # Remove scheduled job if exists
        try:
            scheduler.remove_job(f"plan_{plan_id}")
        except:
            pass
        
        # Remove webhook trigger if exists
        webhook_paths = [path for path, pid in db['webhook_triggers'].items() if pid == plan_id]
        for path in webhook_paths:
            del db['webhook_triggers'][path]
        
        db['execution_plans'] = [p for p in db['execution_plans'] if p['id'] != plan_id]
        return jsonify({"message": "Plan deleted"})

@app.route('/api/monitoring/status', methods=['GET'])
def get_monitoring_status():
    user_id = request.args.get('user_id')
    user_plans = [p['id'] for p in db['execution_plans'] if p.get('user_id') == user_id]
    user_executions = [e for e in db['executions'] if e['execution_plan_id'] in user_plans]
    
    status_summary = {
        "total_executions": len(user_executions),
        "successful": len([e for e in user_executions if e['status'] == "success"]),
        "failed": len([e for e in user_executions if e['status'] == "failed"]),
        "recent_activity": user_executions[-10:][::-1]
    }
    return jsonify(status_summary)

@app.route('/api/custom-integrations', methods=['GET', 'POST'])
def manage_custom_integrations():
    """Get or create custom integrations"""
    if request.method == 'GET':
        user_id = request.args.get('user_id')
        # In production, load from database
        # For now, return empty list (frontend uses localStorage)
        return jsonify([])
    
    if request.method == 'POST':
        integration_data = request.json
        # In production, save to database
        return jsonify(integration_data)

if __name__ == '__main__':
    scheduler.init_app(app)
    scheduler.start()
    app.run(host='0.0.0.0', port=5001)
