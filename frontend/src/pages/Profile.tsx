import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";

interface Profile {
  display_name: string | null;
  email: string | null;
  skill_level: string;
  is_admin: boolean;
}

const SKILL_LEVELS = ["beginner", "intermediate", "advanced"];

export function ProfilePage() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["profile"],
    queryFn: () => apiFetch<Profile>("/me/profile"),
  });

  const [displayName, setDisplayName] = useState("");
  const [skillLevel, setSkillLevel] = useState("beginner");
  const [saved, setSaved] = useState(false);

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
    </div>
  );
}
