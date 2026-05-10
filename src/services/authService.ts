import apiFetch from './api';

export interface LoginPayload {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface User {
  id: string;
  email: string;
  username: string;
}

export const authService = {
  login: (data: LoginPayload) =>
    apiFetch<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Optional token param bypasses the localStorage timing issue —
  // pass data.access_token directly from onSuccess instead of waiting
  // for Zustand persist to flush to localStorage.
  me: (token?: string) =>
    apiFetch<User>('/auth/me', {
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    }),
};