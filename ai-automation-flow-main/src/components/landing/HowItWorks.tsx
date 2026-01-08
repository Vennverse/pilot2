import { motion } from "framer-motion";
import { MessageCircle, Lightbulb, CheckCircle, Zap } from "lucide-react";

const steps = [
  {
    icon: MessageCircle,
    step: "1",
    title: "Ask",
    description: "Describe your automation in plain English. Tell us what you want to happen.",
    example: '"When I get a Stripe payment, save it to Google Sheets"',
    color: "from-blue-500/20 to-blue-500/0",
  },
  {
    icon: Lightbulb,
    step: "2",
    title: "AI Builds",
    description: "Our AI instantly creates your complete workflow. Every step, integration, and condition.",
    example: "Trigger → Fetch data → Transform → Save → Notify",
    color: "from-purple-500/20 to-purple-500/0",
  },
  {
    icon: CheckCircle,
    step: "3",
    title: "Review",
    description: "See exactly what will run. Approve, tweak, or add more steps. Full control.",
    example: "Visual workflow preview with full transparency",
    color: "from-green-500/20 to-green-500/0",
  },
  {
    icon: Zap,
    step: "4",
    title: "Execute",
    description: "One click to activate. Your automation runs immediately with live monitoring.",
    example: "Watch it happen with real-time execution logs",
    color: "from-amber-500/20 to-amber-500/0",
  },
];

export const HowItWorks = () => {
  return (
    <section className="py-24 relative bg-secondary/30">
      <div className="container px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-20"
        >
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            4 Simple Steps to <span className="text-gradient">Automate Anything</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            From thought to execution in just minutes. No complexity, no friction.
          </p>
        </motion.div>

        {/* Steps Grid */}
        <div className="grid md:grid-cols-4 gap-6 max-w-6xl mx-auto">
          {steps.map((step, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="relative"
            >
              <div className={`group relative overflow-hidden rounded-xl border border-primary/20 p-6 h-full bg-gradient-to-b ${step.color} hover:border-primary/40 transition-all duration-300`}>
                {/* Step number */}
                <div className="absolute -right-8 -top-8 w-24 h-24 bg-primary/5 rounded-full group-hover:bg-primary/10 transition-colors" />
                
                {/* Icon */}
                <div className="relative z-10 w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4 group-hover:bg-primary/20 transition-colors">
                  <step.icon className="w-6 h-6 text-primary" />
                </div>

                {/* Content */}
                <div className="relative z-10">
                  <div className="inline-block px-2 py-1 rounded bg-primary/20 text-primary text-xs font-semibold mb-3">
                    Step {step.step}
                  </div>
                  <h3 className="text-2xl font-bold mb-2">{step.title}</h3>
                  <p className="text-muted-foreground mb-4 text-sm">{step.description}</p>
                  <div className="px-3 py-2 rounded bg-secondary/50 text-xs text-muted-foreground border border-primary/10 italic">
                    {step.example}
                  </div>
                </div>

                {/* Connector arrow to next step */}
                {index < steps.length - 1 && (
                  <div className="hidden md:flex absolute -right-3 top-1/2 z-20">
                    <div className="w-6 h-0.5 bg-gradient-to-r from-primary/50 to-transparent" />
                    <div className="w-0 h-0 border-l-3 border-l-transparent border-r-0 border-y-2 border-y-primary/50" />
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </div>

        {/* Bottom message */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="text-center mt-16"
        >
          <p className="text-lg text-muted-foreground">
            <span className="font-semibold text-foreground">That's it.</span> Your automation is now live and working 24/7.
          </p>
        </motion.div>
    </section>
  );
};
