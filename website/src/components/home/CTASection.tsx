import React from 'react';
import { motion } from 'framer-motion';
import { ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useInView } from 'react-intersection-observer';

const CTASection: React.FC = () => {
  const [ref, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
  });

  return (
    <section className="py-20 relative overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-surface-950 via-primary-950/20 to-surface-950 opacity-50"></div>
      
      <div className="container-custom relative z-10">
        <motion.div
          ref={ref}
          initial={{ opacity: 0, y: 20 }}
          animate={inView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
          transition={{ duration: 0.6 }}
          className="bg-surface-900/80 backdrop-blur-sm rounded-2xl p-8 md:p-12 border border-surface-800 max-w-5xl mx-auto text-center"
        >
          <div className="mb-8">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Ready to Transform Your Development Experience?
            </h2>
            <p className="text-lg text-surface-300 max-w-2xl mx-auto">
              Join the waitlist for our hosted solution or inquire about our on-premise 
              options for enterprise deployment.
            </p>
          </div>
          
          <div className="flex flex-col sm:flex-row justify-center gap-4">
            <Link 
              to="/hosted" 
              className="btn btn-primary"
            >
              Join the Waitlist
              <ArrowRight className="ml-2 h-5 w-5" />
            </Link>
            <Link 
              to="/on-premise" 
              className="btn btn-outline"
            >
              Explore On-Premise Options
            </Link>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

export default CTASection;