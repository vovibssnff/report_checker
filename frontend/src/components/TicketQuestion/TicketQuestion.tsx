import React from 'react';
import type { TicketResponse } from '../../types/ticket';

function formatDifficulty(d: string): string {
  if (d === 'easy') return 'Easy';
  if (d === 'medium') return 'Medium';
  if (d === 'high') return 'High';
  return d;
}

interface TicketQuestionProps {
  ticket: TicketResponse;
}

const TicketQuestion: React.FC<TicketQuestionProps> = ({ ticket }) => {
  const meta = [ticket.product, ticket.category + " Category", ticket.module + " Module", formatDifficulty(ticket.difficulty) + " Difficulty"]
    .filter(Boolean)
    .join(' · ');
  return (
    <div className="mb-6">
      <p className="text-sm">{ticket.question}</p>
      {meta && (
        <p className="text-xs opacity-50 mt-2 min-w-0 max-w-full truncate" title={meta}>
          {meta}
        </p>
      )}
    </div>
  );
};

export default TicketQuestion;
