import React, { useEffect } from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, Shield, ServerCog } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useInView } from 'react-intersection-observer';
import OnPremiseFeatures from '../components/onpremise/OnPremiseFeatures';

const OnPremisePage: React.FC = () => {
  useEffect(() => {
    document.title = 'On-Premise Solution - Baid.dev';
  }, []);

  const [topRef, topInView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
  });

  const [contactRef, contactInView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
  });

  return (
    <>
      {/* Hero Section */}
      <section className="pt-28 pb-20 md:pt-32 md:pb-24 relative overflow-hidden">
        {/* Background elements */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-primary-900/20 rounded-full blur-[120px] -z-10"></div>
        </div>

        <div className="container-custom">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <motion.div
              ref={topRef}
              initial={{ opacity: 0, y: 20 }}
              animate={topInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
              transition={{ duration: 0.6 }}
            >
              <div className="mb-6">
                <span className="badge badge-primary mb-4">On-Premise Solution</span>
                <h1 className="mb-6 title">
                  <span className="gradient-text">Complete Control</span>
                  <br />
                  Over Your Environment
                </h1>
                <p className="text-lg md:text-xl text-surface-300 mb-8 max-w-lg">
                  Our enterprise-grade on-premise solution lets you deploy Baid.dev entirely 
                  within your own infrastructure, ensuring maximum security, control, and 
                  compliance.
                </p>
              </div>

              <div className="flex flex-col sm:flex-row gap-4">
                <a 
                  href="mailto:sales@beskar.tech" 
                  className="btn btn-primary"
                >
                  Contact Sales
                  <ArrowRight className="ml-2 h-5 w-5" />
                </a>
                <Link to="/hosted" className="btn btn-outline">
                  Explore Hosted Option
                </Link>
              </div>
            </motion.div>

            {/* Illustration/Image */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={topInView ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="p-6 bg-surface-900/50 rounded-2xl border border-surface-800"
            >
              <div className="aspect-video relative overflow-hidden rounded-lg bg-surface-800 flex items-center justify-center">
                <ServerCog className="h-24 w-24 text-primary-500" />
                <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-surface-900 to-transparent">
                  <div className="flex items-center space-x-2">
                    <Shield className="h-5 w-5 text-secondary-500" />
                    <span className="text-sm font-medium text-secondary-400">Secure On-Premise Deployment</span>
                  </div>
                </div>
              </div>
              <div className="mt-6 space-y-4">
                <div className="flex items-start space-x-3">
                  <div className="h-6 w-6 rounded-full bg-primary-900 flex items-center justify-center mt-0.5">
                    <span className="text-primary-500 text-sm font-bold">1</span>
                  </div>
                  <div>
                    <h3 className="font-medium">Complete Data Isolation</h3>
                    <p className="text-sm text-surface-400">Your data never leaves your environment</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="h-6 w-6 rounded-full bg-primary-900 flex items-center justify-center mt-0.5">
                    <span className="text-primary-500 text-sm font-bold">2</span>
                  </div>
                  <div>
                    <h3 className="font-medium">Custom Security Policies</h3>
                    <p className="text-sm text-surface-400">Integrate with your existing security framework</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="h-6 w-6 rounded-full bg-primary-900 flex items-center justify-center mt-0.5">
                    <span className="text-primary-500 text-sm font-bold">3</span>
                  </div>
                  <div>
                    <h3 className="font-medium">Enterprise Integration</h3>
                    <p className="text-sm text-surface-400">Connect with your internal development tools</p>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Features */}
      <OnPremiseFeatures />

      {/* Contact Section */}
      <section className="py-20 bg-surface-950 relative">
        <div className="container-custom">
          <motion.div
            ref={contactRef}
            initial={{ opacity: 0, y: 20 }}
            animate={contactInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
            transition={{ duration: 0.5 }}
            className="bg-surface-900 rounded-2xl p-8 md:p-12 border border-surface-800 max-w-4xl mx-auto"
          >
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold mb-4">Request On-Premise Information</h2>
              <p className="text-surface-300 max-w-2xl mx-auto">
                Interested in deploying Baid.dev in your own environment? Contact our sales team
                to discuss your specific requirements and get a custom quote.
              </p>
            </div>
            
            <div className="flex flex-col items-center">
              <div className="bg-surface-800 rounded-lg p-6 max-w-md w-full mb-6">
                <h3 className="text-xl font-semibold mb-4">Contact Us</h3>
                <p className="mb-6 text-surface-300">
                  Reach out to our sales team directly to discuss your on-premise deployment needs:
                </p>
                <a 
                  href="mailto:sales@beskar.tech" 
                  className="text-primary-400 hover:text-primary-300 transition text-lg font-medium flex items-center"
                >
                  sales@beskar.tech
                  <ArrowRight className="ml-2 h-5 w-5" />
                </a>
              </div>
              
              <p className="text-surface-400 text-sm max-w-md text-center">
                Our team will get back to you within 24 hours to schedule a consultation
                and discuss your specific requirements.
              </p>
            </div>
          </motion.div>
        </div>
      </section>
    </>
  );
};

export default OnPremisePage;