import React from 'react';
import type { IconProps } from '../IconProps';

interface CheckIconProps extends IconProps { }

const CheckIcon: React.FC<CheckIconProps> = ({
  size = '24px',
  fill = 'black',
  className = '',
  ...props
}) => {
  return (
    <svg
      width={size}
      height={size}
      fill={fill}
      className={`check-icon ${className}`}
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 16 20"
      {...props}
    >
      <g clip-path="url(#clip0_146_940)">
        <path fill-rule="evenodd" clip-rule="evenodd" d="M15.8435 6.3435L5.50003 16.687L0.156525 11.3435L1.50003 10L5.50003 14L14.5 5L15.8435 6.3435Z" fill={fill} />
      </g>
      <defs>
        <clipPath id="clip0_146_940">
          <rect width="16" height="20" fill="white" />
        </clipPath>
      </defs>
    </svg>
  );
};

export default CheckIcon;
