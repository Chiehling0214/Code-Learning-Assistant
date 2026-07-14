import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";

export interface SampleCase {
  input: string;
  expected: string;
}

export interface Exercise {
  id: string;
  lesson_id: string;
  language: string;
  title: string;
  slug: string;
  prompt: string;
  starter_code: string;
  sample_cases: SampleCase[];
}

export interface ExerciseSummary {
  id: string;
  title: string;
  slug: string;
  language: string;
}

export type SubmissionStatus = "pending" | "passed" | "failed" | "error";

export interface TestResult {
  index: number;
  passed: boolean;
  status: string | null;
  input?: string;
  expected?: string;
  actual?: string;
  stderr?: string;
}

export interface GradingResult {
  verdict?: SubmissionStatus;
  passed?: number;
  total?: number;
  error?: string;
  compile_output?: string | null;
  tests?: TestResult[];
}

export interface Submission {
  id: string;
  exercise_id: string;
  code: string;
  status: SubmissionStatus;
  result: GradingResult | null;
  created_at: string;
}

export interface RunResult {
  stdout: string;
  stderr: string;
  status: string | null;
  compile_output: string | null;
  error: string | null;
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

export function useRun(exerciseId: string | undefined) {
  return useMutation({
    mutationFn: (vars: { code: string; stdin?: string }) =>
      apiFetch<RunResult>(`/exercises/${exerciseId}/run`, {
        method: "POST",
        body: JSON.stringify({ code: vars.code, stdin: vars.stdin ?? "" }),
      }),
  });
}

/**
 * Poll a single submission until it reaches a terminal status, so the UI can
 * show the verdict once background grading finishes.
 */
export function useSubmission(submissionId: string | undefined, exerciseId: string | undefined) {
  const queryClient = useQueryClient();
  return useQuery({
    queryKey: ["submission", submissionId],
    queryFn: async () => {
      const submission = await apiFetch<Submission>(`/submissions/${submissionId}`);
      if (submission.status !== "pending") {
        // Verdict is in — refresh the history list too.
        queryClient.invalidateQueries({ queryKey: ["submissions", exerciseId] });
      }
      return submission;
    },
    enabled: Boolean(submissionId),
    refetchInterval: (query) =>
      query.state.data && query.state.data.status === "pending" ? 1500 : false,
  });
}
