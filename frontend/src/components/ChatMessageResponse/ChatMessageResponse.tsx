import React from 'react';
import './ChatMessageResponse.css';
import type { Source } from '../Card/Card';
import SourceTag from '../SourceTag/SourceTag';

interface ChatMessageResponseProps {
  className?: string;
  body?: string;
  sources?: Source[];
}

const ChatMessageResponse: React.FC<ChatMessageResponseProps> = (props) => {
  const finalClassName = 'chat-message-response w-full h-fit flex flex-col pb-12 ' + (props.className || '');
  
  const isExpertVerified = props.sources?.includes('expert' as Source);

  return (
    <div className={finalClassName}>
      {props.body && <p className='pb-5'>{props.body}</p>}
      
      <div className='flex flex-row gap-3 opacity-60'>
        {isExpertVerified ? (
          <p className='text-xs'>
            This answer was verified by an expert.
          </p>
        ) : (
          <>
            {props.sources && props.sources.length > 0 && (
              <>
                <p className='text-xs'>This answer based on:</p>
                <div className='flex flex-row gap-5'>
                  {props.sources.map((source) => (
                    <SourceTag key={source} source={source} />
                  ))}
                </div>
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default ChatMessageResponse;