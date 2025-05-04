import React from 'react';
import { motion } from 'framer-motion';
import { Code2, Terminal, FileSearch, Shield, Briefcase, Cpu } from 'lucide-react';
import { useInView } from 'react-intersection-observer';

interface FeatureCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  delay: number;
}

const FeatureCard: React.FC<FeatureCardProps> = ({ icon, title, description, delay }) => {
  const [ref, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
  });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 20 }}
      animate={inView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
      transition={{ duration: 0.5, delay: delay }}
      className="feature-card rounded-xl p-6"
    >
      <div className="rounded-full bg-primary-900/50 w-12 h-12 flex items-center justify-center mb-4 border border-primary-800/50">
        <div className="text-primary-400">{icon}</div>
      </div>
      <h3 className="text-xl font-semibold mb-2 text-white">{title}</h3>
      <p className="text-surface-300">{description}</p>
    </motion.div>
  );
};

const Features: React.FC = () => {
  const [ref, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
  });

  const features = [
    {
      icon: <Code2 size={24} />,
      title: "Intelligent Code Generation",
      description: "Generate clean, maintainable code that follows best practices and design patterns."
    },
    {
      icon: <Terminal size={24} />,
      title: "Automated Debugging",
      description: "Quickly identify and fix bugs with intelligent analysis and suggestions."
    },
    {
      icon: <FileSearch size={24} />,
      title: "Code Review & Refactoring",
      description: "Get recommendations to improve code quality and maintain SOLID principles."
    },
    {
      icon: <Shield size={24} />,
      title: "Security Analysis",
      description: "Identify potential security vulnerabilities and receive remediation guidance."
    },
    {
      icon: <Briefcase size={24} />,
      title: "Multi-Language Support",
      description: "Works with all major programming languages and frameworks."
    },
    {
      icon: <Cpu size={24} />,
      title: "IDE Integration",
      description: "Seamlessly integrates with VSCode, IntelliJ, and other popular IDEs."
    }
  ];

  return (
    <section className="py-20 relative overflow-hidden">
      <div className="container-custom">
        <motion.div
          ref={ref}
          initial={{ opacity: 0, y: 20 }}
          animate={inView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
          transition={{ duration: 0.5 }}
          className="text-center mb-16"
        >
          <h2 className="mb-4">
            <span className="gradient-text sub-heading">Powerful Features</span>
          </h2>
          <p className="text-lg text-surface-300 max-w-2xl mx-auto">
            Baid.dev comes packed with features to help developers write better code faster,
            debug more efficiently, and maintain high-quality codebases.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <FeatureCard
              key={index}
              icon={feature.icon}
              title={feature.title}
              description={feature.description}
              delay={index * 0.1}
            />
          ))}
        </div>
      </div>
    </section>
  );
};

export default Features;