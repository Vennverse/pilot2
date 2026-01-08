import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import Index from "./pages/Index";
import Dashboard from "./pages/Dashboard";
import Auth from "./pages/Auth";
import Settings from "./pages/Settings";
import WorkflowEditor from "./pages/WorkflowEditor";
import NotFound from "./pages/NotFound";
import Pricing from "./pages/Pricing";
import TeamSettings from "./pages/TeamSettings";
import Analytics from "./pages/Analytics";
import Marketplace from "./pages/Marketplace";
import ExecutionMonitor from "./pages/ExecutionMonitor";
import CodeEditor from "./pages/CodeEditor";
import AgentInterface from "./pages/AgentInterface";

const queryClient = new QueryClient();

const App = () => (
  <ErrorBoundary>
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Index />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/workflow/:id" element={<WorkflowEditor />} />
            <Route path="/auth" element={<Auth />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/pricing" element={<Pricing />} />
            <Route path="/team" element={<TeamSettings />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/marketplace" element={<Marketplace />} />
            <Route path="/monitoring" element={<ExecutionMonitor />} />
            <Route path="/code" element={<CodeEditor />} />
            <Route path="/agents" element={<AgentInterface />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  </ErrorBoundary>
);

export default App;
