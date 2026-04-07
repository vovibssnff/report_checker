import React from 'react';
import type { IconProps } from '../IconProps';

interface CrossIconProps extends IconProps { }

const CrossIcon: React.FC<CrossIconProps> = ({
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
      className={`cross-icon ${className}`}
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 14 20"
      {...props}
    >
      <path d="M7 12.2729L11.8636 17.1364L13.1364 15.8636L8.27279 11.0001L13.1364 6.13644L11.8636 4.86365L7 9.72727L2.13638 4.86365L0.863586 6.13644L5.72721 11.0001L0.863621 15.8636L2.13641 17.1364L7 12.2729Z" fill={fill} />
    </svg>
  );
};

export default CrossIcon;
