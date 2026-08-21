export interface HealthResponse {
  status: string;
  app_name: string;
  environment: string;
  database_connected: boolean;
}

export interface ApiErrorPayload {
  detail?: string;
  message?: string;
}
