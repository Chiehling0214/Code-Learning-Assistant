import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";

export interface TopicMastery {
  topic: string;
  attempts: number;
  correct: number;
  correct_rate: number;
  level: "weak" | "ok" | "strong";
}

/** Per-topic mastery for one of the learner's languages (weakest first). */
export function useMastery(language: string | undefined) {
  return useQuery({
    queryKey: ["mastery", language],
    queryFn: () =>
      apiFetch<{ language: string; topics: TopicMastery[] }>(
        `/me/mastery?language=${language}`,
      ),
    enabled: Boolean(language),
  });
}
