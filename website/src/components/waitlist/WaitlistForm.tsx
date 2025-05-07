import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Check, AlertCircle } from 'lucide-react';
import ReCAPTCHA from 'react-google-recaptcha';

interface WaitlistFormProps {
  title?: string;
  subtitle?: string;
}

const WaitlistForm: React.FC<WaitlistFormProps> = ({ 
  title = "Join the Waitlist",
  subtitle = "Be the first to get access to our agent."
}) => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    role: ''
  });
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');
  const [captchaValue, setCaptchaValue] = useState<string | null>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    if (status === 'error') setStatus('idle');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate form fields
    if (!formData.name) {
      setStatus('error');
      setErrorMessage('Please enter your name');
      return;
    }

    if (!formData.email) {
      setStatus('error');
      setErrorMessage('Please enter your email address');
      return;
    }

    if (!formData.role) {
      setStatus('error');
      setErrorMessage('Please select your role');
      return;
    }

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      setStatus('error');
      setErrorMessage('Please enter a valid email address');
      return;
    }

    // Validate reCAPTCHA
    if (!captchaValue) {
      setStatus('error');
      setErrorMessage('Please complete the reCAPTCHA verification');
      return;
    }

    setStatus('loading');

    try {
      // Make POST request to core.baid.dev/waitlist with form data
      const response = await fetch('https://core.baid.dev/waitlist', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: formData.name,
          email: formData.email,
          role: formData.role,
          captcha: captchaValue
        }),
      });

      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }
      
      // Successful submission
      setStatus('success');
      setFormData({
        name: '',
        email: '',
        role: ''
      });
      setCaptchaValue(null);
      
      // Reset success state after 3 seconds
      setTimeout(() => {
        setStatus('idle');
      }, 3000);
    } catch (error) {
      console.error('Error submitting form:', error);
      setStatus('error');
      setErrorMessage('Something went wrong. Please try again.');
    }
  };

  const handleCaptchaChange = (value: string | null) => {
    setCaptchaValue(value);
    if (status === 'error') setStatus('idle');
  };

  return (
    <div className="bg-surface-900 rounded-xl p-6 md:p-8 border border-surface-800">
      <div className="mb-6 text-center">
        <h3 className="text-2xl font-semibold mb-2">{title}</h3>
        <p className="text-surface-300">{subtitle}</p>
      </div>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Name Field */}
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-surface-300 mb-1">
            Full Name
          </label>
          <input
            type="text"
            id="name"
            name="name"
            value={formData.name}
            onChange={handleInputChange}
            placeholder="John Doe"
            className="input"
            disabled={status === 'loading' || status === 'success'}
          />
        </div>

        {/* Email Field */}
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-surface-300 mb-1">
            Email Address
          </label>
          <input
            type="email"
            id="email"
            name="email"
            value={formData.email}
            onChange={handleInputChange}
            placeholder="you@example.com"
            className="input"
            disabled={status === 'loading' || status === 'success'}
          />
        </div>

        {/* Role Field */}
        <div>
          <label htmlFor="role" className="block text-sm font-medium text-surface-300 mb-1">
            Your Role
          </label>
          <select
            id="role"
            name="role"
            value={formData.role}
            onChange={handleInputChange}
            className="input"
            disabled={status === 'loading' || status === 'success'}
          >
            <option value="" disabled>Select your role</option>
            <option value="developer">Developer</option>
            <option value="designer">Designer</option>
            <option value="product_manager">Product Manager</option>
            <option value="engineering_manager">Engineering Manager</option>
            <option value="executive">Executive</option>
            <option value="student">Student</option>
            <option value="other">Other</option>
          </select>
        </div>
        
        {/* reCAPTCHA */}
        {/* Local: 6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI */}
        {/* Production: 6LeKlzErAAAAALxy5KTqLGq7xqBTf5YM996xm1Y0 */}
        <div className="flex justify-center my-4">
          <ReCAPTCHA
            sitekey="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
            onChange={handleCaptchaChange}
            theme="dark"
          />
        </div>
          
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
          We'll never share your information with anyone else.
        </p>
      </form>
    </div>
  );
};

export default WaitlistForm;