import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import type { Course } from "@/features/content/hooks";

export interface GenerationJob {
  id: string;
  track_id: string;
  status: "pending" | "running" | "done" | "error";
  total: number;
  completed: number;
  course_id: string | null;
  error: string | null;
}

/** Kick off (or re-attach to) curriculum generation for a track. */
export function useGenerateCourse(trackId: string | undefined) {
  return useMutation({
    mutationFn: () => apiFetch<GenerationJob>(`/me/tracks/${trackId}/generate`, { method: "POST" }),
  });
}

/** Poll the generation job until it reaches a terminal state. */
export function useGenerationStatus(trackId: string | undefined, enabled: boolean) {
  return useQuery({
    queryKey: ["generation", trackId],
    queryFn: () => apiFetch<GenerationJob>(`/me/tracks/${trackId}/generation`),
    enabled: enabled && Boolean(trackId),
    // Keep polling until the job reaches a terminal state. Also poll while there
    // is no data yet (e.g. the job row was just created and the first fetch 404'd).
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "done" || status === "error") return false;
      return 2000;
    },
    // The job is created by the POST; a poll firing a hair earlier can 404, so retry.
    retry: 5,
    retryDelay: 1000,
  });
}

/** The learner's own (AI-generated, track-scoped) courses. */
export function useMyCourses() {
  return useQuery({
    queryKey: ["my-courses"],
    queryFn: () => apiFetch<Course[]>("/me/courses"),
  });
}

// ----- Continuous learning: extend + in-course chat (Sprint 12) -----

export interface AddedLesson {
  id: string;
  title: string;
  slug: string;
  order_index: number;
}

export interface ExtensionStatus {
  course_id: string;
  lesson_count: number;
  completion_percent: number;
  can_extend: boolean;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

/** Near-completion hint + lesson count for a course. */
export function useCourseExtension(courseId: string | undefined) {
  return useQuery({
    queryKey: ["extension", courseId],
    queryFn: () => apiFetch<ExtensionStatus>(`/courses/${courseId}/extension`),
    enabled: Boolean(courseId),
  });
}

/** Generate more lessons into the course (optionally on a topic, and a count). */
export function useExtendCourse(courseId: string | undefined, courseSlug: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (vars?: { topic?: string; count?: number }) =>
      apiFetch<{ added: AddedLesson[]; lesson_count: number }>(
        `/courses/${courseId}/extend`,
        {
          method: "POST",
          body: JSON.stringify({ topic: vars?.topic ?? null, count: vars?.count ?? null }),
        },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["course", courseSlug] });
      queryClient.invalidateQueries({ queryKey: ["extension", courseId] });
    },
  });
}

/** The persisted in-course chat conversation. */
export function useCourseChat(courseId: string | undefined) {
  return useQuery({
    queryKey: ["course-chat", courseId],
    queryFn: () =>
      apiFetch<{ messages: ChatMessage[] }>(`/courses/${courseId}/chat`).then((r) => r.messages),
    enabled: Boolean(courseId),
  });
}

/** Send a chat message; the AI appends matching content and replies. */
export function useSendCourseChat(courseId: string | undefined, courseSlug: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (vars: { message: string; count?: number }) =>
      apiFetch<{ reply: ChatMessage; added: AddedLesson[] }>(`/courses/${courseId}/chat`, {
        method: "POST",
        body: JSON.stringify({ message: vars.message, count: vars.count ?? null }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["course-chat", courseId] });
      queryClient.invalidateQueries({ queryKey: ["course", courseSlug] });
      queryClient.invalidateQueries({ queryKey: ["extension", courseId] });
    },
  });
}
