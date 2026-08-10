import { ArrowRight, BookOpen } from "lucide-react";
import { Link } from "react-router-dom";

import { ProgressBar } from "@/components/ProgressBar";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { Course } from "@/features/content/hooks";
import type { CourseProgress } from "@/features/progress/hooks";

export function CourseCard({
  course,
  courseProgress,
  index,
  language,
}: {
  course: Course;
  courseProgress?: CourseProgress;
  index: number;
  language?: string;
}) {
  return (
    <Card className="group flex h-full flex-col transition-[border-color,transform] hover:-translate-y-0.5 hover:border-primary/25">
      <CardHeader>
        <div className="mb-3 flex items-center justify-between">
          <span className="font-mono text-xs text-muted-foreground">
            COURSE {String(index + 1).padStart(2, "0")}
            {language ? ` · ${language}` : ""}
          </span>
          <BookOpen className="size-4 text-muted-foreground group-hover:text-primary" />
        </div>
        <CardTitle className="text-lg leading-snug">{course.title}</CardTitle>
        {course.description && (
          <CardDescription className="line-clamp-2 leading-5">{course.description}</CardDescription>
        )}
      </CardHeader>
      {courseProgress && (
        <CardContent className="flex-1 space-y-2">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>{courseProgress.completed} / {courseProgress.total} items</span>
            <span>{courseProgress.percent}%</span>
          </div>
          <ProgressBar percent={courseProgress.percent} />
          {courseProgress.next_item && (
            <p className="truncate pt-1 text-xs text-muted-foreground">
              Next: {courseProgress.next_item.title}
            </p>
          )}
        </CardContent>
      )}
      <CardFooter className="mt-auto gap-2">
        <Button variant="outline" size="sm" asChild>
          <Link to={`/courses/${course.slug}`}>View course</Link>
        </Button>
        {courseProgress?.next_item && (
          <Button variant="ghost" size="sm" asChild>
            <Link to={courseProgress.next_item.path}>
              Continue <ArrowRight className="size-4" />
            </Link>
          </Button>
        )}
      </CardFooter>
    </Card>
  );
}
