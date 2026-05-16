import { backend } from "@/lib/api";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  return fetch(backend("/healthz"), { cache: "no-store" });
}
