import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LessonCountSelect } from "@/components/LessonCountSelect";
import { Markdown } from "@/components/Markdown";
import { useCourseChat, useSendCourseChat } from "@/features/curriculum/hooks";
import { cn } from "@/lib/utils";

interface Props {
  courseId: string;
  courseSlug: string | undefined;
}

/** In-course chat: ask for a topic and the AI appends matching lessons. */
export function CourseChatPanel({ courseId, courseSlug }: Props) {
  const { data: messages } = useCourseChat(courseId);
  const send = useSendCourseChat(courseId, courseSlug);
  const [draft, setDraft] = useState("");
  const [count, setCount] = useState(1);
  const listRef = useRef<HTMLDivElement>(null);

  // Keep the newest message in view.
  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight });
  }, [messages, send.isPending]);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const text = draft.trim();
    if (!text || send.isPending) return;
    send.mutate({ message: text, count });
    setDraft("");
  };

  return (
    <Card>
      <CardHeader className="py-4">
        <CardTitle className="text-base font-semibold">Ask for more to learn</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div ref={listRef} className="max-h-72 space-y-3 overflow-y-auto">
          {(!messages || messages.length === 0) && !send.isPending ? (
            <p className="text-sm text-muted-foreground">
              Try “teach me decorators” or “add a lesson on error handling”. I’ll create a
              lesson with exercises and a quiz and add it to this course.
            </p>
          ) : (
            messages?.map((m) => (
              <div
                key={m.id}
                className={cn("flex", m.role === "user" ? "justify-end" : "justify-start")}
              >
                <div
                  className={cn(
                    "max-w-[85%] rounded-lg px-3 py-2 text-sm",
                    m.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-foreground",
                  )}
                >
                  {m.role === "assistant" ? <Markdown content={m.content} /> : m.content}
                </div>
              </div>
            ))
          )}
          {send.isPending && (
            <p className="text-sm text-muted-foreground">Generating new content…</p>
          )}
        </div>

        {send.isError && (
          <p className="text-sm text-destructive">
            Couldn’t generate that just now — please try again in a moment.
          </p>
        )}

        <form onSubmit={submit} className="flex gap-2">
          <input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="What do you want to learn next?"
            disabled={send.isPending}
            className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:opacity-50"
          />
          <LessonCountSelect value={count} onChange={setCount} disabled={send.isPending} />
          <Button type="submit" disabled={send.isPending || !draft.trim()}>
            Send
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
