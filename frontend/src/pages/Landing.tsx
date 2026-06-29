import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const FEATURES = [
  { title: "AI Teacher", body: "Lessons explained and adapted to your level." },
  { title: "Hands-on Practice", body: "Write and run real code in the browser." },
  { title: "Personalized Plan", body: "A daily plan tuned to your progress." },
];

export function LandingPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="container flex flex-col items-center gap-10 py-24 text-center">
        <div className="space-y-4">
          <h1 className="text-5xl font-bold tracking-tight">CodePath AI</h1>
          <p className="mx-auto max-w-xl text-lg text-muted-foreground">
            Learn to code with a personalized, AI-guided path of lessons, exercises, and quizzes.
          </p>
        </div>
        <div className="flex gap-3">
          <Button asChild size="lg">
            <Link to="/login">Get started</Link>
          </Button>
          <Button asChild size="lg" variant="outline">
            <Link to="/dashboard">View dashboard</Link>
          </Button>
        </div>
        <div className="grid w-full max-w-4xl gap-4 pt-8 md:grid-cols-3">
          {FEATURES.map((f) => (
            <Card key={f.title} className="text-left">
              <CardHeader>
                <CardTitle className="text-xl">{f.title}</CardTitle>
                <CardDescription>{f.body}</CardDescription>
              </CardHeader>
              <CardContent />
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
