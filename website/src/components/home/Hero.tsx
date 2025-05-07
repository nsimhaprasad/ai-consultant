import React from 'react';
import { motion } from 'framer-motion';
import { ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import ScreenshotCarousel from './ScreenshotCarousel';

const Hero: React.FC = () => {
  return (
    <section className="relative pt-24 pb-16 md:pt-32 md:pb-24 overflow-hidden">
      {/* Background elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-primary-900/20 rounded-full blur-[120px] -z-10"></div>
      </div>

      <div className="container-custom relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          {/* Left Column - Text Content */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="flex flex-col items-start"
          >
            <div className="mb-6">
              <span className="badge badge-primary mb-8">Intelligent Coding Assistant</span>
              <h1 className="mb-8 title">
                <span className="gradient-text">An agent ecosystem</span>
                <br />
                that works for you
              </h1>
              <p className="text-lg md:text-xl text-surface-300 mb-8 max-w-lg md:leading-loose">
                A powerful clean code agent that implements your ideas, reviews, refactors and monitors your changes.
                It runs in your <b>environment</b> or <b>in the cloud</b>, making it easy to integrate into your workflow.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-4">
              <Link to="/hosted" className="btn btn-primary">
                Try now
                <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
              <Link to="/on-premise" className="btn btn-outline">
                Explore On-Premise
              </Link>
            </div>
          </motion.div>

          {/* Right Column - Screenshot Carousel */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="lg:ml-auto"
          >
            <ScreenshotCarousel />
          </motion.div>
        </div>
      </div>
    </section>
  );
};

export default Hero;