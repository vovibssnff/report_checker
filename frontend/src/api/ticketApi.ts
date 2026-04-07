import type { TicketCreate, TicketResponse, TicketUpdate } from '../types/ticket';
import { apiDelete, apiGet, apiPatch, apiPost } from './client';

export async function listTickets(): Promise<TicketResponse[]> {
  return apiGet<TicketResponse[]>('/tickets');
}

export async function createTicket(payload: TicketCreate): Promise<TicketResponse> {
  return apiPost<TicketResponse>('/tickets', payload);
}

export async function getTicket(ticketId: string): Promise<TicketResponse> {
  return apiGet<TicketResponse>(`/tickets/${ticketId}`);
}

export async function updateTicket(ticketId: string, payload: TicketUpdate): Promise<TicketResponse> {
  return apiPatch<TicketResponse>(`/tickets/${ticketId}`, payload);
}

export async function deleteTicket(ticketId: string): Promise<void> {
  return apiDelete(`/tickets/${ticketId}`);
}
