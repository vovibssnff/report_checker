import React from 'react';
import { observer } from 'mobx-react-lite';
import { ticketStore } from '../../store/ticketStore';
import TicketQuestion from '../TicketQuestion/TicketQuestion';
import TicketForm from '../TicketForm/TicketForm';
import DotsLoader from '../DotsLoader/DotsLoader';

const TicketDetail: React.FC = observer(() => {
  const { ticketDetail, selectedTicketId, loadingTicket } = ticketStore;

  if (!selectedTicketId) {
    return <TicketForm />;
  }

  if (loadingTicket || !ticketDetail) {
    return (
      <div className="max-w-3xl mx-auto flex items-center justify-center min-h-48">
        <div className='flex items-center gap-2'>
          <DotsLoader size={5} className="loading-text__loader" />
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto p-6">
      <TicketQuestion ticket={ticketDetail.ticket} />
    </div>
  );
});

export default TicketDetail;
