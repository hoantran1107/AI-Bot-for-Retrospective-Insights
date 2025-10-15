import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Types
export interface SprintMetrics {
  sprint_id: string;
  sprint_name: string;
  start_date: string;
  end_date: string;
  team_happiness?: number;
  story_points_completed?: number;
  story_points_planned?: number;
  review_time?: number;
  coding_time?: number;
  testing_time?: number;
  bugs_prod?: number;
  defect_rate_production?: number;
  story_point_distribution?: Record<string, number>;
}

export interface TrendAnalysis {
  metric_name: string;
  direction: "up" | "down" | "stable";
  magnitude: number;
  significance: string;
  current_value: number;
  previous_value: number;
  change_percent: number;
}

export interface Evidence {
  metric_name: string;
  trend: string;
  value: string;
  significance: string;
}

export interface Hypothesis {
  title: string;
  description: string;
  confidence: string;
  confidence_score: number;
  potential_impact: string;
  affected_metrics: string[];
  evidence: Evidence[];
  hypothesis_type?: string;
}

export interface ExperimentSuggestion {
  title: string;
  description: string;
  rationale: string;
  duration_sprints: number;
  success_metrics: string[];
  implementation_steps: string[];
  expected_outcome: string;
}

export interface ChartData {
  chart_type: string;
  title: string;
  data: any;
  config?: any;
}

export interface FacilitationGuide {
  retro_questions: string[];
  agenda_15min: string[];
  focus_areas: string[];
}

export interface RetrospectiveReport {
  report_id: string;
  headline: string;
  summary: string;
  sprint_period: string;
  generated_at: string;
  trends: TrendAnalysis[];
  correlations?: any[];
  charts: ChartData[];
  hypotheses: Hypothesis[];
  suggested_experiments: ExperimentSuggestion[];
  facilitation_guide: FacilitationGuide;
  sprints_analyzed: number;
  confidence_overall: string;
}

export interface ReportListItem {
  id: number;
  report_date: string;
  headline: string;
  summary: string;
  sprint_ids: string[];
  created_at: string;
}

export interface TaskStatus {
  task_id: string;
  status: "PENDING" | "STARTED" | "SUCCESS" | "FAILURE" | "RETRY" | "REVOKED";
  result?: any;
  error?: string;
}

// API Functions

// Health
export const healthCheck = () => api.get("/health");

// Metrics
export const fetchMetrics = (count: number = 5, team_id?: string) =>
  api.post("/metrics/fetch", { count, team_id });

export const listMetrics = (limit?: number, offset?: number) =>
  api.get("/metrics", { params: { limit, offset } });

// Reports
export const generateReport = (data: {
  sprint_count?: number;
  sprint_ids?: string[];
  custom_context?: string;
  focus_metrics?: string[];
}) => api.post<RetrospectiveReport>("/reports/generate", data);

export const listReports = (limit?: number, offset?: number) =>
  api.get<ReportListItem[]>("/reports", { params: { limit, offset } });

export const getReportById = (id: number) =>
  api.get<RetrospectiveReport>(`/reports/${id}`);

export const deleteReport = (id: number) => api.delete(`/reports/${id}`);

// Async Tasks
export const generateReportAsync = (data: {
  sprint_count?: number;
  sprint_ids?: string[];
  custom_context?: string;
  focus_metrics?: string[];
}) => api.post("/tasks/reports/generate", data);

export const syncMetricsAsync = (data: {
  sprint_count?: number;
  team_id?: string;
  force_refresh?: boolean;
}) => api.post("/tasks/metrics/sync", data);

export const getTaskStatus = (taskId: string) =>
  api.get<TaskStatus>(`/tasks/status/${taskId}`);

export const revokeTask = (taskId: string) => api.delete(`/tasks/${taskId}`);

export default api;
