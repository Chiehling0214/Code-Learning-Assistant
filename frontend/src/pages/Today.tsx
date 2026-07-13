import { Link } from "react-router-dom";

import { Card, CardContent } from "@/components/ui/card";
import { useToday, type TodayItem } from "@/features/progress/hooks";

const LINK_FOR: Record<TodayItem["type"], (id: string) => string> = {
  lesson: (id) => `/lessons/${id}`,
  exercise: (id) => `/exercises/${id}`,
  quiz: (id) => `/quizzes/${id}`,
};

export function TodayPage() {
  const { data, isLoading, isError } = useToday();

  if (isLoading) return <p className="text-muted-foreground">Loading your plan…</p>;
  if (isError) return <p className="text-destructive">Could not load your plan.</p>;

  const items = data?.items ?? [];
  const reviewsDue = data?.reviews_due ?? 0;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Today</h1>
        <p className="text-muted-foreground">Your next steps, tailored to your progress.</p>
      </div>

      {reviewsDue > 0 && (
        <Card className="border-primary/40 transition-colors hover:bg-accent">
          <Link to="/review">
            <CardContent className="flex items-center justify-between py-4">
              <span className="font-medium">
                🔁 {reviewsDue} review{reviewsDue !== 1 ? "s" : ""} due — clear these first
              </span>
              <span className="rounded-full bg-muted px-2 py-0.5 text-xs uppercase text-muted-foreground">
                review
              </span>
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
        <div className="space-y-3">
          {items.map((item) => (
            <Card key={`${item.type}-${item.id}`} className="transition-colors hover:bg-accent">
              <Link to={LINK_FOR[item.type](item.id)}>
                <CardContent className="flex items-center justify-between py-4">
                  <span className="font-medium">{item.title}</span>
                  <span className="rounded-full bg-muted px-2 py-0.5 text-xs uppercase text-muted-foreground">
                    {item.type}
                  </span>
                </CardContent>
              </Link>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
