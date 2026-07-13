import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";

export interface ReviewChoice {
  id: string;
  text: string;
  is_correct: boolean;
}

export interface ReviewPayload {
  kind: "mcq" | "exercise";
  // MCQ snapshot
  prompt?: string;
  choices?: ReviewChoice[];
  explanation?: string;
  quiz_title?: string;
  // Exercise snapshot
  exercise_id?: string;
  title?: string;
  language?: string;
}

export interface ReviewItem {
  id: string;
  source: "quiz" | "placement" | "exercise";
  payload: ReviewPayload;
  interval_days: number;
  due_at: string;
  lapses: number;
  passes: number;
  retired: boolean;
}

/** Reviews due right now. */
export function useDueReviews() {
  return useQuery({
    queryKey: ["reviews-due"],
    queryFn: () => apiFetch<{ due_count: number; items: ReviewItem[] }>("/me/review"),
  });
}

/** The full mistakes notebook (active + retired). */
export function useNotebook() {
  return useQuery({
    queryKey: ["reviews-all"],
    queryFn: () => apiFetch<{ items: ReviewItem[] }>("/me/review/all").then((r) => r.items),
  });
}

/** Report a review outcome; the schedule advances (or resets) server-side. */
export function useAnswerReview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ itemId, correct }: { itemId: string; correct: boolean }) =>
      apiFetch<ReviewItem>(`/me/review/${itemId}/answer`, {
        method: "POST",
        body: JSON.stringify({ correct }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reviews-due"] });
      queryClient.invalidateQueries({ queryKey: ["reviews-all"] });
      queryClient.invalidateQueries({ queryKey: ["today"] });
    },
  });
}
