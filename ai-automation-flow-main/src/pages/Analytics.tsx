import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, DollarSign, Clock, BarChart3, Download, Share2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

interface ROIDashboard {
  total_workflows: number;
  total_executions: number;
  successful_executions: number;
  total_time_saved_hours: number;
  total_cost_saved_dollars: number;
  avg_success_rate: number;
  workflows: {
    workflow_id: string;
    name: string;
    executions: number;
    success_rate: number;
    time_saved: number;
    cost_saved: number;
  }[];
}

export default function Analytics() {
  const { toast } = useToast();
  const [user, setUser] = useState<any>(null);
  const [roi, setROI] = useState<ROIDashboard | null>(null);
  const [projection, setProjection] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const user_id = localStorage.getItem("user_id");
    setUser({ id: user_id });
    if (user_id) {
      fetchAnalytics(user_id);
      fetchProjection(user_id);
    }
  }, []);

  const fetchAnalytics = async (user_id: string) => {
    try {
      const response = await fetch(`/api/analytics/roi?user_id=${user_id}`);
      if (!response.ok) throw new Error("Failed to fetch analytics");
      const data = await response.json();
      setROI(data);
    } catch (error) {
      console.error("Error fetching analytics:", error);
      toast({
        title: "Error",
        description: "Failed to load analytics",
        variant: "destructive",
      });
    }
  };

  const fetchProjection = async (user_id: string) => {
    try {
      const response = await fetch(`/api/analytics/roi-projection?user_id=${user_id}`);
      if (!response.ok) throw new Error("Failed to fetch projection");
      const data = await response.json();
      setProjection(data);
    } catch (error) {
      console.error("Error fetching projection:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-white">Loading analytics...</div>
      </div>
    );
  }

  if (!roi) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-white text-center">
          <h2 className="text-2xl font-bold mb-2">No Data Available</h2>
          <p className="text-gray-400">Run some workflows to see analytics</p>
        </div>
      </div>
    );
  }

  const chartData = projection?.monthly_projections?.map((month: any) => ({
    month: month.month,
    cost_saved: month.total_cost_saved,
    time_saved: month.total_time_saved_hours,
  })) || [];

  const workflowData = roi.workflows?.map((w) => ({
    name: w.name.substring(0, 20),
    executions: w.executions,
    success: w.success_rate,
    time_saved: Math.round(w.time_saved),
  })) || [];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 py-8">
      <div className="max-w-7xl mx-auto px-4">
        <h1 className="text-4xl font-bold text-white mb-8">Analytics & ROI</h1>

        {/* KPI Cards */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-white text-sm font-medium">Total Executions</CardTitle>
              <TrendingUp className="h-4 w-4 text-purple-500" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-white">{roi.total_executions}</div>
              <p className="text-xs text-gray-400 mt-1">
                {roi.successful_executions} successful
              </p>
            </CardContent>
          </Card>

          <Card className="bg-slate-800 border-slate-700">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-white text-sm font-medium">Time Saved</CardTitle>
              <Clock className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-white">
                {roi.total_time_saved_hours.toFixed(1)}h
              </div>
              <p className="text-xs text-gray-400 mt-1">vs manual execution</p>
            </CardContent>
          </Card>

          <Card className="bg-slate-800 border-slate-700">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-white text-sm font-medium">Cost Saved</CardTitle>
              <DollarSign className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-white">
                ${roi.total_cost_saved_dollars.toFixed(0)}
              </div>
              <p className="text-xs text-gray-400 mt-1">Labor cost reduction</p>
            </CardContent>
          </Card>

          <Card className="bg-slate-800 border-slate-700">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-white text-sm font-medium">Success Rate</CardTitle>
              <BarChart3 className="h-4 w-4 text-emerald-500" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-white">
                {(roi.avg_success_rate * 100).toFixed(1)}%
              </div>
              <p className="text-xs text-gray-400 mt-1">Average across all workflows</p>
            </CardContent>
          </Card>
        </div>

        {/* Charts */}
        <div className="grid lg:grid-cols-2 gap-8 mb-8">
          {/* ROI Projection */}
          {chartData.length > 0 && (
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">12-Month ROI Projection</CardTitle>
                <CardDescription className="text-gray-400">
                  Projected cost and time savings
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
                    <XAxis stroke="#9CA3AF" />
                    <YAxis stroke="#9CA3AF" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#1E293B",
                        border: "1px solid #475569",
                      }}
                    />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="cost_saved"
                      stroke="#10B981"
                      name="Cost Saved ($)"
                    />
                    <Line
                      type="monotone"
                      dataKey="time_saved"
                      stroke="#3B82F6"
                      name="Time Saved (hrs)"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}

          {/* Workflow Performance */}
          {workflowData.length > 0 && (
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Workflow Performance</CardTitle>
                <CardDescription className="text-gray-400">
                  Executions by workflow
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={workflowData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
                    <XAxis stroke="#9CA3AF" dataKey="name" />
                    <YAxis stroke="#9CA3AF" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#1E293B",
                        border: "1px solid #475569",
                      }}
                    />
                    <Legend />
                    <Bar dataKey="executions" fill="#8B5CF6" name="Executions" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Workflows Table */}
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white">Workflow Details</CardTitle>
            <CardDescription className="text-gray-400">
              Performance metrics for each workflow
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700">
                    <th className="text-left py-3 px-4 text-gray-400">Workflow</th>
                    <th className="text-center py-3 px-4 text-gray-400">Executions</th>
                    <th className="text-center py-3 px-4 text-gray-400">Success Rate</th>
                    <th className="text-center py-3 px-4 text-gray-400">Time Saved</th>
                    <th className="text-center py-3 px-4 text-gray-400">Cost Saved</th>
                  </tr>
                </thead>
                <tbody>
                  {roi.workflows?.map((workflow) => (
                    <tr key={workflow.workflow_id} className="border-b border-slate-700 hover:bg-slate-700/50">
                      <td className="py-3 px-4 text-white font-medium">{workflow.name}</td>
                      <td className="text-center py-3 px-4 text-gray-300">{workflow.executions}</td>
                      <td className="text-center py-3 px-4">
                        <Badge variant="outline">
                          {(workflow.success_rate * 100).toFixed(1)}%
                        </Badge>
                      </td>
                      <td className="text-center py-3 px-4 text-blue-400">
                        {workflow.time_saved.toFixed(1)}h
                      </td>
                      <td className="text-center py-3 px-4 text-green-400">
                        ${workflow.cost_saved.toFixed(0)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Actions */}
        <div className="mt-8 flex gap-4">
          <Button
            onClick={() => {
              const report = JSON.stringify(roi, null, 2);
              const blob = new Blob([report], { type: "application/json" });
              const url = URL.createObjectURL(blob);
              const a = document.createElement("a");
              a.href = url;
              a.download = "analytics-report.json";
              a.click();
              toast({ title: "Downloaded report" });
            }}
            className="flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            Download Report
          </Button>
          <Button variant="outline" className="flex items-center gap-2">
            <Share2 className="w-4 h-4" />
            Share Analytics
          </Button>
        </div>
      </div>
    </div>
  );
}
