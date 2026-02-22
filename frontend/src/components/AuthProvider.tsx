"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { fetchMe, login as apiLogin } from "@/lib/api";

type AuthState =
  | { status: "loading" }
  | { status: "unauthenticated" }
  | { status: "authenticated"; username: string };

type AuthContextValue = AuthState & {
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
};

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [state, setState] = useState<AuthState>({ status: "loading" });

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      setState({ status: "unauthenticated" });
      return;
    }
    fetchMe()
      .then((data) =>
        setState({ status: "authenticated", username: data.username })
      )
      .catch(() => {
        localStorage.removeItem("token");
        setState({ status: "unauthenticated" });
      });
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const data = await apiLogin(username, password);
    localStorage.setItem("token", data.token);
    setState({ status: "authenticated", username: data.username });
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("token");
    setState({ status: "unauthenticated" });
  }, []);

  return (
    <AuthContext.Provider value={{ ...state, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
