import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";

export interface TopicMastery {
  topic: string;
  attempts: number;
  correct: number;
  correct_rate: number;
  level: "weak" | "ok" | "strong";
  /** The course lesson teaching this topic (null for drill-only topics). */
  lesson_id: string | null;
}

export interface AbilityAssessment {
  current_level: "beginner" | "intermediate" | "advanced";
  evidence_level: "beginner" | "intermediate" | "advanced";
  attempts: number;
  correct: number;
  accuracy: number | null;
  source: string;
  next_evaluation: string;
}

export interface MasterySnapshot {
  language: string;
  topics: TopicMastery[];
  assessment: AbilityAssessment;
}

/** Per-topic mastery for one of the learner's languages (weakest first). */
export function useMastery(language: string | undefined) {
  return useQuery({
    queryKey: ["mastery", language],
    queryFn: () =>
      apiFetch<MasterySnapshot>(`/me/mastery?language=${language}`),
    enabled: Boolean(language),
  });
}
