import { Navigate, Outlet } from "react-router-dom";

import { useTracks } from "@/features/tracks/hooks";

/**
 * Sits inside ProtectedRoute: sends first-login learners (no language tracks yet)
 * to onboarding instead of the app shell.
 */
export function OnboardingGate() {
  const { data: tracks, isLoading, isError } = useTracks();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-muted-foreground">
        Loading…
      </div>
    );
  }

  // On error, fall through to the app rather than trapping the user.
  if (!isError && (tracks?.length ?? 0) === 0) {
    return <Navigate to="/onboarding" replace />;
  }

  return <Outlet />;
}
