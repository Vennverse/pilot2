import { motion } from "framer-motion";
import { Play, MoreVertical, Loader2, Zap, Settings, Webhook, Clock, MousePointerClick, Edit, Copy, Trash2, ExternalLink } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import type { ExecutionPlan } from "@/types/execution";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useState } from "react";

interface ExecutionPlanCardProps {
  plan: ExecutionPlan;
  onExecute: (id: string) => void;
  onConfigureTrigger?: (plan: ExecutionPlan) => void;
  onDuplicate?: (plan: ExecutionPlan) => void;
  onDelete?: (plan: ExecutionPlan) => void;
  isExecuting?: boolean;
}

export const ExecutionPlanCard = ({ 
  plan, 
  onExecute, 
  onConfigureTrigger, 
  onDuplicate,
  onDelete,
  isExecuting 
}: ExecutionPlanCardProps) => {
  const navigate = useNavigate();
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins} min ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const getTriggerIcon = () => {
    if (!plan.trigger) return <MousePointerClick className="w-3 h-3" />;
    switch (plan.trigger.type) {
      case "webhook":
        return <Webhook className="w-3 h-3" />;
      case "schedule":
        return <Clock className="w-3 h-3" />;
      default:
        return <MousePointerClick className="w-3 h-3" />;
    }
  };

  const getTriggerLabel = () => {
    if (!plan.trigger) return "Manual";
    switch (plan.trigger.type) {
      case "webhook":
        return "Webhook";
      case "schedule":
        return "Scheduled";
      default:
        return "Manual";
    }
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      whileHover={{ y: -5 }}
      className="glass rounded-2xl p-6 group relative overflow-hidden border border-white/5 hover:border-primary/50 transition-all duration-300 shadow-xl cursor-pointer"
      onClick={(e) => {
        // Don't navigate if clicking on buttons or dropdown
        const target = e.target as HTMLElement;
        if (!target.closest('button') && !target.closest('[role="menu"]')) {
          navigate(`/workflow/${plan.id}`);
        }
      }}
    >
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
      
      <div className="relative z-10">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-4">
            <div className={`w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center glow transition-transform group-hover:scale-110`}>
              <Zap className={`w-6 h-6 text-primary`} />
            </div>
            <div>
              <h3 className="text-xl font-bold text-foreground group-hover:text-primary transition-colors">{plan.name}</h3>
              <div className="flex items-center gap-2 mt-1">
                <div className={`inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider ${plan.enabled ? 'text-primary' : 'text-muted-foreground'}`}>
                  <span className={`w-2 h-2 rounded-full ${plan.enabled ? 'bg-primary animate-pulse' : 'bg-muted-foreground'}`} />
                  {plan.enabled ? "Active" : "Paused"}
                </div>
                {plan.trigger && (
                  <Badge variant="outline" className="text-xs flex items-center gap-1">
                    {getTriggerIcon()}
                    {getTriggerLabel()}
                  </Badge>
                )}
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {onConfigureTrigger && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onConfigureTrigger(plan)}
                className="opacity-0 group-hover:opacity-100 transition-all"
              >
                <Settings className="w-4 h-4" />
              </Button>
            )}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button 
                  className="p-2 rounded-xl opacity-0 group-hover:opacity-100 hover:bg-white/10 transition-all"
                  onClick={(e) => e.stopPropagation()}
                >
                  <MoreVertical className="w-5 h-5 text-muted-foreground" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" onClick={(e) => e.stopPropagation()}>
                <DropdownMenuItem onClick={(e) => {
                  e.stopPropagation();
                  navigate(`/workflow/${plan.id}`);
                }}>
                  <Edit className="w-4 h-4 mr-2" />
                  Edit Workflow
                </DropdownMenuItem>
                <DropdownMenuItem onClick={(e) => {
                  e.stopPropagation();
                  navigate(`/workflow/${plan.id}`);
                }}>
                  <ExternalLink className="w-4 h-4 mr-2" />
                  View Details
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                {onDuplicate && (
                  <DropdownMenuItem onClick={(e) => {
                    e.stopPropagation();
                    onDuplicate(plan);
                  }}>
                    <Copy className="w-4 h-4 mr-2" />
                    Duplicate
                  </DropdownMenuItem>
                )}
                {onConfigureTrigger && (
                  <DropdownMenuItem onClick={(e) => {
                    e.stopPropagation();
                    onConfigureTrigger(plan);
                  }}>
                    <Settings className="w-4 h-4 mr-2" />
                    Configure Trigger
                  </DropdownMenuItem>
                )}
                {onDelete && (
                  <>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem 
                      onClick={(e) => {
                        e.stopPropagation();
                        setShowDeleteDialog(true);
                      }}
                      className="text-destructive"
                    >
                      <Trash2 className="w-4 h-4 mr-2" />
                      Delete
                    </DropdownMenuItem>
                  </>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        <p className="text-sm text-muted-foreground mb-6 line-clamp-2 min-h-[40px] leading-relaxed">
          {plan.original_prompt}
        </p>

        {/* Missing auth indicator */}
        {plan.missing_auth && plan.missing_auth.length > 0 && (
          <div className="mb-6 flex flex-col gap-3">
            <div className="flex flex-wrap gap-2">
              {plan.missing_auth.map((provider) => (
                <Badge
                  key={provider}
                  variant="destructive"
                  className="bg-destructive/10 text-destructive border-none text-[10px] font-bold uppercase"
                >
                  {provider} disconnected
                </Badge>
              ))}
            </div>
            <Button 
              variant="outline" 
              size="sm" 
              className="w-full border-destructive/20 text-destructive hover:bg-destructive/5 hover:text-destructive text-xs font-bold"
              onClick={() => navigate("/settings")}
            >
              <Settings className="w-3 h-3 mr-2" />
              Connect {plan.missing_auth[0]} {plan.missing_auth.length > 1 ? `& ${plan.missing_auth.length - 1} more` : ""}
            </Button>
          </div>
        )}

        <div className="flex items-center justify-between pt-6 border-t border-white/5">
          <div className="flex items-center gap-4">
            <div className="flex -space-x-2">
              {plan.required_providers?.map((p, i) => (
                <div key={i} className="w-8 h-8 rounded-full bg-secondary border-2 border-background flex items-center justify-center shadow-sm" title={p}>
                  <span className="text-[10px] font-bold uppercase text-primary">{p.charAt(0)}</span>
                </div>
              ))}
            </div>
            <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
              {plan.plan_json?.length || 0} Steps
            </div>
          </div>

          <Button
            onClick={() => onExecute(plan.id)}
            disabled={plan.status !== "approved" || isExecuting}
            size="sm"
            className="rounded-full px-6 shadow-lg shadow-primary/20 hover:shadow-primary/40 transition-all font-bold"
          >
            {isExecuting ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <>
                <Play className="w-3.5 h-3.5 mr-2 fill-current" />
                Execute
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent onClick={(e) => e.stopPropagation()}>
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
            <Button 
              variant="destructive" 
              onClick={(e) => {
                e.stopPropagation();
                if (onDelete) {
                  onDelete(plan);
                  setShowDeleteDialog(false);
                }
              }}
            >
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  );
};
