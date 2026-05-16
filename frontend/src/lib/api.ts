/**
 * Backend URL helper.
 *
 * URUSAI frontend runs on :3000 (Next.js dev); backend FastAPI on :8000.
 * Server-side fetches use absolute URL; route handlers proxy via fetch().
 *
 * Route handlers that stream SSE responses MUST declare runtime='nodejs',
 * dynamic='force-dynamic', and maxDuration=300 — the Edge runtime does not
 * support the Node.js streaming APIs used by the SSE encoder.
 */
export const BACKEND_URL =
  process.env.URUSAI_BACKEND_URL ?? "http://127.0.0.1:8000";

export function backend(path: string): string {
  return new URL(path, BACKEND_URL).toString();
}
