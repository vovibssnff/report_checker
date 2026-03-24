export interface User {
  id: string;
  email: string;
  name: string;
  organization?: string;
  role?: string;
}

export interface DevLoginPayload {
  email: string;
  name: string;
}

export interface DevLogoutPayload {
  // reserved for future compatibility; backend uses cookie-based logout
}
