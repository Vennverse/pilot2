"""
Pricing & Quota System - Freemium model with usage tracking
Plans: Free, Pro, Business, Enterprise
"""

import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from enum import Enum
import json

class PlanTier(Enum):
    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


class PricingPlans:
    """Define all pricing tiers"""
    
    PLANS = {
        PlanTier.FREE.value: {
            "name": "Free",
            "price": 0,
            "features": {
                "workflows_per_month": 3,
                "executions_per_month": 50,
                "integrations": 10,  # Limited to 10 providers
                "team_members": 1,
                "custom_code": False,
                "api_access": False,
                "priority_support": False,
                "sso": False,
                "audit_logs": False,
                "advanced_analytics": False
            }
        },
        PlanTier.PRO.value: {
            "name": "Pro",
            "price": 29,
            "features": {
                "workflows_per_month": 100,
                "executions_per_month": 5000,
                "integrations": 50,  # All providers
                "team_members": 3,
                "custom_code": True,
                "api_access": True,
                "priority_support": False,
                "sso": False,
                "audit_logs": False,
                "advanced_analytics": True
            }
        },
        PlanTier.BUSINESS.value: {
            "name": "Business",
            "price": 99,
            "features": {
                "workflows_per_month": 500,
                "executions_per_month": 50000,
                "integrations": 200,  # Unlimited
                "team_members": 20,
                "custom_code": True,
                "api_access": True,
                "priority_support": True,
                "sso": True,
                "audit_logs": True,
                "advanced_analytics": True
            }
        },
        PlanTier.ENTERPRISE.value: {
            "name": "Enterprise",
            "price": "Custom",
            "features": {
                "workflows_per_month": -1,  # Unlimited
                "executions_per_month": -1,
                "integrations": 200,
                "team_members": -1,  # Unlimited
                "custom_code": True,
                "api_access": True,
                "priority_support": True,
                "sso": True,
                "audit_logs": True,
                "advanced_analytics": True,
                "dedicated_support": True,
                "custom_integrations": True
            }
        }
    }


class QuotaManager:
    """Track and enforce usage quotas"""
    
    def __init__(self):
        self.user_quotas = {}  # user_id -> quota tracking
    
    def initialize_user_quota(self, user_id: str, plan_tier: str = PlanTier.FREE.value):
        """Initialize quota for new user"""
        plan = PricingPlans.PLANS.get(plan_tier, PricingPlans.PLANS[PlanTier.FREE.value])
        
        self.user_quotas[user_id] = {
            "plan_tier": plan_tier,
            "plan_name": plan["name"],
            "subscribed_at": datetime.now().isoformat(),
            "billing_cycle_start": datetime.now().isoformat(),
            "usage": {
                "workflows_created": 0,
                "executions_run": 0,
                "custom_code_runs": 0,
                "team_members_added": 1,
                "api_calls": 0
            },
            "features_used": {
                "custom_code": False,
                "api_access": False,
                "sso": False
            }
        }
        
        return self.user_quotas[user_id]
    
    def check_quota(self, user_id: str, quota_type: str) -> Dict[str, Any]:
        """Check if user can perform action"""
        if user_id not in self.user_quotas:
            self.initialize_user_quota(user_id, PlanTier.FREE.value)
        
        quota = self.user_quotas[user_id]
        plan = PricingPlans.PLANS[quota["plan_tier"]]
        usage = quota["usage"]
        
        # Check if billing cycle reset needed
        self._check_reset_cycle(user_id)
        
        quota_name = quota_type.replace("_", "_quota_")
        limit = plan["features"].get(quota_name.replace("_quota_", "_"), -1)
        current_usage = usage.get(quota_type, 0)
        
        # -1 means unlimited
        if limit == -1:
            return {"allowed": True, "current": current_usage, "limit": "unlimited"}
        
        return {
            "allowed": current_usage < limit,
            "current": current_usage,
            "limit": limit,
            "remaining": max(0, limit - current_usage)
        }
    
    def increment_usage(self, user_id: str, quota_type: str, amount: int = 1) -> bool:
        """Increment usage counter"""
        if user_id not in self.user_quotas:
            self.initialize_user_quota(user_id)
        
        check = self.check_quota(user_id, quota_type)
        
        if not check["allowed"] and check["limit"] != "unlimited":
            return False
        
        self.user_quotas[user_id]["usage"][quota_type] = \
            self.user_quotas[user_id]["usage"].get(quota_type, 0) + amount
        
        return True
    
    def upgrade_plan(self, user_id: str, new_plan_tier: str) -> Dict[str, Any]:
        """Upgrade user to new plan"""
        if user_id not in self.user_quotas:
            self.initialize_user_quota(user_id)
        
        old_plan = self.user_quotas[user_id]["plan_tier"]
        self.user_quotas[user_id]["plan_tier"] = new_plan_tier
        self.user_quotas[user_id]["plan_name"] = PricingPlans.PLANS[new_plan_tier]["name"]
        self.user_quotas[user_id]["upgraded_at"] = datetime.now().isoformat()
        self.user_quotas[user_id]["billing_cycle_start"] = datetime.now().isoformat()
        
        return {
            "user_id": user_id,
            "old_plan": old_plan,
            "new_plan": new_plan_tier,
            "upgraded_at": datetime.now().isoformat()
        }
    
    def get_user_quota_status(self, user_id: str) -> Dict[str, Any]:
        """Get detailed quota status for user"""
        if user_id not in self.user_quotas:
            self.initialize_user_quota(user_id)
        
        quota = self.user_quotas[user_id]
        plan = PricingPlans.PLANS[quota["plan_tier"]]
        usage = quota["usage"]
        
        return {
            "plan_tier": quota["plan_tier"],
            "plan_name": quota["plan_name"],
            "subscribed_at": quota["subscribed_at"],
            "billing_cycle_start": quota["billing_cycle_start"],
            "usage": usage,
            "limits": plan["features"],
            "usage_percentage": {
                "workflows": (usage["workflows_created"] / plan["features"]["workflows_per_month"] * 100) 
                             if plan["features"]["workflows_per_month"] != -1 else 0,
                "executions": (usage["executions_run"] / plan["features"]["executions_per_month"] * 100)
                             if plan["features"]["executions_per_month"] != -1 else 0
            },
            "days_until_reset": 30 - (datetime.now() - datetime.fromisoformat(quota["billing_cycle_start"])).days
        }
    
    def _check_reset_cycle(self, user_id: str):
        """Reset monthly quotas if cycle expired"""
        quota = self.user_quotas[user_id]
        cycle_start = datetime.fromisoformat(quota["billing_cycle_start"])
        
        if (datetime.now() - cycle_start).days >= 30:
            quota["billing_cycle_start"] = datetime.now().isoformat()
            quota["usage"] = {
                "workflows_created": 0,
                "executions_run": 0,
                "custom_code_runs": 0,
                "team_members_added": 1,
                "api_calls": 0
            }


