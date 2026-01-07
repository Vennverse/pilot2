import { motion } from "framer-motion";
import { Play, Pause, MoreVertical, Clock, CheckCircle, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

interface AutomationCardProps {
  automation: {
    id: string;
    name: string;
    description: string;
    status: "active" | "paused" | "error";
    lastRun: string;
    runCount: number;
  };
  onToggle: (id: string) => void;
}

export const AutomationCard = ({ automation, onToggle }: AutomationCardProps) => {
  const statusConfig = {
    active: {
      color: "text-success",
      bg: "bg-success/10",
      icon: CheckCircle,
      label: "Active",
    },
    paused: {
      color: "text-muted-foreground",
      bg: "bg-muted",
      icon: Pause,
      label: "Paused",
    },
    error: {
      color: "text-destructive",
      bg: "bg-destructive/10",
      icon: AlertCircle,
      label: "Error",
    },
  };

  const status = statusConfig[automation.status];
  const StatusIcon = status.icon;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="glass glass-hover rounded-xl p-5 group"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-lg ${status.bg} flex items-center justify-center`}>
            <StatusIcon className={`w-5 h-5 ${status.color}`} />
          </div>
          <div>
            <h3 className="font-semibold text-foreground">{automation.name}</h3>
            <div className={`inline-flex items-center gap-1 text-xs ${status.color}`}>
              <span className={`w-1.5 h-1.5 rounded-full ${status.color.replace("text-", "bg-")}`} />
              {status.label}
            </div>
          </div>
        </div>
        
        <button className="p-2 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-secondary transition-all">
          <MoreVertical className="w-4 h-4 text-muted-foreground" />
        </button>
      </div>

      <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
        {automation.description}
      </p>

      <div className="flex items-center justify-between pt-4 border-t border-border">
        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <div className="flex items-center gap-1">
            <Clock className="w-3.5 h-3.5" />
            {automation.lastRun}
          </div>
          <div>{automation.runCount} runs</div>
        </div>

        <Button
          variant="ghost"
          size="sm"
          onClick={() => onToggle(automation.id)}
          className="h-8"
        >
          {automation.status === "active" ? (
            <>
              <Pause className="w-3.5 h-3.5 mr-1" />
              Pause
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 mr-1" />
              Start
            </>
          )}
        </Button>
      </div>
    </motion.div>
  );
};
