import React from 'react';
import { CheckCircle2 } from 'lucide-react';
import { Link } from 'react-router-dom';

interface PricingFeature {
  text: string;
  included: boolean;
}

interface PricingCardProps {
  name: string;
  description: string;
  price: string;
  priceDetails: string;
  features: PricingFeature[];
  highlighted?: boolean;
  buttonText: string;
  buttonLink: string;
}

const PricingCard: React.FC<PricingCardProps> = ({
  name,
  description,
  price,
  priceDetails,
  features,
  highlighted = false,
  buttonText,
  buttonLink,
}) => {
  return (
    <div 
      className={`rounded-2xl p-6 md:p-8 border ${
        highlighted 
          ? 'border-primary-500 relative bg-surface-900/70' 
          : 'border-surface-800 bg-surface-900/40'
      }`}
    >
      {highlighted && (
        <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 bg-primary-600 text-white px-4 py-1 rounded-full text-sm font-medium">
          Popular Choice
        </div>
      )}
      
      <div className="mb-6">
        <h3 className="text-2xl font-semibold mb-2">{name}</h3>
        <p className="text-surface-300">{description}</p>
      </div>
      
      <div className="mb-6">
        <div className="flex items-end">
          <span className="text-4xl font-bold">{price}</span>
          {priceDetails && (
            <span className="text-surface-400 ml-2">{priceDetails}</span>
          )}
        </div>
      </div>
      
      <ul className="mb-8 space-y-3">
        {features.map((feature, index) => (
          <li key={index} className="flex items-start">
            <CheckCircle2 
              className={`h-5 w-5 mr-2 mt-0.5 ${
                feature.included 
                  ? 'text-primary-500' 
                  : 'text-surface-600'
              }`} 
            />
            <span 
              className={feature.included ? 'text-surface-200' : 'text-surface-500 line-through'}
            >
              {feature.text}
            </span>
          </li>
        ))}
      </ul>
      
      <Link 
        to={buttonLink} 
        className={`btn w-full ${
          highlighted ? 'btn-primary' : 'btn-outline'
        }`}
      >
        {buttonText}
      </Link>
    </div>
  );
};

export default PricingCard;