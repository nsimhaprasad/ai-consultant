import React, { useEffect } from 'react';
import { motion } from 'framer-motion';
import { useInView } from 'react-intersection-observer';
import PricingCard from '../components/pricing/PricingCard';

const PricingPage: React.FC = () => {
  useEffect(() => {
    document.title = 'Pricing - <b>baid';
  }, []);

  const [headerRef, headerInView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
  });

  const [pricingRef, pricingInView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
  });

  const [faqRef, faqInView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
  });

  // Pricing data
  const pricingTiers = [
    {
      name: "Starter",
      description: "Perfect for individual developers and small projects",
      price: "$49",
      priceDetails: "/month",
      features: [
        { text: "AI code assistance", included: true },
        { text: "Basic debugging help", included: true },
        { text: "Standard refactoring suggestions", included: true },
        { text: "Single IDE integration", included: true },
        { text: "5 GB code analysis/month", included: true },
        { text: "Email support", included: true },
        { text: "Advanced security analysis", included: false },
        { text: "Team collaboration features", included: false },
        { text: "Custom model training", included: false },
      ],
      highlighted: false,
      buttonText: "Join Waitlist",
      buttonLink: "/hosted",
    },
    {
      name: "Pro",
      description: "Ideal for professional developers and growing teams",
      price: "$129",
      priceDetails: "/month",
      features: [
        { text: "AI code assistance", included: true },
        { text: "Advanced debugging", included: true },
        { text: "Advanced refactoring suggestions", included: true },
        { text: "Multiple IDE integrations", included: true },
        { text: "25 GB code analysis/month", included: true },
        { text: "Priority email & chat support", included: true },
        { text: "Basic security analysis", included: true },
        { text: "Team collaboration features", included: true },
        { text: "Custom model training", included: false },
      ],
      highlighted: true,
      buttonText: "Join Waitlist",
      buttonLink: "/hosted",
    },
    {
      name: "Enterprise",
      description: "Comprehensive solution for larger teams and organizations",
      price: "Custom",
      priceDetails: "",
      features: [
        { text: "AI code assistance", included: true },
        { text: "Advanced debugging", included: true },
        { text: "Advanced refactoring suggestions", included: true },
        { text: "All IDE integrations", included: true },
        { text: "Unlimited code analysis", included: true },
        { text: "24/7 premium support with SLA", included: true },
        { text: "Advanced security analysis", included: true },
        { text: "Advanced team collaboration", included: true },
        { text: "Custom model training", included: true },
      ],
      highlighted: false,
      buttonText: "Contact Sales",
      buttonLink: "/on-premise",
    },
  ];

  // FAQ data
  const faqItems = [
    {
      question: "What's included in the Starter plan?",
      answer: "The Starter plan includes AI code assistance for generating code suggestions, basic debugging help, standard refactoring suggestions, integration with one IDE of your choice, 5 GB of code analysis per month, and email support. It's perfect for individual developers and small projects."
    },
    {
      question: "How does the billing work?",
      answer: "Billing is done on a monthly subscription basis. You'll be charged the same amount each month until you cancel or change your plan. We also offer annual billing with a discount compared to monthly billing."
    },
    {
      question: "Can I switch between plans?",
      answer: "Yes, you can upgrade or downgrade your plan at any time. When upgrading, you'll get immediate access to the new features and will be charged the prorated difference for the remainder of your billing cycle. When downgrading, the changes will take effect at the start of your next billing cycle."
    },
    {
      question: "Is there a free trial?",
      answer: "Yes, we offer a 14-day free trial on the Starter and Pro plans so you can test the features before committing. No credit card is required for the trial."
    },
    {
      question: "What's the difference between hosted and on-premise solutions?",
      answer: "Our hosted solution is a fully managed service where we handle all the infrastructure, updates, and maintenance. The on-premise solution is deployed within your own infrastructure, giving you complete control over the environment and ensuring your data never leaves your network."
    },
    {
      question: "How does the Enterprise plan differ from the Pro plan?",
      answer: "The Enterprise plan includes unlimited code analysis, 24/7 premium support with SLA, advanced security analysis, enhanced team collaboration features, and custom model training. It also offers additional customization options and integration capabilities that aren't available in the Pro plan."
    },
  ];

  return (
    <>
      {/* Header Section */}
      <section className="pt-28 pb-16 md:pt-32 md:pb-20 relative overflow-hidden">
        {/* Background elements */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-primary-900/20 rounded-full blur-[120px] -z-10"></div>
        </div>

        <div className="container-custom text-center">
          <motion.div
            ref={headerRef}
            initial={{ opacity: 0, y: 20 }}
            animate={headerInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
            transition={{ duration: 0.6 }}
            className="max-w-2xl mx-auto"
          >
            <span className="badge badge-primary mb-4">Pricing</span>
            <h1 className="mb-6 title">
              <span className="gradient-text">Simple, Transparent Pricing</span>
            </h1>
            <p className="text-lg md:text-xl text-surface-300 mb-8">
              Choose the plan that best fits your needs. All plans include core <b>baid</b> features
              with different resource limits and capabilities.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="pb-20 relative">
        <div className="container-custom">
          <motion.div
            ref={pricingRef}
            initial={{ opacity: 0, y: 20 }}
            animate={pricingInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
            transition={{ duration: 0.6 }}
            className="grid grid-cols-1 md:grid-cols-3 gap-8"
          >
            {pricingTiers.map((tier, index) => (
              <PricingCard
                key={index}
                name={tier.name}
                description={tier.description}
                price={tier.price}
                priceDetails={tier.priceDetails}
                features={tier.features}
                highlighted={tier.highlighted}
                buttonText={tier.buttonText}
                buttonLink={tier.buttonLink}
              />
            ))}
          </motion.div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-20 bg-surface-950 relative">
        <div className="container-custom">
          <motion.div
            ref={faqRef}
            initial={{ opacity: 0, y: 20 }}
            animate={faqInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
            transition={{ duration: 0.5 }}
            className="text-center mb-12"
          >
            <h2 className="mb-4">
              <span className="gradient-text sub-heading">Frequently Asked Questions</span>
            </h2>
            <p className="text-lg text-surface-300 max-w-2xl mx-auto">
              Find answers to common questions about our pricing and features.
            </p>
          </motion.div>

          <div className="max-w-3xl mx-auto">
            <div className="space-y-6">
              {faqItems.map((item, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={faqInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  className="bg-surface-900 rounded-lg p-6 border border-surface-800"
                >
                  <h3 className="text-xl font-semibold mb-3">{item.question}</h3>
                  <p className="text-surface-300">{item.answer}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </section>
    </>
  );
};

export default PricingPage;