import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, CheckCircle, XCircle, Clock, Copy, Download, AlertCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useToast } from "@/hooks/use-toast";

interface ExecutionDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  executionId: string;
  planName?: string;
}

export const ExecutionDetailsModal = ({
  isOpen,
  onClose,
  executionId,
  planName,
}: ExecutionDetailsModalProps) => {
  const { toast } = useToast();
  const [execution, setExecution] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set());

  useEffect(() => {
    if (isOpen && executionId) {
      fetchExecutionDetails();
    }
  }, [isOpen, executionId]);

  const fetchExecutionDetails = async () => {
    setLoading(true);
    try {
      // Fetch execution details - you may need to adjust the endpoint
      const response = await fetch(`/api/executions/${executionId}`);
      if (response.ok) {
        const data = await response.json();
        setExecution(data);
        // Expand first failed step if any
        const failedStep = data.logs?.findIndex((log: any) => log.status === "failed");
        if (failedStep !== -1) {
          setExpandedSteps(new Set([failedStep]));
        }
      }
    } catch (error) {
      console.error("Error fetching execution details:", error);
      toast({
        title: "Error",
        description: "Failed to load execution details",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const toggleStep = (index: number) => {
    setExpandedSteps((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: "Copied!",
      description: "Content copied to clipboard",
    });
  };

  const downloadExecution = () => {
    if (!execution) return;
    const dataStr = JSON.stringify(execution, null, 2);
    const dataBlob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `execution-${executionId}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const formatDuration = (start: string, end: string) => {
    if (!start || !end) return "—";
    const startTime = new Date(start).getTime();
    const endTime = new Date(end).getTime();
    const duration = (endTime - startTime) / 1000;
    return `${duration.toFixed(2)}s`;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "success":
        return <CheckCircle className="w-5 h-5 text-green-400" />;
      case "failed":
        return <XCircle className="w-5 h-5 text-red-400" />;
      case "running":
        return <Clock className="w-5 h-5 text-blue-400 animate-spin" />;
      default:
        return <AlertCircle className="w-5 h-5 text-yellow-400" />;
    }
  };

  if (!isOpen) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh]">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <div>
              <DialogTitle className="text-2xl">
                Execution Details
              </DialogTitle>
              <DialogDescription className="mt-1">
                {planName || "Workflow Execution"}
              </DialogDescription>
            </div>
            <div className="flex items-center gap-2">
              {execution && (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={downloadExecution}
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Export
                  </Button>
                </>
              )}
            </div>
          </div>
        </DialogHeader>

        <ScrollArea className="max-h-[70vh] pr-4">
          {loading ? (
            <div className="space-y-4">
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-20 w-full" />
            </div>
          ) : execution ? (
            <div className="space-y-4">
              {/* Execution Summary */}
              <div className="glass rounded-xl p-4 border border-white/5">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <div className="text-xs text-muted-foreground mb-1">Status</div>
                    <div className="flex items-center gap-2">
                      {getStatusIcon(execution.status)}
                      <Badge
                        variant={
                          execution.status === "success"
                            ? "default"
                            : execution.status === "failed"
                            ? "destructive"
                            : "secondary"
                        }
                        className="text-xs"
                      >
                        {execution.status}
                      </Badge>
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-muted-foreground mb-1">Duration</div>
                    <div className="font-semibold">
                      {formatDuration(execution.started_at, execution.finished_at)}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-muted-foreground mb-1">Steps</div>
                    <div className="font-semibold">{execution.logs?.length || 0}</div>
                  </div>
                  <div>
                    <div className="text-xs text-muted-foreground mb-1">Started</div>
                    <div className="font-semibold text-sm">
                      {execution.started_at
                        ? new Date(execution.started_at).toLocaleTimeString()
                        : "—"}
                    </div>
                  </div>
                </div>
              </div>

              {/* Execution Steps */}
              <div className="space-y-3">
                <h3 className="font-semibold text-lg">Execution Steps</h3>
                {execution.logs && execution.logs.length > 0 ? (
                  execution.logs.map((log: any, index: number) => {
                    const isExpanded = expandedSteps.has(index);
                    const isFailed = log.status === "failed";

                    return (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.05 }}
                        className={`glass rounded-xl border transition-all ${
                          isFailed
                            ? "border-red-500/30 bg-red-500/5"
                            : log.status === "success"
                            ? "border-green-500/30 bg-green-500/5"
                            : "border-white/5"
                        }`}
                      >
                        <button
                          onClick={() => toggleStep(index)}
                          className="w-full p-4 flex items-center justify-between hover:bg-white/5 transition-colors rounded-xl"
                        >
                          <div className="flex items-center gap-4 flex-1 text-left">
                            <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center font-bold text-sm">
                              {log.step || index + 1}
                            </div>
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="font-semibold">
                                  {log.action_name || `Step ${index + 1}`}
                                </span>
                                {log.provider && (
                                  <Badge variant="outline" className="text-xs">
                                    {log.provider}
                                  </Badge>
                                )}
                                <Badge
                                  variant={
                                    log.status === "success"
                                      ? "default"
                                      : log.status === "failed"
                                      ? "destructive"
                                      : "secondary"
                                  }
                                  className="text-xs"
                                >
                                  {log.status}
                                </Badge>
                              </div>
                              <p className="text-sm text-muted-foreground">
                                {log.message || "No message"}
                              </p>
                            </div>
                            {getStatusIcon(log.status)}
                          </div>
                        </button>

                        <AnimatePresence>
                          {isExpanded && (
                            <motion.div
                              initial={{ height: 0, opacity: 0 }}
                              animate={{ height: "auto", opacity: 1 }}
                              exit={{ height: 0, opacity: 0 }}
                              className="overflow-hidden"
                            >
                              <div className="p-4 pt-0 space-y-3 border-t border-white/5 mt-2">
                                {log.output && (
                                  <div>
                                    <div className="text-xs font-semibold text-muted-foreground mb-2 flex items-center justify-between">
                                      <span>Output</span>
                                      <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() =>
                                          copyToClipboard(
                                            typeof log.output === "string"
                                              ? log.output
                                              : JSON.stringify(log.output, null, 2)
                                          )
                                        }
                                      >
                                        <Copy className="w-3 h-3" />
                                      </Button>
                                    </div>
                                    <pre className="text-xs bg-secondary rounded-lg p-3 overflow-x-auto">
                                      {typeof log.output === "string"
                                        ? log.output
                                        : JSON.stringify(log.output, null, 2)}
                                    </pre>
                                  </div>
                                )}

                                {log.data && (
                                  <div>
                                    <div className="text-xs font-semibold text-muted-foreground mb-2 flex items-center justify-between">
                                      <span>Data</span>
                                      <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() =>
                                          copyToClipboard(JSON.stringify(log.data, null, 2))
                                        }
                                      >
                                        <Copy className="w-3 h-3" />
                                      </Button>
                                    </div>
                                    <pre className="text-xs bg-secondary rounded-lg p-3 overflow-x-auto">
                                      {JSON.stringify(log.data, null, 2)}
                                    </pre>
                                  </div>
                                )}

                                {log.error && (
                                  <div>
                                    <div className="text-xs font-semibold text-red-400 mb-2">
                                      Error
                                    </div>
                                    <div className="text-xs text-red-300 bg-red-500/10 rounded-lg p-3">
                                      {log.error}
                                    </div>
                                  </div>
                                )}

                                {log.timestamp && (
                                  <div className="text-xs text-muted-foreground">
                                    Executed at: {new Date(log.timestamp).toLocaleString()}
                                  </div>
                                )}
                              </div>
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </motion.div>
                    );
                  })
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    No execution steps available
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              No execution data found
            </div>
          )}
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
};
