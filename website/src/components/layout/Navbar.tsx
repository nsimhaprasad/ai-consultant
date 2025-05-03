import React, { useState, useEffect } from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import { Menu, X, Bot } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const Navbar: React.FC = () => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Close mobile menu when changing routes
  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [location.pathname]);

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled || isMobileMenuOpen ? 'bg-surface-900/95 backdrop-blur-lg shadow-md' : 'bg-transparent'
      }`}
    >
      <div className="container-custom py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2 text-white">
            <Bot className="h-8 w-8 text-primary-500" />
            <span className="text-xl font-bold">baid.dev</span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-8">
            <NavLink to="/" className={({ isActive }) => 
              isActive ? 'active-nav-link' : 'nav-link'
            }>
              Home
            </NavLink>
            <NavLink to="/hosted" className={({ isActive }) => 
              isActive ? 'active-nav-link' : 'nav-link'
            }>
              Hosted
            </NavLink>
            <NavLink to="/on-premise" className={({ isActive }) => 
              isActive ? 'active-nav-link' : 'nav-link'
            }>
              On-Premise
            </NavLink>
            <NavLink to="/pricing" className={({ isActive }) => 
              isActive ? 'active-nav-link' : 'nav-link'
            }>
              Pricing
            </NavLink>
          </nav>

          {/* CTA Button */}
          <div className="hidden md:block">
            <Link to="/hosted" className="btn btn-primary">
              Join Waitlist
            </Link>
          </div>

          {/* Mobile Menu Button */}
          <button 
            className="md:hidden text-white"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            aria-label={isMobileMenuOpen ? "Close menu" : "Open menu"}
          >
            {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {/* Mobile Menu */}
        <AnimatePresence>
          {isMobileMenuOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
              className="md:hidden mt-4 pb-4"
            >
              <nav className="flex flex-col space-y-4">
                <NavLink to="/" className={({ isActive }) => 
                  `px-2 py-2 rounded ${isActive ? 'active-nav-link bg-surface-800' : 'nav-link'}`
                }>
                  Home
                </NavLink>
                <NavLink to="/hosted" className={({ isActive }) => 
                  `px-2 py-2 rounded ${isActive ? 'active-nav-link bg-surface-800' : 'nav-link'}`
                }>
                  Hosted
                </NavLink>
                <NavLink to="/on-premise" className={({ isActive }) => 
                  `px-2 py-2 rounded ${isActive ? 'active-nav-link bg-surface-800' : 'nav-link'}`
                }>
                  On-Premise
                </NavLink>
                <NavLink to="/pricing" className={({ isActive }) => 
                  `px-2 py-2 rounded ${isActive ? 'active-nav-link bg-surface-800' : 'nav-link'}`
                }>
                  Pricing
                </NavLink>
                <Link to="/hosted" className="btn btn-primary w-full">
                  Join Waitlist
                </Link>
              </nav>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </header>
  );
};

export default Navbar;