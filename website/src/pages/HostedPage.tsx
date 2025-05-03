import React, { useEffect } from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, Bot, Code, CheckCircle2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useInView } from 'react-intersection-observer';
import WaitlistForm from '../components/waitlist/WaitlistForm';

const HostedPage: React.FC = () => {
  useEffect(() => {
    document.title = 'Hosted Solution - Baid.dev';
  }, []);

  const [topRef, topInView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
  });

  const [featuresRef, featuresInView] = useInView({
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
                <span className="badge badge-primary mb-4">Hosted Solution</span>
                <h1 className="mb-6">
                  <span className="gradient-text font-bold">Write Better Code</span>
                  <br />
                  Without the Setup Hassle
                </h1>
                <p className="text-lg md:text-xl text-surface-300 mb-8 max-w-lg">
                  Our fully managed cloud solution gives you all the power of Baid.dev
                  with zero infrastructure maintenance, automatic updates, and immediate
                  availability.
                </p>
              </div>

              <div className="flex flex-col sm:flex-row gap-4">
                <Link to="/pricing" className="btn btn-primary">
                  View Pricing
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Link>
              </div>
            </motion.div>

            {/* Waitlist Form */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={topInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              <WaitlistForm />
            </motion.div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 bg-surface-950 relative">
        <div className="container-custom">
          <motion.div
            ref={featuresRef}
            initial={{ opacity: 0, y: 20 }}
            animate={featuresInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
            transition={{ duration: 0.5 }}
            className="text-center mb-16"
          >
            <h2 className="mb-4">
              <span className="gradient-text">Hosted Solution Benefits</span>
            </h2>
            <p className="text-lg text-surface-300 max-w-2xl mx-auto">
              Get all the power of Baid.dev without worrying about infrastructure,
              updates, or maintenance.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Feature 1 */}
            <div className="bg-surface-900/50 p-6 rounded-xl border border-surface-800">
              <Bot className="h-8 w-8 text-primary-500 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Zero Setup Time</h3>
              <p className="text-surface-300 mb-4">
                Start using Baid.dev immediately after sign-up with no complex
                configuration or installation required.
              </p>
              <ul className="space-y-2">
                {['Instant access', 'No infrastructure management', 'Pre-configured for optimal performance'].map((item, i) => (
                  <li key={i} className="flex items-center">
                    <CheckCircle2 className="h-5 w-5 text-primary-500 mr-2" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Feature 2 */}
            <div className="bg-surface-900/50 p-6 rounded-xl border border-surface-800">
              <Code className="h-8 w-8 text-primary-500 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Seamless Integrations</h3>
              <p className="text-surface-300 mb-4">
                Connect with your existing tools and workflows through our
                comprehensive API and pre-built integrations.
              </p>
              <ul className="space-y-2">
                {['GitHub/GitLab integration', 'IDE plugins for all major editors', 'CI/CD pipeline support'].map((item, i) => (
                  <li key={i} className="flex items-center">
                    <CheckCircle2 className="h-5 w-5 text-primary-500 mr-2" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Feature 3 */}
            <div className="bg-surface-900/50 p-6 rounded-xl border border-surface-800">
              <svg className="h-8 w-8 text-primary-500 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <h3 className="text-xl font-semibold mb-2">Always Up-to-Date</h3>
              <p className="text-surface-300 mb-4">
                Benefit from continuous updates, new features, and improvements
                without any manual intervention.
              </p>
              <ul className="space-y-2">
                {['Automatic updates', 'Latest AI models', 'New language support as released'].map((item, i) => (
                  <li key={i} className="flex items-center">
                    <CheckCircle2 className="h-5 w-5 text-primary-500 mr-2" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Feature 4 */}
            <div className="bg-surface-900/50 p-6 rounded-xl border border-surface-800">
              <svg className="h-8 w-8 text-primary-500 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <h3 className="text-xl font-semibold mb-2">Scalable Resources</h3>
              <p className="text-surface-300 mb-4">
                Automatically scale computing resources based on your team's needs
                without manual intervention.
              </p>
              <ul className="space-y-2">
                {['Pay only for what you use', 'Handle large codebases easily', 'Support for teams of any size'].map((item, i) => (
                  <li key={i} className="flex items-center">
                    <CheckCircle2 className="h-5 w-5 text-primary-500 mr-2" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-surface-950 via-primary-950/20 to-surface-950 opacity-50"></div>
        
        <div className="container-custom relative z-10">
          <div className="bg-surface-900/80 backdrop-blur-sm rounded-2xl p-8 md:p-12 border border-surface-800 max-w-5xl mx-auto text-center">
            <div className="mb-8">
              <h2 className="text-3xl md:text-4xl font-bold mb-4">
                Ready to Get Started?
              </h2>
              <p className="text-lg text-surface-300 max-w-2xl mx-auto">
                Join the waitlist today for early access to our hosted solution.
              </p>
            </div>
            
            <div className="flex flex-col sm:flex-row justify-center gap-4">
              <Link 
                to="/pricing" 
                className="btn btn-primary"
              >
                View Pricing Options
                <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
              <Link 
                to="/on-premise" 
                className="btn btn-outline"
              >
                Need On-Premise?
              </Link>
            </div>
          </div>
        </div>
      </section>
    </>
  );
};

export default HostedPage;