import { Navigate, Outlet } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { useTracks } from "@/features/tracks/hooks";
import { useSessionStore } from "@/store/session";

/**
 * Restores the learner to the first unfinished setup step after a refresh or a
 * new sign-in. The database remains the source of truth: a track without a
 * completed placement still needs the test, while an assessed track without a
 * course needs generation. Admins are not forced through the learner setup flow.
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

  const awaitingPlacement = learnerTracks.find(
    (track) => track.placement_status !== "completed",
  );
  if (awaitingPlacement) {
    return <Navigate to={`/tracks/${awaitingPlacement.id}/placement`} replace />;
  }

  const awaitingCourse = learnerTracks.find((track) => !track.has_course);
  if (awaitingCourse) {
    return <Navigate to={`/tracks/${awaitingCourse.id}/generating`} replace />;
  }

  return <Outlet />;
}
