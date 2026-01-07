import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { ArrowLeft } from "lucide-react";

const Settings = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50 w-full">
        <div className="container flex items-center gap-4 h-16 px-4 mx-auto max-w-7xl">
          <Button variant="ghost" size="sm" onClick={() => navigate("/dashboard")}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          <h1 className="text-xl font-semibold">Settings</h1>
        </div>
      </header>

      <main className="container px-4 py-8 max-w-7xl mx-auto w-full">
        <div className="text-center py-20">
          <h2 className="text-2xl font-bold mb-4">Settings Content Removed</h2>
          <p className="text-muted-foreground">Starting from scratch as requested.</p>
        </div>
      </main>
    </div>
  );
};

export default Settings;
