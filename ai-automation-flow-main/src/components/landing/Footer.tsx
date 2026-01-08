import { MessageCircle } from "lucide-react";
import { Link } from "react-router-dom";

export const Footer = () => {
  return (
    <footer className="py-16 border-t border-border/50 bg-secondary/20">
      <div className="container px-4">
        <div className="grid md:grid-cols-4 gap-12 mb-12">
          {/* Brand */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center">
                <MessageCircle className="w-4 h-4 text-primary" />
              </div>
              <span className="text-lg font-bold">Ask</span>
            </div>
            <p className="text-sm text-muted-foreground">
              Just ask. AI builds. You automate. The future of workflow automation.
            </p>
          </div>

          {/* Product */}
          <div>
            <h4 className="font-semibold mb-4">Product</h4>
            <nav className="space-y-2">
              <Link to="/dashboard" className="block text-sm text-muted-foreground hover:text-foreground transition-colors">
                Dashboard
              </Link>
              <a href="#features" className="block text-sm text-muted-foreground hover:text-foreground transition-colors">
                Features
              </a>
              <a href="#how-it-works" className="block text-sm text-muted-foreground hover:text-foreground transition-colors">
                How It Works
              </a>
              <a href="#" className="block text-sm text-muted-foreground hover:text-foreground transition-colors">
                Integrations
              </a>
            </nav>
          </div>

          {/* Company */}
          <div>
            <h4 className="font-semibold mb-4">Company</h4>
            <nav className="space-y-2">
              <a href="#" className="block text-sm text-muted-foreground hover:text-foreground transition-colors">
                About
              </a>
              <a href="#" className="block text-sm text-muted-foreground hover:text-foreground transition-colors">
                Blog
              </a>
              <a href="#" className="block text-sm text-muted-foreground hover:text-foreground transition-colors">
                Status
              </a>
              <a href="#" className="block text-sm text-muted-foreground hover:text-foreground transition-colors">
                Contact
              </a>
            </nav>
          </div>

          {/* Legal */}
          <div>
            <h4 className="font-semibold mb-4">Legal</h4>
            <nav className="space-y-2">
              <a href="#" className="block text-sm text-muted-foreground hover:text-foreground transition-colors">
                Privacy
              </a>
              <a href="#" className="block text-sm text-muted-foreground hover:text-foreground transition-colors">
                Terms
              </a>
              <a href="#" className="block text-sm text-muted-foreground hover:text-foreground transition-colors">
                Security
              </a>
            </nav>
          </div>
        </div>

        {/* Bottom section */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-4 pt-8 border-t border-border/50">
          <p className="text-sm text-muted-foreground">
            © 2026 Ask. All rights reserved. Just ask. AI builds. You automate.
          </p>
          <div className="flex items-center gap-6">
            <a href="#" className="text-muted-foreground hover:text-foreground transition-colors">
              Twitter
            </a>
            <a href="#" className="text-muted-foreground hover:text-foreground transition-colors">
              Discord
            </a>
            <a href="#" className="text-muted-foreground hover:text-foreground transition-colors">
              GitHub
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
};
