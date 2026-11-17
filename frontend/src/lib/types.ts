/**
 * SupportPulse AI - Frontend TypeScript Definitions
 */

export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: 'admin' | 'manager' | 'agent';
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  role: string;
  username: string;
  full_name: string;
}

export interface Ticket {
  id: number;
  ticket_id: string;
  created_at: string;
  subject: string;
  body: string;
  requester_id: string;
  department: string;
  channel: string;
  category: string;
  priority: 'P1' | 'P2' | 'P3' | 'P4';
  assigned_team: string;
  agent_id?: string | null;
  first_response_at?: string | null;
  resolved_at?: string | null;
  sla_hours: number;
  breached: boolean;
  reopen_count: number;
  contact_count: number;
  escalated: boolean;
  status: 'open' | 'in_progress' | 'waiting_on_customer' | 'resolved' | 'closed';

  // ML Enrichment
  predicted_category?: string;
  category_confidence?: number;
  predicted_priority?: string;
  priority_confidence?: number;
  needs_human_triage: boolean;
  sla_breach_probability?: number;
  sla_risk_band: 'Low' | 'Medium' | 'High' | 'Critical';
  estimated_minutes_to_breach?: number;
  friction_score: number;
  friction_band: 'Calm' | 'Uneasy' | 'Frustrated' | 'Critical';
  routing_recommendation?: string;
  explanation_data?: string;
}

export interface TicketListResponse {
  total: number;
  page: number;
  page_size: number;
  items: Ticket[];
}

export interface Alert {
  id: number;
  ticket_id: string;
  alert_type: string;
  previous_band: string;
  current_band: string;
  message: string;
  acknowledged: boolean;
  acknowledged_by?: string | null;
  acknowledged_at?: string | null;
  created_at: string;
}

export interface DashboardSummary {
  total_tickets: number;
  open_tickets: number;
  high_critical_risk_count: number;
  predicted_breaches_next_4h: number;
  avg_friction_score: number;
  auto_triaged_share_pct: number;
  volume_by_day: Array<{ date: string; tickets: number; breached: number }>;
  category_distribution: Array<{ category: string; count: number }>;
  recent_alerts: Alert[];
  top_at_risk_tickets: Array<{
    ticket_id: string;
    subject: string;
    category: string;
    priority: string;
    assigned_team: string;
    risk_band: string;
    probability: number;
    friction_score: number;
    estimated_minutes: number;
  }>;
}

export interface RiskForecastItem {
  ticket_id: string;
  subject: string;
  category: string;
  priority: string;
  assigned_team: string;
  sla_risk_band: string;
  sla_breach_probability: number;
  estimated_minutes_to_breach: number;
  elapsed_minutes: number;
  target_minutes: number;
}

export interface RiskForecastResponse {
  total_at_risk: number;
  high_critical_count: number;
  team_hour_heatmap: Array<{ team: string; hours: Record<string, number> }>;
  at_risk_tickets: RiskForecastItem[];
  precision_recall_curve: Array<{ mean_predicted_probability: number; fraction_of_positives: number }>;
  active_threshold: number;
}

export interface ThemeItem {
  id: number;
  label: string;
  top_terms: string[];
  ticket_count: number;
  weekly_trend: number[];
  is_emerging: boolean;
  z_score: number;
  representative_tickets: Array<{
    ticket_id: string;
    subject: string;
    category: string;
    created_at: string;
  }>;
}

export interface ThemeListResponse {
  themes: ThemeItem[];
  total_themes: number;
  emerging_count: number;
  nmi_sanity_score: number;
  ari_sanity_score: number;
  last_refreshed: string;
}

export interface ModelVersion {
  id: number;
  version: string;
  model_type: string;
  status: string;
  macro_f1: number;
  roc_auc?: number;
  accuracy: number;
  metrics: Record<string, any>;
  created_at: string;
}

export interface AnalysisResponse {
  category: string;
  category_confidence: number;
  category_probabilities: Record<string, number>;
  priority: string;
  priority_confidence: number;
  priority_probabilities: Record<string, number>;
  needs_human_triage: boolean;
  sla_breach_probability: number;
  sla_risk_band: string;
  estimated_minutes_to_breach: number;
  friction_score: number;
  friction_band: string;
  friction_breakdown: Record<string, any>;
  routing_recommendation: string;
  routing_reasoning: string;
  top_contributing_ngrams: Array<{ ngram: string; score: number }>;
  sla_top_drivers: Array<{ feature: string; impact_pct: number; description: string }>;
}
