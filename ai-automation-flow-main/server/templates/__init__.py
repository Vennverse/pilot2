"""
Agent Workflow Templates Index
Pre-built workflow templates for each specialized agent
"""

TEMPLATES = {
    "sales": [
        {
            "id": "sales_lead_enrichment",
            "name": "Lead Enrichment & Outreach",
            "description": "Find, enrich, and automatically reach out to qualified leads",
            "file": "sales_lead_enrichment.json",
            "steps": 4,
            "providers": ["hubspot", "clearbit", "sendgrid"],
            "estimated_execution_time_minutes": 5
        }
    ],
    "marketing": [
        {
            "id": "marketing_campaign",
            "name": "Marketing Email Campaign",
            "description": "Create, segment audience, and send marketing email campaign",
            "file": "marketing_campaign.json",
            "steps": 5,
            "providers": ["openai", "hubspot", "mailchimp", "google_analytics"],
            "estimated_execution_time_minutes": 10
        }
    ],
    "finance": [
        {
            "id": "finance_monthly_report",
            "name": "Monthly Financial Report",
            "description": "Reconcile accounts, generate P&L, and send to stakeholders",
            "file": "finance_monthly_report.json",
            "steps": 5,
            "providers": ["stripe", "quickbooks", "openai", "sendgrid"],
            "estimated_execution_time_minutes": 15
        }
    ],
    "support": [
        {
            "id": "support_auto_response",
            "name": "Support Ticket Auto-Response",
            "description": "Classify tickets, search knowledge base, and auto-respond to common issues",
            "file": "support_auto_response.json",
            "steps": 4,
            "providers": ["openai", "zendesk", "sendgrid"],
            "estimated_execution_time_minutes": 2
        }
    ],
    "hr": [
        {
            "id": "hr_onboarding",
            "name": "Employee Onboarding",
            "description": "Create employee record, send forms, schedule training, and notify team",
            "file": "hr_onboarding.json",
            "steps": 5,
            "providers": ["workday", "docusign", "google_calendar", "slack", "okta"],
            "estimated_execution_time_minutes": 20
        }
    ]
}


def get_template_by_id(template_id: str) -> dict:
    """Get template by ID"""
    for agent_templates in TEMPLATES.values():
        for template in agent_templates:
            if template["id"] == template_id:
                return template
    return None


def get_agent_templates(agent_name: str) -> list:
    """Get all templates for an agent"""
    return TEMPLATES.get(agent_name, [])


def list_all_templates() -> dict:
    """List all available templates"""
    return TEMPLATES


def get_template_workflow_file(agent_name: str, template_id: str) -> str:
    """Get the file path for a template workflow"""
    templates = get_agent_templates(agent_name)
    for template in templates:
        if template["id"] == template_id:
            return f"templates/{template['file']}"
    return None
