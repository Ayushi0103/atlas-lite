import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  changePassword as changePasswordRequest,
  getCurrentUser,
  loginAccount,
  loginWithGoogle,
  registerAccount,
  setAuthToken,
  setUnauthorizedHandler,
  updateProfile as updateProfileRequest,
} from "../services/atlasApi";
import type { AuthUser } from "../types/atlas";

const TOKEN_STORAGE_KEY = "atlas_token";

type AuthContextValue = {
  user: AuthUser | null;
  isInitializing: boolean;
  isSubmitting: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  googleSignIn: (credential: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  clearError: () => void;
  updateProfile: (name: string) => Promise<void>;
  changePassword: (currentPassword: string, newPassword: string) => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    setAuthToken(null);
    setUser(null);
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(logout);
    return () => setUnauthorizedHandler(null);
  }, [logout]);

  useEffect(() => {
    const storedToken = localStorage.getItem(TOKEN_STORAGE_KEY);
    if (!storedToken) {
      setIsInitializing(false);
      return;
    }

    setAuthToken(storedToken);
    getCurrentUser()
      .then((currentUser) => setUser(currentUser))
      .catch(() => {
        localStorage.removeItem(TOKEN_STORAGE_KEY);
        setAuthToken(null);
      })
      .finally(() => setIsInitializing(false));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setIsSubmitting(true);
    setError(null);
    try {
      const response = await loginAccount(email, password);
      localStorage.setItem(TOKEN_STORAGE_KEY, response.access_token);
      setAuthToken(response.access_token);
      setUser(response.user);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not log in.");
      throw err;
    } finally {
      setIsSubmitting(false);
    }
  }, []);

  const googleSignIn = useCallback(async (credential: string) => {
    setIsSubmitting(true);
    setError(null);
    try {
      const response = await loginWithGoogle(credential);
      localStorage.setItem(TOKEN_STORAGE_KEY, response.access_token);
      setAuthToken(response.access_token);
      setUser(response.user);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not sign in with Google.");
      throw err;
    } finally {
      setIsSubmitting(false);
    }
  }, []);

  const register = useCallback(async (name: string, email: string, password: string) => {
    setIsSubmitting(true);
    setError(null);
    try {
      const response = await registerAccount(name, email, password);
      localStorage.setItem(TOKEN_STORAGE_KEY, response.access_token);
      setAuthToken(response.access_token);
      setUser(response.user);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create account.");
      throw err;
    } finally {
      setIsSubmitting(false);
    }
  }, []);

  const clearError = useCallback(() => setError(null), []);

  const updateProfile = useCallback(async (name: string) => {
    const updatedUser = await updateProfileRequest(name);
    setUser(updatedUser);
  }, []);

  const changePassword = useCallback(async (currentPassword: string, newPassword: string) => {
    await changePasswordRequest(currentPassword, newPassword);
  }, []);

  const value = useMemo(
    () => ({
      user,
      isInitializing,
      isSubmitting,
      error,
      login,
      googleSignIn,
      register,
      logout,
      clearError,
      updateProfile,
      changePassword,
    }),
    [user, isInitializing, isSubmitting, error, login, googleSignIn, register, logout, clearError, updateProfile, changePassword],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }

  return context;
}
