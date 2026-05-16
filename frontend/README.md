# URUSAI frontend

Next.js 16 (App Router) + React 19 + Vercel AI SDK v5 + Tailwind v4 + shadcn/ui (base-ui).

## Local development

```bash
# From repo root (recommended; monorepo workspace handles deps):
pnpm install
pnpm --filter @urusai/frontend dev

# Or directly inside frontend/:
cd frontend
pnpm dev
```

Dev server at http://localhost:3000.

## Backend dependency

`URUSAI_BACKEND_URL` env var (defaults `http://127.0.0.1:8000`). The backend FastAPI app must be running for `/api/*` proxies to work:

```bash
cd ../backend
conda activate urusai
uvicorn urusai.api.main:app --reload --port 8000
```

## Deployment

URUSAI defaults to self-hosting (Docker or VPS). SSE streams typically run 30s–3min; Vercel Pro tops out at 300s, Hobby at 10s, Edge at 25s.

API route handlers under `src/app/api/**/*.ts` declare:

```typescript
export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';
export const maxDuration = 300;   // Pro ceiling; self-host ignores
```

For nginx reverse proxy, the `X-Accel-Buffering: no` header is set on streaming routes via `next.config.ts`.
