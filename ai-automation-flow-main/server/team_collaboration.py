"""
Team Collaboration System - Multi-user workspaces with role-based access
Roles: Admin, Editor, Viewer
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import uuid


class UserRole(Enum):
    ADMIN = "admin"        # Full access, manage team
    EDITOR = "editor"      # Create/edit workflows, execute
    VIEWER = "viewer"      # View only, can't execute
    GUEST = "guest"        # Temporary access


class Workspace:
    """Shared workspace for team collaboration"""
    
    def __init__(self, workspace_id: str, name: str, owner_id: str):
        self.workspace_id = workspace_id
        self.name = name
        self.owner_id = owner_id
        self.created_at = datetime.now().isoformat()
        self.members = {owner_id: UserRole.ADMIN.value}
        self.shared_workflows = {}  # workflow_id -> metadata
        self.shared_integrations = {}  # integration_id -> metadata
        self.audit_log = []
    
    def add_member(self, user_id: str, role: str = UserRole.EDITOR.value) -> bool:
        """Add team member to workspace"""
        if user_id in self.members:
            return False
        
        self.members[user_id] = role
        self._log_action("member_added", {"user_id": user_id, "role": role})
        return True
    
    def remove_member(self, user_id: str) -> bool:
        """Remove team member"""
        if user_id == self.owner_id:
            return False  # Can't remove owner
        
        if user_id in self.members:
            del self.members[user_id]
            self._log_action("member_removed", {"user_id": user_id})
            return True
        return False
    
    def change_member_role(self, user_id: str, new_role: str) -> bool:
        """Change member's role"""
        if user_id not in self.members:
            return False
        
        old_role = self.members[user_id]
        self.members[user_id] = new_role
        self._log_action("role_changed", {
            "user_id": user_id,
            "old_role": old_role,
            "new_role": new_role
        })
        return True
    
    def can_user_access(self, user_id: str) -> bool:
        """Check if user has access"""
        return user_id in self.members
    
    def can_user_edit(self, user_id: str) -> bool:
        """Check if user can edit"""
        role = self.members.get(user_id)
        return role in [UserRole.ADMIN.value, UserRole.EDITOR.value]
    
    def can_user_execute(self, user_id: str) -> bool:
        """Check if user can execute workflows"""
        role = self.members.get(user_id)
        return role in [UserRole.ADMIN.value, UserRole.EDITOR.value]
    
    def can_user_manage(self, user_id: str) -> bool:
        """Check if user can manage workspace"""
        role = self.members.get(user_id)
        return role == UserRole.ADMIN.value
    
    def share_workflow(self, workflow_id: str, user_ids: List[str], 
                      permission: str = "edit") -> bool:
        """Share workflow with specific users"""
        self.shared_workflows[workflow_id] = {
            "shared_with": user_ids,
            "permission": permission,
            "shared_at": datetime.now().isoformat()
        }
        self._log_action("workflow_shared", {
            "workflow_id": workflow_id,
            "user_ids": user_ids,
            "permission": permission
        })
        return True
    
    def share_integration(self, integration_id: str, user_ids: List[str]) -> bool:
        """Share integration credential with users"""
        self.shared_integrations[integration_id] = {
            "shared_with": user_ids,
            "shared_at": datetime.now().isoformat()
        }
        self._log_action("integration_shared", {
            "integration_id": integration_id,
            "user_ids": user_ids
        })
        return True
    
    def _log_action(self, action: str, details: Dict):
        """Log workspace action for audit"""
        self.audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details
        })
    
    def get_audit_log(self, limit: int = 100) -> List[Dict]:
        """Get workspace audit log"""
        return self.audit_log[-limit:]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "workspace_id": self.workspace_id,
            "name": self.name,
            "owner_id": self.owner_id,
            "created_at": self.created_at,
            "members": self.members,
            "shared_workflows": self.shared_workflows,
            "shared_integrations": self.shared_integrations
        }


