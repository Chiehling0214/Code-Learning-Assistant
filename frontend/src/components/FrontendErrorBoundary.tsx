import { Component, type ErrorInfo, type ReactNode } from "react";

import { reportFrontendError } from "@/lib/monitoring";

export class FrontendErrorBoundary extends Component<
  { children: ReactNode },
  { hasError: boolean }
> {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    reportFrontendError(error, "frontend_error", info.componentStack ?? "");
  }

  render() {
    if (this.state.hasError) {
      return (
        <main className="flex min-h-screen items-center justify-center bg-background p-6">
          <div className="w-full max-w-md rounded-xl border bg-card p-6 text-center shadow-sm">
            <p className="page-kicker">Something went wrong</p>
            <h1 className="mt-2 text-xl font-semibold">This page could not be displayed.</h1>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              The error was recorded so an administrator can investigate it.
            </p>
            <button
              type="button"
              className="mt-5 h-10 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground"
              onClick={() => window.location.reload()}
            >
              Reload page
            </button>
          </div>
        </main>
      );
    }
    return this.props.children;
  }
}
