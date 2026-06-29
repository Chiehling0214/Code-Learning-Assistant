import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";

interface Readiness {
  status: string;
  database: string;
}

const SHORTCUTS = [
  { to: "/today", label: "Today's plan" },
  { to: "/progress", label: "Your progress" },
  { to: "/courses/python-basics", label: "Sample course" },
];

export function DashboardPage() {
  // Demonstrates the TanStack Query + API wiring against the backend.
  const { data, isLoading, isError } = useQuery({
    queryKey: ["health"],
    queryFn: () => apiFetch<Readiness>("/health"),
  });

  const apiStatus = isLoading ? "checking…" : isError ? "unreachable" : (data?.status ?? "unknown");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">Welcome back to CodePath AI.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">API status</CardTitle>
            <CardDescription>Live backend health check.</CardDescription>
          </CardHeader>
          <CardContent>
            <span className="font-mono text-sm">{apiStatus}</span>
          </CardContent>
        </Card>

        {SHORTCUTS.map((s) => (
          <Card key={s.to}>
            <CardHeader>
              <CardTitle className="text-lg">
                <Link to={s.to} className="hover:underline">
                  {s.label}
                </Link>
              </CardTitle>
            </CardHeader>
            <CardContent />
          </Card>
        ))}
      </div>
    </div>
  );
}
