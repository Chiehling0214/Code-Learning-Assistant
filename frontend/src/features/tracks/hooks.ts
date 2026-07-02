import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import { useSessionStore } from "@/store/session";

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
      queryClient.setQueryData<Track[]>(["tracks"], (old = []) =>
        old.some((t) => t.id === track.id) ? old : [...old, track],
      );
      // Mark the session onboarded so the gate lets the learner into the app.
      const { user, setUser } = useSessionStore.getState();
      if (user && !user.onboarded) setUser({ ...user, onboarded: true });
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
