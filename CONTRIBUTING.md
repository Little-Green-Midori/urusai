# 貢獻指南

歡迎 issue / PR。

## 目錄

- [開發環境](#開發環境)
- [程式碼規範](#程式碼規範)
- [Commit message 規則](#commit-message-規則)
- [PR 流程](#pr-流程)
- [文件貢獻](#文件貢獻)

---

## 開發環境

### 系統需求

- Python 3.11+
- `ffmpeg`、`yt-dlp` 在 `PATH` 上
- CUDA-capable GPU（建議；本地 ASR 需要）

### 安裝

```bash
git clone https://github.com/Little-Green-Midori/urusai.git
cd urusai
python -m venv .venv
source .venv/bin/activate     # Windows PowerShell：.venv\Scripts\Activate.ps1
pip install -e .[dev]
cp .env.example .env
# 編輯 .env、至少填 GEMINI_API_KEY
```

### 跑測試

```bash
pytest
```

### Lint / format

```bash
ruff check .
ruff format .
```

### 跑開發 UI

```bash
streamlit run streamlit_app.py
```

### 跑 API server

```bash
uvicorn urusai.api.main:app --reload
```

---

## 程式碼規範

- **Python style**：依 `pyproject.toml` 內 `[tool.ruff]` 設定，line-length 100，target Python 3.11。
- **Type hints**：所有 public function 必須帶 type hints。
- **Pydantic**：domain 層用 v2 syntax，避免 deprecated pattern（`.dict()` / `.parse_obj()` / `class Config:` 等）。
- **註解語言**：source code 註解 zh-TW + 必要英文 jargon；docstring 同。docs 預設 zh-TW。

---

## Commit message 規則

採用 [Conventional Commits](https://www.conventionalcommits.org/)：

```
<type>(<scope>): <subject>

<body>

<footer>
```

常用 type：

- `feat`：新功能
- `fix`：bug 修正
- `docs`：純文件變更
- `refactor`：重構，無行為變更
- `test`：測試新增 / 修改
- `chore`：build / config / dep 變更
- `perf`：效能改善

scope 範例：`agent`、`channels`、`api`、`store`、`ui`、`docs`。

不在 commit message 中加 AI 模型相關 trailer。

---

## PR 流程

1. Fork repo（如非主 repo 維護者）。
2. 建分支：`feat/short-name`、`fix/short-name`、`docs/short-name` 等。
3. 寫 code + 測試 + 文件。
4. `ruff check .` + `pytest` 通過。
5. 推到分支、開 PR。
6. PR 描述包含：
   - 解決什麼問題（連結 issue 如有）
   - 技術 approach 摘要
   - 測試 / 驗證方式
   - 影響的模組

主分支（`main`）僅接受通過 review 的 PR。

---

## 開新 channel

實作步驟：

1. 繼承 `urusai.channels.base.Channel` Protocol（`name`、`async extract`）
2. 產出的每條 `EvidenceClaim` 必須帶 `source_tool`（含工具名 + 版本 / 設定）
3. 預設 `confidence_marker` 必須合理（不要全標 `clear`）
4. 在 `inventory_probe` 加入啟動條件
5. 在 `routes.py` ingest_endpoint 中接 dispatch
6. 寫 unit test
7. 更新 `docs/reference/modules.md` + `CHANGELOG.md`

詳見 [`docs/how-to/add-a-new-channel.md`](docs/how-to/add-a-new-channel.md)。

---

## 文件貢獻

- 文件語言預設 zh-TW；技術名詞（model id、API name、套件名、command）保留英文。
- 文件描述對應 `src/` 內已實作 module；code 改了文件要同步改。
- 不寫尚未實作的功能；對外部工具的版本 / API 描述必須能 cite source URL。
