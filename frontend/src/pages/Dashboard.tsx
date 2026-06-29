import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useCourses } from "@/features/content/hooks";
import { apiFetch } from "@/lib/api";

interface Readiness {
  status: string;
  database: string;
}

export function DashboardPage() {
  // Demonstrates the TanStack Query + API wiring against the backend.
  const { data, isLoading, isError } = useQuery({
    queryKey: ["health"],
    queryFn: () => apiFetch<Readiness>("/health"),
  });
  const { data: courses = [], isLoading: coursesLoading } = useCourses();

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
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">
              <Link to="/today" className="hover:underline">
                Today's plan
              </Link>
            </CardTitle>
          </CardHeader>
          <CardContent />
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">
              <Link to="/progress" className="hover:underline">
                Your progress
              </Link>
            </CardTitle>
          </CardHeader>
          <CardContent />
        </Card>
      </div>

      <div className="space-y-3">
        <h2 className="text-lg font-semibold">Courses</h2>
        {coursesLoading ? (
          <p className="text-sm text-muted-foreground">Loading courses…</p>
        ) : courses.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No courses yet. Seed some via <code className="rounded bg-muted px-1">scripts.seed</code>{" "}
            or add them in <Link to="/admin" className="underline">Admin</Link>.
          </p>
        ) : (
          <div className="grid gap-4 md:grid-cols-3">
            {courses.map((course) => (
              <Card key={course.id} className="transition-colors hover:bg-accent">
                <Link to={`/courses/${course.slug}`}>
                  <CardHeader>
                    <CardTitle className="text-base">{course.title}</CardTitle>
                    {course.description && (
                      <CardDescription className="line-clamp-2">
                        {course.description}
                      </CardDescription>
                    )}
                  </CardHeader>
                  <CardContent />
                </Link>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
