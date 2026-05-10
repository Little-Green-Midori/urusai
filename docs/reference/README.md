# Reference

API / schema / config / module map / hardware baseline。

| 文件 | 內容 |
|---|---|
| [api.md](api.md) | FastAPI endpoints（`/ingest`、`/query`、`/healthz`）的 request / response schema |
| [config.md](config.md) | `.env` 變數對照 |
| [schemas.md](schemas.md) | Domain models：`EvidenceClaim`、`TimeRange`、`InventoryReport`、`AgentState`、`Notebook` 等 |
| [modules.md](modules.md) | `src/urusai/` 各 sub-package 職責與依賴方向 |
| [hardware.md](hardware.md) | 開發機規格基線、各模型 VRAM 估算 |
