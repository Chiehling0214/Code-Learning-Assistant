import DOMPurify from "dompurify";
import { marked } from "marked";

/**
 * Render a markdown string to sanitized HTML.
 *
 * `marked` parses to HTML; `DOMPurify` strips any dangerous markup so the result
 * is safe to inject via `dangerouslySetInnerHTML`.
 */
export function renderMarkdown(markdown: string): string {
  const html = marked.parse(markdown ?? "", { async: false }) as string;
  return DOMPurify.sanitize(html);
}
