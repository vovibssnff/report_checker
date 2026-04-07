import React from 'react';

interface AvatarProps {
  name: string;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

const sizeClasses = {
  sm: 'w-7 h-7 text-xs',
  md: 'w-9 h-9 text-sm',
  lg: 'w-11 h-11 text-base',
};

const Avatar: React.FC<AvatarProps> = ({ name, className = '', size = 'md' }) => {
  const letter = name?.trim().charAt(0).toUpperCase() || '?';
  return (
    <div
      className={`flex items-center justify-center rounded-full bg-gradient-to-br from-neutral-800 to-neutral-600 text-white font-semibold shrink-0 ${sizeClasses[size]} ${className}`.trim()}
      title={name}
      aria-hidden
    >
      {letter}
    </div>
  );
};

export default Avatar;
