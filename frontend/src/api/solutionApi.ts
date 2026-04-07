import type { SolutionCreate, SolutionResponse, SolutionUpdate } from '../types/ticket';
import { apiDelete, apiGet, apiPatch, apiPost } from './client';

export async function createSolution(payload: SolutionCreate): Promise<SolutionResponse> {
  return apiPost<SolutionResponse>('/solutions', payload);
}

export async function listSolutionsByTicket(ticketId: string): Promise<SolutionResponse[]> {
  return apiGet<SolutionResponse[]>(`/solutions/by-ticket/${ticketId}`);
}

export async function getSolution(solutionId: string): Promise<SolutionResponse> {
  return apiGet<SolutionResponse>(`/solutions/${solutionId}`);
}

export async function updateSolution(solutionId: string, payload: SolutionUpdate): Promise<SolutionResponse> {
  return apiPatch<SolutionResponse>(`/solutions/${solutionId}`, payload);
}

export async function deleteSolution(solutionId: string): Promise<void> {
  return apiDelete(`/solutions/${solutionId}`);
}
