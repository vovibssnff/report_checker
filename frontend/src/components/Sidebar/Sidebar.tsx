import React from 'react';
import SidebarHeader from '../SidebarHeader/SidebarHeader';

interface SidebarProps {
  className?: string;
  children?: React.ReactNode;
}

const Sidebar: React.FC<SidebarProps> = (props) => {
  const finalClassName = 'sidebar relative p-1 col-start-1 col-span-4 h-full overflow-y-scroll ' + (props.className || '');
  return (
    <div className={finalClassName}>
      <SidebarHeader />
      {props.children}
    </div>
  );
};

export default Sidebar;
