import { create } from "zustand";

export interface SessionUser {
  id: string;
  uid: string;
  email: string | null;
  displayName: string | null;
  isAdmin: boolean;
  /** True once the learner has chosen at least one language track. */
  onboarded: boolean;
}

interface SessionState {
  user: SessionUser | null;
  setUser: (user: SessionUser | null) => void;
  clear: () => void;
}

/**
 * Lightweight client-side session store. Server data belongs in TanStack Query;
 * this holds only the small slice of session/UI state the app needs everywhere.
 * Populated by the AuthProvider (see src/lib/auth.tsx).
 */
export const useSessionStore = create<SessionState>((set) => ({
  user: null,
  setUser: (user) => set({ user }),
  clear: () => set({ user: null }),
}));
