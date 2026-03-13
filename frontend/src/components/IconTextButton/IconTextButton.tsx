import React from 'react';
import './IconTextButton.css';

export interface IconTextButtonProps extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, 'children'> {
  icon: React.ReactNode;
  children?: React.ReactNode;
}

const IconTextButton: React.FC<IconTextButtonProps> = ({ icon, children, className = '', ...props }) => (
  <button
    type="button"
    className={`icon-text-btn ${className}`.trim()}
    {...props}
  >
    {children != null && children !== '' && (
      <span className="icon-text-btn__text">{children}</span>
    )}
    <span className="icon-text-btn__icon">{icon}</span>
  </button>
);

export default IconTextButton;
