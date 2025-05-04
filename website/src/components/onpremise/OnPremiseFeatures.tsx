import React from 'react';
import { motion } from 'framer-motion';
import { Server, Lock, Database, Zap, Shield, Settings } from 'lucide-react';
import { useInView } from 'react-intersection-observer';

interface FeatureProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  delay: number;
}

const Feature: React.FC<FeatureProps> = ({ icon, title, description, delay }) => {
  const [ref, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
  });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 20 }}
      animate={inView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
      transition={{ duration: 0.5, delay }}
      className="flex gap-4"
    >
      <div className="rounded-full bg-primary-900/50 w-12 h-12 flex-shrink-0 flex items-center justify-center border border-primary-800/50">
        <div className="text-primary-400">{icon}</div>
      </div>
      <div>
        <h3 className="text-xl font-semibold mb-2 text-white">{title}</h3>
        <p className="text-surface-300">{description}</p>
      </div>
    </motion.div>
  );
};

const OnPremiseFeatures: React.FC = () => {
  const [ref, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
  });

  const features = [
    {
      icon: <Server size={24} />,
      title: "Self-Hosted Infrastructure",
      description: "Deploy within your own infrastructure, maintaining complete control over hardware and software resources."
    },
    {
      icon: <Lock size={24} />,
      title: "Data Sovereignty",
      description: "All your code and data stays within your environment, never leaving your secure network boundaries."
    },
    {
      icon: <Database size={24} />,
      title: "Private Model Deployment",
      description: "Deploy AI models within your infrastructure without external API calls for maximum security."
    },
    {
      icon: <Zap size={24} />,
      title: "Custom Integration",
      description: "Seamlessly integrate with your existing development tools, CI/CD pipelines, and security systems."
    },
    {
      icon: <Shield size={24} />,
      title: "Enterprise Security",
      description: "Compatible with your existing security protocols, policies, and compliance requirements."
    },
    {
      icon: <Settings size={24} />,
      title: "Customizable Deployment",
      description: "Tailor the setup to your specific needs with flexible configuration options and scaling capabilities."
    }
  ];

  return (
    <section className="py-20 relative">
      <div className="container-custom">
        <motion.div
          ref={ref}
          initial={{ opacity: 0, y: 20 }}
          animate={inView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
          transition={{ duration: 0.5 }}
          className="text-center mb-16"
        >
          <h2 className="mb-4">
            <span className="gradient-text sub-heading">Enterprise-Grade Security & Control</span>
          </h2>
          <p className="text-lg text-surface-300 max-w-2xl mx-auto">
            Our on-premise solution is designed for organizations that require the highest 
            levels of security, compliance, and data control.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
          {features.map((feature, index) => (
            <Feature
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

export default OnPremiseFeatures;