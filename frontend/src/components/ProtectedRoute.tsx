import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "@/lib/auth";
import { useSessionStore } from "@/store/session";

/** Guards private routes: shows a loader while auth resolves, then redirects
 * unauthenticated users to /login. */
export function ProtectedRoute() {
  const { loading } = useAuth();
  const user = useSessionStore((s) => s.user);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-muted-foreground">
        Loading…
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
