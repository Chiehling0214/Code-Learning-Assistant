import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CourseChatPanel } from "@/components/CourseChatPanel";
import { SkeletonCards } from "@/components/Skeleton";
import { LessonCountSelect } from "@/components/LessonCountSelect";
import { useCourse } from "@/features/content/hooks";
import { useCourseExtension, useExtendCourse } from "@/features/curriculum/hooks";

export function CoursePage() {
  const { slug } = useParams<{ slug: string }>();
  const { data: course, isLoading, isError } = useCourse(slug);
  const courseId = course?.id;

  const { data: extension } = useCourseExtension(courseId);
  const extend = useExtendCourse(courseId, slug);
  const [count, setCount] = useState(2);

  if (isLoading) {
    return <SkeletonCards count={4} />;
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
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Lessons</h2>
          {extension?.can_extend && (
            <div className="flex items-center gap-2">
              <LessonCountSelect value={count} onChange={setCount} disabled={extend.isPending} />
              <Button
                variant="outline"
                size="sm"
                onClick={() => extend.mutate({ count })}
                disabled={extend.isPending}
              >
                {extend.isPending ? "Adding…" : `Learn more (${count})`}
              </Button>
            </div>
          )}
        </div>
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
        {extend.isError && (
          <p className="text-sm text-destructive">
            Couldn’t add more lessons just now — please try again shortly.
          </p>
        )}
      </div>

      {courseId && <CourseChatPanel courseId={courseId} courseSlug={slug} />}
    </div>
  );
}
