import { useEffect, useRef } from "react";
import { useSearchParams } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useCheckout, useConfirmCheckout, useSubscription } from "@/features/billing/hooks";
import { useEntitlements } from "@/features/entitlements/hooks";

const PRO_FEATURES = [
  "More AI Tutor hints per day",
  "Priority access to new courses",
  "A higher daily content-generation quota",
  "Study more languages at once",
];

function UsageRow({ label, used, limit }: { label: string; used: number; limit: number }) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">
        {used} / {limit}
      </span>
    </div>
  );
}

export function SubscriptionPage() {
  const { data: sub, isLoading } = useSubscription();
  const { data: ent } = useEntitlements();
  const checkout = useCheckout();
  const confirm = useConfirmCheckout();
  const [params, setParams] = useSearchParams();
  const confirmedRef = useRef(false);

  // After returning from Stripe Checkout (?session_id=…), activate the plan via
  // the API — no webhook needed. Runs once, then strips the query params.
  const sessionId = params.get("session_id");
  useEffect(() => {
    if (sessionId && !confirmedRef.current) {
      confirmedRef.current = true;
      confirm.mutate(sessionId, {
        onSettled: () => setParams({}, { replace: true }),
      });
    }
  }, [sessionId, confirm, setParams]);

  const active = sub?.active ?? false;

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Subscription</h1>
        <p className="text-muted-foreground">Manage your plan and billing.</p>
      </div>

      {confirm.isPending && (
        <p className="text-sm text-muted-foreground">Confirming your payment…</p>
      )}
      {confirm.isSuccess && (
        <p className="text-sm font-medium text-green-600">
          Payment confirmed — welcome to Pro! 🎉
        </p>
      )}
      {confirm.isError && (
        <p className="text-sm text-destructive">
          {confirm.error instanceof Error
            ? confirm.error.message
            : "Could not confirm your payment."}
        </p>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Current plan</CardTitle>
          <CardDescription>
            {isLoading
              ? "Loading…"
              : active
                ? `Pro — active${sub?.current_period_end ? ` until ${new Date(sub.current_period_end).toLocaleDateString()}` : ""}`
                : "Free"}
          </CardDescription>
        </CardHeader>
        {ent && (
          <CardContent className="space-y-2">
            <UsageRow label="Languages" used={ent.languages_used} limit={ent.max_languages} />
            <UsageRow label="AI Tutor hints today" used={ent.tutor_used_today} limit={ent.tutor_daily} />
            <UsageRow
              label="Content generations today"
              used={ent.generations_used_today}
              limit={ent.generations_daily}
            />
          </CardContent>
        )}
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">CodePath Pro</CardTitle>
          <CardDescription>Unlock premium features.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <ul className="list-inside list-disc text-sm text-muted-foreground">
            {PRO_FEATURES.map((f) => (
              <li key={f}>{f}</li>
            ))}
          </ul>
          {active ? (
            <p className="text-sm font-medium text-green-600">You're subscribed. Thank you! 🎉</p>
          ) : (
            <div className="space-y-2">
              <Button disabled={checkout.isPending} onClick={() => checkout.mutate()}>
                {checkout.isPending ? "Redirecting…" : "Subscribe with Stripe"}
              </Button>
              {checkout.isError && (
                <p className="text-sm text-destructive">
                  {checkout.error instanceof Error
                    ? checkout.error.message
                    : "Could not start checkout"}
                </p>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
