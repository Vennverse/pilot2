import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Code2, Play, Copy, AlertCircle, CheckCircle2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export default function CodeEditor() {
  const { toast } = useToast();
  const [user, setUser] = useState<any>(null);
  const [language, setLanguage] = useState("python");
  const [code, setCode] = useState(
    `# Example Python script
def process_data(data):
    return {
        'count': len(data),
        'sum': sum(data)
    }

result = process_data([1, 2, 3, 4, 5])
print(result)
`
  );
  const [output, setOutput] = useState<any>(null);
  const [executing, setExecuting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const codeExamples = {
    python: `# Python example
def transform(item):
    return item.upper() if isinstance(item, str) else str(item)

data = "hello world"
print(transform(data))`,
    javascript: `// JavaScript example
const transform = (item) => {
    return typeof item === 'string' ? item.toUpperCase() : String(item);
};

const data = "hello world";
console.log(transform(data));`,
    sql: `-- SQL example
SELECT 
    category,
    COUNT(*) as count,
    AVG(price) as avg_price
FROM products
GROUP BY category`,
  };

  const handleExecute = async () => {
    if (!code.trim()) {
      toast({
        title: "Error",
        description: "Please enter some code",
        variant: "destructive",
      });
      return;
    }

    setExecuting(true);
    setError(null);
    setOutput(null);

    try {
      const response = await fetch("/api/code/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: user?.id || "demo",
          language,
          code,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || "Execution failed");
      }

      const result = await response.json();
      setOutput(result.result);
      
      toast({
        title: "Success",
        description: "Code executed successfully",
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Execution failed";
      setError(message);
      toast({
        title: "Error",
        description: message,
        variant: "destructive",
      });
    } finally {
      setExecuting(false);
    }
  };

  const handleInsertExample = () => {
    setCode(codeExamples[language as keyof typeof codeExamples] || "");
    setOutput(null);
    setError(null);
  };

  const handleCopyCode = () => {
    navigator.clipboard.writeText(code);
    toast({ title: "Code copied to clipboard" });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <h1 className="text-4xl font-bold text-white mb-2">Custom Code Editor</h1>
        <p className="text-gray-400 mb-8">Write and test code that integrates with your workflows</p>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Editor */}
          <div className="lg:col-span-2 space-y-6">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-white flex items-center gap-2">
                    <Code2 className="w-5 h-5" />
                    Code Editor
                  </CardTitle>
                  <div className="flex gap-2">
                    <Select value={language} onValueChange={setLanguage}>
                      <SelectTrigger className="w-32 bg-slate-700 border-slate-600">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="python">Python</SelectItem>
                        <SelectItem value="javascript">JavaScript</SelectItem>
                        <SelectItem value="sql">SQL</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <CardDescription className="text-gray-400">
                  Supported: Python, JavaScript, SQL
                </CardDescription>
              </CardHeader>

              <CardContent>
                <div className="space-y-4">
                  {/* Code Editor */}
                  <div className="bg-slate-900 rounded-lg border border-slate-700 overflow-hidden">
                    <div className="flex items-center justify-between p-3 border-b border-slate-700 bg-slate-800">
                      <span className="text-xs text-gray-400 font-mono">{language}</span>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={handleCopyCode}
                        className="text-gray-400 hover:text-white"
                      >
                        <Copy className="w-4 h-4" />
                      </Button>
                    </div>
                    <textarea
                      value={code}
                      onChange={(e) => setCode(e.target.value)}
                      className="w-full p-4 bg-slate-900 text-white font-mono text-sm resize-none focus:outline-none h-80 border-0"
                      spellCheck="false"
                    />
                  </div>

                  {/* Controls */}
                  <div className="flex gap-2">
                    <Button
                      onClick={handleExecute}
                      disabled={executing}
                      className="flex items-center gap-2"
                    >
                      <Play className="w-4 h-4" />
                      {executing ? "Executing..." : "Execute"}
                    </Button>
                    <Button
                      onClick={handleInsertExample}
                      variant="outline"
                    >
                      Load Example
                    </Button>
                  </div>

                  {/* Security Notice */}
                  <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-3 text-sm text-blue-200">
                    <div className="flex gap-2">
                      <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                      <div>
                        <strong>Security:</strong> Code runs in a sandboxed environment with 30-second timeout and 512MB memory limit.
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Output & Sidebar */}
          <div className="space-y-6">
            {/* Language Features */}
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white text-base">Features</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div className="space-y-2">
                  <div className="font-semibold text-white">Python</div>
                  <ul className="text-gray-400 space-y-1 text-xs">
                    <li>• Full Python 3.x support</li>
                    <li>• Data processing (lists, dicts)</li>
                    <li>• Common libraries (json, re)</li>
                  </ul>
                </div>
                <div className="border-t border-slate-700 pt-2 space-y-2">
                  <div className="font-semibold text-white">JavaScript</div>
                  <ul className="text-gray-400 space-y-1 text-xs">
                    <li>• ES6+ syntax</li>
                    <li>• JSON processing</li>
                    <li>• String & array methods</li>
                  </ul>
                </div>
                <div className="border-t border-slate-700 pt-2 space-y-2">
                  <div className="font-semibold text-white">SQL</div>
                  <ul className="text-gray-400 space-y-1 text-xs">
                    <li>• SELECT queries</li>
                    <li>• Data transformation</li>
                    <li>• Aggregations</li>
                  </ul>
                </div>
              </CardContent>
            </Card>

            {/* Output */}
            {output !== null && (
              <Card className="bg-slate-800 border-slate-700 border-green-500/50">
                <CardHeader>
                  <CardTitle className="text-white text-base flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5 text-green-500" />
                    Output
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <pre className="bg-slate-900 p-3 rounded text-green-400 text-xs font-mono overflow-auto max-h-40">
                    {typeof output === "string" ? output : JSON.stringify(output, null, 2)}
                  </pre>
                </CardContent>
              </Card>
            )}

            {/* Error */}
            {error && (
              <Card className="bg-slate-800 border-slate-700 border-red-500/50">
                <CardHeader>
                  <CardTitle className="text-white text-base flex items-center gap-2">
                    <AlertCircle className="w-5 h-5 text-red-500" />
                    Error
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <pre className="bg-slate-900 p-3 rounded text-red-400 text-xs font-mono overflow-auto max-h-40">
                    {error}
                  </pre>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
