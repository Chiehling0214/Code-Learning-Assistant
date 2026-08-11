import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";

export interface Language {
  id: string;
  name: string;
  slug: string;
}

export interface Course {
  id: string;
  language_id: string;
  title: string;
  slug: string;
  description: string | null;
  prerequisite_course_id: string | null;
  sequence_index: number;
  recommendation_reason: string | null;
}

export interface LessonSummary {
  id: string;
  title: string;
  slug: string;
  order_index: number;
  exercises: CourseItemSummary[];
  quizzes: CourseItemSummary[];
}

export interface CourseItemSummary {
  id: string;
  title: string;
  slug: string;
}

export interface CourseDetail extends Course {
  lessons: LessonSummary[];
}

export interface Lesson {
  id: string;
  course_id: string;
  title: string;
  slug: string;
  order_index: number;
  content: string;
}

export type LessonAdjustmentPreset = "simpler" | "examples" | "challenge" | "practical";

export interface LessonAdjustmentPreview {
  adjustment_id: string;
  lesson_id: string;
  title: string;
  content: string;
}

// ----- queries -----

export function useLanguages() {
  return useQuery({ queryKey: ["languages"], queryFn: () => apiFetch<Language[]>("/languages") });
}

export function useCourses() {
  return useQuery({ queryKey: ["courses"], queryFn: () => apiFetch<Course[]>("/courses") });
}

export function useCourse(slug: string | undefined) {
  return useQuery({
    queryKey: ["course", slug],
    queryFn: () => apiFetch<CourseDetail>(`/courses/${slug}`),
    enabled: Boolean(slug),
  });
}

export function useLesson(id: string | undefined) {
  return useQuery({
    queryKey: ["lesson", id],
    queryFn: () => apiFetch<Lesson>(`/lessons/${id}`),
    enabled: Boolean(id),
  });
}

export function usePreviewLessonAdjustment() {
  return useMutation({
    mutationFn: ({
      lessonId,
      preset,
      instructions,
    }: {
      lessonId: string;
      preset: LessonAdjustmentPreset;
      instructions: string;
    }) =>
      apiFetch<LessonAdjustmentPreview>(`/lessons/${lessonId}/adjustments/preview`, {
        method: "POST",
        body: JSON.stringify({ preset, instructions }),
      }),
  });
}

export function useApplyLessonAdjustment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ lessonId, adjustmentId }: { lessonId: string; adjustmentId: string }) =>
      apiFetch<Lesson>(`/lessons/${lessonId}/adjustments/${adjustmentId}/apply`, {
        method: "POST",
      }),
    onSuccess: (lesson) => {
      queryClient.setQueryData(["lesson", lesson.id], lesson);
      queryClient.invalidateQueries({ queryKey: ["admin-content"] });
      queryClient.invalidateQueries({ queryKey: ["content-versions"] });
      queryClient.invalidateQueries({ queryKey: ["entitlements"] });
    },
  });
}

// ----- admin mutations -----

function useInvalidate(keys: string[]) {
  const queryClient = useQueryClient();
  return () => keys.forEach((key) => queryClient.invalidateQueries({ queryKey: [key] }));
}

export function useCreateLanguage() {
  const invalidate = useInvalidate(["languages"]);
  return useMutation({
    mutationFn: (body: { name: string; slug: string }) =>
      apiFetch<Language>("/admin/languages", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: invalidate,
  });
}

export function useDeleteLanguage() {
  const invalidate = useInvalidate(["languages"]);
  return useMutation({
    mutationFn: (id: string) => apiFetch<void>(`/admin/languages/${id}`, { method: "DELETE" }),
    onSuccess: invalidate,
  });
}

export function useCreateCourse() {
  const invalidate = useInvalidate(["courses"]);
  return useMutation({
    mutationFn: (body: {
      language_id: string;
      title: string;
      slug: string;
      description: string | null;
    }) => apiFetch<Course>("/admin/courses", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: invalidate,
  });
}

export function useDeleteCourse() {
  const invalidate = useInvalidate(["courses"]);
  return useMutation({
    mutationFn: (id: string) => apiFetch<void>(`/admin/courses/${id}`, { method: "DELETE" }),
    onSuccess: invalidate,
  });
}

export function useCreateLesson(courseSlug: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: {
      course_id: string;
      title: string;
      slug: string;
      order_index: number;
      content: string;
    }) => apiFetch<Lesson>("/admin/lessons", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["course", courseSlug] }),
  });
}

export function useDeleteLesson(courseSlug: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiFetch<void>(`/admin/lessons/${id}`, { method: "DELETE" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["course", courseSlug] }),
  });
}
