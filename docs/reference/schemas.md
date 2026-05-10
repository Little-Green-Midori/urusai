# Domain schemas

`urusai.domain` 內的 Pydantic models 與 protocols。所有 channel / agent / store 共用這些型別。

> Source: [`src/urusai/domain/`](../../src/urusai/domain/)

## EvidenceClaim

Atomic 觀察單元。每個 final answer 中的事實聲明都必須 cite 一條或多條 `EvidenceClaim`。

```python
class EvidenceClaim(BaseModel):
    channel: str
    time_range: TimeRange
    claim_text: str
    raw_quote: str | None = None
    confidence: ConfidenceMarker
    source_tool: str
    inference_strength: InferenceStrength | None = None
    inference_chain: list[str] | None = None
```

| 欄位 | 型別 | 說明 |
|---|---|---|
| `channel` | `str` | 對應筆記名稱（`"dialogue"` / `"on_screen_text"` / `"scene"` / `"sound_event"` / `"holistic"`）|
| `time_range` | `TimeRange` | 觀察的時間段（秒）|
| `claim_text` | `str` | 觀察內容（文字描述）|
| `raw_quote` | `str?` | 原始引文（如 ASR 逐字稿、OCR 出的字）|
| `confidence` | `ConfidenceMarker` | 觀察清晰度自標（`clear` / `blurry` / `inferred`）|
| `source_tool` | `str` | 工具識別字，**必含版本 / 主要設定**（範例：`"faster-whisper:large-v3-turbo:zh"`）|
| `inference_strength` | `InferenceStrength?` | 若是推論 claim，標推論強度 |
| `inference_chain` | `list[str]?` | 若是推論 claim，附 chain 步驟 |

### 觀察 vs 推論

- **觀察 claim**：`raw_quote` 應有；`inference_strength` / `inference_chain` 為 null。
- **推論 claim**：兩個 inference 欄位必填；推論強度三級：

```python
class InferenceStrength(str, Enum):
    STRONG = "strong"   # 觀察直接蘊含結論
    WEAK = "weak"       # 觀察可疑但傾向某結論
    GUESS = "guess"     # observation 不足
```

### 信心 marker

```python
class ConfidenceMarker(str, Enum):
    CLEAR = "clear"      # 觀察清楚（高信心 ASR 段、清晰 OCR）
    BLURRY = "blurry"    # 觀察模糊（低信心 ASR、糊掉的字、遠景人物）
    INFERRED = "inferred" # 推論出來的、不是直接觀察到
```

## TimeRange

```python
class TimeRange(BaseModel):
    start: float = Field(..., ge=0)
    end: float = Field(..., ge=0)
```

`end > start` 為慣例（`TimeAxis.add()` 容錯處理 `end <= start` 的 degenerate 情況、加極小 epsilon）。

## InventoryReport

Content inventory probe 產出。決定哪幾本筆記能填、哪些直接結構性 abstain。

```python
class ChannelAvailability(BaseModel):
    has_audio: bool = False
    has_speech: bool = False
    has_music: bool = False
    has_visual: bool = True
    visual_static: bool = False
    has_manual_subs: bool = False
    subs_lang: str | None = None
    duration_sec: float = 0.0


class InventoryReport(BaseModel):
    video_id: str
    source_path: str
    inventory: ChannelAvailability
    dispatched_channels: list[str] = Field(default_factory=list)
    skipped_channels: dict[str, str] = Field(default_factory=dict)
```

`dispatched_channels` / `skipped_channels` 是 inventory probe 對 ingest pipeline 的「派工單」。

## AgentState

Query 階段的狀態機快照。

```python
AbstainKind = Literal["structural", "evidence_insufficient"]


class AgentState(BaseModel):
    query: str
    retrieved_evidence: list[EvidenceClaim] = Field(default_factory=list)
    cited_indices: list[int] = Field(default_factory=list)
    final_answer: str | None = None
    abstain_kind: AbstainKind | None = None
    abstain_reason: str | None = None
    history: list[dict[str, Any]] = Field(default_factory=list)


MAX_TURNS = 10
```

`history` 累積每個 node 的 decision / status / error，作為 audit trail。Sequential 流程通常只有兩個 entry（orchestrator + integrator）。

## IngestState

DataClass（非 Pydantic），存 ingest 結果。

```python
@dataclass
class IngestState:
    ingest_id: str
    inventory: InventoryReport
    dialogue: DialogueNotebook
    on_screen_text: OnScreenTextNotebook
    scene: SceneNotebook
    sound_event: SoundEventNotebook
    holistic: HolisticNotebook
    time_axis: TimeAxis
    static_graph: StaticGraph
    created_at: datetime  # UTC
```

主要方法：

- `notebook_by_name(name)` → `Notebook | None`
- `absorb(claims)` → `int`：把 channel 出來的 claims 落到對應 notebook + time_axis
- `notebook_summary()` → `dict[str, int]`：每本 notebook 的 claim 數

## Notebook protocol

```python
class Notebook(Protocol):
    name: str

    def append(self, claim: EvidenceClaim) -> None: ...
    def query_by_time(self, start: float, end: float) -> list[EvidenceClaim]: ...
    def all_claims(self) -> list[EvidenceClaim]: ...
```

具體實作：`DialogueNotebook` / `OnScreenTextNotebook` / `SceneNotebook` / `SoundEventNotebook` / `HolisticNotebook`。

`append()` 會 enforce `claim.channel == notebook.name`，型別不對直接 raise。

## TimeAxis

跨 channel 共同時間軸 substrate，內部用 `intervaltree.IntervalTree` 索引。

```python
class TimeAxis:
    bin_seconds: float = 0.5

    def add(self, claim: EvidenceClaim) -> None: ...
    def at(self, t: float) -> list[EvidenceClaim]: ...
    def overlap(self, start: float, end: float) -> list[EvidenceClaim]: ...
    def all_at_bin(self, t: float) -> list[EvidenceClaim]: ...
```

`bin_seconds` 預設 0.5 秒，跨 channel 對齊容差。

## StaticGraph / DynamicGraph

```python
class NodeType(str, Enum):
    DIALOGUE_SPAN = "dialogue_span"
    OCR_TEXT = "ocr_text"
    SCENE = "scene"
    ENTITY = "entity"
    SOUND_EVENT = "sound_event"


class ObservationEdgeType(str, Enum):
    OCCURS_IN_SCENE = "occurs_in_scene"
    CO_OCCURS_AT = "co_occurs_at"
    PRECEDES = "precedes"
    ALIGNED_WITH = "aligned_with"


class InferenceEdgeType(str, Enum):
    CAUSED_BY = "caused_by"
    RELATED_TO = "related_to"
    PART_OF_THEME = "part_of_theme"
```

兩個 graph 都繼承 `_AuditedGraph`，所有 node / edge 操作落 `history`（audit trail）。

`StaticGraph` 主要方法：

- `add_evidence_node(node_id, node_type, claim)`
- `add_observation_edge(src, dst, edge_type)`
- `nodes_by_type(node_type)` → `list[str]`
- `nodes_in_time_range(start, end)` → `list[str]`
- `get_node(node_id)` → `dict | None`
- `neighbors_by_edge_type(node_id, edge_type)` → `list[str]`

`DynamicGraph` 額外要求推論邊帶 chain：

- `add_inference_edge(src, dst, edge_type, chain, strength)` — `chain` 不能空，否則 raise

## API request / response schemas

見 [`api.md`](api.md)。Source 在 `src/urusai/api/schemas.py`。