class TeamCollaborationManager:
    """Manage team workspaces and permissions"""
    
    def __init__(self):
        self.workspaces = {}  # workspace_id -> Workspace
        self.user_workspaces = {}  # user_id -> [workspace_ids]
    
    def create_workspace(self, name: str, owner_id: str) -> Workspace:
        """Create new workspace"""
        workspace_id = str(uuid.uuid4())
        workspace = Workspace(workspace_id, name, owner_id)
        
        self.workspaces[workspace_id] = workspace
        if owner_id not in self.user_workspaces:
            self.user_workspaces[owner_id] = []
        self.user_workspaces[owner_id].append(workspace_id)
        
        return workspace
    
    def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        """Get workspace by ID"""
        return self.workspaces.get(workspace_id)
    
    def get_user_workspaces(self, user_id: str) -> List[Workspace]:
        """Get all workspaces user is member of"""
        workspace_ids = self.user_workspaces.get(user_id, [])
        workspaces = [self.workspaces[wid] for wid in workspace_ids if wid in self.workspaces]
        
        # Include workspaces where user is member but not owner
        for workspace in self.workspaces.values():
            if user_id in workspace.members and workspace.workspace_id not in workspace_ids:
                workspaces.append(workspace)
        
        return workspaces
    
    def add_member_to_workspace(self, workspace_id: str, user_id: str, 
                               role: str = UserRole.EDITOR.value,
                               added_by: str = None) -> bool:
        """Add member to workspace"""
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return False
        
        # Only admins can add members
        if added_by and not workspace.can_user_manage(added_by):
            return False
        
        if workspace.add_member(user_id, role):
            if user_id not in self.user_workspaces:
                self.user_workspaces[user_id] = []
            if workspace_id not in self.user_workspaces[user_id]:
                self.user_workspaces[user_id].append(workspace_id)
            return True
        
        return False
    
    def generate_invite_link(self, workspace_id: str, role: str = UserRole.EDITOR.value) -> str:
        """Generate shareable invite link"""
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return None
        
        invite_code = str(uuid.uuid4())[:8]
        workspace.invite_codes = getattr(workspace, "invite_codes", {})
        workspace.invite_codes[invite_code] = {
            "role": role,
            "created_at": datetime.now().isoformat(),
            "used_count": 0,
            "max_uses": -1  # Unlimited
        }
        
        return f"https://automation.platform/join/{workspace_id}/{invite_code}"
    
    def accept_invite(self, workspace_id: str, invite_code: str, user_id: str) -> bool:
        """Accept workspace invite"""
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return False
        
        invite_codes = getattr(workspace, "invite_codes", {})
        if invite_code not in invite_codes:
            return False
        
        invite = invite_codes[invite_code]
        role = invite["role"]
        
        return self.add_member_to_workspace(workspace_id, user_id, role)
    
    def get_workspace_permissions(self, workspace_id: str, user_id: str) -> Dict[str, bool]:
        """Get user's permissions in workspace"""
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return {}
        
        return {
            "can_access": workspace.can_user_access(user_id),
            "can_edit": workspace.can_user_edit(user_id),
            "can_execute": workspace.can_user_execute(user_id),
            "can_manage": workspace.can_user_manage(user_id)
        }
    
    def get_team_analytics(self, workspace_id: str) -> Dict[str, Any]:
        """Get analytics for entire team"""
        workspace = self.get_workspace(workspace_id)
        if not workspace:
            return {}
        
        return {
            "workspace_id": workspace_id,
            "workspace_name": workspace.name,
            "total_members": len(workspace.members),
            "members": [
                {
                    "user_id": user_id,
                    "role": role,
                    "email": f"user{user_id[-4:]}@company.com"  # Placeholder
                }
                for user_id, role in workspace.members.items()
            ],
            "shared_workflows": len(workspace.shared_workflows),
            "shared_integrations": len(workspace.shared_integrations),
            "recent_activity": workspace.get_audit_log(10)
        }


# Global instance
team_manager = TeamCollaborationManager()
