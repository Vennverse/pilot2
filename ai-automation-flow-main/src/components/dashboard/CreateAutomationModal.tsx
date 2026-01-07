import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Sparkles, ArrowRight, Loader2, Check, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

interface CreateAutomationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (description: string) => void;
}

interface WorkflowStep {
  id: string;
  type: "trigger" | "action";
  icon: string;
  title: string;
  description: string;
}

export const CreateAutomationModal = ({ isOpen, onClose, onSubmit }: CreateAutomationModalProps) => {
  const [description, setDescription] = useState("");
  const [step, setStep] = useState<"input" | "preview" | "confirming">("input");
  const [isProcessing, setIsProcessing] = useState(false);
  const [previewSteps, setPreviewSteps] = useState<WorkflowStep[]>([]);

  const handleAnalyze = async () => {
    if (!description.trim()) return;
    
    setIsProcessing(true);
    
    // Simulate AI analysis
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // Generate mock preview based on description
    const mockSteps: WorkflowStep[] = [
      {
        id: "1",
        type: "trigger",
        icon: "📧",
        title: "Email Received",
        description: "When a new email arrives in your inbox"
      },
      {
        id: "2",
        type: "action",
        icon: "📁",
        title: "Save to Drive",
        description: "Save attachments to Google Drive folder"
      },
      {
        id: "3",
        type: "action",
        icon: "💬",
        title: "Slack Notification",
        description: "Send a message to #notifications channel"
      }
    ];
    
    setPreviewSteps(mockSteps);
    setIsProcessing(false);
    setStep("preview");
  };

  const handleApprove = async () => {
    setStep("confirming");
    await new Promise(resolve => setTimeout(resolve, 1000));
    onSubmit(description);
    handleClose();
  };

  const handleClose = () => {
    setDescription("");
    setStep("input");
    setPreviewSteps([]);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
      >
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={handleClose}
          className="absolute inset-0 bg-background/80 backdrop-blur-sm"
        />

        {/* Modal */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          className="relative w-full max-w-2xl glass rounded-2xl overflow-hidden"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-border">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-primary" />
              </div>
              <div>
                <h2 className="text-xl font-semibold">Create Automation</h2>
                <p className="text-sm text-muted-foreground">
                  {step === "input" && "Describe what you want to automate"}
                  {step === "preview" && "Review your automation workflow"}
                  {step === "confirming" && "Setting up your automation..."}
                </p>
              </div>
            </div>
            <button
              onClick={handleClose}
              className="p-2 rounded-lg hover:bg-secondary transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6">
            {step === "input" && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="e.g., When I receive an email with an attachment, save it to Google Drive and send me a Slack notification..."
                  className="w-full h-40 p-4 bg-secondary rounded-xl border border-border focus:border-primary focus:ring-1 focus:ring-primary outline-none resize-none text-foreground placeholder:text-muted-foreground transition-all"
                />
                
                <div className="mt-4 p-4 rounded-lg bg-primary/5 border border-primary/20">
                  <div className="flex items-start gap-2">
                    <AlertCircle className="w-4 h-4 text-primary mt-0.5" />
                    <div className="text-sm text-muted-foreground">
                      <strong className="text-foreground">Tip:</strong> Be specific about triggers, actions, and any conditions. The more detail you provide, the better the automation will match your needs.
                    </div>
                  </div>
                </div>

                <div className="flex justify-end mt-6">
                  <Button
                    onClick={handleAnalyze}
                    disabled={!description.trim() || isProcessing}
                    variant="hero"
                    size="lg"
                  >
                    {isProcessing ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        Analyze & Preview
                        <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </Button>
                </div>
              </motion.div>
            )}

            {step === "preview" && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <div className="mb-6">
                  <div className="p-4 rounded-lg bg-secondary/50 border border-border mb-4">
                    <p className="text-sm text-muted-foreground mb-1">Your request:</p>
                    <p className="text-foreground">"{description}"</p>
                  </div>
                </div>

                <div className="space-y-3">
                  {previewSteps.map((workflowStep, index) => (
                    <motion.div
                      key={workflowStep.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="relative"
                    >
                      <div className="flex items-start gap-4 p-4 rounded-xl bg-secondary/50 border border-border">
                        <div className="w-12 h-12 rounded-lg bg-card flex items-center justify-center text-2xl">
                          {workflowStep.icon}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className={`text-xs px-2 py-0.5 rounded-full ${
                              workflowStep.type === "trigger" 
                                ? "bg-primary/20 text-primary" 
                                : "bg-accent/20 text-accent"
                            }`}>
                              {workflowStep.type === "trigger" ? "Trigger" : "Action"}
                            </span>
                          </div>
                          <h4 className="font-medium">{workflowStep.title}</h4>
                          <p className="text-sm text-muted-foreground">{workflowStep.description}</p>
                        </div>
                      </div>
                      {index < previewSteps.length - 1 && (
                        <div className="absolute left-6 top-full w-px h-3 bg-border" />
                      )}
                    </motion.div>
                  ))}
                </div>

                <div className="flex justify-between mt-6">
                  <Button variant="ghost" onClick={() => setStep("input")}>
                    Back to Edit
                  </Button>
                  <Button onClick={handleApprove} variant="hero" size="lg">
                    <Check className="w-4 h-4" />
                    Approve & Create
                  </Button>
                </div>
              </motion.div>
            )}

            {step === "confirming" && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="py-12 text-center"
              >
                <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center mx-auto mb-4">
                  <Loader2 className="w-8 h-8 text-primary animate-spin" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Creating your automation...</h3>
                <p className="text-muted-foreground">This will only take a moment</p>
              </motion.div>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};
