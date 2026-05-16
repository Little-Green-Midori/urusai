# Contributing

## Development setup

```bash
git clone https://github.com/Little-Green-Midori/urusai.git
cd urusai
docker compose up -d           # Postgres + Milvus + etcd + MinIO + Attu

# Backend
cd backend
conda activate urusai          # or your venv equivalent
pip install -e ".[dev]"
cp .env.example .env           # fill in GEMINI_API_KEY at minimum
alembic upgrade head
uvicorn urusai.api.main:app --reload --port 8000

# Frontend (from repo root)
cd ..
pnpm install
pnpm --filter @urusai/frontend dev
```

### System requirements

- Python 3.11+
- Node.js 24+
- `ffmpeg`, `yt-dlp` on `PATH`
- CUDA-capable GPU recommended for local ASR

## Code style

- **Python**: see `backend/pyproject.toml` `[tool.ruff]`; line-length 100, target Python 3.11.
- **Type hints**: required on all public functions.
- **Pydantic**: v2 syntax only (no `.dict()`, `.parse_obj()`, `class Config:`).
- **TypeScript**: see `frontend/tsconfig.json`; strict mode on.
- **Comment language**: zh-TW + technical English jargon for backend; English for frontend public-facing strings.

## Testing

```bash
cd backend
pytest
ruff check src/ tests/

# from repo root
pnpm --filter @urusai/frontend typecheck
pnpm --filter @urusai/frontend build
```

## Commit messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>
```

Common types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`.
Common scopes: `agent`, `channels`, `api`, `db`, `rag`, `providers`, `frontend`.

Author yourself in commits — do not add tool-attribution trailers.

## Pull requests

1. Fork (if not a maintainer).
2. Branch: `feat/<name>`, `fix/<name>`, `docs/<name>`.
3. Implement + tests + relevant doc updates.
4. Verify: `ruff check .`, `pytest`, frontend `typecheck` + `build`.
5. Open PR with:
   - What problem the PR solves (link issues if any)
   - Approach summary
   - Verification method
   - Affected modules

`main` only accepts reviewed PRs.

## Adding a new channel provider

Channels follow a `Channel + Provider` registry pattern.

1. Implement the `Provider` Protocol (`name`, `channel`, `config_class`, `async extract`, `unload`) in `backend/src/urusai/channels/<channel>/<provider>.py`.
2. Add `@ChannelRegistry.register(channel=..., name=...)` decorator.
3. Import the new module in `backend/src/urusai/channels/<channel>/__init__.py` to trigger registration.
4. Every emitted `EvidenceClaim` must carry a `source_tool` string (tool name + version + key config) and a `source_spec` triple (channel / provider / config dump).
5. Set `confidence` honestly — don't blanket-mark `clear`.
6. Add unit tests under `backend/tests/channels/`.
