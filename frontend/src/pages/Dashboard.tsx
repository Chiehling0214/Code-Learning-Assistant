import { ArrowRight, BookOpen, CalendarCheck2, Dumbbell } from "lucide-react";
import { Link } from "react-router-dom";

import { SkeletonCards } from "@/components/Skeleton";
import { CourseCard } from "@/components/CourseCard";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useMyCourses } from "@/features/curriculum/hooks";
import { useProgress } from "@/features/progress/hooks";
import { useSessionStore } from "@/store/session";

export function DashboardPage() {
  const user = useSessionStore((state) => state.user);
  const { data: myCourses = [], isLoading } = useMyCourses();
  const { data: progress } = useProgress();
  const firstName = user?.displayName?.trim().split(/\s+/)[0];
  const resume = progress?.resume;
  const featured = myCourses.find((course) => course.id === resume?.course_id) ?? myCourses[0];
  const progressByCourse = new Map(progress?.courses.map((item) => [item.course_id, item]));

  return (
    <div className="space-y-10">
      <header className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
        <div>
          <p className="page-kicker">Learning workspace</p>
          <h1 className="page-heading">{firstName ? `Good to see you, ${firstName}.` : "Good to see you."}</h1>
          <p className="mt-2 text-muted-foreground">Keep the momentum going with one focused step today.</p>
        </div>
        <Button asChild>
          <Link to="/today">Open today’s plan <ArrowRight className="size-4" /></Link>
        </Button>
      </header>

      <section className="grid gap-4 lg:grid-cols-[1.55fr_0.85fr]">
        <Card className="flex min-h-52 overflow-hidden border-primary/20">
          <CardContent className="flex flex-1 items-center p-6 sm:p-8">
            <div>
              <div>
                <div className="mb-4 flex size-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
                  <BookOpen className="size-5" />
                </div>
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">Continue learning</p>
                <h2 className="mt-2 text-2xl font-semibold tracking-[-0.035em]">{featured?.title ?? "Your next course is being prepared"}</h2>
                <p className="mt-2 max-w-xl text-sm leading-6 text-muted-foreground">
                  {featured?.description || "Once your curriculum is ready, you can pick up from here."}
                </p>
                {resume && featured?.id === resume.course_id && resume.item_type !== "course" && (
                  <p className="mt-3 text-sm font-medium text-foreground">Continue: {resume.title}</p>
                )}
              </div>
              {featured && (
                <Link to={resume?.course_id === featured.id ? resume.path : `/courses/${featured.slug}`} className="mt-6 inline-flex items-center gap-1.5 text-sm font-semibold text-primary hover:underline">
                  {resume?.course_id === featured.id && resume.item_type !== "course" ? "Resume learning" : "View course"} <ArrowRight className="size-4" />
                </Link>
              )}
            </div>
          </CardContent>
        </Card>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-1">
          <Link to="/review" className="group flex min-h-[9.125rem] flex-col justify-center rounded-xl border bg-card p-5 shadow-card transition-colors hover:border-primary/25">
            <div className="flex items-start justify-between">
              <span className="flex size-9 items-center justify-center rounded-lg bg-secondary text-primary"><CalendarCheck2 className="size-[18px]" /></span>
              <ArrowRight className="size-4 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
            </div>
            <h2 className="mt-5 font-semibold">Review mistakes</h2>
            <p className="mt-1 text-sm text-muted-foreground">Revisit the things that need another pass.</p>
          </Link>
          <Link to="/practice" className="group flex min-h-[9.125rem] flex-col justify-center rounded-xl border bg-card p-5 shadow-card transition-colors hover:border-primary/25">
            <div className="flex items-start justify-between">
              <span className="flex size-9 items-center justify-center rounded-lg bg-secondary text-primary"><Dumbbell className="size-[18px]" /></span>
              <ArrowRight className="size-4 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
            </div>
            <h2 className="mt-5 font-semibold">Start a quick drill</h2>
            <p className="mt-1 text-sm text-muted-foreground">Practice a topic or target a weak spot.</p>
          </Link>
        </div>
      </section>

      <section className="space-y-3">
        <div className="flex items-end justify-between gap-4">
          <div>
            <p className="page-kicker">Library</p>
            <h2 className="section-heading">Your courses</h2>
          </div>
          {myCourses.length > 0 && (
            <Link to="/library" className="inline-flex items-center gap-1 text-sm font-semibold text-primary hover:underline">
              View full library <ArrowRight className="size-4" />
            </Link>
          )}
        </div>
        {isLoading ? (
          <SkeletonCards count={2} />
        ) : myCourses.length === 0 ? (
          <Card><CardContent className="py-8 text-sm text-muted-foreground">Your personalized courses will appear here after placement.</CardContent></Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {myCourses.slice(0, 3).map((course, index) => (
              <CourseCard
                key={course.id}
                course={course}
                courseProgress={progressByCourse.get(course.id)}
                index={index}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
