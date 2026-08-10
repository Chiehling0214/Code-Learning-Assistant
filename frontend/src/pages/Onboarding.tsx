import { ArrowRight, Code2 } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { Card, CardContent } from "@/components/ui/card";
import { useLanguages } from "@/features/content/hooks";
import { useAddTrack } from "@/features/tracks/hooks";

/** First-login screen: "What do you want to study?" — pick a language. */
export function OnboardingPage() {
  const navigate = useNavigate();
  const { data: languages = [], isLoading } = useLanguages();
  const addTrack = useAddTrack();

  const pick = (languageId: string) =>
    addTrack.mutate(languageId, {
      // Straight into the placement test for the new track.
      onSuccess: (track) => navigate(`/tracks/${track.id}/placement`, { replace: true }),
    });

  return (
    <div className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center gap-9 p-6 py-14">
      <div className="mx-auto max-w-xl space-y-3 text-center">
        <span className="mx-auto flex size-10 items-center justify-center rounded-xl bg-primary text-primary-foreground"><Code2 className="size-5" /></span>
        <p className="page-kicker pt-3">Let’s set up your path</p>
        <h1 className="page-heading">What would you like to learn?</h1>
        <p className="leading-6 text-muted-foreground">Choose a language. A short placement check will help us find the right starting point.</p>
      </div>

      {isLoading ? (
        <p className="text-center text-muted-foreground">Loading languages…</p>
      ) : languages.length === 0 ? (
        <p className="text-center text-sm text-muted-foreground">
          No languages are available yet.
        </p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {languages.map((lang) => (
            <Card key={lang.id} className="group overflow-hidden transition-[border-color,transform] hover:-translate-y-0.5 hover:border-primary/35">
              <button className="block min-h-20 w-full text-left" disabled={addTrack.isPending} onClick={() => pick(lang.id)}>
                <CardContent className="flex min-h-20 items-center gap-4 px-5 py-0 sm:px-6 sm:py-0">
                  <span className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-secondary font-mono text-sm font-semibold leading-none text-primary">{lang.name.slice(0, 2).toUpperCase()}</span>
                  <span className="flex min-h-10 flex-1 items-center text-lg font-medium leading-none">{lang.name}</span>
                  <ArrowRight className="block size-4 shrink-0 text-muted-foreground group-hover:text-primary" />
                </CardContent>
              </button>
            </Card>
          ))}
        </div>
      )}

      {addTrack.isError && (
        <p className="text-center text-sm text-destructive">
          {addTrack.error instanceof Error ? addTrack.error.message : "Could not start"}
        </p>
      )}
    </div>
  );
}
