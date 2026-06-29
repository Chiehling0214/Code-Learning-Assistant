import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { isFirebaseConfigured } from "@/lib/firebase";

export function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Sign in</CardTitle>
          <CardDescription>
            {isFirebaseConfigured
              ? "Sign in with your account to continue."
              : "Firebase is not configured — running in development mode."}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Button className="w-full" disabled={!isFirebaseConfigured}>
            Continue with Firebase
          </Button>
          <Button asChild variant="outline" className="w-full">
            <Link to="/dashboard">Continue to dashboard</Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
