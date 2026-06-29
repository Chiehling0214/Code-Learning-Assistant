import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";

export interface Exercise {
  id: string;
  lesson_id: string;
  language: string;
  title: string;
  slug: string;
  prompt: string;
  starter_code: string;
}

export interface ExerciseSummary {
  id: string;
  title: string;
  slug: string;
  language: string;
}

export type SubmissionStatus = "pending" | "passed" | "failed" | "error";

export interface Submission {
  id: string;
  exercise_id: string;
  code: string;
  status: SubmissionStatus;
  result: Record<string, unknown> | null;
  created_at: string;
}

export function useExercise(id: string | undefined) {
  return useQuery({
    queryKey: ["exercise", id],
    queryFn: () => apiFetch<Exercise>(`/exercises/${id}`),
    enabled: Boolean(id),
  });
}

export function useLessonExercises(lessonId: string | undefined) {
  return useQuery({
    queryKey: ["lesson-exercises", lessonId],
    queryFn: () => apiFetch<ExerciseSummary[]>(`/lessons/${lessonId}/exercises`),
    enabled: Boolean(lessonId),
  });
}

export function useSubmissions(exerciseId: string | undefined) {
  return useQuery({
    queryKey: ["submissions", exerciseId],
    queryFn: () => apiFetch<Submission[]>(`/exercises/${exerciseId}/submissions`),
    enabled: Boolean(exerciseId),
  });
}

export function useSubmit(exerciseId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (code: string) =>
      apiFetch<Submission>(`/exercises/${exerciseId}/submit`, {
        method: "POST",
        body: JSON.stringify({ code }),
      }),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["submissions", exerciseId] }),
  });
}
