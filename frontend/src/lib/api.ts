/**
 * SupportPulse AI - API Client
 */

import {
  AnalysisResponse,
  AuthResponse,
  DashboardSummary,
  ModelVersion,
  RiskForecastResponse,
  ThemeListResponse,
  Ticket,
  TicketListResponse,
  User,
} from './types';

const API_BASE = '/api';

export function getAuthToken(): string | null {
  return localStorage.getItem('supportpulse_token');
}

export function setAuthToken(token: string | null) {
  if (token) {
    localStorage.setItem('supportpulse_token', token);
  } else {
    localStorage.removeItem('supportpulse_token');
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = getAuthToken();
  const headers = new Headers(options.headers || {});

  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let errMsg = `Request failed: ${res.status} ${res.statusText}`;
    try {
      const errJson = await res.json();
      if (errJson.detail) errMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
    } catch {
      // Ignore fallback
    }
    throw new Error(errMsg);
  }

  return res.json();
}

export const api = {
  // Auth
  async login(username: string, password: string):Promise<AuthResponse> {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData.toString(),
    });

    if (!res.ok) {
      throw new Error('Invalid username or password');
    }

    const data: AuthResponse = await res.json();
    setAuthToken(data.access_token);
    return data;
  },

  async getMe(): Promise<User> {
    return request<User>('/auth/me');
  },

  // Dashboard
  async getDashboardSummary(): Promise<DashboardSummary> {
    return request<DashboardSummary>('/dashboard/summary');
  },

  async getRiskForecast(threshold?: number): Promise<RiskForecastResponse> {
    const q = threshold !== undefined ? `?threshold=${threshold}` : '';
    return request<RiskForecastResponse>(`/risk/forecast${q}`);
  },

  // Tickets
  async listTickets(params: {
    page?: number;
    pageSize?: number;
    status?: string;
    category?: string;
    priority?: string;
    riskBand?: string;
    frictionBand?: string;
    assignedTeam?: string;
    needsTriage?: boolean;
    search?: string;
    sortBy?: string;
    sortOrder?: 'asc' | 'desc';
  }): Promise<TicketListResponse> {
    const searchParams = new URLSearchParams();
    if (params.page) searchParams.set('page', params.page.toString());
    if (params.pageSize) searchParams.set('page_size', params.pageSize.toString());
    if (params.status) searchParams.set('status', params.status);
    if (params.category) searchParams.set('category', params.category);
    if (params.priority) searchParams.set('priority', params.priority);
    if (params.riskBand) searchParams.set('risk_band', params.riskBand);
    if (params.frictionBand) searchParams.set('friction_band', params.frictionBand);
    if (params.assignedTeam) searchParams.set('assigned_team', params.assignedTeam);
    if (params.needsTriage !== undefined) searchParams.set('needs_triage', params.needsTriage.toString());
    if (params.search) searchParams.set('search', params.search);
    if (params.sortBy) searchParams.set('sort_by', params.sortBy);
    if (params.sortOrder) searchParams.set('sort_order', params.sortOrder);

    return request<TicketListResponse>(`/tickets?${searchParams.toString()}`);
  },

  async getTicket(id: string): Promise<Ticket> {
    return request<Ticket>(`/tickets/${id}`);
  },

  async createTicket(payload: {
    subject: string;
    body: string;
    department?: string;
    channel?: string;
    category?: string;
    priority?: string;
    contact_count?: number;
    reopen_count?: number;
  }): Promise<Ticket> {
    return request<Ticket>('/tickets', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async updateTicket(id: string, payload: Partial<Ticket>): Promise<Ticket> {
    return request<Ticket>(`/tickets/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  },

  async submitFeedback(id: string, payload: {
    corrected_category: string;
    corrected_priority: string;
    notes?: string;
  }): Promise<{ status: string; message: string }> {
    return request<{ status: string; message: string }>(`/tickets/${id}/feedback`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  // Playground
  async analyzeText(payload: {
    text: string;
    department?: string;
    channel?: string;
    contact_count?: number;
    reopen_count?: number;
    elapsed_minutes?: number;
  }): Promise<AnalysisResponse> {
    return request<AnalysisResponse>('/analyze', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  // Alerts
  async listAlerts(acknowledged?: boolean): Promise<any[]> {
    const q = acknowledged !== undefined ? `?acknowledged=${acknowledged}` : '';
    return request<any[]>(`/alerts${q}`);
  },

  async acknowledgeAlert(id: number): Promise<any> {
    return request<any>(`/alerts/${id}/ack`, {
      method: 'POST',
    });
  },

  // Themes
  async getThemes(): Promise<ThemeListResponse> {
    return request<ThemeListResponse>('/themes');
  },

  async refreshThemes(): Promise<ThemeListResponse> {
    return request<ThemeListResponse>('/themes/refresh', {
      method: 'POST',
    });
  },

  // Models
  async listModels(): Promise<ModelVersion[]> {
    return request<ModelVersion[]>('/models');
  },

  async triggerRetrain(): Promise<any> {
    return request<any>('/models/retrain', {
      method: 'POST',
      body: JSON.stringify({ min_feedback_samples: 0 }),
    });
  },

  async rollbackModel(version: string): Promise<any> {
    return request<any>(`/models/${version}/rollback`, {
      method: 'POST',
    });
  },

  // Health and Reports
  async getHealth(): Promise<any> {
    return request<any>('/health');
  },

  async getReportsData(): Promise<any> {
    return request<any>('/reports');
  },
};
