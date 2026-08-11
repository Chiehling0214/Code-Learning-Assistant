import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "@/App";
import { FrontendErrorBoundary } from "@/components/FrontendErrorBoundary";
import "@/index.css";
import { installGlobalErrorMonitoring } from "@/lib/monitoring";

installGlobalErrorMonitoring();

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Root element #root not found");
}

createRoot(rootElement).render(
  <StrictMode>
    <FrontendErrorBoundary>
      <App />
    </FrontendErrorBoundary>
  </StrictMode>,
);
