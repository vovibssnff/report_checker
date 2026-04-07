import { makeAutoObservable, runInAction } from 'mobx';
import type { SolutionResponse, TicketCreate, TicketResponse, TicketSummary } from '../types/ticket';
import * as ticketApi from '../api/ticketApi';
import * as solutionApi from '../api/solutionApi';

const MOCK_SOLUTION_TEXT =
  'Based on the property management documentation and scripts, the recommended steps are as follows. ' +
  'First, open the relevant module (e.g. Residents / Move-In or Accounting) and locate the record. ' +
  'For lease-related changes, ensure the unit and household are correctly linked in the system. ' +
  'If the issue concerns HAP or vouchers, verify the subsidy details in the Affordable section before applying updates. ' +
  'For TRACS file transmission, confirm that the property and period are selected and run the validation report. ' +
  'If the problem persists, check the activity history and contact support with the record ID.';

const MOCK_SOLUTION_SOURCES: ('script' | 'docs' | 'expert' | 'new_doc')[] = ['docs', 'script', 'expert', 'new_doc'];
const MOCK_SOLUTION_SOURCE_RECORD = MOCK_SOLUTION_SOURCES.join(',');

export interface TicketDetailState {
  ticket: TicketResponse;
  solutions: SolutionResponse[];
}

export class TicketStore {
  tickets: TicketSummary[] = [];
  selectedTicketId: string | null = null;
  ticketDetail: TicketDetailState | null = null;
  loadingTickets = false;
  loadingTicket = false;
  creatingTicket = false;
  error: string | null = null;

  constructor() {
    makeAutoObservable(this);
  }

  get selectedTicket(): TicketSummary | null {
    if (!this.selectedTicketId) return null;
    return this.tickets.find((t) => t.id === this.selectedTicketId) ?? null;
  }

  get currentSolution(): SolutionResponse | null {
    if (!this.ticketDetail?.solutions?.length) return null;
    return this.ticketDetail.solutions[this.ticketDetail.solutions.length - 1];
  }

  setSelectedTicket = (id: string | null) => {
    this.selectedTicketId = id;
    this.ticketDetail = null;
    if (id) this.loadTicketById(id);
  };

  loadTickets = async () => {
    this.loadingTickets = true;
    this.error = null;
    try {
      const list = await ticketApi.listTickets();
      runInAction(() => {
        this.tickets = list;
        this.loadingTickets = false;
      });
    } catch (e) {
      runInAction(() => {
        this.error = e instanceof Error ? e.message : 'Failed to load tickets';
        this.loadingTickets = false;
      });
    }
  };

  loadTicketById = async (id: string) => {
    this.loadingTicket = true;
    this.error = null;
    try {
      const [ticket, solutions] = await Promise.all([
        ticketApi.getTicket(id),
        solutionApi.listSolutionsByTicket(id),
      ]);
      runInAction(() => {
        this.ticketDetail = { ticket, solutions };
        const idx = this.tickets.findIndex((t) => t.id === id);
        if (idx >= 0) {
          const next = [...this.tickets];
          const latest = solutions.length ? solutions[solutions.length - 1] : null;
          next[idx] = {
            ...next[idx],
            solution_status: latest?.status,
            solution_preview: latest?.text?.slice(0, 80) ?? null,
            solution_sources: latest ? parseSolutionSources(latest) : undefined,
          };
          this.tickets = next;
        }
        this.loadingTicket = false;
      });
    } catch (e) {
      runInAction(() => {
        this.error = e instanceof Error ? e.message : 'Failed to load ticket';
        this.loadingTicket = false;
      });
    }
  };

  createTicket = async (payload: TicketCreate) => {
    this.creatingTicket = true;
    this.error = null;
    try {
      const ticket = await ticketApi.createTicket(payload);
      await solutionApi.createSolution({ ticket_id: ticket.id });
      await this.loadTickets();
      runInAction(() => {
        this.selectedTicketId = ticket.id;
        this.ticketDetail = null;
        this.creatingTicket = false;
      });
      await this.loadTicketById(ticket.id);
      if (import.meta.env.VITE_MOCK_SOLUTIONS === 'true') {
        this.scheduleMockSolution(ticket.id, payload.question);
      }
    } catch (e) {
      runInAction(() => {
        this.error = e instanceof Error ? e.message : 'Failed to create ticket';
        this.creatingTicket = false;
      });
      throw e;
    }
  };

