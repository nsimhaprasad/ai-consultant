import React from 'react';
import { motion } from 'framer-motion';
import { useInView } from 'react-intersection-observer';

interface TestimonialProps {
  quote: string;
  author: string;
  role: string;
  company: string;
  delay: number;
}

const Testimonial: React.FC<TestimonialProps> = ({ quote, author, role, company, delay }) => {
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
      className="bg-surface-900 p-6 rounded-xl border border-surface-800"
    >
      <svg
        className="h-8 w-8 text-primary-500 mb-4"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M8 10.5c0-1.243.857-2.5 2-2.5V6c-1.714 0-3 1.5-3 3.5v2a2.5 2.5 0 015 0v2a2.5 2.5 0 01-5 0V10.5zm9 0c0-1.243.857-2.5 2-2.5V6c-1.714 0-3 1.5-3 3.5v2a2.5 2.5 0 015 0v2a2.5 2.5 0 01-5 0V10.5z"
        />
      </svg>
      <p className="text-surface-200 mb-6 italic">{quote}</p>
      <div>
        <p className="font-medium text-white">{author}</p>
        <p className="text-surface-400 text-sm">
          {role}, {company}
        </p>
      </div>
    </motion.div>
  );
};

const Testimonials: React.FC = () => {
  const [ref, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
  });

  const testimonials = [
    {
      quote:
        "Baid has the potential to replace all my other AI tools. It's getting so much better everyday. It's my goto for chats now.",
      author: "Sriram KK",
      role: "Developer",
      company: "Beskar Tech",
    },
    {
      quote:
        "The best part about baid for me is that this works with you while working on tool and works on the code even when I step out for lunch or sleep.",
      author: "Narasimha Prasad",
      role: "Lead Developer",
      company: "Beskar Tech",
    },
    {
      quote:
        "I call this Jake for all. It's like Jake watching your code changes and giving you suggestions real-time. Sometimes when I want bad code, or any code generated, I turn it off!",
      author: "Nikshep",
      role: "Developer",
      company: "Beskar Tech",
    },
  ];

  return (
    <section className="py-20 bg-surface-950 relative">
      <div className="container-custom">
        <motion.div
          ref={ref}
          initial={{ opacity: 0, y: 20 }}
          animate={inView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
          transition={{ duration: 0.5 }}
          className="text-center mb-16"
        >
          <h2 className="mb-4">
            <span className="gradient-text sub-heading">What Our Developers Are Saying</span>
          </h2>
          <p className="text-lg text-surface-300 max-w-2xl mx-auto">
            Our feature sets seem completely different from other coding agents. We focus on code quality, not just code generation and completion.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {testimonials.map((testimonial, index) => (
            <Testimonial
              key={index}
              quote={testimonial.quote}
              author={testimonial.author}
              role={testimonial.role}
              company={testimonial.company}
              delay={index * 0.1}
            />
          ))}
        </div>
      </div>
    </section>
  );
};

export default Testimonials;