import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/lib/auth";
import { useSessionStore } from "@/store/session";

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
      setError(err instanceof Error ? err.message : "Authentication failed");
      setBusy(false);
    }
  }

  const isSignup = mode === "signup";

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>{isSignup ? "Create account" : "Sign in"}</CardTitle>
          <CardDescription>
            {isConfigured
              ? isSignup
                ? "Create an account to get started."
                : "Sign in with your account to continue."
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
          {error && <p className="text-sm text-destructive">{error}</p>}
        </CardContent>
      </Card>
    </div>
  );
}
