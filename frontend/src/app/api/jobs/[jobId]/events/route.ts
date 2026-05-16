import { backend } from "@/lib/api";

/** Job progress SSE proxy (ingest job; same resumability + heartbeat discipline as run events). */
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 300;

export async function GET(
  req: Request,
  { params }: { params: Promise<{ jobId: string }> },
) {
  const { jobId } = await params;
  const url = backend(`/v1/jobs/${jobId}/events`);

  const headers = new Headers();
  const lastEventId = req.headers.get("last-event-id");
  if (lastEventId) headers.set("Last-Event-ID", lastEventId);

  return fetch(url, { method: "GET", headers, cache: "no-store" });
}
