import { ArrowRight, BookOpen, CircleHelp, Code2, RotateCcw } from "lucide-react";
import { Link } from "react-router-dom";

import { Card, CardContent } from "@/components/ui/card";
import { useToday, type TodayItem } from "@/features/progress/hooks";

const LINK_FOR: Record<TodayItem["type"], (id: string) => string> = {
  lesson: (id) => `/lessons/${id}`,
  exercise: (id) => `/exercises/${id}`,
  quiz: (id) => `/quizzes/${id}`,
};

const ICON_FOR = { lesson: BookOpen, exercise: Code2, quiz: CircleHelp };

export function TodayPage() {
  const { data, isLoading, isError } = useToday();

  if (isLoading) return <p className="text-muted-foreground">Loading your plan…</p>;
  if (isError) return <p className="text-destructive">Could not load your plan.</p>;

  const items = data?.items ?? [];
  const reviewsDue = data?.reviews_due ?? 0;

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <div>
        <p className="page-kicker">Daily plan</p>
        <h1 className="page-heading">A few good steps for today.</h1>
        <p className="mt-2 text-muted-foreground">Work from top to bottom, or choose what fits your time.</p>
      </div>

      {reviewsDue > 0 && (
        <Card className="border-primary/25 bg-primary/[0.035] transition-colors hover:bg-primary/[0.06]">
          <Link to="/review" className="flex min-h-[4.5rem]">
            <CardContent className="flex flex-1 items-center gap-4 px-5 py-0 sm:px-6">
              <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground"><RotateCcw className="size-4" /></span>
              <span className="flex-1">
                <span className="block font-semibold">Start with review</span>
                <span className="text-sm text-muted-foreground">{reviewsDue} item{reviewsDue !== 1 ? "s" : ""} ready to revisit</span>
              </span>
              <ArrowRight className="size-4 text-primary" />
            </CardContent>
          </Link>
        </Card>
      )}

      {items.length === 0 ? (
        <Card>
          <CardContent className="py-6 text-sm text-muted-foreground">
            You're all caught up. Add more content in Admin, or check back later.
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-2.5">
          {items.map((item, index) => {
            const Icon = ICON_FOR[item.type];
            return (
            <Card key={`${item.type}-${item.id}`} className="group transition-colors hover:border-primary/25">
              <Link to={LINK_FOR[item.type](item.id)} className="flex min-h-[4.5rem]">
                <CardContent className="flex flex-1 items-center gap-4 px-5 py-0 sm:px-6">
                  <span className="w-5 shrink-0 font-mono text-xs text-muted-foreground">{String(index + 1).padStart(2, "0")}</span>
                  <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-secondary text-primary"><Icon className="size-4" /></span>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate font-medium">{item.title}</span>
                    <span className="text-xs capitalize text-muted-foreground">{item.type}</span>
                  </span>
                  <ArrowRight className="size-4 text-muted-foreground group-hover:text-primary" />
                </CardContent>
              </Link>
            </Card>
          );})}
        </div>
      )}
    </div>
  );
}
