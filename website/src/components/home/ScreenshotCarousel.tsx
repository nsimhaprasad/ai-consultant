import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

// Define the screenshot data
const screenshots = [
  {
    id: 1,
    title: 'Terminal Debugging',
    description: 'Failure debugging with LLM assistance',
    imageUrl: '/images/terminal.png',
    alt: 'Terminal showing Java debugging session with AI assistance'
  },
  {
    id: 2,
    title: 'VSCode Integration',
    description: 'Code refactoring suggestions based on clean code principles',
    imageUrl: '/images/vscode.png',
    alt: 'VSCode with code refactoring suggestions from AI'
  },
  {
    id: 3,
    title: 'IntelliJ Integration',
    description: 'Intelligent code reviews in your IDE',
    imageUrl: '/images/intellij.png',
    alt: 'IntelliJ IDEA with AI code review comments'
  }
];

const ScreenshotCarousel: React.FC = () => {
  const [currentIndex, setCurrentIndex] = useState(0);
  
  // Auto rotation
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentIndex((prevIndex) => (prevIndex + 1) % screenshots.length);
    }, 5000);
    
    return () => clearInterval(interval);
  }, []);

  // Handle manual navigation
  const goToSlide = (index: number) => {
    setCurrentIndex(index);
  };

  return (
    <div className="relative bg-surface-900/50 p-2 rounded-2xl border border-surface-800">
      <div className="relative overflow-hidden rounded-xl aspect-video md:max-w-[600px]">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentIndex}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
            className="relative w-full h-full screenshot-shadow"
          >
            <img 
              src={screenshots[currentIndex].imageUrl} 
              alt={screenshots[currentIndex].alt}
              className="w-full h-full object-cover rounded-lg"
            />
            
            {/* Caption overlay */}
            <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-surface-950/90 to-transparent p-4">
              <h3 className="text-lg font-medium text-white">
                {screenshots[currentIndex].title}
              </h3>
              <p className="text-sm text-surface-300">
                {screenshots[currentIndex].description}
              </p>
            </div>
          </motion.div>
        </AnimatePresence>
      </div>
      
      {/* Navigation dots */}
      <div className="flex justify-center mt-4 space-x-2">
        {screenshots.map((_, index) => (
          <button
            key={index}
            onClick={() => goToSlide(index)}
            className={`w-2 h-2 rounded-full transition-all duration-300 ${
              index === currentIndex 
                ? 'bg-primary-500 w-6' 
                : 'bg-surface-700 hover:bg-surface-600'
            }`}
            aria-label={`Go to slide ${index + 1}`}
          />
        ))}
      </div>
    </div>
  );
};

export default ScreenshotCarousel;