import { ApiError } from "@/lib/api";
import { getIdToken } from "@/lib/firebase";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

/**
 * POST to a Server-Sent-Events endpoint and invoke `onChunk` per text delta.
 *
 * Pre-stream failures (quota, 402, 404…) arrive as normal JSON errors and throw
 * `ApiError`; a mid-stream `{"error": …}` event throws a plain `Error`.
 */
export async function streamSSE(
  path: string,
  body: unknown,
  onChunk: (text: string) => void,
): Promise<void> {
  const token = await getIdToken();
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  if (!response.ok || !response.body) {
    let detail = response.statusText;
    try {
      detail = (await response.json()).detail ?? detail;
    } catch {
      // non-JSON error body
    }
    throw new ApiError(response.status, detail);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() ?? "";
    for (const event of events) {
      const line = event.trim();
      if (!line.startsWith("data: ")) continue;
      const data = line.slice("data: ".length);
      if (data === "[DONE]") return;
      const payload = JSON.parse(data) as { text?: string; error?: string };
      if (payload.error) throw new Error(payload.error);
      if (payload.text) onChunk(payload.text);
    }
  }
}
