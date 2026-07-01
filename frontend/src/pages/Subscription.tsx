import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useCheckout, useSubscription } from "@/features/billing/hooks";

const PRO_FEATURES = [
  "AI Tutor hints on your code",
  "Priority access to new courses",
  "Unlimited practice generation",
];

export function SubscriptionPage() {
  const { data: sub, isLoading } = useSubscription();
  const checkout = useCheckout();

  const active = sub?.active ?? false;

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Subscription</h1>
        <p className="text-muted-foreground">Manage your plan and billing.</p>
      </div>

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
