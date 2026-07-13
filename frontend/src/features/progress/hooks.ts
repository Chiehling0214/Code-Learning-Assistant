import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";

export interface TodayItem {
  type: "lesson" | "exercise" | "quiz";
  id: string;
  title: string;
  course_slug: string;
}

export interface CourseProgress {
  course_id: string;
  title: string;
  slug: string;
  total: number;
  completed: number;
  percent: number;
}

export interface Progress {
  courses: CourseProgress[];
  total: number;
  completed: number;
  percent: number;
  streak: number;
}

export function useToday() {
  return useQuery({
    queryKey: ["today"],
    queryFn: () => apiFetch<{ items: TodayItem[]; reviews_due: number }>("/today"),
  });
}

export function useProgress() {
  return useQuery({
    queryKey: ["progress"],
    queryFn: () => apiFetch<Progress>("/progress"),
  });
}

/** Mark a lesson complete; refreshes the plan and progress views. */
export function useMarkLessonComplete() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (lessonId: string) =>
      apiFetch<{ status: string }>(`/lessons/${lessonId}/complete`, { method: "POST" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["today"] });
      queryClient.invalidateQueries({ queryKey: ["progress"] });
    },
  });
}
