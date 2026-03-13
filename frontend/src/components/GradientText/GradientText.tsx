import React from 'react';
import './GradientText.css';

export interface GradientTextProps {
  children: React.ReactNode;
  className?: string;
}

const GradientText: React.FC<GradientTextProps> = ({ children, className = '' }) => (
  <span className={`gradient-text ${className}`.trim()}>{children}</span>
);

export default GradientText;
