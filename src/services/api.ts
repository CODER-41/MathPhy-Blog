const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const getToken = () =>
  JSON.parse(localStorage.getItem('auth-storage') || '{}')?.state?.token;

const getRefreshToken = () =>
  JSON.parse(localStorage.getItem('auth-storage') || '{}')?.state?.refreshToken;

const saveNewToken = (token: string) => {
  const storage = JSON.parse(localStorage.getItem('auth-storage') || '{}');
  storage.state.token = token;
  localStorage.setItem('auth-storage', JSON.stringify(storage));
};

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return null;

  const res = await fetch(`${API_BASE}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!res.ok) return null;

  const data = await res.json();
  saveNewToken(data.access_token);
  return data.access_token;
}

async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {},
  retry = true
): Promise<T> {
  const token = getToken();

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (res.status === 401 && retry) {
    const newToken = await refreshAccessToken();

    if (newToken) {
      return apiFetch<T>(endpoint, options, false);
    } else {
      localStorage.clear();
      window.location.href = '/login';
      throw new Error('Session expired. Please log in again.');
    }
  }

  if (!res.ok) {
    const error = await res.json().catch(() => ({ message: 'Request failed' }));
    throw new Error(error.message || `HTTP ${res.status}`);
  }

  return res.json();
}

export default apiFetch;