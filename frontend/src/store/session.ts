import { create } from "zustand";

export interface SessionUser {
  uid: string;
  email: string | null;
  isAdmin: boolean;
}

interface SessionState {
  user: SessionUser | null;
  setUser: (user: SessionUser | null) => void;
  clear: () => void;
}

/**
 * Lightweight client-side session store. Server data belongs in TanStack Query;
 * this holds only the small slice of session/UI state the app needs everywhere.
 */
export const useSessionStore = create<SessionState>((set) => ({
  user: null,
  setUser: (user) => set({ user }),
  clear: () => set({ user: null }),
}));
