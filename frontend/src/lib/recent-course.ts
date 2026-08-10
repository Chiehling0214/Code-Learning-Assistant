const KEY_PREFIX = "code-learning-assistant:recent-course:";

export function rememberRecentCourse(userId: string | undefined, courseId: string | undefined) {
  if (!userId || !courseId || typeof window === "undefined") return;
  window.localStorage.setItem(`${KEY_PREFIX}${userId}`, courseId);
}

export function getRecentCourseId(userId: string | undefined): string | null {
  if (!userId || typeof window === "undefined") return null;
  return window.localStorage.getItem(`${KEY_PREFIX}${userId}`);
}
