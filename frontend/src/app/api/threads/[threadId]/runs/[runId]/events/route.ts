import { backend } from "@/lib/api";

/**
 * SSE Data Stream Protocol proxy — frontend client to FastAPI backend.
 *
 * - Forwards Last-Event-ID for resumable streams.
 * - 300s maxDuration covers Vercel Pro; ignored when self-hosted.
 * - X-Accel-Buffering: no header set in next.config.ts; nginx-safe.
 */
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 300;

export async function GET(
  req: Request,
  { params }: { params: Promise<{ threadId: string; runId: string }> },
) {
  const { threadId, runId } = await params;
  const url = backend(`/v1/threads/${threadId}/runs/${runId}/events`);

  const headers = new Headers();
  const lastEventId = req.headers.get("last-event-id");
  if (lastEventId) headers.set("Last-Event-ID", lastEventId);
  const accept = req.headers.get("accept");
  if (accept) headers.set("Accept", accept);

  return fetch(url, { method: "GET", headers, cache: "no-store" });
}
