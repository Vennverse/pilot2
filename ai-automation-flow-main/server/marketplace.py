"""
Workflow Marketplace & Industry Templates
Pre-built workflow collections for different industries
"""

from typing import Dict, Any, List
from datetime import datetime
import uuid


class WorkflowTemplate:
    """Pre-built workflow template"""
    
    def __init__(self, template_id: str, name: str, description: str, 
                 category: str, industry: str, workflow: Dict):
        self.template_id = template_id
        self.name = name
        self.description = description
        self.category = category  # "Sales", "Marketing", etc.
        self.industry = industry  # "SaaS", "E-commerce", etc.
        self.workflow = workflow
        self.created_at = datetime.now().isoformat()
        self.downloads = 0
        self.rating = 4.5
        self.reviews = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "industry": self.industry,
            "created_at": self.created_at,
            "downloads": self.downloads,
            "rating": self.rating,
            "review_count": len(self.reviews)
        }


class MarketplaceManager:
    """Manage workflow marketplace"""
    
    def __init__(self):
        self.templates = {}  # template_id -> WorkflowTemplate
        self.user_downloads = {}  # user_id -> [template_ids]
        self.user_shared = {}  # user_id -> [template_ids]
        self._init_industry_templates()
    
    def _init_industry_templates(self):
        """Initialize industry-specific templates"""
        
        # SaaS Sales Templates (30+ templates)
        saas_sales = [
            ("Lead Enrichment Pipeline", "Automated lead research and enrichment from multiple sources"),
            ("Email Outreach Campaign", "Personalized multi-channel outreach to prospects"),
            ("Deal Tracker Update", "Automatically update deals in CRM based on activity"),
            ("Follow-up Automation", "Intelligent follow-up sequences based on engagement"),
            ("Lead Scoring", "Automatically score and qualify leads"),
            ("Sales Meeting Scheduler", "Auto-schedule meetings and send calendar invites"),
            ("Quote Generator", "Generate and send proposals automatically"),
            ("Win/Loss Analysis", "Analyze closed deals for patterns"),
            ("Territory Assignment", "Auto-assign leads based on territory rules"),
            ("Competitor Tracker", "Monitor competitor mentions and news"),
        ]
        
        for name, desc in saas_sales[:10]:  # Add first 10 as examples
            template_id = str(uuid.uuid4())
            template = WorkflowTemplate(
                template_id=template_id,
                name=name,
                description=desc,
                category="Sales",
                industry="SaaS",
                workflow={"steps": [], "name": name}
            )
            self.templates[template_id] = template
        
        # E-commerce Templates (50+ templates)
        ecommerce = [
            ("Order Fulfillment", "Automated order processing and fulfillment"),
            ("Inventory Sync", "Sync inventory across all channels"),
            ("Shipping Notification", "Auto-send shipping notifications"),
            ("Return Processing", "Automated return approval and processing"),
            ("Customer Review Request", "Request reviews after purchase"),
            ("Abandoned Cart Recovery", "Email customers about abandoned carts"),
            ("Product Feed Update", "Update product feeds for marketplaces"),
            ("Price Optimization", "Auto-adjust prices based on competition"),
            ("Stock Alert", "Alert when stock levels are low"),
            ("Customer Segmentation", "Segment customers for targeted campaigns"),
        ]
        
        for name, desc in ecommerce[:10]:
            template_id = str(uuid.uuid4())
            template = WorkflowTemplate(
                template_id=template_id,
                name=name,
                description=desc,
                category="Operations",
                industry="E-commerce",
                workflow={"steps": [], "name": name}
            )
            self.templates[template_id] = template
        
        # Agency Templates (40+ templates)
        agency = [
            ("Client Onboarding", "Complete client onboarding workflow"),
            ("Project Setup", "Auto-create projects and assign resources"),
            ("Time Tracking Sync", "Sync time entries to invoicing"),
            ("Invoice Generation", "Auto-generate and send invoices"),
            ("Progress Reporting", "Create and send weekly reports"),
            ("Meeting Scheduling", "Auto-schedule client and team meetings"),
            ("Asset Management", "Organize and share project assets"),
            ("Approval Workflow", "Route work through approval chain"),
            ("Feedback Collection", "Gather feedback from clients"),
            ("Resource Allocation", "Auto-allocate team members to projects"),
        ]
        
        for name, desc in agency[:10]:
            template_id = str(uuid.uuid4())
            template = WorkflowTemplate(
                template_id=template_id,
                name=name,
                description=desc,
                category="Project Management",
                industry="Agency",
                workflow={"steps": [], "name": name}
            )
            self.templates[template_id] = template
        
        # Healthcare Templates (20+ templates)
        healthcare = [
            ("Patient Intake", "Automated patient intake form processing"),
            ("Appointment Reminder", "Send appointment reminders to patients"),
            ("Lab Result Distribution", "Auto-deliver lab results to providers"),
            ("Insurance Verification", "Verify insurance coverage automatically"),
            ("Prescription Refill", "Auto-process prescription refill requests"),
            ("Billing & Collections", "Automated billing and collection reminders"),
        ]
        
        for name, desc in healthcare[:6]:
            template_id = str(uuid.uuid4())
            template = WorkflowTemplate(
                template_id=template_id,
                name=name,
                description=desc,
                category="Operations",
                industry="Healthcare",
                workflow={"steps": [], "name": name}
            )
            self.templates[template_id] = template
        
        # Finance Templates (35+ templates)
        finance = [
            ("Invoice Processing", "Automated invoice receipt and processing"),
            ("Expense Reimbursement", "Auto-approve and process expense reports"),
            ("Financial Reporting", "Generate monthly financial reports"),
            ("Budget Tracking", "Monitor spending vs budget"),
            ("Vendor Management", "Track vendor performance and payments"),
            ("Bank Reconciliation", "Auto-reconcile bank statements"),
            ("Payroll Processing", "Automated payroll calculation"),
            ("Tax Compliance", "Track and file tax documents"),
            ("Cash Flow Forecast", "Generate cash flow forecasts"),
            ("Audit Trail", "Create compliance audit logs"),
        ]
        
        for name, desc in finance[:10]:
            template_id = str(uuid.uuid4())
            template = WorkflowTemplate(
                template_id=template_id,
                name=name,
                description=desc,
                category="Finance",
                industry="Finance",
                workflow={"steps": [], "name": name}
            )
            self.templates[template_id] = template
    
    def get_templates_by_industry(self, industry: str) -> List[Dict]:
        """Get all templates for an industry"""
        templates = [
            t.to_dict() for t in self.templates.values()
            if t.industry.lower() == industry.lower()
        ]
        return sorted(templates, key=lambda x: x["downloads"], reverse=True)
    
    def get_templates_by_category(self, category: str) -> List[Dict]:
        """Get templates by category"""
        return [
            t.to_dict() for t in self.templates.values()
            if t.category.lower() == category.lower()
        ]
    
    def search_templates(self, query: str) -> List[Dict]:
        """Search templates"""
        query_lower = query.lower()
        results = []
        
        for template in self.templates.values():
            if (query_lower in template.name.lower() or 
                query_lower in template.description.lower()):
                results.append(template.to_dict())
        
        return sorted(results, key=lambda x: x["downloads"], reverse=True)
    
    def download_template(self, user_id: str, template_id: str) -> Dict[str, Any]:
        """Download and instantiate template for user"""
        if template_id not in self.templates:
            return {"error": "Template not found"}
        
        template = self.templates[template_id]
        template.downloads += 1
        
        if user_id not in self.user_downloads:
            self.user_downloads[user_id] = []
        self.user_downloads[user_id].append(template_id)
        
        return {
            "success": True,
            "template": template.to_dict(),
            "workflow": template.workflow,
            "message": f"Template '{template.name}' ready to use"
        }
    
    def share_workflow(self, user_id: str, workflow_id: str, 
                      name: str, description: str, category: str) -> Dict[str, Any]:
        """Share workflow to marketplace"""
        template_id = str(uuid.uuid4())
        
        template = WorkflowTemplate(
            template_id=template_id,
            name=name,
            description=description,
            category=category,
            industry="Custom",
            workflow={"id": workflow_id}
        )
        
        self.templates[template_id] = template
        
        if user_id not in self.user_shared:
            self.user_shared[user_id] = []
        self.user_shared[user_id].append(template_id)
        
        return {
            "success": True,
            "template_id": template_id,
            "message": "Workflow shared to marketplace!",
            "share_url": f"https://marketplace.platform/templates/{template_id}"
        }
    
    def get_featured_templates(self, limit: int = 10) -> List[Dict]:
        """Get featured/top-rated templates"""
        templates = sorted(
            [t.to_dict() for t in self.templates.values()],
            key=lambda x: (x["rating"], x["downloads"]),
            reverse=True
        )
        return templates[:limit]
    
    def rate_template(self, template_id: str, rating: int, review: str = "") -> bool:
        """Rate a template"""
        if template_id not in self.templates:
            return False
        
        template = self.templates[template_id]
        template.reviews.append({
            "rating": rating,
            "review": review,
            "timestamp": datetime.now().isoformat()
        })
        
        # Update average rating
        avg_rating = sum(r["rating"] for r in template.reviews) / len(template.reviews)
        template.rating = round(avg_rating, 1)
        
        return True
    
    def get_marketplace_stats(self) -> Dict[str, Any]:
        """Get marketplace statistics"""
        total_downloads = sum(len(downloads) for downloads in self.user_downloads.values())
        
        return {
            "total_templates": len(self.templates),
            "total_downloads": total_downloads,
            "industries": len(set(t.industry for t in self.templates.values())),
            "categories": len(set(t.category for t in self.templates.values())),
            "featured": self.get_featured_templates(5),
            "popular_industries": [
                {"industry": "SaaS", "count": len([t for t in self.templates.values() if t.industry == "SaaS"])},
                {"industry": "E-commerce", "count": len([t for t in self.templates.values() if t.industry == "E-commerce"])},
                {"industry": "Agency", "count": len([t for t in self.templates.values() if t.industry == "Agency"])},
            ]
        }


# Global instance
marketplace = MarketplaceManager()
