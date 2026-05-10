# How-to：新增一個 channel

寫一個從影片抽 evidence 的新 channel。

## 設計前先讀

- [`../reference/modules.md`](../reference/modules.md)：`urusai.channels` 結構、`Channel` Protocol
- [`../reference/schemas.md`](../reference/schemas.md)：`EvidenceClaim` 必填欄位

## 實作步驟

### 1. 確認 slot 沒被佔用

打開 [`src/urusai/channels/`](../../src/urusai/channels/)，確認你要的 slot 沒已存在 module。

### 2. 寫 channel module

新檔 `src/urusai/channels/<your_channel>.py`：

```python
"""<簡述 channel 用途>。"""
from __future__ import annotations

from pathlib import Path

from urusai.domain.evidence import (
    ConfidenceMarker,
    EvidenceClaim,
    TimeRange,
)


class YourChannel:
    name = "<notebook_name>"  # "dialogue" / "on_screen_text" / "scene" / "sound_event" / "holistic"

    def __init__(self, **kwargs) -> None:
        # 工具初始化參數（model size / threshold / etc.）
        ...

    async def extract(
        self,
        source: Path,
        time_range: tuple[float, float] | None = None,
        **kwargs,
    ) -> list[EvidenceClaim]:
        # 1. 跑工具，拿 raw 觀察
        # 2. 把每條觀察包成 EvidenceClaim
        # 3. 回傳 list

        claims: list[EvidenceClaim] = []
        # ... your logic ...
        claims.append(
            EvidenceClaim(
                channel=self.name,
                time_range=TimeRange(start=..., end=...),
                claim_text=...,
                raw_quote=...,
                confidence=ConfidenceMarker.CLEAR,  # 或 BLURRY / INFERRED
                source_tool=f"<tool>:<version>:<setting>",
            )
        )
        return claims

    def unload(self) -> None:
        """釋放 GPU / 大型 resource（如有需要）。"""
        ...
```

### 3. `source_tool` 命名規則

**必須**含工具名 + 版本 + 主要設定，能讓 trace 讀者一眼識別：

| 範例 | 說明 |
|---|---|
| `faster-whisper:large-v3-turbo:zh` | model size + 偵測到的 lang |
| `PaddleOCR:3.4.0:PP-OCRv5` | 套件版本 + model 系列 |
| `PySceneDetect:ContentDetector:t=27.0` | detector 類別 + threshold |

不能只寫 `whisper` / `ocr` 這種。

### 4. `confidence` 怎麼標

不要全標 `clear`。判斷依據：

- **CLEAR**：工具自評信心高（例如 ASR 段 avg_logprob > -0.7、OCR 信心 > 0.9）
- **BLURRY**：工具自評信心中下、可能有錯（avg_logprob ∈ [-1.0, -0.7]、OCR 信心 [0.5, 0.9]）
- **INFERRED**：本條不是直接觀察、是工具推斷

### 5. 在 `inventory_probe` 加觸發條件

如果新 channel 應該由 inventory 條件啟動，編輯 [`src/urusai/channels/inventory_probe.py`](../../src/urusai/channels/inventory_probe.py) 的 `run_inventory_probe()`：

```python
# 既有：
if has_speech and has_manual_subs:
    dispatched.append("SubtitleChannel")
elif has_speech:
    dispatched.append("ASRChannel")
else:
    skipped["ASRChannel"] = "no speech detected"

# 加上你的：
if <your-condition>:
    dispatched.append("YourChannel")
else:
    skipped["YourChannel"] = "<reason>"
```

### 6. 在 `routes.py` ingest_endpoint 中接 dispatch

編輯 [`src/urusai/api/routes.py`](../../src/urusai/api/routes.py) 的 `ingest_endpoint()`：

```python
if "YourChannel" in dispatched:
    yc = YourChannel()
    try:
        claims = await yc.extract(source_path)
        state.absorb(claims)
    finally:
        yc.unload()  # 如果有 GPU resource
```

### 7. 寫測試

新檔 `tests/channels/test_<your_channel>.py`：

```python
import pytest
from pathlib import Path

from urusai.channels.<your_channel> import YourChannel


@pytest.mark.asyncio
async def test_extract_returns_evidence_claims(tmp_video_fixture):
    ch = YourChannel()
    try:
        claims = await ch.extract(tmp_video_fixture)
    finally:
        ch.unload()

    assert all(c.channel == ch.name for c in claims)
    assert all(c.source_tool.startswith("<expected-prefix>") for c in claims)
```

跑測試：

```bash
pytest tests/channels/test_<your_channel>.py
```

### 8. Lint + format

```bash
ruff check .
ruff format .
```

### 9. 更新文件

- [`docs/reference/modules.md`](../reference/modules.md) channel 表格加一行
- [`CHANGELOG.md`](../../CHANGELOG.md) 加條目

### 10. Commit

依 [`CONTRIBUTING.md`](../../CONTRIBUTING.md#commit-message-規則) 的 Conventional Commits：

```
feat(channels): add <YourChannel> for <slot>

- ...
- ...
```

## 紀律提醒

- 不要為了「答得出來」就把 `confidence` 全標 `clear`。
- 不要把工具的 raw 輸出直接當 `claim_text`；應該保留 `raw_quote` + 寫對應的 `claim_text`。
- 不要 hardcode model 路徑；走 settings / 環境變數。
- 不要在 channel 內做整合判斷——channel 是觀察器，judgement 留給整合代理人。
