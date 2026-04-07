import React from 'react';

interface ChatAreaContentProps {
  children: React.ReactNode;
}

const ChatAreaContent: React.FC<ChatAreaContentProps> = ({ children }) => (
  <div className="h-full w-full relative overflow-hidden z-0">
    {children}
  </div>
);

export default ChatAreaContent;
