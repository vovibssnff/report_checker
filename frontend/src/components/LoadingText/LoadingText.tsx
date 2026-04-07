import React from 'react';
import GradientText from '../GradientText/GradientText';
import './LoadingText.css';

export interface LoadingTextProps {
  children: React.ReactNode;
  showLoader?: boolean;
  loaderSize?: number;
  className?: string;
}

const LoadingText: React.FC<LoadingTextProps> = ({
  children,
  className = '',
}) => (
  <span className={`loading-text ${className}`.trim()}>
    <GradientText>{children}</GradientText>
  </span>
);

export default LoadingText;
