import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useSessionStore } from "@/store/session";

interface Profile {
  display_name: string | null;
  email: string | null;
  skill_level: string;
  is_admin: boolean;
}

const SKILL_LEVELS = ["beginner", "intermediate", "advanced"];

export function ProfilePage() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { signOut } = useAuth();
  const user = useSessionStore((s) => s.user);
  const setUser = useSessionStore((s) => s.setUser);
  const { data, isLoading } = useQuery({
    queryKey: ["profile"],
    queryFn: () => apiFetch<Profile>("/me/profile"),
  });

  const [displayName, setDisplayName] = useState("");
  const [skillLevel, setSkillLevel] = useState("beginner");
  const [saved, setSaved] = useState(false);

  const [confirmEmail, setConfirmEmail] = useState("");
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const deleteAccount = async () => {
    setDeleting(true);
    setDeleteError(null);
    try {
      await apiFetch<void>("/me", { method: "DELETE" });
      await signOut();
      navigate("/login", { replace: true });
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : "Could not delete the account");
      setDeleting(false);
    }
  };

  const emailMatches = confirmEmail.trim().toLowerCase() === (data?.email ?? "").toLowerCase();

  useEffect(() => {
    if (data) {
      setDisplayName(data.display_name ?? "");
      setSkillLevel(data.skill_level);
    }
  }, [data]);

  const mutation = useMutation({
    mutationFn: () =>
      apiFetch<Profile>("/me/profile", {
        method: "PUT",
        body: JSON.stringify({ display_name: displayName || null, skill_level: skillLevel }),
      }),
    onSuccess: (updated) => {
      queryClient.setQueryData(["profile"], updated);
      // Keep the header's name in sync.
      if (user) setUser({ ...user, displayName: updated.display_name });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    },
  });

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Profile</h1>
        <p className="text-muted-foreground">Manage your account details.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Account</CardTitle>
          <CardDescription>{isLoading ? "Loading…" : (data?.email ?? "—")}</CardDescription>
        </CardHeader>
        <CardContent>
          <form
            className="space-y-4"
            onSubmit={(e) => {
              e.preventDefault();
              mutation.mutate();
            }}
          >
            <div className="space-y-1.5">
              <label htmlFor="displayName" className="text-sm font-medium">
                Display name
              </label>
              <input
                id="displayName"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="Your name"
              />
            </div>

            <div className="space-y-1.5">
              <label htmlFor="skillLevel" className="text-sm font-medium">
                Skill level
              </label>
              <select
                id="skillLevel"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                value={skillLevel}
                onChange={(e) => setSkillLevel(e.target.value)}
              >
                {SKILL_LEVELS.map((level) => (
                  <option key={level} value={level}>
                    {level}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-3">
              <Button type="submit" disabled={mutation.isPending || isLoading}>
                {mutation.isPending ? "Saving…" : "Save changes"}
              </Button>
              {saved && <span className="text-sm text-muted-foreground">Saved ✓</span>}
              {mutation.isError && (
                <span className="text-sm text-destructive">Failed to save.</span>
              )}
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Plan</CardTitle>
          <CardDescription>
            Limits and usage live on the{" "}
            <Link to="/subscription" className="text-primary underline">
              Subscription page
            </Link>
            .
          </CardDescription>
        </CardHeader>
      </Card>

      <Card className="border-destructive/40">
        <CardHeader>
          <CardTitle className="text-lg text-destructive">Danger zone</CardTitle>
          <CardDescription>
            Deleting your account permanently removes all your data — languages, courses,
            submissions, quiz attempts, reviews, and chats. This cannot be undone.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          <p className="text-sm text-muted-foreground">
            Type your email (<span className="font-mono">{data?.email}</span>) to confirm:
          </p>
          <input
            className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            placeholder="you@example.com"
            value={confirmEmail}
            onChange={(e) => setConfirmEmail(e.target.value)}
          />
          <Button
            variant="destructive"
            size="sm"
            disabled={!emailMatches || deleting}
            onClick={deleteAccount}
          >
            {deleting ? "Deleting…" : "Delete my account"}
          </Button>
          {deleteError && <p className="text-sm text-destructive">{deleteError}</p>}
        </CardContent>
      </Card>
    </div>
  );
}
