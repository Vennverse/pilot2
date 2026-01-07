import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, Search, Filter, Zap, TrendingUp, Clock, CheckCircle, Settings, Rocket, Grid3x3, List, X, Calendar, Activity, BarChart3, Download, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { DashboardHeader } from "@/components/dashboard/DashboardHeader";
import { ExecutionPlanCard } from "@/components/dashboard/ExecutionPlanCard";
import { CreatePlanModal } from "@/components/dashboard/CreatePlanModal";
import { TriggerConfigModal } from "@/components/dashboard/TriggerConfigModal";
import { ExecutionDetailsModal } from "@/components/dashboard/ExecutionDetailsModal";
import { supabase } from "@/integrations/supabase/client";
import { useToast } from "@/hooks/use-toast";
import type { ExecutionPlan, Trigger } from "@/types/execution";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const Dashboard = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [executionPlans, setExecutionPlans] = useState<ExecutionPlan[]>([]);
  const [executingPlanId, setExecutingPlanId] = useState<string | null>(null);
  const [executionLogs, setExecutionLogs] = useState<any[]>([]);
  const [showLogs, setShowLogs] = useState(false);
  const [triggerConfigPlan, setTriggerConfigPlan] = useState<ExecutionPlan | null>(null);
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [sortBy, setSortBy] = useState<string>("recent");
  const [logsFilter, setLogsFilter] = useState<string>("all");
  const [isLoadingPlans, setIsLoadingPlans] = useState(true);
  const [isLoadingLogs, setIsLoadingLogs] = useState(false);
  const [isLoadingStats, setIsLoadingStats] = useState(true);
  const [selectedExecutionId, setSelectedExecutionId] = useState<string | null>(null);

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
    if (!loading && !user) {
      navigate("/auth");
    }
  }, [loading, user, navigate]);

  useEffect(() => {
    if (user) {
      fetchExecutionPlans();
    }
  }, [user]);

  const fetchExecutionPlans = async () => {
    if (!user) return;
    
    setIsLoadingPlans(true);
    try {
      const response = await fetch(`/api/execution-plans?user_id=${user.id}`);
      if (!response.ok) throw new Error("Failed to fetch plans");
      const data = await response.json();
      setExecutionPlans(data);
    } catch (error) {
      console.error("Error fetching execution plans:", error);
      toast({
        title: "Error loading plans",
        description: error instanceof Error ? error.message : "Failed to fetch execution plans",
        variant: "destructive",
      });
    } finally {
      setIsLoadingPlans(false);
    }
  };

  const fetchExecutionLogs = async () => {
    if (!user) return;
    setIsLoadingLogs(true);
    try {
      const response = await fetch(`/api/execution-logs?user_id=${user.id}`);
      if (response.ok) {
        const data = await response.json();
        setExecutionLogs(data);
      }
    } catch (error) {
      console.error("Error fetching logs:", error);
      toast({
        title: "Error loading logs",
        description: "Failed to fetch execution logs",
        variant: "destructive",
      });
    } finally {
      setIsLoadingLogs(false);
    }
  };

  const handleExecutePlan = async (planId: string) => {
    setExecutingPlanId(planId);

    try {
      const response = await fetch("/api/execute-plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ execution_plan_id: planId }),
      });

      if (!response.ok) {
        throw new Error("Failed to execute plan");
      }

      const result = await response.json();
      fetchMonitoringStats(); // Refresh stats after execution

      if (result.status === "success") {
        toast({
          title: "Execution complete!",
          description: `Plan executed successfully with ${result.logs?.length || 0} steps.`,
        });
      } else {
        toast({
          title: "Execution finished with issues",
          description: result.logs?.find((l: any) => l.status === "failed")?.message || "Some steps failed",
          variant: "destructive",
        });
      }

    } catch (error) {
      console.error("Execute plan error:", error);
      toast({
        title: "Execution failed",
        description: error instanceof Error ? error.message : "Unknown error",
        variant: "destructive",
      });
    } finally {
      setExecutingPlanId(null);
    }
  };

  const handleConfigureTrigger = (plan: ExecutionPlan) => {
    setTriggerConfigPlan(plan);
  };

  const handleTriggerSave = async (trigger: Trigger | null, enabled: boolean) => {
    if (!triggerConfigPlan) return;
    
    // Update local state
    setExecutionPlans(prev => prev.map(p => 
      p.id === triggerConfigPlan.id 
        ? { ...p, trigger, enabled }
        : p
    ));
    
    // Refresh plans
    fetchExecutionPlans();
  };

  const handleDuplicatePlan = async (plan: ExecutionPlan) => {
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

      toast({
        title: "Workflow duplicated",
        description: "The workflow has been duplicated successfully.",
      });
      fetchExecutionPlans();
    } catch (error) {
      toast({
        title: "Duplication failed",
        description: error instanceof Error ? error.message : "Failed to duplicate workflow",
        variant: "destructive",
      });
    }
  };

  const handleDeletePlan = async (plan: ExecutionPlan) => {
    try {
      const response = await fetch(`/api/execution-plans/${plan.id}`, {
        method: "DELETE",
      });

      if (!response.ok) throw new Error("Failed to delete");

      toast({
        title: "Workflow deleted",
        description: "The workflow has been deleted successfully.",
      });
      fetchExecutionPlans();
    } catch (error) {
      toast({
        title: "Deletion failed",
        description: error instanceof Error ? error.message : "Failed to delete workflow",
        variant: "destructive",
      });
    }
  };

  const filteredAndSortedPlans = executionPlans
    .filter((plan) => {
      // Search filter
      const matchesSearch =
        plan.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        plan.original_prompt.toLowerCase().includes(searchQuery.toLowerCase());
      
      // Status filter
      const matchesStatus =
        statusFilter === "all" ||
        (statusFilter === "active" && plan.enabled) ||
        (statusFilter === "paused" && !plan.enabled) ||
        (statusFilter === "needs-auth" && plan.missing_auth && plan.missing_auth.length > 0);
      
      return matchesSearch && matchesStatus;
    })
    .sort((a, b) => {
      switch (sortBy) {
        case "name":
          return a.name.localeCompare(b.name);
        case "recent":
          return new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime();
        case "oldest":
          return new Date(a.created_at || 0).getTime() - new Date(b.created_at || 0).getTime();
        default:
          return 0;
      }
    });

  const filteredLogs = executionLogs.filter((log) => {
    if (logsFilter === "all") return true;
    return log.status === logsFilter;
  });

  const [stats, setStats] = useState([
    { icon: Zap, label: "Total Plans", value: 0, change: "Active flows" },
    { icon: CheckCircle, label: "Success Rate", value: "0%", change: "Last 10 runs" },
    { icon: TrendingUp, label: "Total Runs", value: 0, change: "All time" },
    { icon: Rocket, label: "Speed", value: "Ultra", change: "Powered by Groq" },
  ]);

  useEffect(() => {
    if (user) {
      fetchExecutionPlans();
      fetchMonitoringStats();
    }
  }, [user]);

  const fetchMonitoringStats = async () => {
    if (!user) return;
    setIsLoadingStats(true);
    try {
      const resp = await fetch(`/api/monitoring/status?user_id=${user.id}`);
      if (resp.ok) {
        const data = await resp.json();
        const successRate = data.total_executions > 0 
          ? Math.round((data.successful / data.total_executions) * 100) + "%"
          : "0%";
          
        setStats([
          { icon: Zap, label: "Total Plans", value: executionPlans.length, change: "Active flows" },
          { icon: CheckCircle, label: "Success Rate", value: successRate, change: "Last 10 runs" },
          { icon: TrendingUp, label: "Total Runs", value: data.total_executions, change: "All time" },
          { icon: Rocket, label: "Speed", value: "Ultra", change: "Powered by Groq" },
        ]);
        
        // Auto-refresh logs if we are looking at them
        if (showLogs) {
          fetchExecutionLogs();
        }
      }
    } catch (e) {
      console.error("Monitoring stats error:", e);
    } finally {
      setIsLoadingStats(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <DashboardHeader userEmail={user?.email} />

      <main className="container px-4 py-8">
        {/* Welcome section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 mb-6">
            <div className="flex-1">
              <motion.h1 
                className="text-4xl md:text-5xl font-extrabold mb-3 text-gradient glow-text tracking-tight"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
              >
                Welcome back{user?.email ? `, ${user.email.split("@")[0]}` : ""}
              </motion.h1>
              <p className="text-muted-foreground text-lg mb-6 max-w-2xl">
                Manage your execution plans, monitor performance, and automate workflows with AI-powered intelligence.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-2xl">
                <motion.div 
                  className="p-4 rounded-xl bg-primary/5 border border-primary/10 flex items-start gap-3 hover:bg-primary/10 transition-colors group"
                  whileHover={{ scale: 1.02, x: 4 }}
                >
                  <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center shrink-0 group-hover:bg-primary/30 transition-colors">
                    <span className="text-primary font-bold">1</span>
                  </div>
                  <p className="text-sm text-muted-foreground leading-snug">
                    Click <strong className="text-foreground">New Plan</strong> and tell the AI what you want to automate in plain English.
                  </p>
                </motion.div>
                <motion.div 
                  className="p-4 rounded-xl bg-primary/5 border border-primary/10 flex items-start gap-3 hover:bg-primary/10 transition-colors group"
                  whileHover={{ scale: 1.02, x: 4 }}
                >
                  <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center shrink-0 group-hover:bg-primary/30 transition-colors">
                    <span className="text-primary font-bold">2</span>
                  </div>
                  <p className="text-sm text-muted-foreground leading-snug">
                    Review the plan, connect any missing apps, and click <strong className="text-foreground">Execute</strong>.
                  </p>
                </motion.div>
              </div>
            </div>
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.2 }}
            >
              <Button 
                variant="outline" 
                size="lg" 
                onClick={() => navigate("/settings")} 
                className="glass-hover border-primary/20 hover:border-primary/50 shadow-lg"
              >
                <Settings className="w-5 h-5 mr-2" />
                Integrations
              </Button>
            </motion.div>
          </div>
        </motion.div>

        {/* Stats grid */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-10"
        >
          {isLoadingStats ? (
            stats.map((_, index) => (
              <div key={index} className="glass rounded-2xl p-6 border border-white/5 shadow-xl">
                <Skeleton className="w-12 h-12 rounded-xl mb-4" />
                <Skeleton className="h-8 w-20 mb-2" />
                <Skeleton className="h-4 w-24 mb-3" />
                <Skeleton className="h-3 w-16" />
              </div>
            ))
          ) : (
            stats.map((stat, index) => (
              <motion.div 
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 + index * 0.05 }}
                whileHover={{ scale: 1.02, y: -4 }}
                className="glass rounded-2xl p-6 border border-white/5 shadow-xl relative overflow-hidden group cursor-pointer"
              >
                <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-primary/2 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                <div className="relative z-10">
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center glow transition-transform group-hover:scale-110 group-hover:rotate-3">
                      <stat.icon className="w-6 h-6 text-primary" />
                    </div>
                    {index === 3 && (
                      <div className="px-2 py-1 rounded-full bg-primary/10 border border-primary/20">
                        <span className="text-[10px] font-bold text-primary uppercase">Fast</span>
                      </div>
                    )}
                  </div>
                  <motion.div 
                    className="text-3xl font-bold mb-1 tracking-tight"
                    initial={{ scale: 0.8, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ delay: 0.2 + index * 0.05, type: "spring" }}
                  >
                    {typeof stat.value === "number" && stat.value > 0 ? (
                      <motion.span
                        key={stat.value}
                        initial={{ scale: 1.2 }}
                        animate={{ scale: 1 }}
                        className="inline-block"
                      >
                        {stat.value}
                      </motion.span>
                    ) : (
                      stat.value
                    )}
                  </motion.div>
                  <div className="text-sm text-muted-foreground font-medium mb-3">{stat.label}</div>
                  <div className="text-xs text-primary font-bold mt-2 flex items-center gap-1.5">
                    <motion.div 
                      className="w-1.5 h-1.5 rounded-full bg-primary"
                      animate={{ scale: [1, 1.2, 1] }}
                      transition={{ duration: 2, repeat: Infinity, delay: index * 0.2 }}
                    />
                    {stat.change}
                  </div>
                </div>
              </motion.div>
            ))
          )}
        </motion.div>

        {/* Actions bar */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="flex flex-col gap-4 mb-6"
        >
          <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
            <div className="relative flex-1 max-w-md w-full">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground z-10" />
              <Input
                placeholder="Search execution plans..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 bg-secondary border-border"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery("")}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-full hover:bg-secondary"
                >
                  <X className="w-3 h-3 text-muted-foreground" />
                </button>
              )}
            </div>

            <div className="flex items-center gap-3 flex-wrap">
              {!showLogs && (
                <>
                  <div className="flex items-center gap-2 border rounded-lg p-1 bg-secondary">
                    <Button
                      variant={viewMode === "grid" ? "secondary" : "ghost"}
                      size="sm"
                      onClick={() => setViewMode("grid")}
                      className="h-8 px-3"
                    >
                      <Grid3x3 className="w-4 h-4" />
                    </Button>
                    <Button
                      variant={viewMode === "list" ? "secondary" : "ghost"}
                      size="sm"
                      onClick={() => setViewMode("list")}
                      className="h-8 px-3"
                    >
                      <List className="w-4 h-4" />
                    </Button>
                  </div>
                  <Select value={sortBy} onValueChange={setSortBy}>
                    <SelectTrigger className="w-[140px] bg-secondary border-border">
                      <SelectValue placeholder="Sort by" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="recent">Most Recent</SelectItem>
                      <SelectItem value="oldest">Oldest First</SelectItem>
                      <SelectItem value="name">Name (A-Z)</SelectItem>
                    </SelectContent>
                  </Select>
                  <Select value={statusFilter} onValueChange={setStatusFilter}>
                    <SelectTrigger className="w-[140px] bg-secondary border-border">
                      <SelectValue placeholder="Filter" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Status</SelectItem>
                      <SelectItem value="active">Active</SelectItem>
                      <SelectItem value="paused">Paused</SelectItem>
                      <SelectItem value="needs-auth">Needs Auth</SelectItem>
                    </SelectContent>
                  </Select>
                </>
              )}
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => { 
                  if (!showLogs) fetchExecutionLogs();
                  setShowLogs(!showLogs); 
                }}
              >
                {showLogs ? (
                  <>
                    <Grid3x3 className="w-4 h-4 mr-2" />
                    Show Plans
                  </>
                ) : (
                  <>
                    <Clock className="w-4 h-4 mr-2" />
                    Execution Logs
                  </>
                )}
              </Button>
              <Button onClick={() => setIsModalOpen(true)} variant="hero" size="sm">
                <Plus className="w-4 h-4 mr-2" />
                New Plan
              </Button>
            </div>
          </div>

          {!showLogs && (searchQuery || statusFilter !== "all") && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              className="flex items-center gap-2 text-sm text-muted-foreground"
            >
              <span>Showing {filteredAndSortedPlans.length} of {executionPlans.length} plans</span>
              {(searchQuery || statusFilter !== "all") && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setSearchQuery("");
                    setStatusFilter("all");
                  }}
                  className="h-6 px-2 text-xs"
                >
                  <X className="w-3 h-3 mr-1" />
                  Clear filters
                </Button>
              )}
            </motion.div>
          )}
        </motion.div>

        {/* Execution Plans */}
        {!showLogs ? (
          <>
            {isLoadingPlans ? (
              <div className={viewMode === "grid" ? "grid md:grid-cols-2 lg:grid-cols-3 gap-4" : "space-y-4"}>
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="glass rounded-2xl p-6 border border-white/5">
                    <Skeleton className="h-12 w-12 rounded-xl mb-4" />
                    <Skeleton className="h-6 w-3/4 mb-2" />
                    <Skeleton className="h-4 w-1/2 mb-4" />
                    <Skeleton className="h-20 w-full mb-4" />
                    <div className="flex justify-between items-center pt-4 border-t border-white/5">
                      <Skeleton className="h-8 w-20" />
                      <Skeleton className="h-10 w-24 rounded-full" />
                    </div>
                  </div>
                ))}
              </div>
            ) : viewMode === "grid" ? (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 }}
                className="grid md:grid-cols-2 lg:grid-cols-3 gap-4"
              >
                <AnimatePresence mode="popLayout">
                  {filteredAndSortedPlans.map((plan) => (
                    <ExecutionPlanCard
                      key={plan.id}
                      plan={plan}
                      onExecute={handleExecutePlan}
                      onConfigureTrigger={handleConfigureTrigger}
                      onDuplicate={handleDuplicatePlan}
                      onDelete={handleDeletePlan}
                      isExecuting={executingPlanId === plan.id}
                    />
                  ))}
                </AnimatePresence>
              </motion.div>
            ) : (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 }}
                className="space-y-3"
              >
                <AnimatePresence mode="popLayout">
                  {filteredAndSortedPlans.map((plan) => (
                    <motion.div
                      key={plan.id}
                      layout
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 20 }}
                      className="glass rounded-xl p-5 border border-white/5 hover:border-primary/50 transition-all"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4 flex-1">
                          <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                            <Zap className="w-6 h-6 text-primary" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-3 mb-1">
                              <h3 className="text-lg font-bold truncate">{plan.name}</h3>
                              <Badge variant={plan.enabled ? "default" : "outline"} className="text-xs">
                                {plan.enabled ? "Active" : "Paused"}
                              </Badge>
                            </div>
                            <p className="text-sm text-muted-foreground truncate">{plan.original_prompt}</p>
                          </div>
                          <div className="text-sm text-muted-foreground">
                            {plan.plan_json?.length || 0} steps
                          </div>
                        </div>
                        <div className="flex items-center gap-2 ml-4">
                          {onConfigureTrigger && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleConfigureTrigger(plan)}
                            >
                              <Settings className="w-4 h-4" />
                            </Button>
                          )}
                          <Button
                            onClick={() => handleExecutePlan(plan.id)}
                            disabled={plan.status !== "approved" || executingPlanId === plan.id}
                            size="sm"
                            className="rounded-full"
                          >
                            Execute
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => navigate(`/workflow/${plan.id}`)}
                          >
                            <ExternalLink className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </motion.div>
            )}
          </>
        ) : (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-4"
          >
            {/* Logs filters */}
            <div className="flex items-center justify-between gap-4 flex-wrap">
              <div className="flex items-center gap-2">
                <Select value={logsFilter} onValueChange={setLogsFilter}>
                  <SelectTrigger className="w-[140px] bg-secondary border-border">
                    <SelectValue placeholder="Filter logs" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Logs</SelectItem>
                    <SelectItem value="success">Success</SelectItem>
                    <SelectItem value="failed">Failed</SelectItem>
                    <SelectItem value="running">Running</SelectItem>
                  </SelectContent>
                </Select>
                <Badge variant="outline" className="text-xs">
                  {filteredLogs.length} {filteredLogs.length === 1 ? "log" : "logs"}
                </Badge>
              </div>
              <Button variant="outline" size="sm" onClick={fetchExecutionLogs} disabled={isLoadingLogs}>
                <Activity className="w-4 h-4 mr-2" />
                Refresh
              </Button>
            </div>

            {/* Logs table */}
            <div className="glass rounded-2xl overflow-hidden border border-white/5">
              {isLoadingLogs ? (
                <div className="p-8 space-y-4">
                  {[...Array(5)].map((_, i) => (
                    <div key={i} className="space-y-2">
                      <Skeleton className="h-4 w-full" />
                      <Skeleton className="h-4 w-3/4" />
                    </div>
                  ))}
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left">
                    <thead>
                      <tr className="bg-white/5 border-b border-white/10">
                        <th className="p-4 text-xs font-bold uppercase tracking-wider">Plan Name</th>
                        <th className="p-4 text-xs font-bold uppercase tracking-wider">Status</th>
                        <th className="p-4 text-xs font-bold uppercase tracking-wider">Time</th>
                        <th className="p-4 text-xs font-bold uppercase tracking-wider">Steps</th>
                        <th className="p-4 text-xs font-bold uppercase tracking-wider">Duration</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                      <AnimatePresence>
                        {filteredLogs.map((log, index) => (
                          <motion.tr
                            key={log.id}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.05 }}
                            className="hover:bg-white/5 transition-colors cursor-pointer"
                            onClick={() => setSelectedExecutionId(log.id)}
                          >
                            <td className="p-4 font-medium">{log.plan_name || "Unknown Plan"}</td>
                            <td className="p-4">
                              <Badge 
                                variant={log.status === "success" ? "default" : log.status === "failed" ? "destructive" : "secondary"} 
                                className="text-[10px] uppercase flex items-center gap-1 w-fit"
                              >
                                {log.status === "success" && <CheckCircle className="w-3 h-3" />}
                                {log.status === "failed" && <X className="w-3 h-3" />}
                                {log.status === "running" && <Clock className="w-3 h-3 animate-spin" />}
                                {log.status || "unknown"}
                              </Badge>
                            </td>
                            <td className="p-4 text-sm text-muted-foreground">
                              <div className="flex items-center gap-2">
                                <Calendar className="w-3 h-3" />
                                {new Date(log.timestamp || Date.now()).toLocaleDateString()}
                              </div>
                              <div className="text-xs mt-1">
                                {new Date(log.timestamp || Date.now()).toLocaleTimeString()}
                              </div>
                            </td>
                            <td className="p-4">
                              <div className="flex items-center gap-2">
                                <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center">
                                  <span className="text-xs font-bold text-primary">{log.steps?.length || 0}</span>
                                </div>
                                <span className="text-xs text-muted-foreground">steps</span>
                              </div>
                            </td>
                            <td className="p-4 text-xs text-muted-foreground">
                              {log.duration ? `${(log.duration / 1000).toFixed(1)}s` : "—"}
                            </td>
                          </motion.tr>
                        ))}
                      </AnimatePresence>
                      {filteredLogs.length === 0 && (
                        <tr>
                          <td colSpan={5} className="p-12 text-center">
                            <div className="flex flex-col items-center gap-3">
                              <div className="w-16 h-16 rounded-full bg-secondary flex items-center justify-center">
                                <Activity className="w-8 h-8 text-muted-foreground" />
                              </div>
                              <div>
                                <h3 className="font-semibold mb-1">No execution logs found</h3>
                                <p className="text-sm text-muted-foreground">
                                  {logsFilter !== "all" 
                                    ? `No logs match the "${logsFilter}" filter.`
                                    : "Execution logs will appear here after you run your plans."}
                                </p>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </motion.div>
        )}

        {!isLoadingPlans && filteredAndSortedPlans.length === 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center py-16"
          >
            <div className="w-20 h-20 rounded-full bg-gradient-to-br from-primary/20 to-transparent flex items-center justify-center mx-auto mb-6">
              <Zap className="w-10 h-10 text-primary" />
            </div>
            <h3 className="text-2xl font-bold mb-2">
              {searchQuery || statusFilter !== "all"
                ? "No plans match your filters"
                : "No execution plans found"}
            </h3>
            <p className="text-muted-foreground mb-6 max-w-md mx-auto">
              {searchQuery || statusFilter !== "all"
                ? "Try adjusting your search or filters to see more results."
                : "Create your first execution plan to automate your workflows with AI."}
            </p>
            {searchQuery || statusFilter !== "all" ? (
              <Button 
                onClick={() => {
                  setSearchQuery("");
                  setStatusFilter("all");
                }} 
                variant="outline"
              >
                <X className="w-4 h-4 mr-2" />
                Clear filters
              </Button>
            ) : (
              <Button onClick={() => setIsModalOpen(true)} variant="hero" size="lg">
                <Plus className="w-5 h-5 mr-2" />
                Create Execution Plan
              </Button>
            )}
          </motion.div>
        )}
      </main>

      <CreatePlanModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onPlanCreated={fetchExecutionPlans}
      />

      {triggerConfigPlan && (
        <TriggerConfigModal
          isOpen={!!triggerConfigPlan}
          onClose={() => setTriggerConfigPlan(null)}
          planId={triggerConfigPlan.id}
          currentTrigger={triggerConfigPlan.trigger}
          enabled={triggerConfigPlan.enabled ?? false}
          onSave={handleTriggerSave}
        />
      )}

      {selectedExecutionId && (
        <ExecutionDetailsModal
          isOpen={!!selectedExecutionId}
          onClose={() => setSelectedExecutionId(null)}
          executionId={selectedExecutionId}
          planName={executionLogs.find(log => log.id === selectedExecutionId)?.plan_name}
        />
      )}
    </div>
  );
};

export default Dashboard;
