import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";

export interface Entitlements {
  plan: "free" | "pro";
  max_languages: number;
  tutor_daily: number;
  generations_daily: number;
  languages_used: number;
  tutor_used_today: number;
  generations_used_today: number;
}

/** The current user's plan limits and today's usage (Sprint 13). */
export function useEntitlements() {
  return useQuery({
    queryKey: ["entitlements"],
    queryFn: () => apiFetch<Entitlements>("/me/entitlements"),
  });
}
