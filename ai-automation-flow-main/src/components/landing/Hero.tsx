import { motion } from "framer-motion";
import { ArrowRight, MessageCircle, Lightbulb, Zap, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";

export const Hero = () => {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0 hero-gradient" />
      <div className="absolute inset-0">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl animate-float" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-accent/5 rounded-full blur-3xl animate-float" style={{ animationDelay: '-3s' }} />
      </div>
      
      {/* Grid pattern */}
      <div 
        className="absolute inset-0 opacity-[0.02]"
        style={{
          backgroundImage: `linear-gradient(hsl(var(--foreground)) 1px, transparent 1px),
                           linear-gradient(90deg, hsl(var(--foreground)) 1px, transparent 1px)`,
          backgroundSize: '60px 60px'
        }}
      />

      <div className="container relative z-10 px-4 py-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center max-w-4xl mx-auto"
        >
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass mb-8"
          >
            <MessageCircle className="w-4 h-4 text-primary" />
            <span className="text-sm text-muted-foreground">Just Ask. AI Builds. You Automate.</span>
          </motion.div>

          {/* Main heading */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="text-6xl md:text-8xl font-bold leading-tight mb-6"
          >
            Just{" "}
            <span className="text-gradient glow-text">Ask</span>
          </motion.h1>

          {/* Subheading */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="text-2xl md:text-3xl font-light text-muted-foreground mb-10 max-w-3xl mx-auto"
          >
            Tell us what you want to automate. In plain English. <br/>
            <span className="text-primary font-semibold">AI builds the workflow. You approve and automate.</span>
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="flex flex-col sm:flex-row gap-4 justify-center mb-12"
          >
            <Button variant="hero" size="xl" asChild>
              <Link to="/dashboard">
                <MessageCircle className="w-5 h-5" />
                Try It Now
                <ArrowRight className="w-5 h-5" />
              </Link>
            </Button>
            <Button variant="hero-outline" size="xl" asChild>
              <Link to="/auth">
                <Zap className="w-5 h-5" />
                Get Started Free
              </Link>
            </Button>
          </motion.div>

          {/* Quick benefits */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.45 }}
            className="flex flex-wrap gap-4 justify-center mb-16"
          >
            {[
              "✨ No code needed",
              "🚀 60 seconds to automate",
              "🔗 100+ integrations",
            ].map((benefit, index) => (
              <div key={index} className="flex items-center gap-2 px-4 py-2 rounded-lg glass">
                <span className="text-sm font-medium">{benefit}</span>
              </div>
            ))}
          </motion.div>

          {/* Stats */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="mt-8 grid grid-cols-3 gap-8 max-w-lg mx-auto"
          >
            {[
              { value: "Ask", label: "Describe What You Want" },
              { value: "Build", label: "AI Creates Workflow" },
              { value: "Run", label: "One-Click Automation" },
            ].map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-2xl md:text-3xl font-bold text-gradient">{stat.value}</div>
                <div className="text-sm text-muted-foreground mt-1">{stat.label}</div>
              </div>
            ))}
          </motion.div>
        </motion.div>

        {/* Preview mockup */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.8 }}
          className="mt-20 max-w-4xl mx-auto"
        >
          <div className="glass rounded-2xl p-1 glow">
            <div className="bg-card rounded-xl overflow-hidden">
              {/* Window header */}
              <div className="flex items-center gap-2 px-4 py-3 border-b border-border">
                <div className="flex gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-destructive/60" />
                  <div className="w-3 h-3 rounded-full bg-warning/60" />
                  <div className="w-3 h-3 rounded-full bg-success/60" />
                </div>
                <div className="flex-1 text-center">
                  <span className="text-xs text-muted-foreground font-mono">flowpilot.app/dashboard</span>
                </div>
              </div>
              
              {/* Content preview */}
              <div className="p-6 bg-gradient-to-b from-card to-background">
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center">
                    <Sparkles className="w-5 h-5 text-primary" />
                  </div>
                  <div className="flex-1">
                    <div className="glass rounded-lg p-4 mb-4">
                      <p className="text-foreground font-medium">
                        "When I receive an email with an attachment, save it to Drive and notify me on Slack"
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="h-8 w-8 rounded bg-secondary flex items-center justify-center">
                        <span className="text-xs">📧</span>
                      </div>
                      <div className="h-px flex-1 bg-gradient-to-r from-primary/50 to-primary/20" />
                      <div className="h-8 w-8 rounded bg-secondary flex items-center justify-center">
                        <span className="text-xs">📁</span>
                      </div>
                      <div className="h-px flex-1 bg-gradient-to-r from-primary/50 to-primary/20" />
                      <div className="h-8 w-8 rounded bg-secondary flex items-center justify-center">
                        <span className="text-xs">💬</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
};
