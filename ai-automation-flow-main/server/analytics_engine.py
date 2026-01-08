"""
Analytics & ROI Tracking Engine
Tracks time saved, cost reduction, success rates, and workflow performance
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import statistics


class AnalyticsEngine:
    """Track workflow performance and calculate ROI"""
    
    def __init__(self):
        self.workflow_stats = {}  # workflow_id -> stats
        self.execution_records = []  # All executions
        self.user_roi = {}  # user_id -> ROI metrics
    
    def record_execution(self, execution_id: str, user_id: str, workflow_id: str,
                        workflow_name: str, success: bool, duration_seconds: float,
                        steps_count: int, integrations_used: List[str]) -> None:
        """Record workflow execution"""
        
        record = {
            "execution_id": execution_id,
            "user_id": user_id,
            "workflow_id": workflow_id,
            "workflow_name": workflow_name,
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "duration_seconds": duration_seconds,
            "steps_count": steps_count,
            "integrations_used": integrations_used
        }
        
        self.execution_records.append(record)
        self._update_workflow_stats(workflow_id, record)
        self._update_user_roi(user_id, record)
    
    def _update_workflow_stats(self, workflow_id: str, record: Dict) -> None:
        """Update stats for a workflow"""
        if workflow_id not in self.workflow_stats:
            self.workflow_stats[workflow_id] = {
                "workflow_id": workflow_id,
                "workflow_name": record["workflow_name"],
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "success_rate": 0,
                "avg_duration": 0,
                "total_duration": 0,
                "durations": [],
                "time_saved_total": 0,
                "cost_saved_total": 0,
                "last_executed": None,
                "created_at": datetime.now().isoformat()
            }
        
        stats = self.workflow_stats[workflow_id]
        stats["total_executions"] += 1
        
        if record["success"]:
            stats["successful_executions"] += 1
        else:
            stats["failed_executions"] += 1
        
        stats["success_rate"] = (
            stats["successful_executions"] / stats["total_executions"] * 100
            if stats["total_executions"] > 0 else 0
        )
        
        stats["durations"].append(record["duration_seconds"])
        stats["total_duration"] += record["duration_seconds"]
        stats["avg_duration"] = stats["total_duration"] / stats["total_executions"]
        
        # Calculate time saved (manual would take 10x longer)
        stats["time_saved_total"] = stats["total_duration"] * 9  # 9x time saved
        
        # Calculate cost saved ($0.30 per minute manual work)
        cost_per_minute = 0.30
        stats["cost_saved_total"] = (stats["time_saved_total"] / 60) * cost_per_minute
        
        stats["last_executed"] = record["timestamp"]
    
    def _update_user_roi(self, user_id: str, record: Dict) -> None:
        """Update ROI metrics for user"""
        if user_id not in self.user_roi:
            self.user_roi[user_id] = {
                "user_id": user_id,
                "total_workflows_created": 0,
                "total_executions": 0,
                "successful_executions": 0,
                "total_time_saved_hours": 0,
                "total_cost_saved": 0,
                "avg_success_rate": 0,
                "favorite_agents": {},
                "most_used_integrations": {},
                "first_execution": datetime.now().isoformat(),
                "last_execution": None
            }
        
        roi = self.user_roi[user_id]
        roi["total_executions"] += 1
        
        if record["success"]:
            roi["successful_executions"] += 1
        
        # Time saved calculation
        time_saved_hours = (record["duration_seconds"] * 9) / 3600
        roi["total_time_saved_hours"] += time_saved_hours
        
        # Cost saved
        cost_saved = time_saved_hours * 50  # $50/hour labor rate
        roi["total_cost_saved"] += cost_saved
        
        roi["avg_success_rate"] = (
            roi["successful_executions"] / roi["total_executions"] * 100
            if roi["total_executions"] > 0 else 0
        )
        
        # Track integrations used
        for integration in record["integrations_used"]:
            roi["most_used_integrations"][integration] = \
                roi["most_used_integrations"].get(integration, 0) + 1
        
        roi["last_execution"] = datetime.now().isoformat()
    
    def get_workflow_performance(self, workflow_id: str) -> Dict[str, Any]:
        """Get performance metrics for specific workflow"""
        if workflow_id not in self.workflow_stats:
            return {"error": "Workflow not found"}
        
        stats = self.workflow_stats[workflow_id]
        
        return {
            "workflow_id": workflow_id,
            "workflow_name": stats["workflow_name"],
            "performance": {
                "total_executions": stats["total_executions"],
                "successful_executions": stats["successful_executions"],
                "failed_executions": stats["failed_executions"],
                "success_rate": f"{stats['success_rate']:.1f}%",
                "avg_execution_time": f"{stats['avg_duration']:.1f}s"
            },
            "roi": {
                "time_saved_hours": f"{stats['time_saved_total'] / 3600:.1f}",
                "cost_saved": f"${stats['cost_saved_total']:.2f}",
                "efficiency_gain": "90%"  # 9x faster than manual
            },
            "trend": self._calculate_trend(workflow_id),
            "recommendations": self._get_recommendations(workflow_id)
        }
    
    def get_user_roi_dashboard(self, user_id: str) -> Dict[str, Any]:
        """Get ROI dashboard for user"""
        if user_id not in self.user_roi:
            return {
                "message": "No execution history yet",
                "next_steps": "Create and execute your first workflow"
            }
        
        roi = self.user_roi[user_id]
        
        return {
            "user_id": user_id,
            "summary": {
                "total_workflows": len([e for e in self.execution_records if e["user_id"] == user_id]),
                "total_executions": roi["total_executions"],
                "success_rate": f"{roi['avg_success_rate']:.1f}%"
            },
            "roi_metrics": {
                "time_saved_hours": f"{roi['total_time_saved_hours']:.1f}",
                "time_saved_days": f"{roi['total_time_saved_hours'] / 8:.1f}",
                "cost_saved": f"${roi['total_cost_saved']:.2f}",
                "efficiency_gain": "90%"
            },
            "most_used": {
                "integrations": sorted(
                    roi["most_used_integrations"].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5],
                "workflows": self._get_top_workflows(user_id, limit=5)
            },
            "recommendations": self._get_user_recommendations(user_id)
        }
    
    def get_team_analytics(self, workspace_id: str, user_ids: List[str]) -> Dict[str, Any]:
        """Get team analytics"""
        team_executions = [e for e in self.execution_records if e["user_id"] in user_ids]
        
        if not team_executions:
            return {"message": "No team executions yet"}
        
        successful = [e for e in team_executions if e["success"]]
        durations = [e["duration_seconds"] for e in team_executions]
        
        total_time_saved = sum(e["duration_seconds"] * 9 for e in team_executions) / 3600
        total_cost_saved = total_time_saved * 50
        
        return {
            "workspace_id": workspace_id,
            "team_size": len(user_ids),
            "total_executions": len(team_executions),
            "successful_executions": len(successful),
            "success_rate": f"{len(successful) / len(team_executions) * 100:.1f}%",
            "avg_execution_time": f"{statistics.mean(durations):.1f}s",
            "roi": {
                "total_time_saved_hours": f"{total_time_saved:.1f}",
                "total_cost_saved": f"${total_cost_saved:.2f}",
                "avg_per_person": f"${total_cost_saved / len(user_ids):.2f}"
            },
            "top_workflows": self._get_team_top_workflows(user_ids, limit=5)
        }
    
    def calculate_roi_projection(self, user_id: str, months_ahead: int = 12) -> Dict[str, Any]:
        """Project ROI for future months"""
        if user_id not in self.user_roi:
            return {"error": "No execution history"}
        
        current_roi = self.user_roi[user_id]
        monthly_rate = current_roi["total_cost_saved"] / 1  # Normalize to monthly
        
        projections = []
        for month in range(1, months_ahead + 1):
            projected_savings = monthly_rate * month
            projections.append({
                "month": month,
                "projected_savings": f"${projected_savings:.2f}",
                "payoff_status": "Breakeven" if projected_savings >= 29 else "Not yet"
            })
        
        return {
            "user_id": user_id,
            "current_monthly_rate": f"${monthly_rate:.2f}",
            "projection_months": months_ahead,
            "total_projected_savings": f"${monthly_rate * months_ahead:.2f}",
            "payoff_month": next(
                (p["month"] for p in projections if float(p["projected_savings"].replace("$", "")) >= 29),
                "Never"
            ),
            "projections": projections
        }
    
    def _calculate_trend(self, workflow_id: str) -> Dict[str, str]:
        """Calculate success rate trend"""
        recent = [e for e in self.execution_records if e["workflow_id"] == workflow_id][-10:]
        if len(recent) < 2:
            return {"trend": "Insufficient data"}
        
        recent_success = sum(1 for e in recent if e["success"]) / len(recent)
        overall_success = (
            self.workflow_stats[workflow_id]["success_rate"] / 100
            if workflow_id in self.workflow_stats else 0
        )
        
        trend = "↑ Improving" if recent_success > overall_success else "↓ Declining"
        return {"trend": trend, "recent_success_rate": f"{recent_success * 100:.1f}%"}
    
    def _get_recommendations(self, workflow_id: str) -> List[str]:
        """Get recommendations for workflow"""
        stats = self.workflow_stats.get(workflow_id, {})
        recommendations = []
        
        if stats.get("success_rate", 0) < 70:
            recommendations.append("Success rate is low - consider adjusting workflow parameters")
        
        if stats.get("avg_duration", 0) > 60:
            recommendations.append("Execution is slow - consider simplifying or parallelizing steps")
        
        if stats.get("total_executions", 0) < 5:
            recommendations.append("Run more executions to gather better analytics")
        
        return recommendations or ["Workflow performing well!"]
    
    def _get_user_recommendations(self, user_id: str) -> List[str]:
        """Get recommendations for user"""
        roi = self.user_roi.get(user_id, {})
        recommendations = []
        
        if roi.get("total_executions", 0) < 10:
            recommendations.append("Run more workflows to maximize time savings")
        
        if len(roi.get("most_used_integrations", {})) < 3:
            recommendations.append("Try more integrations to automate different tasks")
        
        total_saved = roi.get("total_cost_saved", 0)
        if total_saved > 100 and len(roi.get("most_used_integrations", {})) > 0:
            recommendations.append("Great ROI! Consider upgrading to Pro plan for unlimited workflows")
        
        return recommendations or ["Keep automating!"]
    
    def _get_top_workflows(self, user_id: str, limit: int = 5) -> List[Dict]:
        """Get user's most-executed workflows"""
        user_workflows = {}
        for e in self.execution_records:
            if e["user_id"] == user_id:
                workflow_id = e["workflow_id"]
                if workflow_id not in user_workflows:
                    user_workflows[workflow_id] = {"name": e["workflow_name"], "count": 0}
                user_workflows[workflow_id]["count"] += 1
        
        return sorted(user_workflows.items(), key=lambda x: x[1]["count"], reverse=True)[:limit]
    
    def _get_team_top_workflows(self, user_ids: List[str], limit: int = 5) -> List[Dict]:
        """Get team's most-used workflows"""
        team_workflows = {}
        for e in self.execution_records:
            if e["user_id"] in user_ids:
                workflow_id = e["workflow_id"]
                if workflow_id not in team_workflows:
                    team_workflows[workflow_id] = {"name": e["workflow_name"], "count": 0}
                team_workflows[workflow_id]["count"] += 1
        
        return sorted(team_workflows.items(), key=lambda x: x[1]["count"], reverse=True)[:limit]


# Global instance
analytics_engine = AnalyticsEngine()