  scheduleMockSolution = (ticketId: string, _question: string) => {
    const MOCK_DELAY_MS = 3000;
    const timer = setTimeout(() => {
      runInAction(() => {
        if (!this.ticketDetail || this.ticketDetail.ticket.id !== ticketId) return;
        const solutions = this.ticketDetail.solutions;
        if (!solutions.length) return;
        const pending = solutions[solutions.length - 1];
        const mock: SolutionResponse = {
          ...pending,
          status: 'done',
          text: MOCK_SOLUTION_TEXT,
          generation_source_record: MOCK_SOLUTION_SOURCE_RECORD,
        };
        const nextSolutions = [...solutions.slice(0, -1), mock];
        this.ticketDetail = { ...this.ticketDetail, solutions: nextSolutions };
        const idx = this.tickets.findIndex((t) => t.id === ticketId);
        if (idx >= 0) {
          const next = [...this.tickets];
          next[idx] = {
            ...next[idx],
            solution_status: 'done' as const,
            solution_preview: mock.text?.slice(0, 80) ?? null,
            solution_sources: MOCK_SOLUTION_SOURCES,
          };
          this.tickets = next;
        }
      });
    }, MOCK_DELAY_MS);
    return () => clearTimeout(timer);
  };

  updateTicket = async (ticketId: string, payload: Parameters<typeof ticketApi.updateTicket>[1]) => {
    this.error = null;
    try {
      const updated = await ticketApi.updateTicket(ticketId, payload);
      runInAction(() => {
        const idx = this.tickets.findIndex((t) => t.id === ticketId);
        if (idx >= 0) {
          const next = [...this.tickets];
          next[idx] = { ...next[idx], ...updated };
          this.tickets = next;
        }
        if (this.ticketDetail?.ticket.id === ticketId) {
          this.ticketDetail = { ...this.ticketDetail, ticket: updated };
        }
      });
    } catch (e) {
      runInAction(() => {
        this.error = e instanceof Error ? e.message : 'Failed to update ticket';
      });
      throw e;
    }
  };

  deleteTicket = async (ticketId: string) => {
    this.error = null;
    try {
      await ticketApi.deleteTicket(ticketId);
      runInAction(() => {
        this.tickets = this.tickets.filter((t) => t.id !== ticketId);
        if (this.selectedTicketId === ticketId) {
          this.selectedTicketId = null;
          this.ticketDetail = null;
        }
      });
    } catch (e) {
      runInAction(() => {
        this.error = e instanceof Error ? e.message : 'Failed to delete ticket';
      });
      throw e;
    }
  };

  refreshSolution = async (ticketId: string) => {
    const solutions = await solutionApi.listSolutionsByTicket(ticketId);
    runInAction(() => {
      if (this.ticketDetail?.ticket.id === ticketId) {
        this.ticketDetail = { ...this.ticketDetail, solutions };
      }
      const idx = this.tickets.findIndex((t) => t.id === ticketId);
      if (idx >= 0) {
        const next = [...this.tickets];
        const latest = solutions.length ? solutions[solutions.length - 1] : null;
        next[idx] = {
          ...next[idx],
          solution_status: latest?.status,
          solution_preview: latest?.text?.slice(0, 80) ?? null,
          solution_sources: latest ? parseSolutionSources(latest) : undefined,
        };
        this.tickets = next;
      }
    });
  };
}

function parseSolutionSources(s: SolutionResponse): ('script' | 'docs' | 'expert' | 'new_doc')[] {
  const record = s.generation_source_record?.toLowerCase() ?? '';
  const out: ('script' | 'docs' | 'expert' | 'new_doc')[] = [];
  if (record.includes('docs')) out.push('docs');
  if (record.includes('script')) out.push('script');
  if (record.includes('expert')) out.push('expert');
  if (record.includes('new_doc')) out.push('new_doc');
  return out.length ? out : ['docs'];
}

export const ticketStore = new TicketStore();
