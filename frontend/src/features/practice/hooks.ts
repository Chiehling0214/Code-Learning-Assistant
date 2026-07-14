import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";

export interface PracticeExercise {
  exercise_id: string;
  title: string;
  topic: string;
  language: string;
}

export interface PracticeHistoryEntry {
  exercise_id: string;
  title: string;
  topic: string;
  language: string;
  last_verdict: "passed" | "failed" | "error" | "pending" | null;
}

/** Generate a drill on a topic (omit topic to train the weakest one). */
export function useGeneratePractice() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (vars: { language: string; topic?: string; difficulty?: string }) =>
      apiFetch<PracticeExercise>("/practice/generate", {
        method: "POST",
        body: JSON.stringify({
          language: vars.language,
          topic: vars.topic || null,
          difficulty: vars.difficulty || null,
        }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["practice-history"] });
      queryClient.invalidateQueries({ queryKey: ["entitlements"] });
    },
  });
}

/** Past drills, newest first, with the latest verdict. */
export function usePracticeHistory(language?: string) {
  return useQuery({
    queryKey: ["practice-history", language ?? "all"],
    queryFn: () =>
      apiFetch<PracticeHistoryEntry[]>(
        `/practice/history${language ? `?language=${language}` : ""}`,
      ),
  });
}
