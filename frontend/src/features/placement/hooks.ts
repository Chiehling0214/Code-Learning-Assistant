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

export interface PlacementResult {
  level: string;
  percent: number;
  breakdown: Record<string, unknown>;
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
