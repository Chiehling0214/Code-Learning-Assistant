import { apiFetch } from "@/lib/api";

type FrontendErrorKind = "frontend_error" | "unhandled_rejection";

function errorDetails(value: unknown): { message: string; stack: string } {
  if (value instanceof Error) {
    return { message: value.message || value.name, stack: value.stack ?? "" };
  }
  if (typeof value === "string") return { message: value, stack: "" };
  try {
    return { message: JSON.stringify(value), stack: "" };
  } catch {
    return { message: "Unknown frontend error", stack: "" };
  }
}

export function reportFrontendError(
  value: unknown,
  kind: FrontendErrorKind = "frontend_error",
  extraStack = "",
) {
  const error = errorDetails(value);
  void apiFetch<void>("/monitoring/frontend-errors", {
    method: "POST",
    body: JSON.stringify({
      kind,
      message: error.message.slice(0, 2000),
      stack: [error.stack, extraStack].filter(Boolean).join("\n").slice(0, 6000),
      path: `${window.location.pathname}${window.location.search}`.slice(0, 500),
    }),
  }).catch(() => {
    // Monitoring must never create another visible application error.
  });
}

export function installGlobalErrorMonitoring() {
  window.addEventListener("error", (event) => {
    reportFrontendError(event.error ?? event.message);
  });
  window.addEventListener("unhandledrejection", (event) => {
    reportFrontendError(event.reason, "unhandled_rejection");
  });
}
