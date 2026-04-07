import React from 'react';
import './ChatMessageRequest.css';
import type { MessageStatus } from '../../types/chat';

interface ChatMessageRequestProps {
  className?: string;
  body: string;
  status?: MessageStatus;
}

const ChatMessageRequest: React.FC<ChatMessageRequestProps> = (props) => {
  const finalClassName = 'chat-message-request w-full h-fit flex flrex-rw justify-end pb-12 ' + (props.className || '');
  return (
    <div className={finalClassName}>
      <div className=' bg-[rgb(240,240,240)] py-2 px-4 h-fit w-fit max-w-[20rem] rounded-[1.5rem]'>
        <p className=''>{props.body}</p>
      </div>
    </div>
  );
};

export default ChatMessageRequest;
