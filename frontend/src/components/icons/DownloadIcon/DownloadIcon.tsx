import React from 'react';
import type { IconProps } from '../IconProps';

interface DownloadIconProps extends IconProps { }

const DownloadIcon: React.FC<DownloadIconProps> = ({
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
      className={`download-icon ${className}`}
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 8 9"
      {...props}
    >
      <path d="M3.52911 0C3.20896 0 2.93639 0.269275 2.93639 0.593783V5.92403L2.98411 7.67086C2.99771 8.00231 3.25661 8.19561 3.52911 8.19561C3.80168 8.19561 4.06735 8.00231 4.07419 7.67086L4.12867 5.92403V0.593783C4.12867 0.269275 3.85617 0 3.52911 0ZM3.52911 8.91366C3.68587 8.91366 3.81529 8.86537 3.96514 8.71343L6.88112 5.84117C6.99017 5.7238 7.05826 5.59951 7.05826 5.44071C7.05826 5.13005 6.8198 4.90217 6.51325 4.90217C6.36333 4.90217 6.20663 4.96432 6.09766 5.08861L4.65331 6.62829L3.52911 7.8228L2.40498 6.62829L0.953824 5.08861C0.851625 4.96432 0.688116 4.90217 0.538225 4.90217C0.224832 4.90217 0 5.13005 0 5.44071C0 5.59951 0.0613167 5.7238 0.177141 5.84117L3.09992 8.71343C3.243 8.86537 3.37926 8.91366 3.52911 8.91366Z" fill={fill} />
    </svg>
  );
};

export default DownloadIcon;
