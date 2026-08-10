import { useEffect, useState } from "react";
import { Code2 } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/lib/auth";
import { useSessionStore } from "@/store/session";

const AUTH_ERROR_MESSAGES: Record<string, string> = {
  "auth/invalid-credential":
    "The email or password is incorrect. If you joined with Google, use Continue with Google instead.",
  "auth/email-already-in-use":
    "An account already exists for this email. Sign in instead, or use the same provider you originally chose.",
  "auth/invalid-email": "Enter a valid email address.",
  "auth/weak-password": "Choose a password with at least 6 characters.",
  "auth/operation-not-allowed":
    "This sign-in method is not enabled yet. Ask the project owner to enable it in Firebase Authentication.",
  "auth/popup-closed-by-user": "Google sign-in was closed before it finished.",
  "auth/popup-blocked": "The browser blocked the Google sign-in window. Allow pop-ups and try again.",
  "auth/unauthorized-domain":
    "This site is not authorized in Firebase. Add localhost to Authentication → Settings → Authorized domains.",
  "auth/network-request-failed": "Could not reach Firebase. Check your connection and try again.",
};

function authErrorMessage(error: unknown): string {
  if (error && typeof error === "object" && "code" in error) {
    const code = String((error as { code?: unknown }).code ?? "");
    if (AUTH_ERROR_MESSAGES[code]) return AUTH_ERROR_MESSAGES[code];
  }
  return error instanceof Error ? error.message : "Authentication failed. Please try again.";
}

export function LoginPage() {
  const navigate = useNavigate();
  const { isConfigured, signInWithGoogle, signInWithEmail, signUpWithEmail, devSignIn } = useAuth();
  const user = useSessionStore((s) => s.user);

  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  // Navigate only once the session is actually populated by the AuthProvider.
  // (Firebase sign-in resolves before onAuthStateChanged sets our session, so
  // navigating immediately would race the auth guard and bounce back here.)
  useEffect(() => {
    if (user) navigate("/dashboard", { replace: true });
  }, [user, navigate]);

  async function run(action: () => Promise<void>) {
    setError(null);
    setBusy(true);
    try {
      await action();
      // No navigate() here — the effect above fires when the session is ready.
    } catch (err) {
      setError(authErrorMessage(err));
      setBusy(false);
    }
  }

  const isSignup = mode === "signup";

  return (
    <div className="grid min-h-screen bg-background lg:grid-cols-[0.9fr_1.1fr]">
      <div className="hidden border-r bg-primary px-12 py-10 text-primary-foreground lg:flex lg:flex-col">
        <Link to="/" className="flex items-center gap-2.5 font-semibold">
          <span className="flex size-8 items-center justify-center rounded-lg bg-white/10"><Code2 className="size-4" /></span>
          Code Learning Assistant
        </Link>
        <div className="my-auto max-w-md">
          <p className="text-sm font-medium text-primary-foreground/65">Your learning path</p>
          <p className="mt-4 text-4xl font-semibold leading-tight tracking-[-0.04em]">
            Small lessons. Real practice. Steady progress.
          </p>
          <p className="mt-5 leading-7 text-primary-foreground/70">
            Pick up where you left off, review what needs attention, and keep moving forward.
          </p>
        </div>
        <p className="text-xs text-primary-foreground/50">Code Learning Assistant workspace</p>
      </div>
      <div className="flex items-center justify-center p-5 sm:p-10">
      <Card className="w-full max-w-md">
        <CardHeader>
          <Link to="/" className="mb-7 flex items-center gap-2 text-sm font-semibold lg:hidden"><Code2 className="size-5 shrink-0 text-primary" /> Code Learning Assistant</Link>
          <CardTitle className="text-2xl">{isSignup ? "Create your account" : "Welcome back"}</CardTitle>
          <CardDescription>
            {isConfigured
              ? isSignup
                ? "Set up your learning path in a few minutes."
                : "Sign in to continue your learning path."
              : "Firebase is not configured — continue in development mode."}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {isConfigured ? (
            <>
              <Button className="w-full" disabled={busy} onClick={() => run(signInWithGoogle)}>
                Continue with Google
              </Button>

              <div className="flex items-center gap-3 text-xs text-muted-foreground">
                <span className="h-px flex-1 bg-border" />
                or
                <span className="h-px flex-1 bg-border" />
              </div>

              <form
                className="space-y-3"
                onSubmit={(e) => {
                  e.preventDefault();
                  run(() =>
                    isSignup ? signUpWithEmail(email, password) : signInWithEmail(email, password),
                  );
                }}
              >
                <input
                  type="email"
                  required
                  placeholder="Email"
                  autoComplete="email"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
                <input
                  type="password"
                  required
                  minLength={6}
                  placeholder="Password (min 6 characters)"
                  autoComplete={isSignup ? "new-password" : "current-password"}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
                <Button type="submit" variant="outline" className="w-full" disabled={busy}>
                  {isSignup ? "Create account" : "Sign in with email"}
                </Button>
              </form>

              <button
                type="button"
                className="w-full text-center text-sm text-muted-foreground hover:text-foreground"
                onClick={() => {
                  setError(null);
                  setMode(isSignup ? "signin" : "signup");
                }}
              >
                {isSignup
                  ? "Already have an account? Sign in"
                  : "Need an account? Create one"}
              </button>
            </>
          ) : (
            <Button className="w-full" disabled={busy} onClick={() => run(devSignIn)}>
              Continue (development mode)
            </Button>
          )}
          {error && (
            <p role="alert" className="rounded-lg bg-destructive/10 px-3 py-2.5 text-sm leading-5 text-destructive">
              {error}
            </p>
          )}
        </CardContent>
      </Card>
      </div>
    </div>
  );
}
