import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import { apiFetch, ApiError } from "@/lib/api";
import { streamSSE } from "@/lib/sse";

export interface AIAnswer {
  answer: string;
  model: string;
  total_tokens: number;
}

/**
 * Streaming AI answer with graceful fallback: tries `{path}/stream` (SSE) and
 * renders progressively; on transport failures it retries the non-stream
 * endpoint once. Server rejections (`ApiError`, e.g. 402/429) surface as-is.
 */
export function useStreamingAnswer(path: string) {
  const [answer, setAnswer] = useState("");
  const [isPending, setPending] = useState(false);
  const [error, setError] = useState<unknown>(null);

  const ask = async (body: Record<string, unknown>) => {
    setPending(true);
    setError(null);
    setAnswer("");
    let received = false;
    try {
      await streamSSE(`${path}/stream`, body, (text) => {
        received = true;
        setAnswer((a) => a + text);
      });
    } catch (err) {
      if (err instanceof ApiError || received) {
        setError(err);
      } else {
        // Transport hiccup before any chunk — fall back to the plain endpoint.
        try {
          const res = await apiFetch<AIAnswer>(path, {
            method: "POST",
            body: JSON.stringify(body),
          });
          setAnswer(res.answer);
        } catch (fallbackErr) {
          setError(fallbackErr);
        }
      }
    } finally {
      setPending(false);
    }
  };

  const reset = () => {
    setAnswer("");
    setError(null);
  };

  return { answer, isPending, error, ask, reset };
}

/** Ask the AI Teacher to explain a lesson concept (by lesson, topic, or question). */
export function useAskTeacher() {
  return useMutation({
    mutationFn: (vars: {
      lesson_id?: string;
      topic?: string;
      question?: string;
      /** Material the question refers to (e.g. the test being reviewed). */
      context?: string;
    }) =>
      apiFetch<AIAnswer>("/ai/teacher", {
        method: "POST",
        body: JSON.stringify({
          lesson_id: vars.lesson_id ?? null,
          topic: vars.topic ?? "",
          question: vars.question ?? "",
          context: vars.context ?? "",
        }),
      }),
  });
}

/** Ask the AI Tutor for a hint on the current exercise code (never the full answer). */
export function useAskTutor(exerciseId: string | undefined) {
  return useMutation({
    mutationFn: (vars: { code: string; question?: string }) =>
      apiFetch<AIAnswer>("/ai/tutor", {
        method: "POST",
        body: JSON.stringify({
          exercise_id: exerciseId,
          code: vars.code,
          question: vars.question ?? "",
        }),
      }),
  });
}
