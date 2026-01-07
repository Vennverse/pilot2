import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, Play, Save, Copy, Trash2, Settings, Clock, CheckCircle, XCircle, AlertCircle, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { DashboardHeader } from "@/components/dashboard/DashboardHeader";
import { WorkflowBuilder } from "@/components/dashboard/WorkflowBuilder";
import { TriggerConfigModal } from "@/components/dashboard/TriggerConfigModal";
import { useToast } from "@/hooks/use-toast";
import { supabase } from "@/integrations/supabase/client";
import type { ExecutionPlan, PlanStep } from "@/types/execution";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const WorkflowEditor = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [plan, setPlan] = useState<ExecutionPlan | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showTriggerModal, setShowTriggerModal] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

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
    if (id && user) {
      fetchPlan();
    }
  }, [id, user]);

  const fetchPlan = async () => {
    if (!user || !id) return;
    
    try {
      const response = await fetch(`/api/execution-plans?user_id=${user.id}`);
      if (!response.ok) throw new Error("Failed to fetch plan");
      const data = await response.json();
      const foundPlan = data.find((p: ExecutionPlan) => p.id === id);
      if (foundPlan) {
        setPlan(foundPlan);
      } else {
        toast({
          title: "Workflow not found",
          description: "The workflow you're looking for doesn't exist.",
          variant: "destructive",
        });
        navigate("/dashboard");
      }
    } catch (error) {
      console.error("Error fetching plan:", error);
      toast({
        title: "Error",
        description: "Failed to load workflow",
        variant: "destructive",
      });
    }
  };

  const handleSave = async () => {
    if (!plan || !user) return;
    
    try {
      const response = await fetch(`/api/execution-plans/${plan.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(plan),
      });

      if (!response.ok) throw new Error("Failed to save");
      
      toast({
        title: "Workflow saved",
        description: "Your changes have been saved successfully.",
      });
      setHasChanges(false);
    } catch (error) {
      toast({
        title: "Save failed",
        description: error instanceof Error ? error.message : "Failed to save workflow",
        variant: "destructive",
      });
    }
  };

  const handleExecute = async () => {
    if (!plan) return;
    setIsExecuting(true);

    try {
      const response = await fetch("/api/execute-plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ execution_plan_id: plan.id }),
      });

      if (!response.ok) throw new Error("Failed to execute");

      const result = await response.json();

      if (result.status === "success") {
        toast({
          title: "Execution complete!",
          description: `Workflow executed successfully with ${result.logs?.length || 0} steps.`,
        });
      } else {
        toast({
          title: "Execution finished with issues",
          description: result.logs?.find((l: any) => l.status === "failed")?.message || "Some steps failed",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Execution failed",
        description: error instanceof Error ? error.message : "Unknown error",
        variant: "destructive",
      });
    } finally {
      setIsExecuting(false);
    }
  };

  const handleDuplicate = async () => {
    if (!plan || !user) return;

    try {
      const newPlan = {
        ...plan,
        name: `${plan.name} (Copy)`,
        id: undefined,
        created_at: new Date().toISOString(),
      };

      const response = await fetch("/api/execution-plans", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newPlan),
      });

      if (!response.ok) throw new Error("Failed to duplicate");

      const duplicated = await response.json();
      toast({
        title: "Workflow duplicated",
        description: "The workflow has been duplicated successfully.",
      });
      navigate(`/workflow/${duplicated.id}`);
    } catch (error) {
      toast({
        title: "Duplication failed",
        description: error instanceof Error ? error.message : "Failed to duplicate workflow",
        variant: "destructive",
      });
    }
  };

  const handleDelete = async () => {
    if (!plan) return;

    try {
      const response = await fetch(`/api/execution-plans/${plan.id}`, {
        method: "DELETE",
      });

      if (!response.ok) throw new Error("Failed to delete");

      toast({
        title: "Workflow deleted",
        description: "The workflow has been deleted successfully.",
      });
      navigate("/dashboard");
    } catch (error) {
      toast({
        title: "Deletion failed",
        description: error instanceof Error ? error.message : "Failed to delete workflow",
        variant: "destructive",
      });
    }
  };

  const handleStepsChange = (steps: PlanStep[]) => {
    if (!plan) return;
    setPlan({ ...plan, plan_json: steps });
    setHasChanges(true);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "approved":
      case "active":
        return "bg-green-500/20 text-green-400 border-green-500/30";
      case "paused":
        return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30";
      case "failed":
        return "bg-red-500/20 text-red-400 border-red-500/30";
      default:
        return "bg-gray-500/20 text-gray-400 border-gray-500/30";
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!user) {
    navigate("/auth");
    return null;
  }

  if (!plan) {
    return (
      <div className="min-h-screen bg-background">
        <DashboardHeader userEmail={user?.email} />
        <main className="container px-4 py-8">
          <div className="space-y-4">
            <Skeleton className="h-12 w-64" />
            <Skeleton className="h-96 w-full" />
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <DashboardHeader userEmail={user?.email} />

      <main className="container px-4 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate("/dashboard")}
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </Button>
              <div>
                <h1 className="text-3xl font-bold flex items-center gap-3">
                  {plan.name}
                  <Badge className={getStatusColor(plan.status)} variant="outline">
                    {plan.status}
                  </Badge>
                  {plan.enabled && (
                    <Badge className="bg-primary/20 text-primary border-primary/30" variant="outline">
                      <div className="w-2 h-2 rounded-full bg-primary animate-pulse mr-2" />
                      Active
                    </Badge>
                  )}
                </h1>
                <p className="text-muted-foreground mt-1">{plan.original_prompt}</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="sm">
                    <Settings className="w-4 h-4 mr-2" />
                    Actions
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={handleDuplicate}>
                    <Copy className="w-4 h-4 mr-2" />
                    Duplicate
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => setShowTriggerModal(true)}>
                    <Settings className="w-4 h-4 mr-2" />
                    Configure Trigger
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onClick={() => setShowDeleteDialog(true)}
                    className="text-destructive"
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Delete
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>

              {hasChanges && (
                <Button onClick={handleSave} variant="outline" size="sm">
                  <Save className="w-4 h-4 mr-2" />
                  Save Changes
                </Button>
              )}
              <Button
                onClick={handleExecute}
                disabled={isExecuting || plan.status !== "approved"}
                size="sm"
                variant="hero"
              >
                {isExecuting ? (
                  <>
                    <Clock className="w-4 h-4 mr-2 animate-spin" />
                    Executing...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2" />
                    Execute
                  </>
                )}
              </Button>
            </div>
          </div>

          {/* Metadata */}
          <div className="flex items-center gap-6 text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4" />
              Created {new Date(plan.created_at).toLocaleDateString()}
            </div>
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4" />
              {plan.plan_json?.length || 0} steps
            </div>
            {plan.required_providers && plan.required_providers.length > 0 && (
              <div className="flex items-center gap-2">
                <span>Providers:</span>
                <div className="flex gap-1">
                  {plan.required_providers.map((p) => (
                    <Badge key={p} variant="secondary" className="text-xs">
                      {p}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        </motion.div>

        {/* Workflow Builder */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="glass rounded-2xl p-6 border border-white/5"
        >
          <WorkflowBuilder
            steps={plan.plan_json || []}
            onStepsChange={handleStepsChange}
            readOnly={false}
          />
        </motion.div>

        {/* Missing Auth Warning */}
        {plan.missing_auth && plan.missing_auth.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-6 glass rounded-xl p-4 border border-yellow-500/30 bg-yellow-500/5"
          >
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-yellow-400 mt-0.5" />
              <div className="flex-1">
                <h3 className="font-semibold mb-1">Missing Authentication</h3>
                <p className="text-sm text-muted-foreground mb-3">
                  The following providers need to be connected:
                </p>
                <div className="flex flex-wrap gap-2 mb-3">
                  {plan.missing_auth.map((provider) => (
                    <Badge key={provider} variant="destructive" className="text-xs">
                      {provider}
                    </Badge>
                  ))}
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate("/settings")}
                >
                  Connect Providers
                </Button>
              </div>
            </div>
          </motion.div>
        )}
      </main>

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Workflow</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{plan.name}"? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeleteDialog(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDelete}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Trigger Config Modal */}
      {showTriggerModal && plan && (
        <TriggerConfigModal
          isOpen={showTriggerModal}
          onClose={() => setShowTriggerModal(false)}
          planId={plan.id}
          currentTrigger={plan.trigger}
          enabled={plan.enabled ?? false}
          onSave={(trigger, enabled) => {
            setPlan({ ...plan, trigger, enabled });
            setShowTriggerModal(false);
            fetchPlan();
          }}
        />
      )}
    </div>
  );
};

export default WorkflowEditor;
