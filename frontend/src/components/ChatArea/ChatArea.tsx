import React from 'react';
import { observer } from 'mobx-react-lite';
import ChatAreaHeader from '../ChatAreaHeader/ChatAreaHeader';
import ChatAreaContent from '../ChatAreaContent/ChatAreaContent';
import TicketDetail from '../TicketDetail/TicketDetail';

interface ChatAreaProps {
  className?: string;
  children?: React.ReactNode;
}

const ChatArea: React.FC<ChatAreaProps> = observer((props) => {

  const finalClassName = 'relative h-full w-full overflow-x-hidden flex flex-col ' + (props.className || '');
  return (
    <div className={finalClassName}>
      {/* <ChatAreaHeader /> */}
      <ChatAreaContent>
        <TicketDetail />
      </ChatAreaContent>
    </div>
  );
});

export default ChatArea;
