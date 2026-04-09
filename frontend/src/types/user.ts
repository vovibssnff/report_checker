export interface User {
  id: string;
  email: string;
  name: string;
  organization?: string;
  role: 'student' | 'teacher' | 'admin';
}

export interface DevLoginPayload {
  email: string;
  password: string;
}

export interface DevRegisterPayload {
  email: string;
  name: string;
  password: string;
  role: 'student' | 'teacher';
}

export interface DevLogoutPayload {
  // reserved for future compatibility; backend uses cookie-based logout
}
