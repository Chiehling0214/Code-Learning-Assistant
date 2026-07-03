import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";

export interface ReviewItem {
  lesson_id: string;
  title: string;
  course_id: string;
  course_title: string;
  source: string;
  review_status: "approved" | "pending" | "hidden";
  exercise_count: number;
  quiz_count: number;
}

export interface AdminUsage {
  ai_lessons: number;
  pending: number;
  approved: number;
  hidden: number;
  ai_exercises: number;
  ai_quizzes: number;
}

/** List AI-generated content for review. */
export function useAdminContent(source = "ai") {
  return useQuery({
    queryKey: ["admin-content", source],
    queryFn: () => apiFetch<ReviewItem[]>(`/admin/content?source=${source}`),
  });
}

/** Aggregate AI-content review stats. */
export function useAdminUsage() {
  return useQuery({
    queryKey: ["admin-usage"],
    queryFn: () => apiFetch<AdminUsage>("/admin/usage"),
  });
}

/** Hide or approve a generated lesson. */
export function useSetLessonReview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ lessonId, action }: { lessonId: string; action: "hide" | "approve" }) =>
      apiFetch<ReviewItem>(`/admin/content/lessons/${lessonId}/${action}`, { method: "POST" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-content"] });
      queryClient.invalidateQueries({ queryKey: ["admin-usage"] });
    },
  });
}
