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

export interface ReviewContentPage {
  items: ReviewItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ReviewCourseOption {
  course_id: string;
  title: string;
  total: number;
  pending: number;
}

export interface ReviewUserOption {
  user_id: string;
  email: string;
  display_name: string | null;
  course_count: number;
  lesson_count: number;
  pending: number;
}

export interface AdminUsage {
  ai_lessons: number;
  pending: number;
  approved: number;
  hidden: number;
  ai_exercises: number;
  ai_quizzes: number;
}

export interface ReviewPreview {
  lesson_id: string;
  title: string;
  content: string;
  exercises: Array<{
    id: string;
    title: string;
    language: string;
    prompt: string;
    starter_code: string;
    test_spec: Record<string, unknown>;
  }>;
  quizzes: Array<{
    id: string;
    title: string;
    questions: Array<{
      prompt: string;
      explanation: string;
      choices: Array<{ text: string; is_correct: boolean }>;
    }>;
  }>;
}

export interface BulkReviewResult {
  course_id: string;
  reviewed: number;
}

export interface ContentVersion {
  id: string;
  item_type: "lesson" | "exercise" | "quiz";
  item_id: string;
  created_by: string | null;
  created_at: string;
  snapshot: Record<string, unknown>;
}

export interface ContentVersionHistory {
  current_snapshot: Record<string, unknown>;
  versions: ContentVersion[];
}

export interface ContentReport {
  id: string;
  user_id: string;
  item_type: "lesson" | "exercise" | "quiz";
  item_id: string;
  reason: string;
  details: string;
  status: "open" | "resolved" | "dismissed";
  created_at: string;
  updated_at: string;
}

export interface AdminGenerationJob {
  id: string;
  user_email: string;
  language: string;
  kind: "initial" | "course_set";
  status: string;
  completed: number;
  total: number;
  attempt_count: number;
  max_attempts: number;
  error: string | null;
  cancel_requested: boolean;
  created_at: string;
  updated_at: string;
}

export interface OperationalEvent {
  id: string;
  category: string;
  level: string;
  message: string;
  details: Record<string, unknown>;
  created_at: string;
}

export interface MonitoringSummary {
  window_hours: number;
  counts: Record<string, number>;
  recent: OperationalEvent[];
}

/** Search AI-generated content using server-side filtering and pagination. */
export function useAdminContent({
  source = "ai",
  status,
  query = "",
  courseId,
  userId,
  page = 1,
  pageSize = 20,
  enabled = true,
}: {
  source?: string;
  status?: ReviewItem["review_status"];
  query?: string;
  courseId?: string;
  userId?: string;
  page?: number;
  pageSize?: number;
  enabled?: boolean;
} = {}) {
  const params = new URLSearchParams({
    source,
    page: String(page),
    page_size: String(pageSize),
  });
  if (status) params.set("review_status", status);
  if (query.trim()) params.set("query", query.trim());
  if (courseId) params.set("course_id", courseId);
  if (userId) params.set("user_id", userId);
  return useQuery({
    queryKey: ["admin-content", source, status, query, courseId, userId, page, pageSize],
    queryFn: () => apiFetch<ReviewContentPage>(`/admin/content?${params.toString()}`),
    placeholderData: (previous) => previous,
    enabled,
  });
}

export function useAdminReviewCourses(source = "ai", userId?: string) {
  const params = new URLSearchParams({ source });
  if (userId) params.set("user_id", userId);
  return useQuery({
    queryKey: ["admin-content-courses", source, userId],
    queryFn: () =>
      apiFetch<ReviewCourseOption[]>(`/admin/content/courses?${params.toString()}`),
    enabled: Boolean(userId),
  });
}

export function useAdminReviewUsers(source = "ai") {
  return useQuery({
    queryKey: ["admin-content-users", source],
    queryFn: () => apiFetch<ReviewUserOption[]>(`/admin/content/users?source=${source}`),
  });
}

/** Aggregate AI-content review stats. */
export function useAdminUsage() {
  return useQuery({
    queryKey: ["admin-usage"],
    queryFn: () => apiFetch<AdminUsage>("/admin/usage"),
  });
}

export function useAdminContentPreview(lessonId: string | null) {
  return useQuery({
    queryKey: ["admin-content-preview", lessonId],
    queryFn: () =>
      apiFetch<ReviewPreview>(`/admin/content/lessons/${lessonId}/preview`),
    enabled: Boolean(lessonId),
  });
}

export function useContentVersions(
  itemType: "lesson" | "exercise" | "quiz",
  itemId: string,
) {
  return useQuery({
    queryKey: ["content-versions", itemType, itemId],
    queryFn: () =>
      apiFetch<ContentVersionHistory>(`/admin/content/${itemType}/${itemId}/versions`),
    enabled: Boolean(itemId),
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
      queryClient.invalidateQueries({ queryKey: ["admin-content-courses"] });
      queryClient.invalidateQueries({ queryKey: ["admin-usage"] });
    },
  });
}

