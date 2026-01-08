import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Lightbulb, Send, Copy, AlertCircle } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { Input } from "@/components/ui/input";

interface AgentResponse {
  agent: string;
  response: string;
  alternatives?: string[];
  confidence: number;
  reasoning: string;
}

const agents = [
  {
    id: "sales",
    name: "Sales Agent",
    description: "Analyzes sales workflows and suggests optimizations",
    color: "from-purple-600 to-purple-700",
  },
  {
    id: "marketing",
    name: "Marketing Agent",
    description: "Optimizes marketing automation sequences",
    color: "from-blue-600 to-blue-700",
  },
  {
    id: "finance",
    name: "Finance Agent",
    description: "Automates financial processes and reporting",
    color: "from-green-600 to-green-700",
  },
  {
    id: "support",
    name: "Support Agent",
    description: "Enhances customer support workflows",
    color: "from-pink-600 to-pink-700",
  },
  {
    id: "hr",
    name: "HR Agent",
    description: "Streamlines human resources processes",
    color: "from-orange-600 to-orange-700",
  },
];

export default function AgentInterface() {
  const { toast } = useToast();
  const [user, setUser] = useState<any>(null);
  const [query, setQuery] = useState("");
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [response, setResponse] = useState<AgentResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<AgentResponse[]>([]);

  useEffect(() => {
    const user_id = localStorage.getItem("user_id");
    setUser({ id: user_id });
  }, []);

  const handleAsk = async () => {
    if (!query.trim() || !selectedAgent) {
      toast({
        title: "Error",
        description: "Please select an agent and enter a query",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);

    try {
      const response = await fetch("/api/agents/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: user?.id || "demo",
          agent: selectedAgent,
          query,
        }),
      });

      if (!response.ok) throw new Error("Query failed");

      const result = await response.json();
      setResponse(result);
      setHistory([result, ...history.slice(0, 4)]);
      setQuery("");

      toast({
        title: "Success",
        description: "Agent response received",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to get agent response",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCopyResponse = () => {
    if (response) {
      navigator.clipboard.writeText(response.response);
      toast({ title: "Copied to clipboard" });
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-white mb-2">AI Agent Interface</h1>
          <p className="text-gray-400 text-lg">
            Ask specialized AI agents for workflow recommendations and automation insights
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Agents Selector */}
          <div className="lg:col-span-1">
            <Card className="bg-slate-800 border-slate-700 sticky top-4">
              <CardHeader>
                <CardTitle className="text-white">Available Agents</CardTitle>
                <CardDescription className="text-gray-400">
                  {selectedAgent
                    ? agents.find((a) => a.id === selectedAgent)?.name
                    : "Select an agent"}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {agents.map((agent) => (
                  <button
                    key={agent.id}
                    onClick={() => setSelectedAgent(agent.id)}
                    className={`w-full text-left p-4 rounded-lg border transition-all ${
                      selectedAgent === agent.id
                        ? `bg-gradient-to-r ${agent.color} border-transparent text-white`
                        : "bg-slate-700/50 border-slate-600 text-gray-300 hover:border-slate-500"
                    }`}
                  >
                    <div className="font-semibold">{agent.name}</div>
                    <div className="text-xs opacity-75 mt-1">{agent.description}</div>
                  </button>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Main Chat Area */}
          <div className="lg:col-span-2 space-y-6">
            {/* Input Area */}
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Lightbulb className="w-5 h-5" />
                  Ask a Question
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-2">
                  <Input
                    placeholder="e.g., How can I optimize my lead qualification workflow?"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyPress={(e) => e.key === "Enter" && handleAsk()}
                    className="bg-slate-700 border-slate-600 text-white"
                    disabled={!selectedAgent}
                  />
                  <Button
                    onClick={handleAsk}
                    disabled={loading || !selectedAgent}
                    className="flex items-center gap-2"
                  >
                    <Send className="w-4 h-4" />
                    Ask
                  </Button>
                </div>
                <p className="text-xs text-gray-400">
                  {selectedAgent
                    ? "Ready to ask the agent a question"
                    : "Please select an agent first"}
                </p>
              </CardContent>
            </Card>

            {/* Current Response */}
            {response && (
              <Card className="bg-slate-800 border-slate-700 border-purple-500/30">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-white">
                        {agents.find((a) => a.id === response.agent)?.name}
                      </CardTitle>
                      <CardDescription className="text-gray-400">
                        Confidence: {(response.confidence * 100).toFixed(0)}%
                      </CardDescription>
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={handleCopyResponse}
                      className="text-gray-400 hover:text-white"
                    >
                      <Copy className="w-4 h-4" />
                    </Button>
                  </div>
                </CardHeader>

                <CardContent className="space-y-6">
                  {/* Main Response */}
                  <div>
                    <h4 className="font-semibold text-white mb-2">Recommendation</h4>
                    <p className="text-gray-300 leading-relaxed">{response.response}</p>
                  </div>

                  {/* Reasoning */}
                  <div className="bg-slate-700/50 p-4 rounded-lg border border-slate-600">
                    <h4 className="font-semibold text-white mb-2 text-sm">Reasoning</h4>
                    <p className="text-gray-400 text-sm leading-relaxed">{response.reasoning}</p>
                  </div>

                  {/* Alternatives */}
                  {response.alternatives && response.alternatives.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-white mb-2">Alternative Approaches</h4>
                      <div className="space-y-2">
                        {response.alternatives.map((alt, idx) => (
                          <div
                            key={idx}
                            className="bg-slate-700/50 p-3 rounded border border-slate-600 text-sm text-gray-300"
                          >
                            <span className="text-purple-400 font-semibold">Option {idx + 1}:</span> {alt}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Action Buttons */}
                  <div className="flex gap-2 pt-2 border-t border-slate-700">
                    <Button
                      size="sm"
                      onClick={() => {
                        setQuery(`Implement: ${response.response}`);
                      }}
                      className="text-xs"
                    >
                      Implement
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setQuery(`Explain more about: ${response.response}`);
                      }}
                      className="text-xs"
                    >
                      Learn More
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* History */}
            {history.length > 0 && (
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-white text-base">Recent Responses</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {history.map((h, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-slate-700/50 rounded border border-slate-600 cursor-pointer hover:border-slate-500 transition-colors"
                      onClick={() => setResponse(h)}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-semibold text-white text-sm">
                            {agents.find((a) => a.id === h.agent)?.name}
                          </div>
                          <div className="text-xs text-gray-400 mt-1 line-clamp-2">
                            {h.response}
                          </div>
                        </div>
                        <Badge variant="outline" className="text-xs">
                          {(h.confidence * 100).toFixed(0)}%
                        </Badge>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}

            {/* Tips */}
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white text-base flex items-center gap-2">
                  <AlertCircle className="w-4 h-4" />
                  Tips
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm text-gray-400">
                <p>• Be specific about your workflows and goals</p>
                <p>• Agents learn from your history for better recommendations</p>
                <p>• Use "Implement" to start building suggested workflows</p>
                <p>• Ask follow-up questions for more details</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
