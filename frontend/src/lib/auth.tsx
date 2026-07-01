/* eslint-disable react-refresh/only-export-components */
import {
  createUserWithEmailAndPassword,
  GoogleAuthProvider,
  onAuthStateChanged,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut as firebaseSignOut,
} from "firebase/auth";
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

import { apiFetch } from "@/lib/api";
import { auth, isFirebaseConfigured } from "@/lib/firebase";
import { useSessionStore, type SessionUser } from "@/store/session";

/** Marks a dev-mode (Firebase-less) session so it survives a page refresh. */
const DEV_SESSION_KEY = "codepath.devSession";

interface MeResponse {
  id: string;
  uid: string;
  email: string | null;
  display_name: string | null;
  is_admin: boolean;
}

async function fetchSessionUser(): Promise<SessionUser> {
  const me = await apiFetch<MeResponse>("/me");
  return {
    id: me.id,
    uid: me.uid,
    email: me.email,
    displayName: me.display_name,
    isAdmin: me.is_admin,
  };
}

/** Resolve the session, retrying a couple of times to ride out a transient
 * failure right after sign-in (e.g. brief token/clock skew). */
async function resolveSessionUser(attempts = 3): Promise<SessionUser> {
  let lastError: unknown;
  for (let i = 0; i < attempts; i += 1) {
    try {
      return await fetchSessionUser();
    } catch (err) {
      lastError = err;
      await new Promise((resolve) => setTimeout(resolve, 700 * (i + 1)));
    }
  }
  throw lastError;
}

interface AuthContextValue {
  loading: boolean;
  isConfigured: boolean;
  signInWithGoogle: () => Promise<void>;
  signInWithEmail: (email: string, password: string) => Promise<void>;
  signUpWithEmail: (email: string, password: string) => Promise<void>;
  /** Dev sign-in for when Firebase is not configured (backend runs in stub mode). */
  devSignIn: () => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const setUser = useSessionStore((s) => s.setUser);
  const clear = useSessionStore((s) => s.clear);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isFirebaseConfigured && auth) {
      // Firebase persists auth across refreshes; re-sync our session on change.
      return onAuthStateChanged(auth, async (firebaseUser) => {
        if (firebaseUser) {
          try {
            setUser(await resolveSessionUser());
          } catch {
            clear();
          }
        } else {
          clear();
        }
        setLoading(false);
      });
    }

    // Dev mode: restore a persisted dev session if one exists.
    if (localStorage.getItem(DEV_SESSION_KEY) === "1") {
      fetchSessionUser()
        .then(setUser)
        .catch(() => clear())
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [setUser, clear]);

  const value: AuthContextValue = {
    loading,
    isConfigured: isFirebaseConfigured,
    signInWithGoogle: async () => {
      if (!auth) throw new Error("Firebase is not configured");
      await signInWithPopup(auth, new GoogleAuthProvider());
    },
    signInWithEmail: async (email, password) => {
      if (!auth) throw new Error("Firebase is not configured");
      await signInWithEmailAndPassword(auth, email, password);
    },
    signUpWithEmail: async (email, password) => {
      if (!auth) throw new Error("Firebase is not configured");
      await createUserWithEmailAndPassword(auth, email, password);
    },
    devSignIn: async () => {
      localStorage.setItem(DEV_SESSION_KEY, "1");
      setUser(await fetchSessionUser());
    },
    signOut: async () => {
      localStorage.removeItem(DEV_SESSION_KEY);
      if (auth) await firebaseSignOut(auth);
      clear();
    },
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
