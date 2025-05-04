import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Check, AlertCircle } from 'lucide-react';

interface WaitlistFormProps {
  title?: string;
  subtitle?: string;
}

const WaitlistForm: React.FC<WaitlistFormProps> = ({ 
  title = "Join the Waitlist",
  subtitle = "Be the first to get access to our agent."
}) => {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email) {
      setStatus('error');
      setErrorMessage('Please enter your email address');
      return;
    }

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setStatus('error');
      setErrorMessage('Please enter a valid email address');
      return;
    }

    setStatus('loading');

    try {
      // In a real implementation, you would send this to your backend API
      // which would then store it in a Google Sheets document
      
      // Simulate API call with timeout
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Simulate successful submission
      setStatus('success');
      setEmail('');
      
      // Reset success state after 3 seconds
      setTimeout(() => {
        setStatus('idle');
      }, 3000);
    } catch (error) {
      console.error('Error submitting email:', error);
      setStatus('error');
      setErrorMessage('Something went wrong. Please try again.');
    }
  };

  return (
    <div className="bg-surface-900 rounded-xl p-6 md:p-8 border border-surface-800">
      <div className="mb-6 text-center">
        <h3 className="text-2xl font-semibold mb-2">{title}</h3>
        <p className="text-surface-300">{subtitle}</p>
      </div>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-surface-300 mb-1">
            Email Address
          </label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => {
              setEmail(e.target.value);
              if (status === 'error') setStatus('idle');
            }}
            placeholder="you@example.com"
            className="input"
            disabled={status === 'loading' || status === 'success'}
          />
          
          {/* Error Message */}
          {status === 'error' && (
            <motion.div 
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-2 flex items-center text-error-500 text-sm"
            >
              <AlertCircle className="h-4 w-4 mr-1" />
              {errorMessage}
            </motion.div>
          )}
        </div>
        
        <button
          type="submit"
          className={`btn w-full ${
            status === 'loading' 
              ? 'bg-primary-700 cursor-not-allowed' 
              : status === 'success'
              ? 'bg-success-600 hover:bg-success-700'
              : 'btn-primary'
          }`}
          disabled={status === 'loading' || status === 'success'}
        >
          {status === 'loading' ? (
            <>
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Processing...
            </>
          ) : status === 'success' ? (
            <>
              <Check className="mr-2 h-5 w-5" />
              Thank you for joining!
            </>
          ) : (
            'Join the Waitlist'
          )}
        </button>
        
        <p className="text-xs text-surface-400 text-center mt-4">
          We'll never share your email with anyone else.
        </p>
      </form>
    </div>
  );
};

export default WaitlistForm;