# Global instance
quota_manager = QuotaManager()


def get_pricing_page_data() -> Dict[str, Any]:
    """Data for pricing page"""
    return {
        "plans": PricingPlans.PLANS,
        "comparison": {
            "rows": [
                {"feature": "Monthly Workflows", "free": 3, "pro": 100, "business": 500, "enterprise": "Unlimited"},
                {"feature": "Monthly Executions", "free": 50, "pro": 5000, "business": 50000, "enterprise": "Unlimited"},
                {"feature": "Available Integrations", "free": 10, "pro": 50, "business": "All", "enterprise": "All + Custom"},
                {"feature": "Team Members", "free": 1, "pro": 3, "business": 20, "enterprise": "Unlimited"},
                {"feature": "Custom Code", "free": False, "pro": True, "business": True, "enterprise": True},
                {"feature": "API Access", "free": False, "pro": True, "business": True, "enterprise": True},
                {"feature": "SSO", "free": False, "pro": False, "business": True, "enterprise": True},
                {"feature": "Audit Logs", "free": False, "pro": False, "business": True, "enterprise": True},
                {"feature": "Advanced Analytics", "free": False, "pro": True, "business": True, "enterprise": True},
                {"feature": "Priority Support", "free": False, "pro": False, "business": True, "enterprise": True},
                {"feature": "Dedicated Support", "free": False, "pro": False, "business": False, "enterprise": True}
            ]
        },
        "faq": [
            {
                "question": "Can I change plans anytime?",
                "answer": "Yes! Upgrade or downgrade at any time. Changes take effect immediately."
            },
            {
                "question": "Do you offer a free trial?",
                "answer": "No need - start with our Free plan with 3 workflows and 50 executions/month."
            },
            {
                "question": "What happens if I exceed my quota?",
                "answer": "We'll notify you. You can upgrade anytime. Unused quota rolls over at month end."
            },
            {
                "question": "Is there a setup fee?",
                "answer": "No setup fees. Pay-as-you-go on credit card."
            },
            {
                "question": "Do you offer discounts?",
                "answer": "Yes! Annual billing saves 20%. Contact us for volume discounts."
            }
        ]
    }
