import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Activity, AlertCircle, CheckCircle2, Clock, Zap } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface ExecutionEvent {
  execution_id: string;
  timestamp: string;
  event_type: string;
  step_id?: string;
  step_name?: string;
  data?: Record<string, any>;
  error?: string;
}

interface ExecutionStream {
  execution_id: string;
  workflow_id: string;
  user_id: string;
  status: string;
  started_at: string;
  events: ExecutionEvent[];
}

export default function ExecutionMonitor() {
  const { toast } = useToast();
  const [user, setUser] = useState<any>(null);
  const [executions, setExecutions] = useState<ExecutionStream[]>([]);
  const [selectedExecution, setSelectedExecution] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    const user_id = localStorage.getItem("user_id");
    setUser({ id: user_id });
  }, []);

  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      // In a real app, fetch active executions and their event streams
      fetchExecutions();
    }, 2000); // Refresh every 2 seconds

    return () => clearInterval(interval);
  }, [autoRefresh]);

  const fetchExecutions = async () => {
    // Mock data for demonstration
    // In production, this would fetch from /api/monitoring endpoints
    setLoading(false);
  };

  const handlePause = async (execution_id: string) => {
    try {
      const response = await fetch("/api/execution/advanced/pause", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          execution_id,
          user_id: user?.id,
        }),
      });

      if (!response.ok) throw new Error("Pause failed");

      toast({
        title: "Success",
        description: "Execution paused",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to pause execution",
        variant: "destructive",
      });
    }
  };

  const handleResume = async (execution_id: string) => {
    try {
      const response = await fetch("/api/execution/advanced/resume", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          execution_id,
          user_id: user?.id,
        }),
      });

      if (!response.ok) throw new Error("Resume failed");

      toast({
        title: "Success",
        description: "Execution resumed",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to resume execution",
        variant: "destructive",
      });
    }
  };

  const getEventIcon = (eventType: string) => {
    switch (eventType) {
      case "started":
        return <Zap className="w-4 h-4 text-blue-500" />;
      case "step_completed":
        return <CheckCircle2 className="w-4 h-4 text-green-500" />;
      case "step_failed":
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case "completed":
        return <CheckCircle2 className="w-4 h-4 text-green-500" />;
      default:
        return <Activity className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "running":
        return "bg-blue-500/20 text-blue-400 border-blue-500/30";
      case "success":
        return "bg-green-500/20 text-green-400 border-green-500/30";
      case "failed":
        return "bg-red-500/20 text-red-400 border-red-500/30";
      case "paused":
        return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30";
      default:
        return "bg-gray-500/20 text-gray-400 border-gray-500/30";
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-4xl font-bold text-white">Execution Monitor</h1>
          <div className="flex gap-2">
            <Button
              variant={autoRefresh ? "default" : "outline"}
              onClick={() => setAutoRefresh(!autoRefresh)}
              className="flex items-center gap-2"
            >
              <Activity className="w-4 h-4" />
              {autoRefresh ? "Live" : "Paused"}
            </Button>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Executions List */}
          <div className="lg:col-span-1">
            <Card className="bg-slate-800 border-slate-700 sticky top-4">
              <CardHeader>
                <CardTitle className="text-white">Active Executions</CardTitle>
                <CardDescription className="text-gray-400">
                  {executions.length} running
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 max-h-96 overflow-y-auto">
                {executions.length === 0 ? (
                  <div className="text-gray-400 text-sm py-4 text-center">
                    No active executions
                  </div>
                ) : (
                  executions.map((exec) => (
                    <button
                      key={exec.execution_id}
                      onClick={() => setSelectedExecution(exec.execution_id)}
                      className={`w-full text-left p-3 rounded-lg border transition-all ${
                        selectedExecution === exec.execution_id
                          ? "bg-purple-600/20 border-purple-500/50"
                          : "bg-slate-700/50 border-slate-600 hover:border-slate-500"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-white font-semibold text-sm truncate">
                          Exec #{exec.execution_id.substring(0, 8)}
                        </span>
                        <Badge variant="outline" className={`text-xs ${getStatusColor(exec.status)}`}>
                          {exec.status}
                        </Badge>
                      </div>
                      <div className="text-xs text-gray-400">
                        {new Date(exec.started_at).toLocaleTimeString()}
                      </div>
                    </button>
                  ))
                )}
              </CardContent>
            </Card>
          </div>

          {/* Execution Details */}
          <div className="lg:col-span-2 space-y-6">
            {selectedExecution && executions.find((e) => e.execution_id === selectedExecution) ? (
              <>
                {/* Header */}
                <Card className="bg-slate-800 border-slate-700">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle className="text-white">
                          Execution {selectedExecution.substring(0, 12)}...
                        </CardTitle>
                        <CardDescription className="text-gray-400">
                          Real-time event monitoring
                        </CardDescription>
                      </div>
                      {executions.find((e) => e.execution_id === selectedExecution)?.status === "running" && (
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            onClick={() => handlePause(selectedExecution)}
                          >
                            Pause
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleResume(selectedExecution)}
                          >
                            Resume
                          </Button>
                        </div>
                      )}
                    </div>
                  </CardHeader>
                </Card>

                {/* Events Timeline */}
                <Card className="bg-slate-800 border-slate-700">
                  <CardHeader>
                    <CardTitle className="text-white">Event Timeline</CardTitle>
                    <CardDescription className="text-gray-400">
                      Step-by-step execution flow
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {executions
                        .find((e) => e.execution_id === selectedExecution)
                        ?.events?.map((event, idx) => (
                          <div key={idx} className="flex gap-3">
                            <div className="flex flex-col items-center">
                              {getEventIcon(event.event_type)}
                              {idx < (executions.find((e) => e.execution_id === selectedExecution)?.events?.length || 0) - 1 && (
                                <div className="w-0.5 h-8 bg-slate-600 mt-1" />
                              )}
                            </div>
                            <div className="flex-1 pt-1">
                              <div className="font-semibold text-white text-sm">
                                {event.step_name || event.event_type.replace("_", " ").toUpperCase()}
                              </div>
                              <div className="text-xs text-gray-400">
                                {new Date(event.timestamp).toLocaleTimeString()}
                              </div>
                              {event.data && Object.keys(event.data).length > 0 && (
                                <div className="text-xs text-gray-500 mt-1 bg-slate-700/50 p-2 rounded mt-2 font-mono">
                                  {JSON.stringify(event.data, null, 2).substring(0, 100)}...
                                </div>
                              )}
                              {event.error && (
                                <div className="text-xs text-red-400 mt-1 bg-red-500/10 p-2 rounded border border-red-500/20">
                                  Error: {event.error}
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Performance Metrics */}
                <Card className="bg-slate-800 border-slate-700">
                  <CardHeader>
                    <CardTitle className="text-white">Performance</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-slate-700/50 p-4 rounded">
                        <div className="text-gray-400 text-sm">Duration</div>
                        <div className="text-white font-semibold text-lg flex items-center gap-1">
                          <Clock className="w-4 h-4" />
                          --
                        </div>
                      </div>
                      <div className="bg-slate-700/50 p-4 rounded">
                        <div className="text-gray-400 text-sm">Steps Executed</div>
                        <div className="text-white font-semibold text-lg">
                          {executions.find((e) => e.execution_id === selectedExecution)?.events?.length || 0}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </>
            ) : (
              <div className="text-center py-12">
                <Activity className="w-12 h-12 text-gray-500 mx-auto mb-4" />
                <p className="text-gray-400 text-lg">Select an execution to view details</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
