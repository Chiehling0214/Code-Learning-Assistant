import hljs from "highlight.js/lib/core";
import cpp from "highlight.js/lib/languages/cpp";
import java from "highlight.js/lib/languages/java";
import javascript from "highlight.js/lib/languages/javascript";
import python from "highlight.js/lib/languages/python";
import { useEffect, useRef } from "react";

import { renderMarkdown } from "@/lib/markdown";
import { cn } from "@/lib/utils";

hljs.registerLanguage("c", cpp);
hljs.registerLanguage("cpp", cpp);
hljs.registerLanguage("java", java);
hljs.registerLanguage("javascript", javascript);
hljs.registerLanguage("js", javascript);
hljs.registerLanguage("python", python);
hljs.registerLanguage("py", python);

// Shared prose styling for rendered Markdown (inline code + fenced code blocks).
const PROSE =
  "markdown-content prose-sm max-w-none " +
  "[&_h1]:mb-3 [&_h1]:text-2xl [&_h1]:font-bold [&_h2]:mb-2 [&_h2]:mt-4 [&_h2]:text-xl " +
  "[&_h2]:font-semibold [&_p]:my-2 [&_ul]:my-2 [&_ul]:list-disc [&_ul]:pl-5 " +
  "[&_pre]:my-3";

/** Renders a Markdown string (with fenced code blocks) as sanitized HTML. */
export function Markdown({ content, className }: { content: string; className?: string }) {
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;
    const cleanups: Array<() => void> = [];

    root.querySelectorAll("pre code").forEach((code) => {
      const rawCode = code.textContent ?? "";
      if (!(code as HTMLElement).dataset.highlighted) {
        hljs.highlightElement(code as HTMLElement);
      }

      const languageClass = [...code.classList].find((name) => name.startsWith("language-"));
      const language = languageClass?.replace("language-", "") || "code";
      const toolbar = document.createElement("div");
      toolbar.className = "code-toolbar";

      const label = document.createElement("span");
      label.textContent = language;
      const copy = document.createElement("button");
      copy.type = "button";
      copy.textContent = "Copy";
      copy.setAttribute("aria-label", "Copy code");
      const onCopy = async () => {
        await navigator.clipboard.writeText(rawCode);
        copy.textContent = "Copied";
        window.setTimeout(() => { copy.textContent = "Copy"; }, 1400);
      };
      copy.addEventListener("click", onCopy);
      toolbar.append(label, copy);
      code.parentElement?.prepend(toolbar);
      cleanups.push(() => {
        copy.removeEventListener("click", onCopy);
        toolbar.remove();
      });
    });

    return () => cleanups.forEach((cleanup) => cleanup());
  }, [content]);

  return (
    <div
      ref={rootRef}
      className={cn(PROSE, className)}
      dangerouslySetInnerHTML={{ __html: renderMarkdown(content) }}
    />
  );
}
