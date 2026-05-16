import Link from "next/link";

export default function HomePage() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <h1 className="text-3xl font-semibold tracking-tight">URUSAI</h1>
      <p className="mt-2 text-sm text-zinc-500">
        Video RAG agent · refuses to answer without grounded evidence
      </p>

      <section className="mt-10 space-y-3">
        <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">
          backend health
        </h2>
        <ul className="space-y-1 font-mono text-sm">
          <li>
            <Link href="/api/healthz" className="underline">
              /api/healthz
            </Link>
          </li>
          <li>
            <Link href="/api/readyz" className="underline">
              /api/readyz
            </Link>
          </li>
        </ul>
      </section>
    </main>
  );
}
