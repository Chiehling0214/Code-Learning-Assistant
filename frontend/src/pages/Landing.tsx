import { ArrowRight, Check, Code2, RotateCcw, TerminalSquare } from "lucide-react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";

const FEATURES = [
  {
    number: "01",
    title: "A path built around you",
    body: "Start at the right level and follow a focused course instead of piecing together random tutorials.",
  },
  {
    number: "02",
    title: "Practice in the browser",
    body: "Write, run, and submit real code. Get a useful hint when you need one, without being handed the answer.",
  },
  {
    number: "03",
    title: "Remember what you learn",
    body: "Missed questions return on a spaced schedule, so weak spots become skills you can actually use.",
  },
];

export function LandingPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b bg-card/60">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-5 sm:px-8">
          <Link to="/" className="flex items-center gap-2.5 font-semibold tracking-[-0.02em]">
            <span className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <Code2 className="size-4" strokeWidth={2.2} />
            </span>
            <span className="text-sm sm:text-base">Code Learning Assistant</span>
          </Link>
          <Button asChild variant="ghost" size="sm">
            <Link to="/login">Sign in <ArrowRight className="size-4" /></Link>
          </Button>
        </div>
      </header>

      <main>
        <section className="mx-auto grid max-w-6xl items-center gap-14 px-5 py-16 sm:px-8 sm:py-24 lg:grid-cols-[1fr_0.92fr] lg:py-28">
          <div>
            <p className="page-kicker">A practical way to learn programming</p>
            <h1 className="max-w-2xl text-5xl font-semibold leading-[1.04] tracking-[-0.055em] sm:text-6xl">
              Learn by building, not by watching.
            </h1>
            <p className="mt-6 max-w-xl text-lg leading-8 text-muted-foreground">
              A personal curriculum of clear lessons, hands-on exercises, and timely review—adjusted as your skills grow.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <Button asChild size="lg">
                <Link to="/login">Start learning <ArrowRight className="size-4" /></Link>
              </Button>
              <span className="text-sm text-muted-foreground">Choose a language. We’ll find your starting point.</span>
            </div>
          </div>

          <div className="relative">
            <div className="rounded-2xl border bg-card p-4 shadow-card sm:p-5">
              <div className="mb-5 flex items-center justify-between border-b pb-4">
                <div>
                  <p className="text-xs font-medium uppercase tracking-[0.12em] text-muted-foreground">Today</p>
                  <p className="mt-1 font-semibold">Python foundations</p>
                </div>
                <span className="rounded-full bg-primary/10 px-2.5 py-1 text-xs font-medium text-primary">3 of 5 done</span>
              </div>
              <div className="space-y-2.5">
                <div className="flex items-center gap-3 rounded-xl bg-secondary/60 p-3.5 text-sm text-muted-foreground">
                  <span className="flex size-7 items-center justify-center rounded-full bg-primary text-primary-foreground"><Check className="size-4" /></span>
                  Variables and basic types
                </div>
                <div className="flex items-center gap-3 rounded-xl border border-primary/25 bg-primary/[0.035] p-3.5 text-sm font-medium">
                  <span className="flex size-7 items-center justify-center rounded-full bg-primary/10 text-primary"><TerminalSquare className="size-4" /></span>
                  Practice: validate user input
                  <ArrowRight className="ml-auto size-4 text-primary" />
                </div>
                <div className="flex items-center gap-3 rounded-xl p-3.5 text-sm text-muted-foreground">
                  <span className="flex size-7 items-center justify-center rounded-full bg-secondary"><RotateCcw className="size-4" /></span>
                  Review functions and scope
                </div>
              </div>
              <div className="mt-5 rounded-xl bg-[#1d2420] p-4 font-mono text-xs leading-6 text-[#d8e3dc]">
                <span className="text-[#8eb89e]">def</span> validate(name):<br />
                &nbsp;&nbsp;<span className="text-[#8eb89e]">return</span> bool(name.strip())
              </div>
            </div>
            <p className="mt-3 text-center text-xs text-muted-foreground">Built-in feedback keeps you moving without taking over.</p>
          </div>
        </section>

        <section className="border-y bg-card">
          <div className="mx-auto grid max-w-6xl px-5 sm:px-8 md:grid-cols-3">
            {FEATURES.map((feature, index) => (
              <article key={feature.number} className={`py-9 md:px-8 md:py-12 ${index > 0 ? "border-t md:border-l md:border-t-0" : ""}`}>
                <span className="font-mono text-xs text-primary/60">{feature.number}</span>
                <h2 className="mt-3 text-lg font-semibold tracking-[-0.025em]">{feature.title}</h2>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">{feature.body}</p>
              </article>
            ))}
          </div>
        </section>
      </main>

      <footer className="mx-auto flex max-w-6xl items-center justify-between px-5 py-8 text-sm text-muted-foreground sm:px-8">
        <span>Code Learning Assistant</span>
        <span>Learn at your own pace.</span>
      </footer>
    </div>
  );
}
