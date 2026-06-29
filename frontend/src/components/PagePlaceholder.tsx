import type { ReactNode } from "react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

interface PagePlaceholderProps {
  title: string;
  description: string;
  /** The sprint in which this page's functionality is implemented. */
  sprint: number;
  children?: ReactNode;
}

/**
 * Shared scaffold for pages whose business logic ships in a later sprint. The
 * page renders fully and explains what it will become — it is a real component,
 * not a stub awaiting implementation in this file.
 */
export function PagePlaceholder({ title, description, sprint, children }: PagePlaceholderProps) {
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="space-y-1">
        <h1 className="text-3xl font-bold tracking-tight">{title}</h1>
        <p className="text-muted-foreground">{description}</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Coming in Sprint {sprint}</CardTitle>
          <CardDescription>
            This page is part of the Sprint 0 scaffold. Its functionality is scheduled for a later
            sprint.
          </CardDescription>
        </CardHeader>
        {children ? <CardContent>{children}</CardContent> : null}
      </Card>
    </div>
  );
}
