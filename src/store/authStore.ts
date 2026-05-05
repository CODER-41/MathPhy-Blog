import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: string;
  email: string;
  username: string;
}

interface AuthState {
  token: string | null;
  refreshToken: string | null;  // ← add this
  user: User | null;
  setAuth: (token: string, refreshToken: string, user: User) => void;  // ← update signature
  updateToken: (token: string) => void;  // ← add this for silent refresh
  logout: () => void;
}

const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      refreshToken: null,  // ← add this
      user: null,
      setAuth: (token, refreshToken, user) => set({ token, refreshToken, user }),  // ← update
      updateToken: (token) => set({ token }),  // ← add this
      logout: () => set({ token: null, refreshToken: null, user: null }),
    }),
    { name: 'auth-storage' }
  )
);

export default useAuthStore;