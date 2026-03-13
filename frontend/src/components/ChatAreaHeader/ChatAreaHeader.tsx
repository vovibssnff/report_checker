import React from 'react';
import { observer } from 'mobx-react-lite';
import { ticketStore } from '../../store/ticketStore';
import { formatTicketDate } from '../../utils/dateFormat';

const TITLE_MAX_LENGTH = 60;

const ChatAreaHeader: React.FC = observer(() => {
  const { ticketDetail, selectedTicketId } = ticketStore;
  const hasTicket = !!selectedTicketId && !!ticketDetail?.ticket;
  const question = ticketDetail?.ticket?.question ?? '';
  const title = question.length > TITLE_MAX_LENGTH ? question.slice(0, TITLE_MAX_LENGTH) + '…' : question;
  const subtitle = hasTicket && ticketDetail?.ticket?.created_at
    ? formatTicketDate(ticketDetail.ticket.created_at)
    : null;

  return (
    <header className="absolute top-0 left-0 right-0 py-5 px-5 pb-10 flex flex-col items-center justify-center bg-gradient-to-b from-white to-transparent z-10 min-w-0">
      {hasTicket ? (
        <>
          <p className="font-semibold text-center min-w-0 max-w-full truncate px-4" title={question}>
            {title}
          </p>
          {subtitle && <p className="text-xs opacity-60 mt-0.5 uppercase">{subtitle}</p>}
        </>
      ) : null}
    </header>
  );
});

export default ChatAreaHeader;
