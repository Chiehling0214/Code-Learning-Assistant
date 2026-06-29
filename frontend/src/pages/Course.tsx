import { Link, useParams } from "react-router-dom";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useCourse } from "@/features/content/hooks";

export function CoursePage() {
  const { slug } = useParams<{ slug: string }>();
  const { data: course, isLoading, isError } = useCourse(slug);

  if (isLoading) {
    return <p className="text-muted-foreground">Loading course…</p>;
  }
  if (isError || !course) {
    return <p className="text-destructive">Course not found.</p>;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="space-y-1">
        <h1 className="text-3xl font-bold tracking-tight">{course.title}</h1>
        {course.description && <p className="text-muted-foreground">{course.description}</p>}
      </div>

      <div className="space-y-3">
        <h2 className="text-lg font-semibold">Lessons</h2>
        {course.lessons.length === 0 ? (
          <p className="text-sm text-muted-foreground">No lessons yet.</p>
        ) : (
          course.lessons.map((lesson, index) => (
            <Card key={lesson.id} className="transition-colors hover:bg-accent">
              <Link to={`/lessons/${lesson.id}`}>
                <CardHeader className="flex-row items-center gap-3 space-y-0 py-4">
                  <span className="text-sm text-muted-foreground">{index + 1}</span>
                  <CardTitle className="text-base font-medium">{lesson.title}</CardTitle>
                </CardHeader>
              </Link>
              <CardContent className="hidden" />
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
