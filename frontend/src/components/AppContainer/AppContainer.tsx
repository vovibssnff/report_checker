import React from 'react';

interface AppContainerProps {
  className?: string;
  children?: React.ReactNode;
}

const AppContainer: React.FC<AppContainerProps> = (props) => (
  <div
    className={'h-full w-full h-screen overflow-hidden flex flex-col ' + (props.className || '')}
  >
    {props.children}
  </div>
);

export default AppContainer;
