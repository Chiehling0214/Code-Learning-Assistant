import { Navigate, Outlet } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { useTracks } from "@/features/tracks/hooks";
import { useSessionStore } from "@/store/session";

/**
 * Keeps the app shell available once a learner has selected a language. An
 * unfinished placement or course setup is presented as a resumable action in
 * the dashboard instead of blocking access to the rest of the product.
 */
export function OnboardingGate() {
  const user = useSessionStore((s) => s.user);
  const tracks = useTracks();

  if (user?.isAdmin) {
    return <Outlet />;
  }

  if (user && !user.onboarded) {
    return <Navigate to="/onboarding" replace />;
  }

  if (tracks.isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-muted-foreground">
        Restoring your learning path…
      </div>
    );
  }

  if (tracks.isError) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-3 p-6 text-center">
        <p className="text-sm text-destructive">Could not restore your learning path.</p>
        <Button
          variant="outline"
          onClick={() => {
            void tracks.refetch();
          }}
        >
          Try again
        </Button>
      </div>
    );
  }

  const learnerTracks = tracks.data ?? [];
  if (learnerTracks.length === 0) {
    return <Navigate to="/onboarding" replace />;
  }

  return <Outlet />;
}
