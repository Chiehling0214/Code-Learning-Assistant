import { useMutation, useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";

export interface Subscription {
  plan: string;
  status: string;
  active: boolean;
  current_period_end: string | null;
}

export function useSubscription() {
  return useQuery({
    queryKey: ["subscription"],
    queryFn: () => apiFetch<Subscription>("/subscription"),
  });
}

/** Start Stripe checkout and redirect the browser to the hosted session. */
export function useCheckout() {
  return useMutation({
    mutationFn: () =>
      apiFetch<{ checkout_url: string }>("/subscription/checkout", { method: "POST" }),
    onSuccess: (data) => {
      window.location.href = data.checkout_url;
    },
  });
}
