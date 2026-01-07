import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Webhook, Clock, MousePointerClick, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
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
import type { Trigger } from "@/types/execution";

interface TriggerConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  planId: string;
  currentTrigger?: Trigger;
  enabled?: boolean;
  onSave: (trigger: Trigger | null, enabled: boolean) => void;
}

export const TriggerConfigModal = ({
  isOpen,
  onClose,
  planId,
  currentTrigger,
  enabled = false,
  onSave,
}: TriggerConfigModalProps) => {
  const { toast } = useToast();
  const [triggerType, setTriggerType] = useState<"manual" | "webhook" | "schedule" | "event">(
    currentTrigger?.type || "manual"
  );
  const [isEnabled, setIsEnabled] = useState(enabled);
  const [webhookPath, setWebhookPath] = useState("");
  const [cronExpression, setCronExpression] = useState("");
  const [timezone, setTimezone] = useState("UTC");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (currentTrigger) {
      setTriggerType(currentTrigger.type);
      if (currentTrigger.config) {
        setWebhookPath(currentTrigger.config.webhook_path || "");
        setCronExpression(currentTrigger.config.cron_expression || "");
        setTimezone(currentTrigger.config.timezone || "UTC");
      }
    }
    setIsEnabled(enabled);
  }, [currentTrigger, enabled]);

  const generateWebhookPath = () => {
    const randomId = Math.random().toString(36).substring(2, 15);
    setWebhookPath(`trigger-${randomId}`);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      let trigger: Trigger | null = null;

      if (triggerType === "manual") {
        trigger = { type: "manual" };
      } else if (triggerType === "webhook") {
        if (!webhookPath) {
          toast({
            title: "Webhook path required",
            description: "Please enter a webhook path",
            variant: "destructive",
          });
          setSaving(false);
          return;
        }
        trigger = {
          type: "webhook",
          config: {
            webhook_path: webhookPath,
          },
        };
      } else if (triggerType === "schedule") {
        if (!cronExpression) {
          toast({
            title: "Cron expression required",
            description: "Please enter a cron expression (e.g., '0 9 * * *' for daily at 9 AM)",
            variant: "destructive",
          });
          setSaving(false);
          return;
        }
        trigger = {
          type: "schedule",
          config: {
            cron_expression: cronExpression,
            timezone,
          },
        };
      }

      const response = await fetch(`/api/execution-plans/${planId}/trigger`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ trigger, enabled: isEnabled }),
      });

      if (!response.ok) throw new Error("Failed to save trigger");

      onSave(trigger, isEnabled);
      toast({
        title: "Trigger configured!",
        description: `Workflow ${isEnabled ? "enabled" : "disabled"} with ${triggerType} trigger.`,
      });
      onClose();
    } catch (error) {
      console.error("Save trigger error:", error);
      toast({
        title: "Error",
        description: "Failed to save trigger configuration",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  const webhookUrl = triggerType === "webhook" && webhookPath
    ? `${window.location.origin}/api/webhook/${webhookPath}`
    : "";

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Configure Trigger</DialogTitle>
          <DialogDescription>
            Set how this workflow should be triggered
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Trigger Type Selection */}
          <div className="space-y-2">
            <Label>Trigger Type</Label>
            <Select value={triggerType} onValueChange={(v: any) => setTriggerType(v)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="manual">
                  <div className="flex items-center gap-2">
                    <MousePointerClick className="w-4 h-4" />
                    Manual (Run on demand)
                  </div>
                </SelectItem>
                <SelectItem value="webhook">
                  <div className="flex items-center gap-2">
                    <Webhook className="w-4 h-4" />
                    Webhook (Trigger via HTTP)
                  </div>
                </SelectItem>
                <SelectItem value="schedule">
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4" />
                    Schedule (Cron-based)
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Webhook Configuration */}
          {triggerType === "webhook" && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-4 p-4 bg-muted/50 rounded-lg"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Webhook Path</Label>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={generateWebhookPath}
                  >
                    Generate
                  </Button>
                </div>
                <Input
                  value={webhookPath}
                  onChange={(e) => setWebhookPath(e.target.value)}
                  placeholder="trigger-abc123"
                />
                <p className="text-xs text-muted-foreground">
                  Your webhook URL will be:{" "}
                  <code className="bg-background px-1 py-0.5 rounded text-xs">
                    {webhookUrl || "..."}
                  </code>
                </p>
              </div>
            </motion.div>
          )}

          {/* Schedule Configuration */}
          {triggerType === "schedule" && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-4 p-4 bg-muted/50 rounded-lg"
            >
              <div className="space-y-2">
                <Label>Cron Expression</Label>
                <Input
                  value={cronExpression}
                  onChange={(e) => setCronExpression(e.target.value)}
                  placeholder="0 9 * * * (Daily at 9 AM)"
                />
                <p className="text-xs text-muted-foreground">
                  Format: minute hour day month weekday
                  <br />
                  Examples: <code className="bg-background px-1 py-0.5 rounded">0 9 * * *</code> (Daily at 9 AM),{" "}
                  <code className="bg-background px-1 py-0.5 rounded">*/15 * * * *</code> (Every 15 minutes)
                </p>
              </div>
              <div className="space-y-2">
                <Label>Timezone</Label>
                <Select value={timezone} onValueChange={setTimezone}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="UTC">UTC</SelectItem>
                    <SelectItem value="America/New_York">Eastern Time</SelectItem>
                    <SelectItem value="America/Chicago">Central Time</SelectItem>
                    <SelectItem value="America/Denver">Mountain Time</SelectItem>
                    <SelectItem value="America/Los_Angeles">Pacific Time</SelectItem>
                    <SelectItem value="Europe/London">London</SelectItem>
                    <SelectItem value="Asia/Tokyo">Tokyo</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </motion.div>
          )}

          {/* Enable/Disable Toggle */}
          <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
            <div className="space-y-0.5">
              <Label>Workflow Status</Label>
              <p className="text-sm text-muted-foreground">
                {isEnabled ? "Workflow is active and will trigger automatically" : "Workflow is paused"}
              </p>
            </div>
            <Switch checked={isEnabled} onCheckedChange={setIsEnabled} />
          </div>
        </div>

        <DialogFooter>
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={saving}>
            {saving ? "Saving..." : "Save Trigger"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
