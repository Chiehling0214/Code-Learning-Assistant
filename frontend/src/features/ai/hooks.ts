import { useMutation } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";

export interface AIAnswer {
  answer: string;
  model: string;
  total_tokens: number;
}

/** Ask the AI Teacher to explain a lesson concept (by lesson, topic, or question). */
export function useAskTeacher() {
  return useMutation({
    mutationFn: (vars: { lesson_id?: string; topic?: string; question?: string }) =>
      apiFetch<AIAnswer>("/ai/teacher", {
        method: "POST",
        body: JSON.stringify({
          lesson_id: vars.lesson_id ?? null,
          topic: vars.topic ?? "",
          question: vars.question ?? "",
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