export function useMarkCourseReviewed() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (courseId: string) =>
      apiFetch<BulkReviewResult>(`/admin/content/courses/${courseId}/approve`, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-content"] });
      queryClient.invalidateQueries({ queryKey: ["admin-content-courses"] });
      queryClient.invalidateQueries({ queryKey: ["admin-usage"] });
    },
  });
}

export function useContentReports() {
  return useQuery({
    queryKey: ["admin-content-reports"],
    queryFn: () => apiFetch<ContentReport[]>("/admin/content-reports"),
  });
}

export function useSetContentReportStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: "resolved" | "dismissed" }) =>
      apiFetch<ContentReport>(`/admin/content-reports/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-content-reports"] }),
  });
}

export function useRegenerateContent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      itemType,
      itemId,
      instructions,
    }: {
      itemType: string;
      itemId: string;
      instructions?: string;
    }) =>
      apiFetch<void>(`/admin/content/${itemType}/${itemId}/regenerate`, {
        method: "POST",
        body: JSON.stringify({ instructions: instructions ?? "" }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-content"] });
      queryClient.invalidateQueries({ queryKey: ["admin-content-courses"] });
      queryClient.invalidateQueries({ queryKey: ["admin-content-reports"] });
      queryClient.invalidateQueries({ queryKey: ["admin-content-preview"] });
      queryClient.invalidateQueries({ queryKey: ["content-versions"] });
      queryClient.invalidateQueries({ queryKey: ["admin-usage"] });
    },
  });
}

export function useRestoreContentVersion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (versionId: string) =>
      apiFetch<void>(`/admin/content/versions/${versionId}/restore`, {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-content"] });
      queryClient.invalidateQueries({ queryKey: ["admin-content-courses"] });
      queryClient.invalidateQueries({ queryKey: ["admin-content-preview"] });
      queryClient.invalidateQueries({ queryKey: ["content-versions"] });
      queryClient.invalidateQueries({ queryKey: ["admin-usage"] });
    },
  });
}

export function useAdminGenerationJobs() {
  return useQuery({
    queryKey: ["admin-generation-jobs"],
    queryFn: () => apiFetch<AdminGenerationJob[]>("/admin/generation-jobs"),
    refetchInterval: 5000,
  });
}

export function useAdminMonitoring(hours = 24) {
  return useQuery({
    queryKey: ["admin-monitoring", hours],
    queryFn: () => apiFetch<MonitoringSummary>(`/admin/monitoring?hours=${hours}`),
    refetchInterval: 15_000,
  });
}

export function useGenerationJobAction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, action }: { id: string; action: "retry" | "cancel" }) =>
      apiFetch<AdminGenerationJob>(`/admin/generation-jobs/${id}/${action}`, {
        method: "POST",
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-generation-jobs"] }),
  });
}
