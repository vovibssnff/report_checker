import type { SolutionResponse } from '../types/ticket';
import { getWsUrl } from './client';

export type OnSolutionHandler = (ticketId: string, solution: SolutionResponse) => void;

let ws: WebSocket | null = null;
const solutionListeners = new Set<OnSolutionHandler>();

function connect(): WebSocket {
  if (ws?.readyState === WebSocket.OPEN) return ws;
  const url = getWsUrl();
  ws = new WebSocket(url);

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.ticket_id && data.solution) {
        solutionListeners.forEach((fn) => fn(data.ticket_id, data.solution));
      }
    } catch {
    }
  };

  ws.onclose = () => {
    ws = null;
  };

  return ws;
}

export function subscribeToSolution(handler: OnSolutionHandler): () => void {
  solutionListeners.add(handler);
  if (!ws || ws.readyState !== WebSocket.OPEN) connect();
  return () => solutionListeners.delete(handler);
}

export function getWsState(): number {
  return ws?.readyState ?? WebSocket.CLOSED;
}

export function subscribeToMessages(_handler: (payload: unknown) => void): () => void {
  return () => {};
}
