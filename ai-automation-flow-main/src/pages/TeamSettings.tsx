import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Users, Settings, Plus, Trash2, Shield, LogOut } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface WorkspaceMember {
  id: string;
  email: string;
  role: "ADMIN" | "EDITOR" | "VIEWER" | "GUEST";
  joinedAt: string;
}

interface Workspace {
  id: string;
  name: string;
  description: string;
  role: string;
  memberCount: number;
}

export default function TeamSettings() {
  const { toast } = useToast();
  const [user, setUser] = useState<any>(null);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [currentWorkspace, setCurrentWorkspace] = useState<string | null>(null);
  const [members, setMembers] = useState<WorkspaceMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [memberEmail, setMemberEmail] = useState("");
  const [memberRole, setMemberRole] = useState("EDITOR");
  const [inviteLink, setInviteLink] = useState<string | null>(null);
  const [showNewWorkspace, setShowNewWorkspace] = useState(false);
  const [newWorkspaceName, setNewWorkspaceName] = useState("");
  const [auditLogs, setAuditLogs] = useState<any[]>([]);

  useEffect(() => {
    const user_id = localStorage.getItem("user_id");
    setUser({ id: user_id });
    if (user_id) {
      fetchWorkspaces(user_id);
    }
  }, []);

  useEffect(() => {
    if (currentWorkspace) {
      fetchWorkspaceMembers(currentWorkspace);
      fetchAuditLog(currentWorkspace);
    }
  }, [currentWorkspace]);

  const fetchWorkspaces = async (user_id: string) => {
    try {
      const response = await fetch(`/api/team/workspaces?user_id=${user_id}`);
      if (!response.ok) throw new Error("Failed to fetch workspaces");
      const data = await response.json();
      setWorkspaces(Array.isArray(data) ? data : []);
      if (data.length > 0) {
        setCurrentWorkspace(data[0].id);
      }
    } catch (error) {
      console.error("Error fetching workspaces:", error);
      toast({
        title: "Error",
        description: "Failed to load workspaces",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchWorkspaceMembers = async (workspace_id: string) => {
    try {
      const response = await fetch(`/api/team/workspaces/${workspace_id}/members`);
      if (!response.ok) throw new Error("Failed to fetch members");
      const data = await response.json();
      setMembers(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error("Error fetching members:", error);
    }
  };

  const fetchAuditLog = async (workspace_id: string) => {
    try {
      const response = await fetch(`/api/team/workspaces/${workspace_id}/audit-log?limit=10`);
      if (!response.ok) throw new Error("Failed to fetch audit log");
      const data = await response.json();
      setAuditLogs(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error("Error fetching audit log:", error);
    }
  };

  const handleAddMember = async () => {
    if (!currentWorkspace || !memberEmail) {
      toast({
        title: "Error",
        description: "Please enter member email",
        variant: "destructive",
      });
      return;
    }

    try {
      const response = await fetch(`/api/team/workspaces/${currentWorkspace}/members`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: user?.id,
          member_email: memberEmail,
          role: memberRole,
        }),
      });

      if (!response.ok) throw new Error("Failed to add member");

      toast({
        title: "Success",
        description: `Added ${memberEmail} as ${memberRole}`,
      });

      setMemberEmail("");
      setMemberRole("EDITOR");
      fetchWorkspaceMembers(currentWorkspace);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to add member",
        variant: "destructive",
      });
    }
  };

  const handleCreateInvite = async () => {
    if (!currentWorkspace) return;

    try {
      const response = await fetch(`/api/team/workspaces/${currentWorkspace}/invite`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: user?.id,
          role: "EDITOR",
          max_uses: 10,
        }),
      });

      if (!response.ok) throw new Error("Failed to generate invite");
      const data = await response.json();
      setInviteLink(`${window.location.origin}/invite/${data.invite_code}`);

      toast({
        title: "Success",
        description: "Invite link generated",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to generate invite",
        variant: "destructive",
      });
    }
  };

  const handleCreateWorkspace = async () => {
    if (!newWorkspaceName || !user?.id) return;

    try {
      const response = await fetch("/api/team/workspaces", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: user.id,
          name: newWorkspaceName,
          description: "",
        }),
      });

      if (!response.ok) throw new Error("Failed to create workspace");

      toast({
        title: "Success",
        description: "Workspace created",
      });

      setNewWorkspaceName("");
      setShowNewWorkspace(false);
      fetchWorkspaces(user.id);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to create workspace",
        variant: "destructive",
      });
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-white">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <h1 className="text-4xl font-bold text-white mb-8">Team Settings</h1>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Workspaces List */}
          <div className="lg:col-span-1">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Shield className="w-5 h-5" />
                  Workspaces
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {workspaces.map((ws) => (
                  <button
                    key={ws.id}
                    onClick={() => setCurrentWorkspace(ws.id)}
                    className={`w-full text-left p-3 rounded-lg transition-colors ${
                      currentWorkspace === ws.id
                        ? "bg-purple-600 text-white"
                        : "bg-slate-700 text-gray-300 hover:bg-slate-600"
                    }`}
                  >
                    <div className="font-semibold">{ws.name}</div>
                    <div className="text-xs opacity-75">{ws.memberCount} members</div>
                  </button>
                ))}

                {showNewWorkspace ? (
                  <div className="space-y-2">
                    <Input
                      placeholder="Workspace name"
                      value={newWorkspaceName}
                      onChange={(e) => setNewWorkspaceName(e.target.value)}
                      className="bg-slate-700 border-slate-600"
                    />
                    <Button onClick={handleCreateWorkspace} size="sm" className="w-full">
                      Create
                    </Button>
                  </div>
                ) : (
                  <Button
                    onClick={() => setShowNewWorkspace(true)}
                    variant="outline"
                    className="w-full"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    New Workspace
                  </Button>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {currentWorkspace && (
              <>
                {/* Add Member */}
                <Card className="bg-slate-800 border-slate-700">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center gap-2">
                      <Users className="w-5 h-5" />
                      Add Team Member
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex gap-2">
                      <Input
                        placeholder="Email address"
                        value={memberEmail}
                        onChange={(e) => setMemberEmail(e.target.value)}
                        className="bg-slate-700 border-slate-600"
                      />
                      <Select value={memberRole} onValueChange={setMemberRole}>
                        <SelectTrigger className="w-32 bg-slate-700 border-slate-600">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="ADMIN">Admin</SelectItem>
                          <SelectItem value="EDITOR">Editor</SelectItem>
                          <SelectItem value="VIEWER">Viewer</SelectItem>
                          <SelectItem value="GUEST">Guest</SelectItem>
                        </SelectContent>
                      </Select>
                      <Button onClick={handleAddMember}>Add</Button>
                    </div>

                    <Button
                      onClick={handleCreateInvite}
                      variant="outline"
                      className="w-full"
                    >
                      Generate Invite Link
                    </Button>

                    {inviteLink && (
                      <div className="bg-slate-700 p-3 rounded-lg">
                        <p className="text-xs text-gray-400 mb-2">Share this link:</p>
                        <Input
                          value={inviteLink}
                          readOnly
                          className="bg-slate-600 border-slate-500 text-white text-xs"
                        />
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => {
                            navigator.clipboard.writeText(inviteLink);
                            toast({ title: "Copied to clipboard" });
                          }}
                          className="mt-2"
                        >
                          Copy Link
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Current Members */}
                <Card className="bg-slate-800 border-slate-700">
                  <CardHeader>
                    <CardTitle className="text-white">Team Members</CardTitle>
                    <CardDescription className="text-gray-400">
                      {members.length} member{members.length !== 1 ? "s" : ""}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {members.map((member) => (
                        <div
                          key={member.id}
                          className="flex items-center justify-between p-3 bg-slate-700 rounded-lg"
                        >
                          <div>
                            <div className="font-semibold text-white">{member.email}</div>
                            <div className="text-xs text-gray-400">
                              Joined {new Date(member.joinedAt).toLocaleDateString()}
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge variant="outline">{member.role}</Badge>
                            <Button size="sm" variant="ghost" className="text-red-400">
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Audit Log */}
                <Card className="bg-slate-800 border-slate-700">
                  <CardHeader>
                    <CardTitle className="text-white">Audit Log</CardTitle>
                    <CardDescription className="text-gray-400">Recent team activity</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {auditLogs.slice(0, 5).map((log, idx) => (
                        <div key={idx} className="text-sm text-gray-300 py-2 border-b border-slate-700">
                          <div className="font-semibold text-white">{log.action}</div>
                          <div className="text-xs text-gray-500">
                            {new Date(log.timestamp).toLocaleString()}
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
