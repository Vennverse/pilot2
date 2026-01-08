import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Plus, X, Trash2, Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { supabase } from "@/integrations/supabase/client";
import type { Provider } from "@/types/execution";

interface Action {
  id: string;
  name: string;
  description: string;
  params: string[];
  method?: string;
  endpoint?: string;
}

interface CreateCustomIntegrationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (integration: Provider) => void;
  editingIntegration?: Provider | null;
}

export const CreateCustomIntegrationModal = ({
  isOpen,
  onClose,
  editingIntegration,
  onSave,
}: CreateCustomIntegrationModalProps) => {
  const { toast } = useToast();
  const [name, setName] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [description, setDescription] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [authType, setAuthType] = useState<"api_key" | "oauth">("api_key");
  const [authHeader, setAuthHeader] = useState("Authorization");
  const [authPrefix, setAuthPrefix] = useState("Bearer");
  const [actions, setActions] = useState<Action[]>([]);
  const [saving, setSaving] = useState(false);
  const [newAction, setNewAction] = useState<Partial<Action>>({
    id: "",
    name: "",
    description: "",
    params: [],
    method: "POST",
    endpoint: "",
  });

  useEffect(() => {
    if (editingIntegration) {
      setName(editingIntegration.name);
      setDisplayName(editingIntegration.display_name);
      setBaseUrl((editingIntegration.oauth_config?.base_url as string) || "");
      setAuthType(editingIntegration.auth_type);
      // Load actions if available
      if (editingIntegration.actions) {
        setActions(editingIntegration.actions.map(a => ({
          id: a.id,
          name: a.name,
          description: a.description || "",
          params: a.params || [],
          method: "POST",
          endpoint: "",
        })));
      }
    } else {
      resetForm();
    }
  }, [editingIntegration]);

  const resetForm = () => {
    setName("");
    setDisplayName("");
    setDescription("");
    setBaseUrl("");
    setAuthType("api_key");
    setAuthHeader("Authorization");
    setAuthPrefix("Bearer");
    setActions([]);
    setNewAction({
      id: "",
      name: "",
      description: "",
      params: [],
      method: "POST",
      endpoint: "",
    });
  };

  const addAction = () => {
    if (!newAction.id || !newAction.name) {
      toast({
        title: "Action details required",
        description: "Please provide action ID and name",
        variant: "destructive",
      });
      return;
    }

    setActions([
      ...actions,
      {
        id: newAction.id!,
        name: newAction.name!,
        description: newAction.description || "",
        params: newAction.params || [],
        method: newAction.method || "POST",
        endpoint: newAction.endpoint || "",
      },
    ]);

    setNewAction({
      id: "",
      name: "",
      description: "",
      params: [],
      method: "POST",
      endpoint: "",
    });
  };

  const removeAction = (index: number) => {
    setActions(actions.filter((_, i) => i !== index));
  };

  const addParamToAction = (actionIndex: number, param: string) => {
    if (!param.trim()) return;
    const updated = [...actions];
    if (!updated[actionIndex].params) {
      updated[actionIndex].params = [];
    }
    updated[actionIndex].params.push(param.trim());
    setActions(updated);
  };

  const removeParamFromAction = (actionIndex: number, paramIndex: number) => {
    const updated = [...actions];
    updated[actionIndex].params = updated[actionIndex].params.filter(
      (_, i) => i !== paramIndex
    );
    setActions(updated);
  };

  const handleSave = async () => {
    if (!name || !displayName) {
      toast({
        title: "Required fields missing",
        description: "Please provide integration name and display name",
        variant: "destructive",
      });
      return;
    }

    if (actions.length === 0) {
      toast({
        title: "Actions required",
        description: "Please add at least one action",
        variant: "destructive",
      });
      return;
    }

    setSaving(true);

    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session?.user?.id) {
        throw new Error("User not authenticated");
      }

      const integrationData = {
        name: name.toLowerCase().replace(/\s+/g, "_"),
        display_name: displayName,
        description: description,
        auth_type: authType,
        oauth_config: {
          base_url: baseUrl,
          auth_header: authHeader,
          auth_prefix: authPrefix,
        },
        actions: actions.map((a) => ({
          id: a.id,
          name: a.name,
          description: a.description,
          method: a.method,
          endpoint: a.endpoint,
          params: a.params,
        })),
      };

      // Save to database via API
      const url = editingIntegration
        ? `/api/custom-integrations/${editingIntegration.id}?user_id=${session.user.id}`
        : `/api/custom-integrations?user_id=${session.user.id}`;

      const response = await fetch(url, {
        method: editingIntegration ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(integrationData),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || "Failed to save integration");
      }

      const savedIntegration = await response.json();

      // Format for Provider type
      const provider: Provider = {
        id: savedIntegration.id,
        name: savedIntegration.name,
        display_name: savedIntegration.display_name,
        auth_type: savedIntegration.auth_type,
        oauth_config: savedIntegration.oauth_config || {},
        actions: savedIntegration.actions || [],
        icon: "Puzzle",
        created_at: savedIntegration.created_at,
      };

      onSave(provider);
      toast({
        title: editingIntegration ? "Integration updated!" : "Integration created!",
        description: `${displayName} has been saved successfully.`,
      });
      resetForm();
      onClose();
    } catch (error) {
      console.error("Save integration error:", error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to save custom integration",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {editingIntegration ? "Edit Custom Integration" : "Create Custom Integration"}
          </DialogTitle>
          <DialogDescription>
            Add your own API integration with custom endpoints and actions
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Basic Information */}
          <div className="space-y-4 p-4 bg-muted/50 rounded-lg">
            <h3 className="font-semibold">Basic Information</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Integration Name (ID)</Label>
                <Input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="my_custom_api"
                />
              </div>
              <div className="space-y-2">
                <Label>Display Name</Label>
                <Input
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  placeholder="My Custom API"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Description (Optional)</Label>
              <Textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe what this integration does..."
                rows={2}
              />
            </div>
          </div>

          {/* API Configuration */}
          <div className="space-y-4 p-4 bg-muted/50 rounded-lg">
            <h3 className="font-semibold">API Configuration</h3>
            <div className="space-y-2">
              <Label>Base URL</Label>
              <Input
                value={baseUrl}
                onChange={(e) => setBaseUrl(e.target.value)}
                placeholder="https://api.example.com"
              />
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label>Auth Type</Label>
                <Select value={authType} onValueChange={(v: any) => setAuthType(v)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="api_key">API Key</SelectItem>
                    <SelectItem value="oauth">OAuth</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Auth Header Name</Label>
                <Input
                  value={authHeader}
                  onChange={(e) => setAuthHeader(e.target.value)}
                  placeholder="Authorization"
                />
              </div>
              <div className="space-y-2">
                <Label>Auth Prefix</Label>
                <Input
                  value={authPrefix}
                  onChange={(e) => setAuthPrefix(e.target.value)}
                  placeholder="Bearer"
                />
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="space-y-4 p-4 bg-muted/50 rounded-lg">
            <h3 className="font-semibold">Actions</h3>

            {/* Existing Actions */}
            {actions.map((action, actionIndex) => (
              <motion.div
                key={actionIndex}
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-4 border rounded-lg space-y-3"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium">{action.name}</h4>
                    <p className="text-sm text-muted-foreground">{action.description}</p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeAction(actionIndex)}
                    className="text-destructive"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-muted-foreground">Method:</span> {action.method}
                  </div>
                  <div>
                    <span className="text-muted-foreground">Endpoint:</span> {action.endpoint}
                  </div>
                </div>
                {action.params.length > 0 && (
                  <div>
                    <span className="text-sm text-muted-foreground">Parameters: </span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {action.params.map((param, paramIndex) => (
                        <span
                          key={paramIndex}
                          className="text-xs px-2 py-1 bg-secondary rounded"
                        >
                          {param}
                          <button
                            onClick={() => removeParamFromAction(actionIndex, paramIndex)}
                            className="ml-1 text-destructive"
                          >
                            ×
                          </button>
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </motion.div>
            ))}

            {/* Add New Action */}
            <div className="p-4 border-2 border-dashed rounded-lg space-y-3">
              <h4 className="font-medium">Add New Action</h4>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Action ID</Label>
                  <Input
                    value={newAction.id}
                    onChange={(e) => setNewAction({ ...newAction, id: e.target.value })}
                    placeholder="create_item"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Action Name</Label>
                  <Input
                    value={newAction.name}
                    onChange={(e) => setNewAction({ ...newAction, name: e.target.value })}
                    placeholder="Create Item"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Description</Label>
                <Input
                  value={newAction.description}
                  onChange={(e) => setNewAction({ ...newAction, description: e.target.value })}
                  placeholder="Creates a new item in the system"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>HTTP Method</Label>
                  <Select
                    value={newAction.method}
                    onValueChange={(v) => setNewAction({ ...newAction, method: v })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="GET">GET</SelectItem>
                      <SelectItem value="POST">POST</SelectItem>
                      <SelectItem value="PUT">PUT</SelectItem>
                      <SelectItem value="PATCH">PATCH</SelectItem>
                      <SelectItem value="DELETE">DELETE</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Endpoint</Label>
                  <Input
                    value={newAction.endpoint}
                    onChange={(e) => setNewAction({ ...newAction, endpoint: e.target.value })}
                    placeholder="/api/v1/items"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Parameters (comma-separated)</Label>
                <Input
                  placeholder="name, email, phone"
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      const params = e.currentTarget.value
                        .split(",")
                        .map((p) => p.trim())
                        .filter((p) => p);
                      setNewAction({ ...newAction, params });
                    }
                  }}
                />
                {newAction.params && newAction.params.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-1">
                    {newAction.params.map((param, idx) => (
                      <span key={idx} className="text-xs px-2 py-1 bg-secondary rounded">
                        {param}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              <Button onClick={addAction} variant="outline" size="sm">
                <Plus className="w-4 h-4 mr-2" />
                Add Action
              </Button>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={saving || actions.length === 0}>
            <Save className="w-4 h-4 mr-2" />
            {saving ? "Saving..." : editingIntegration ? "Update" : "Create Integration"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
