import useAuthStore from '@/store/authStore';

export function useAuth() {
  const { token, user, setAuth, logout } = useAuthStore();
  return {
    isAuthenticated: !!token,
    token,
    user,
    setAuth,
    logout,
  };
}
