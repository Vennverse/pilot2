import { motion } from "framer-motion";
import { MessageSquare, Sparkles, CheckCircle2, Zap, Lock, Gauge } from "lucide-react";

const features = [
  {
    icon: MessageSquare,
    title: "Just Ask in English",
    description: "Type what you want to automate in natural language. No coding, no technical knowledge required. Pure simplicity.",
    highlight: true,
  },
  {
    icon: Sparkles,
    title: "AI Builds Your Workflow",
    description: "Our AI instantly creates a complete automation plan. From API calls to conditional logic, it figures it out.",
  },
  {
    icon: CheckCircle2,
    title: "Review & Approve",
    description: "See exactly what will run. Tweak any step. Add more integrations. Full transparency, zero surprises.",
  },
  {
    icon: Zap,
    title: "Execute in One Click",
    description: "Approve and your automation runs immediately. Watch live logs. Know exactly what's happening.",
  },
  {
    icon: Gauge,
    title: "100+ Integrations",
    description: "Connect your entire stack. Slack, Stripe, Google Sheets, Salesforce, Notion, and 95+ more services.",
  },
  {
    icon: Lock,
    title: "Enterprise-Grade Security",
    description: "Encrypted credentials. Role-based access. Audit logs. Your data is yours and stays safe.",
  },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5 },
  },
};

export const Features = () => {
  return (
    <section className="py-24 relative">
      <div className="container px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            Automation made <span className="text-gradient">effortless</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Everything you need to build, test, and deploy automations without touching a line of code.
          </p>
        </motion.div>

        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="grid md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {features.map((feature, index) => (
            <motion.div
              key={index}
              variants={itemVariants}
              className="group glass glass-hover rounded-xl p-6 cursor-default"
            >
              <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4 group-hover:bg-primary/20 transition-colors">
                <feature.icon className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
              <p className="text-muted-foreground">{feature.description}</p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
};
