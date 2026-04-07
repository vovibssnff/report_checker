import React from 'react';
import './DotsLoader.css';

export interface DotsLoaderProps {
  size?: number;
  gap?: number;
  className?: string;
}

const DotsLoader: React.FC<DotsLoaderProps> = ({ size = 4, gap, className = '' }) => {
  const gapPx = gap ?? Math.max(2, Math.round(size / 2));
  const style = {
    '--dots-size': `${size}px`,
    '--dots-gap': `${gapPx}px`,
  } as React.CSSProperties;

  return (
    <span
      className={`dots-loader ${className}`.trim()}
      style={style}
      aria-hidden
    >
      <span className="dots-loader__dot" />
      <span className="dots-loader__dot" />
      <span className="dots-loader__dot" />
    </span>
  );
};

export default DotsLoader;
