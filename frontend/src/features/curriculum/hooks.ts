import { useMutation, useQuery } from "@tanstack/react-query";

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
