import { renderMarkdown } from "@/lib/markdown";
import { cn } from "@/lib/utils";

// Shared prose styling for rendered Markdown (inline code + fenced code blocks).
const PROSE =
  "markdown-content prose-sm max-w-none " +
  "[&_h1]:mb-3 [&_h1]:text-2xl [&_h1]:font-bold [&_h2]:mb-2 [&_h2]:mt-4 [&_h2]:text-xl " +
  "[&_h2]:font-semibold [&_p]:my-2 [&_ul]:my-2 [&_ul]:list-disc [&_ul]:pl-5 " +
  "[&_pre]:my-3";

/** Renders a Markdown string (with fenced code blocks) as sanitized HTML. */
export function Markdown({ content, className }: { content: string; className?: string }) {
  return (
    <div
      className={cn(PROSE, className)}
      dangerouslySetInnerHTML={{ __html: renderMarkdown(content) }}
    />
  );
}
