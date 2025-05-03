import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

const NotFoundPage: React.FC = () => {
  useEffect(() => {
    document.title = 'Page Not Found - Baid.dev';
  }, []);

  return (
    <section className="pt-32 pb-20 flex flex-col items-center justify-center min-h-[70vh]">
      <div className="container-custom text-center">
        <h1 className="text-8xl font-bold text-primary-500 mb-6">404</h1>
        <h2 className="text-3xl md:text-4xl font-semibold mb-4">Page Not Found</h2>
        <p className="text-lg text-surface-300 mb-8 max-w-md mx-auto">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <Link to="/" className="btn btn-primary inline-flex items-center">
          <ArrowLeft className="mr-2 h-5 w-5" />
          Back to Home
        </Link>
      </div>
    </section>
  );
};

export default NotFoundPage;