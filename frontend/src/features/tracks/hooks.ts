import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";

export interface Track {
  id: string;
  language_id: string;
  language_name: string;
  language_slug: string;
  level: string | null;
  status: string;
}

export function useTracks() {
  return useQuery({ queryKey: ["tracks"], queryFn: () => apiFetch<Track[]>("/me/tracks") });
}

export function useAddTrack() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (languageId: string) =>
      apiFetch<Track>("/me/tracks", {
        method: "POST",
        body: JSON.stringify({ language_id: languageId }),
      }),
    onSuccess: (track) => {
      // Write the new track into the cache immediately so the onboarding gate
      // doesn't briefly see an empty list (which would bounce back to onboarding).
      queryClient.setQueryData<Track[]>(["tracks"], (old = []) =>
        old.some((t) => t.id === track.id) ? old : [...old, track],
      );
      queryClient.invalidateQueries({ queryKey: ["me"] });
    },
  });
}

export function useRemoveTrack() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (trackId: string) => apiFetch<void>(`/me/tracks/${trackId}`, { method: "DELETE" }),
    onSuccess: (_data, trackId) => {
      queryClient.setQueryData<Track[]>(["tracks"], (old = []) =>
        old.filter((t) => t.id !== trackId),
      );
      queryClient.invalidateQueries({ queryKey: ["me"] });
    },
  });
}
