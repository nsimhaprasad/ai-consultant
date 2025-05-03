import React, { useEffect } from 'react';
import Hero from '../components/home/Hero';
import Features from '../components/home/Features';
import Testimonials from '../components/home/Testimonials';
import CTASection from '../components/home/CTASection';

const HomePage: React.FC = () => {
  useEffect(() => {
    document.title = 'Baid.dev - Clean Coding Agent';
  }, []);

  return (
    <>
      <Hero />
      <Features />
      <Testimonials />
      <CTASection />
    </>
  );
};

export default HomePage;