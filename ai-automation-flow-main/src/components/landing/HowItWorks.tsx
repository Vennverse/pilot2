import { motion } from "framer-motion";
import { MessageSquare, Eye, PlayCircle, CheckCircle } from "lucide-react";

const steps = [
  {
    icon: MessageSquare,
    step: "01",
    title: "Describe Your Workflow",
    description: "Type what you want to automate in plain English. Our AI understands context and intent.",
    example: '"Send a Slack message when a new Stripe payment comes in"',
  },
  {
    icon: Eye,
    step: "02",
    title: "Review the Preview",
    description: "See a visual breakdown of every step. Understand exactly what will happen before it runs.",
    example: "Trigger → Transform → Action",
  },
  {
    icon: PlayCircle,
    step: "03",
    title: "Approve & Execute",
    description: "One click to activate. Your automation starts running immediately with full monitoring.",
    example: "Live execution with real-time logs",
  },
  {
    icon: CheckCircle,
    step: "04",
    title: "Track & Optimize",
    description: "Monitor performance, view history, and let AI suggest improvements over time.",
    example: "Analytics dashboard with insights",
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
          className="text-center mb-16"
        >
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            How it <span className="text-gradient">works</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            From idea to execution in minutes, not hours.
          </p>
        </motion.div>

        <div className="relative max-w-4xl mx-auto">
          {/* Connecting line */}
          <div className="absolute left-8 md:left-1/2 top-0 bottom-0 w-px bg-gradient-to-b from-primary/50 via-primary/20 to-transparent hidden md:block" />

          {steps.map((step, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: index % 2 === 0 ? -20 : 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className={`relative flex items-start gap-6 mb-12 last:mb-0 ${
                index % 2 === 0 ? "md:flex-row" : "md:flex-row-reverse"
              }`}
            >
              {/* Content */}
              <div className={`flex-1 ${index % 2 === 0 ? "md:text-right" : "md:text-left"}`}>
                <div className="glass rounded-xl p-6 inline-block">
                  <span className="text-primary font-mono text-sm mb-2 block">{step.step}</span>
                  <h3 className="text-xl font-semibold mb-2">{step.title}</h3>
                  <p className="text-muted-foreground mb-3">{step.description}</p>
                  <div className="inline-block px-3 py-1.5 rounded-lg bg-secondary text-sm font-mono text-muted-foreground">
                    {step.example}
                  </div>
                </div>
              </div>

              {/* Icon node */}
              <div className="relative z-10 hidden md:flex">
                <div className="w-16 h-16 rounded-xl bg-primary/10 border border-primary/30 flex items-center justify-center">
                  <step.icon className="w-7 h-7 text-primary" />
                </div>
              </div>

              {/* Spacer for alternating layout */}
              <div className="flex-1 hidden md:block" />
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};
