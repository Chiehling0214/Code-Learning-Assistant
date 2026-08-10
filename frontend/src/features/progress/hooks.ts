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
  next_item: LearningItem | null;
  completed_items: Array<{
    item_type: "lesson" | "exercise" | "quiz";
    item_id: string;
  }>;
}

export interface LearningItem {
  item_type: "course" | "lesson" | "exercise" | "quiz";
  item_id: string;
  title: string;
  path: string;
}

export interface ResumePoint extends LearningItem {
  course_id: string;
  course_title: string;
  course_slug: string;
  updated_at: string | null;
}

export interface Progress {
  courses: CourseProgress[];
  total: number;
  completed: number;
  percent: number;
  streak: number;
  resume: ResumePoint | null;
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

export function useRecordLearningActivity() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (item: { item_type: LearningItem["item_type"]; item_id: string }) =>
      apiFetch<ResumePoint>("/progress/activity", {
        method: "POST",
        body: JSON.stringify(item),
      }),
    onSuccess: (resume) => {
      queryClient.setQueryData<Progress>(["progress"], (current) =>
        current ? { ...current, resume } : current,
      );
    },
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
