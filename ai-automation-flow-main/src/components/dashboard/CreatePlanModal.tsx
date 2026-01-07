import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Sparkles, ArrowRight, Loader2, Check, AlertCircle, Link } from "lucide-react";
import { Button } from "@/components/ui/button";
import { supabase } from "@/integrations/supabase/client";
import { useToast } from "@/hooks/use-toast";
import type { AIPlannerResponse, PlanStep } from "@/types/execution";

interface CreatePlanModalProps {
  isOpen: boolean;
  onClose: () => void;
  onPlanCreated: () => void;
}

export const CreatePlanModal = ({ isOpen, onClose, onPlanCreated }: CreatePlanModalProps) => {
  const { toast } = useToast();
  const [description, setDescription] = useState("");
  const [step, setStep] = useState<"input" | "preview" | "confirming">("input");
  const [isProcessing, setIsProcessing] = useState(false);
  const [planData, setPlanData] = useState<AIPlannerResponse | null>(null);

  const handleAnalyze = async () => {
    if (!description.trim()) return;
    
    setIsProcessing(true);
    
    try {
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        toast({
          title: "Not authenticated",
          description: "Please sign in to create execution plans.",
          variant: "destructive",
        });
        return;
      }

      // Load custom integrations from localStorage
      const customIntegrations = JSON.parse(
        localStorage.getItem("custom_integrations") || "[]"
      );

      const response = await fetch("/api/ai-planner", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          prompt: description,
          custom_integrations: customIntegrations
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to connect to AI planner");
      }

      const data = await response.json();

      if (data.error) {
        toast({
          title: "Planning failed",
          description: data.error,
          variant: "destructive",
        });
        return;
      }

      setPlanData(data);
      setStep("preview");

    } catch (error) {
      console.error("AI Planner error:", error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to analyze request",
        variant: "destructive",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleApprove = async () => {
    if (!planData) return;
    
    setStep("confirming");
    
    try {
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        throw new Error("Not authenticated");
      }

      // Check if there are missing auth providers
      const hasMissingAuth = planData.missing_auth && planData.missing_auth.length > 0;

      const response = await fetch("/api/execution-plans", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: session.user.id,
          name: planData.name || "New Execution Plan",
          original_prompt: description,
          plan_json: planData.steps || [],
          plain_english_steps: planData.plain_english_steps || [],
          status: hasMissingAuth ? "draft" : "approved",
          required_providers: planData.required_providers || [],
          missing_auth: planData.missing_auth || [],
          approved_at: hasMissingAuth ? null : new Date().toISOString(),
        }),
      });

      if (!response.ok) throw new Error("Failed to save plan");

      toast({
        title: hasMissingAuth ? "Plan saved as draft" : "Execution plan created!",
        description: hasMissingAuth 
          ? "Connect missing providers to approve this plan." 
          : "Your plan is ready to execute.",
      });

      onPlanCreated();
      handleClose();

    } catch (error) {
      console.error("Save plan error:", error);
      toast({
        title: "Error",
        description: "Failed to save execution plan",
        variant: "destructive",
      });
      setStep("preview");
    }
  };

  const handleClose = () => {
    setDescription("");
    setStep("input");
    setPlanData(null);
    onClose();
  };

  const getProviderIcon = (provider: string): string => {
    const icons: Record<string, string> = {
      gmail: "📧",
      slack: "💬",
      notion: "📝",
      openai: "🧠",
    };
    return icons[provider] || "⚙️";
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
          className="relative w-full max-w-2xl glass rounded-2xl overflow-hidden max-h-[90vh] overflow-y-auto"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-border sticky top-0 bg-card/95 backdrop-blur-sm z-10">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-primary" />
              </div>
              <div>
                <h2 className="text-xl font-semibold">Create Execution Plan</h2>
                <p className="text-sm text-muted-foreground">
                  {step === "input" && "Describe what you want to accomplish"}
                  {step === "preview" && "Review your execution plan"}
                  {step === "confirming" && "Saving your plan..."}
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
                  <div className="flex flex-col gap-4">
                    <div className="flex flex-wrap gap-2">
                      <Button variant="outline" size="sm" onClick={() => setDescription("When I get a new Stripe sale, send a Slack message and create a Shopify order.")} className="text-xs">💰 Sales & Fulfillment</Button>
                      <Button variant="outline" size="sm" onClick={() => setDescription("Summarize the latest tech news from Perplexity and post it to Twitter and TikTok.")} className="text-xs">📰 Social Media Bot</Button>
                      <Button variant="outline" size="sm" onClick={() => setDescription("If a HubSpot lead is updated, send them a personalized SMS with Twilio.")} className="text-xs">📞 CRM Outreach</Button>
                    </div>
                    <textarea
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      placeholder="e.g., When I receive an email with an attachment, save it to Notion and send me a Slack notification..."
                      className="w-full h-40 p-4 bg-secondary rounded-xl border border-border focus:border-primary focus:ring-1 focus:ring-primary outline-none resize-none text-foreground placeholder:text-muted-foreground transition-all"
                    />
                  </div>
                
                <div className="mt-4 p-4 rounded-lg bg-primary/5 border border-primary/20">
                  <div className="flex items-start gap-2">
                    <AlertCircle className="w-4 h-4 text-primary mt-0.5" />
                    <div className="text-sm text-muted-foreground">
                      <strong className="text-foreground">Tip:</strong> Be specific about what triggers the plan, what actions to perform, and any conditions. The AI will generate a step-by-step execution plan.
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

            {step === "preview" && planData && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <div className="mb-6">
                  <h3 className="font-semibold mb-2">{planData.name}</h3>
                  <div className="p-4 rounded-lg bg-secondary/50 border border-border">
                    <p className="text-sm text-muted-foreground mb-1">Your request:</p>
                    <p className="text-foreground">"{description}"</p>
                  </div>
                </div>

                {/* Missing auth warning */}
                {planData.missing_auth && planData.missing_auth.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-6 p-4 rounded-lg bg-destructive/10 border border-destructive/20"
                  >
                    <div className="flex items-start gap-3">
                      <AlertCircle className="w-5 h-5 text-destructive mt-0.5" />
                      <div>
                        <h4 className="font-medium text-destructive">Missing Connections</h4>
                        <p className="text-sm text-muted-foreground mt-1">
                          Connect these providers to execute this plan:
                        </p>
                        <div className="flex flex-wrap gap-2 mt-2">
                          {planData.missing_auth.map((provider) => (
                            <a
                              key={provider}
                              href="/settings"
                              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full bg-destructive/20 text-destructive text-sm hover:bg-destructive/30 transition-colors"
                            >
                              <Link className="w-3 h-3" />
                              Connect {provider}
                            </a>
                          ))}
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )}

                {/* Steps */}
                <div className="space-y-3">
                  {planData.steps?.map((planStep, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="relative"
                    >
                      <div className="flex items-start gap-4 p-4 rounded-xl bg-secondary/50 border border-border">
                        <div className="w-12 h-12 rounded-lg bg-card flex items-center justify-center text-2xl">
                          {getProviderIcon(planStep.provider)}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xs px-2 py-0.5 rounded-full bg-primary/20 text-primary">
                              Step {planStep.order}
                            </span>
                            <span className="text-xs text-muted-foreground">
                              {planStep.provider}
                            </span>
                          </div>
                          <h4 className="font-medium">{planStep.action_name}</h4>
                          <p className="text-sm text-muted-foreground">{planStep.description}</p>
                        </div>
                      </div>
                      {index < (planData.steps?.length || 0) - 1 && (
                        <div className="absolute left-6 top-full w-px h-3 bg-border" />
                      )}
                    </motion.div>
                  ))}
                </div>

                <div className="flex justify-between mt-6">
                  <div className="flex-1 mr-4">
                    <div className="relative">
                      <textarea
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        placeholder="Want to change something? (e.g., 'Add a step to notify me on WhatsApp too')"
                        className="w-full p-3 pr-20 bg-secondary rounded-xl border border-border focus:border-primary focus:ring-1 focus:ring-primary outline-none resize-none text-sm h-12 flex items-center"
                      />
                      <Button 
                        size="sm" 
                        variant="ghost" 
                        className="absolute right-1 top-1 text-xs text-primary font-bold hover:bg-primary/10"
                        onClick={handleAnalyze}
                        disabled={isProcessing}
                      >
                        Refine
                      </Button>
                    </div>
                  </div>
                  <Button onClick={handleApprove} variant="hero" size="lg">
                    <Check className="w-4 h-4" />
                    {planData.missing_auth?.length ? "Save as Draft" : "Approve & Create"}
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
                <h3 className="text-xl font-semibold mb-2">Saving your plan...</h3>
                <p className="text-muted-foreground">This will only take a moment</p>
              </motion.div>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};
