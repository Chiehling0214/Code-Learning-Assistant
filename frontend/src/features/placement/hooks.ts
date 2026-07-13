import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";

export interface PlacementChoice {
  id: string;
  text: string;
}

export interface PlacementMCQ {
  id: string;
  prompt: string;
  choices: PlacementChoice[];
}

export interface PlacementCoding {
  id: string;
  prompt: string;
  language: string;
  starter_code: string;
}

export interface Placement {
  track_id: string;
  status: "ready" | "completed";
  level: string | null;
  mcqs: PlacementMCQ[];
  coding: PlacementCoding[];
}

export interface MCQReview {
  id: string;
  prompt: string;
  choices: { id: string; text: string; is_correct: boolean }[];
  selected_choice_id: string | null;
  correct_choice_id: string | null;
  correct: boolean;
  explanation: string;
  points_earned: number;
  points_possible: number;
}

export interface CodingTestResult {
  index: number;
  passed: boolean;
  status?: string;
  input?: string;
  expected?: string;
  actual?: string;
  stderr?: string;
}

export interface CodingReview {
  id: string;
  prompt: string;
  passed: boolean;
  passed_cases: number;
  total_cases: number;
  code: string;
  language: string;
  tests: CodingTestResult[];
  reference_solution: string;
  points_earned: number;
  points_possible: number;
}

export interface PlacementBreakdown {
  percent: number;
  correct_mcqs: number;
  total_mcqs: number;
  passed_coding: number;
  total_coding: number;
  earned_points: number;
  total_points: number;
  mcq_weight: number;
  coding_weight: number;
  mcqs: MCQReview[];
  coding: CodingReview[];
}

export interface PlacementResult {
  level: string;
  percent: number;
  breakdown: PlacementBreakdown;
}

/** Generate (idempotent) then load the placement for a track. */
export function usePlacement(trackId: string | undefined) {
  return useQuery({
    queryKey: ["placement", trackId],
    queryFn: () => apiFetch<Placement>(`/me/tracks/${trackId}/placement`, { method: "POST" }),
    enabled: Boolean(trackId),
    staleTime: Infinity,
  });
}

export function useSubmitPlacement(trackId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (vars: { mcq_answers: Record<string, string>; code: Record<string, string> }) =>
      apiFetch<PlacementResult>(`/me/tracks/${trackId}/placement/submit`, {
        method: "POST",
        body: JSON.stringify(vars),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tracks"] });
      queryClient.invalidateQueries({ queryKey: ["placement", trackId] });
    },
  });
}
