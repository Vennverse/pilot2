import { useState } from "react";
import { motion } from "framer-motion";
import { Plus, Trash2, GitBranch, Repeat, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { PlanStep } from "@/types/execution";

interface WorkflowBuilderProps {
  steps: PlanStep[];
  onStepsChange: (steps: PlanStep[]) => void;
  readOnly?: boolean;
}

export const WorkflowBuilder = ({ steps, onStepsChange, readOnly = false }: WorkflowBuilderProps) => {
  const [selectedStep, setSelectedStep] = useState<number | null>(null);

  const getStepIcon = (step: PlanStep) => {
    if (step.type === "condition") return <GitBranch className="w-4 h-4" />;
    if (step.type === "loop") return <Repeat className="w-4 h-4" />;
    return <Zap className="w-4 h-4" />;
  };

  const getStepColor = (step: PlanStep) => {
    if (step.type === "condition") return "bg-blue-500/20 text-blue-400 border-blue-500/30";
    if (step.type === "loop") return "bg-purple-500/20 text-purple-400 border-purple-500/30";
    return "bg-primary/20 text-primary border-primary/30";
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Workflow Steps</h3>
        {!readOnly && (
          <Button variant="outline" size="sm">
            <Plus className="w-4 h-4 mr-2" />
            Add Step
          </Button>
        )}
      </div>

      <div className="space-y-3">
        {steps.map((step, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className={`relative p-4 rounded-lg border-2 transition-all cursor-pointer ${
              selectedStep === index
                ? "border-primary shadow-lg shadow-primary/20"
                : "border-border hover:border-primary/50"
            } ${getStepColor(step)}`}
            onClick={() => !readOnly && setSelectedStep(index)}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3 flex-1">
                <div className="mt-0.5">{getStepIcon(step)}</div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-semibold">{step.action_name || `Step ${step.order}`}</span>
                    {step.type && (
                      <Badge variant="outline" className="text-xs">
                        {step.type}
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground">{step.description}</p>
                  {step.provider && (
                    <Badge variant="secondary" className="mt-2 text-xs">
                      {step.provider}
                    </Badge>
                  )}
                </div>
              </div>
              {!readOnly && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    onStepsChange(steps.filter((_, i) => i !== index));
                  }}
                  className="text-destructive hover:text-destructive"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              )}
            </div>

            {/* Connection line */}
            {index < steps.length - 1 && (
              <div className="absolute left-6 bottom-0 top-full w-0.5 h-4 bg-border" />
            )}
          </motion.div>
        ))}
      </div>

      {steps.length === 0 && (
        <div className="text-center py-12 text-muted-foreground">
          <Zap className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>No steps in workflow</p>
          {!readOnly && (
            <Button variant="outline" className="mt-4" onClick={() => onStepsChange([...steps, {
              order: steps.length + 1,
              provider: "",
              action_id: "",
              action_name: "New Step",
              params: {},
              description: "Add your action here"
            }])}>
              <Plus className="w-4 h-4 mr-2" />
              Add First Step
            </Button>
          )}
        </div>
      )}
    </div>
  );
};
