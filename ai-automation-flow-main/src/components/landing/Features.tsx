import { motion } from "framer-motion";
import { Brain, Eye, Shield, Zap, Workflow, Clock } from "lucide-react";

const features = [
  {
    icon: Brain,
    title: "Natural Language Input",
    description: "Describe your automation in plain English. No coding, no complex interfaces—just tell us what you need.",
  },
  {
    icon: Eye,
    title: "Visual Preview",
    description: "See exactly what will happen before it runs. Review every step and approve with confidence.",
  },
  {
    icon: Zap,
    title: "Instant Execution",
    description: "One-click approval triggers your automation. Watch it work in real-time with detailed logs.",
  },
  {
    icon: Workflow,
    title: "Smart Connections",
    description: "Connect to 100+ apps and services. From email to CRM, we integrate with your entire stack.",
  },
  {
    icon: Clock,
    title: "Scheduled & Triggered",
    description: "Run automations on schedule or trigger them from events. Full control over when things happen.",
  },
  {
    icon: Shield,
    title: "Enterprise Security",
    description: "Your data stays safe with end-to-end encryption and SOC 2 compliant infrastructure.",
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
