import React from 'react';
import { Link } from 'react-router-dom';
import { Bot, ExternalLink } from 'lucide-react';

const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-surface-900 border-t border-surface-800 pt-12 pb-8">
      <div className="container-custom">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Logo and company description */}
          <div className="col-span-1 md:col-span-1">
            <Link to="/" className="flex items-center space-x-2 text-white mb-4">
              <Bot className="h-8 w-8 text-primary-500" />
              <span className="text-2xl font-black">baid</span>
            </Link>
            <p className="text-surface-400 mb-4">
              A clean coding agent that helps you realize your ideas, available in hosted and on-premise versions.
            </p>
          </div>

          {/* Solutions */}
          <div className="col-span-1">
            <h4 className="text-white font-medium mb-4">Solutions</h4>
            <ul className="space-y-2">
              <li>
                <Link to="/hosted" className="text-surface-400 hover:text-white transition">
                  Hosted Solution
                </Link>
              </li>
              <li>
                <Link to="/on-premise" className="text-surface-400 hover:text-white transition">
                  On-Premise
                </Link>
              </li>
              <li>
                <Link to="/pricing" className="text-surface-400 hover:text-white transition">
                  Pricing
                </Link>
              </li>
            </ul>
          </div>

          {/* Company */}
          <div className="col-span-1">
            <h4 className="text-white font-medium mb-4">Company</h4>
            <ul className="space-y-2">
              <li>
                <a 
                  href="https://beskar.tech" 
                  className="text-surface-400 hover:text-white transition flex items-center"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Beskar Technologies <ExternalLink className="ml-1 h-3 w-3" />
                </a>
              </li>
              <li>
                <Link to="/privacy" className="text-surface-400 hover:text-white transition">
                  Privacy & Security
                </Link>
              </li>
              <li>
                <Link to="/terms" className="text-surface-400 hover:text-white transition">
                  Terms of Use
                </Link>
              </li>
            </ul>
          </div>

          {/* Contact */}
          <div className="col-span-1">
            <h4 className="text-white font-medium mb-4">Contact</h4>
            <p className="text-surface-400 mb-2">
              Get your own B2B agent for your company
            </p>
            <a 
              href="mailto:sales@beskar.tech" 
              className="text-primary-400 hover:text-primary-300 transition underline"
            >
              sales@beskar.tech
            </a>
          </div>
        </div>

        {/* Bottom copyright section */}
        <div className="mt-12 pt-6 border-t border-surface-800">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <p className="text-surface-500 text-sm mb-4 md:mb-0">
              &copy; {currentYear} Beskar Technologies. All rights reserved.
            </p>
            <div className="flex space-x-6">
              <a 
                href="https://twitter.com" 
                className="text-surface-500 hover:text-white transition"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="Twitter"
              >
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84" />
                </svg>
              </a>
              <a 
                href="https://github.com" 
                className="text-surface-500 hover:text-white transition"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="GitHub"
              >
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
                </svg>
              </a>
              <a 
                href="https://linkedin.com" 
                className="text-surface-500 hover:text-white transition"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="LinkedIn"
              >
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path fillRule="evenodd" d="M4.98 3.5c0 1.381-1.11 2.5-2.48 2.5s-2.48-1.119-2.48-2.5c0-1.38 1.11-2.5 2.48-2.5s2.48 1.12 2.48 2.5zm.02 4.5h-5v16h5v-16zm7.982 0h-4.968v16h4.969v-8.399c0-4.67 6.029-5.052 6.029 0v8.399h4.988v-10.131c0-7.88-8.922-7.593-11.018-3.714v-2.155z" clipRule="evenodd" />
                </svg>
              </a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;