import React from 'react';
import ChatAreaContent from '../ChatAreaContent/ChatAreaContent';
import TicketForm from '../TicketForm/TicketForm';

interface ChatAreaProps {
  className?: string;
  children?: React.ReactNode;
}

const ChatArea: React.FC<ChatAreaProps> = (props) => {

  const finalClassName = 'relative h-full w-full overflow-x-hidden flex flex-col ' + (props.className || '');
  return (
    <div className={finalClassName}>
      {/* <ChatAreaHeader /> */}
      <ChatAreaContent>
        <TicketForm />
      </ChatAreaContent>
    </div>
  );
};

export default ChatArea;
