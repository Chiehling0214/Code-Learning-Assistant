import { Navigate, Outlet } from "react-router-dom";

import { useSessionStore } from "@/store/session";

/**
 * Sits inside ProtectedRoute: sends first-login learners (who haven't picked a
 * language yet) to onboarding instead of the app shell.
 *
 * Uses the `onboarded` flag from the (robustly-fetched) session rather than a
 * separate tracks query, so a transient error on that call can't let a brand-new
 * user slip straight into the dashboard.
 */
export function OnboardingGate() {
  const user = useSessionStore((s) => s.user);

  if (user && !user.onboarded) {
    return <Navigate to="/onboarding" replace />;
  }

  return <Outlet />;
}
