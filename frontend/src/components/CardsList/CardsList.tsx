import React, { useEffect } from 'react';
import { observer } from 'mobx-react-lite';
import './CardsList.css';
import Card from '../Card/Card';
import { chatStore } from '../../store/chatStore';

interface CardsListProps {
  className?: string;
}

const CardsList: React.FC<CardsListProps> = observer((props) => {
  const { chats, selectedChatId, loadChats, setSelectedChat, loadingChats } = chatStore;

  useEffect(() => {
    loadChats();
  }, [loadChats]);

  const finalClassName = 'cards-list w-full flex flex-col h-full ' + (props.className || '');
  return (
    <div className={finalClassName}>
      <p className='w-full font-semibold p-3 pt-4'>Your Chats</p>
      {loadingChats ? (
        <p className="p-3 text-sm opacity-60">Loading...</p>
      ) : (
        chats.map((chat) => (
          <Card
            key={chat.id}
            id={chat.id}
            title={chat.title}
            description={chat.description ?? chat.lastMessagePreview}
            sources={chat.sources}
            active={selectedChatId === chat.id}
            onClick={setSelectedChat}
          />
        ))
      )}
    </div>
  );
});

export default CardsList;
