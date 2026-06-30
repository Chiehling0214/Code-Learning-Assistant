import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";

export interface Choice {
  id: string;
  text: string;
  order_index: number;
}

export interface Question {
  id: string;
  prompt: string;
  type: string;
  order_index: number;
  choices: Choice[];
}

export interface Quiz {
  id: string;
  lesson_id: string;
  title: string;
  slug: string;
  description: string | null;
  questions: Question[];
}

export interface QuizSummary {
  id: string;
  title: string;
  slug: string;
}

export interface QuestionResult {
  question_id: string;
  correct: boolean;
  selected_choice_id: string | null;
  correct_choice_id: string | null;
}

export interface QuizSubmitResult {
  attempt_id: string;
  score: number;
  total: number;
  results: QuestionResult[];
}

export interface Attempt {
  id: string;
  quiz_id: string;
  score: number;
  total: number;
  created_at: string;
}

// ----- queries -----

export function useQuiz(id: string | undefined) {
  return useQuery({
    queryKey: ["quiz", id],
    queryFn: () => apiFetch<Quiz>(`/quizzes/${id}`),
    enabled: Boolean(id),
  });
}

export function useLessonQuizzes(lessonId: string | undefined) {
  return useQuery({
    queryKey: ["lesson-quizzes", lessonId],
    queryFn: () => apiFetch<QuizSummary[]>(`/lessons/${lessonId}/quizzes`),
    enabled: Boolean(lessonId),
  });
}

export function useQuizAttempts(quizId: string | undefined) {
  return useQuery({
    queryKey: ["quiz-attempts", quizId],
    queryFn: () => apiFetch<Attempt[]>(`/quizzes/${quizId}/attempts`),
    enabled: Boolean(quizId),
  });
}

// ----- learner submit -----

export function useSubmitQuiz(quizId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (answers: Record<string, string>) =>
      apiFetch<QuizSubmitResult>(`/quizzes/${quizId}/submit`, {
        method: "POST",
        body: JSON.stringify({ answers }),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["quiz-attempts", quizId] }),
  });
}

// ----- admin authoring -----

export interface ChoiceInput {
  text: string;
  is_correct: boolean;
}

export function useCreateQuiz() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: {
      lesson_id: string;
      title: string;
      slug: string;
      description: string | null;
    }) => apiFetch<Quiz>("/admin/quizzes", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: (quiz) =>
      queryClient.invalidateQueries({ queryKey: ["lesson-quizzes", quiz.lesson_id] }),
  });
}

export function useAddQuestion(quizId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: {
      prompt: string;
      type?: string;
      order_index?: number;
      choices: ChoiceInput[];
    }) =>
      apiFetch<Question>(`/admin/quizzes/${quizId}/questions`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["quiz", quizId] }),
  });
}

export function useDeleteQuiz(lessonId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiFetch<void>(`/admin/quizzes/${id}`, { method: "DELETE" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["lesson-quizzes", lessonId] }),
  });
}
