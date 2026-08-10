import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { ArrowRight, BookOpen } from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CourseChatPanel } from "@/components/CourseChatPanel";
import { SkeletonCards } from "@/components/Skeleton";
import { LessonCountSelect } from "@/components/LessonCountSelect";
import { useCourse } from "@/features/content/hooks";
import {
  useAdvanceCurriculum,
  useCourseExtension,
  useExtendCourse,
  useGenerationStatus,
} from "@/features/curriculum/hooks";
import { rememberRecentCourse } from "@/lib/recent-course";
import { useSessionStore } from "@/store/session";

export function CoursePage() {
  const { slug } = useParams<{ slug: string }>();
  const { data: course, isLoading, isError } = useCourse(slug);
  const courseId = course?.id;
  const userId = useSessionStore((state) => state.user?.id);

  const { data: extension } = useCourseExtension(courseId);
  const extend = useExtendCourse(courseId, slug);
  const advance = useAdvanceCurriculum(courseId);
  const generation = useGenerationStatus(advance.data?.track_id, Boolean(advance.data));
  const queryClient = useQueryClient();
  const advanceChecked = useRef(false);
  const [count, setCount] = useState(2);

  useEffect(() => {
    rememberRecentCourse(userId, courseId);
  }, [courseId, userId]);

  useEffect(() => {
    if (extension?.completion_percent === 100 && courseId && !advanceChecked.current) {
      advanceChecked.current = true;
      advance.mutate();
    }
  }, [advance, courseId, extension?.completion_percent]);

  useEffect(() => {
    if (generation.data?.status === "done") {
      queryClient.invalidateQueries({ queryKey: ["my-courses"] });
      queryClient.invalidateQueries({ queryKey: ["profile"] });
    }
  }, [generation.data?.status, queryClient]);

  if (isLoading) {
    return <SkeletonCards count={4} />;
  }
  if (isError || !course) {
    return <p className="text-destructive">Course not found.</p>;
  }

  return (
    <div className="mx-auto max-w-4xl space-y-9">
      <div className="space-y-2 border-b pb-8">
        <p className="page-kicker">Course</p>
        <h1 className="page-heading max-w-3xl">{course.title}</h1>
        {course.description && <p className="max-w-2xl leading-7 text-muted-foreground">{course.description}</p>}
        <div className="flex items-center gap-2 pt-3 text-sm text-muted-foreground"><BookOpen className="size-4" /> {course.lessons.length} lessons</div>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="section-heading">Course outline</h2>
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
            <Card key={lesson.id} className="group transition-colors hover:border-primary/25">
              <Link to={`/lessons/${lesson.id}`}>
                <CardHeader className="flex-row items-center gap-4 space-y-0 py-4">
                  <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-secondary font-mono text-xs text-primary">{String(index + 1).padStart(2, "0")}</span>
                  <CardTitle className="min-w-0 flex-1 truncate text-base font-medium">{lesson.title}</CardTitle>
                  <ArrowRight className="size-4 text-muted-foreground group-hover:text-primary" />
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

      {advance.data && (
        <Card className="border-primary/25 bg-primary/[0.035]">
          <CardContent className="py-5">
            <p className="font-semibold">
              {generation.data?.status === "done"
                ? "Your next three courses are ready."
                : "We’re assessing your results and building three next-step courses."}
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              They’re based on your quiz and exercise performance and will appear on Home automatically.
            </p>
          </CardContent>
        </Card>
      )}

      {courseId && <CourseChatPanel courseId={courseId} courseSlug={slug} />}
    </div>
  );
}
