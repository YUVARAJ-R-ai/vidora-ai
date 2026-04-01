"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { getToken, clearToken } from "./api";

interface AuthContextType {
  isAuthenticated: boolean;
  userEmail: string | null;
  logout: () => void;
  refreshAuth: () => void;
}

const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  userEmail: null,
  logout: () => {},
  refreshAuth: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userEmail, setUserEmail] = useState<string | null>(null);

  const refreshAuth = () => {
    const token = getToken();
    setIsAuthenticated(!!token);

    if (token) {
      // Decode JWT to get email (JWT payload is base64)
      try {
        const payload = JSON.parse(atob(token.split(".")[1]));
        setUserEmail(payload.sub || null);
      } catch {
        setUserEmail(null);
      }
    } else {
      setUserEmail(null);
    }
  };

  useEffect(() => {
    refreshAuth();
  }, []);

  const logout = () => {
    clearToken();
    setIsAuthenticated(false);
    setUserEmail(null);
    window.location.href = "/login";
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, userEmail, logout, refreshAuth }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
