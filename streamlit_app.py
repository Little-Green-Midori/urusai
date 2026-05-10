"""urusai dev interface（Streamlit 開發測試介面）.

跑：
    streamlit run streamlit_app.py

接 in-process FastAPI（fastapi.testclient.TestClient）—— 同一條 code path、
之後外部 client 走 HTTP 也是同樣 contract。
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st
from fastapi.testclient import TestClient

from urusai.api.main import app


st.set_page_config(page_title="urusai", layout="wide")

st.title("urusai")
st.caption("「URUSAI！source 呢？cite 呢？」")
st.caption("一個會看影片、但拒絕憑印象答題的代理人。")


@st.cache_resource
def get_client() -> TestClient:
    return TestClient(app)


client = get_client()

if "ingest_state" not in st.session_state:
    st.session_state.ingest_state = None
if "last_query_result" not in st.session_state:
    st.session_state.last_query_result = None


# === Sidebar：system status ===
with st.sidebar:
    st.header("System")

    st.subheader("Hardware")
    try:
        import torch

        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            vram_gb = round(
                torch.cuda.get_device_properties(0).total_memory / 1024**3, 1
            )
            cuda_v = torch.version.cuda
            torch_v = torch.__version__
            st.success(
                f"**GPU**: {gpu_name}\n\n"
                f"**VRAM**: {vram_gb} GB\n\n"
                f"**CUDA**: {cuda_v}\n\n"
                f"**torch**: {torch_v}"
            )
            if vram_gb < 8:
                st.warning(
                    "VRAM < 8 GB：本地多模型同時載入會爆。"
                    "channel 用 sequential load/unload。"
                )
        else:
            st.warning("torch installed but CUDA unavailable")
    except ImportError:
        st.error("torch not installed")

    st.divider()
    st.subheader("Backend")
    health = client.get("/healthz").json()
    st.success(f"FastAPI in-process · v{health.get('version', '?')}")

    st.divider()
    st.markdown("[GitHub repo](https://github.com/Little-Green-Midori/urusai)")


# === Main：分頁 ===
tab_video, tab_notebooks, tab_query, tab_trace = st.tabs(
    ["影片 ingest", "5 本筆記", "Query", "Evidence trace"]
)


with tab_video:
    st.markdown("### 影片來源")
    col1, col2 = st.columns(2)
    with col1:
        uploaded = st.file_uploader("上傳影片檔", type=["mp4", "mkv", "webm", "mov"])
    with col2:
        url = st.text_input("或貼 YouTube URL", placeholder="https://...")

    if st.button("開始 ingest", disabled=not (uploaded or url)):
        with st.spinner("inventory probe + channel extraction 中（首次 ASR 會載 ~1.6 GB faster-whisper）..."):
            file_path: str | None = None
            if uploaded is not None:
                tmp = tempfile.NamedTemporaryFile(
                    suffix=Path(uploaded.name).suffix, delete=False
                )
                tmp.write(uploaded.read())
                tmp.close()
                file_path = tmp.name

            payload: dict = {}
            if file_path:
                payload["file_path"] = file_path
            if url:
                payload["url"] = url

            resp = client.post("/ingest", json=payload)
            if resp.status_code != 200:
                st.error(f"ingest 失敗 ({resp.status_code}): {resp.json()}")
            else:
                st.session_state.ingest_state = resp.json()
                st.success(f"ingest_id = {resp.json()['ingest_id']}")

    state = st.session_state.ingest_state
    if state:
        st.divider()
        st.markdown("### Inventory probe 結果")
        inv = state["inventory"]["inventory"]
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("duration_sec", f"{inv['duration_sec']:.1f}")
        col_b.metric("has_speech", str(inv["has_speech"]))
        col_c.metric("has_visual", str(inv["has_visual"]))
        col_d, col_e, col_f = st.columns(3)
        col_d.metric("has_music", str(inv["has_music"]))
        col_e.metric("visual_static", str(inv["visual_static"]))
        col_f.metric("manual_subs", f"{inv['has_manual_subs']} ({inv['subs_lang'] or '-'})")

        st.markdown("**dispatched channels**")
        st.code("\n".join(state["inventory"]["dispatched_channels"]) or "(none)")
        if state["inventory"]["skipped_channels"]:
            st.markdown("**skipped channels**")
            for ch, reason in state["inventory"]["skipped_channels"].items():
                st.caption(f"- {ch}: {reason}")


with tab_notebooks:
    st.markdown("### 5 本筆記")
    st.caption("每本獨立、各記擅長之物、共享時間軸。")

    state = st.session_state.ingest_state
    counts = state["notebooks"] if state else {
        "dialogue": 0, "on_screen_text": 0, "scene": 0, "sound_event": 0, "holistic": 0,
    }

    cols = st.columns(5)
    notebook_specs = [
        ("對白本", "dialogue", "ASR / manual subs"),
        ("畫面字本", "on_screen_text", "OCR / LVLM-OCR"),
        ("場景本", "scene", "PySceneDetect + VLM caption"),
        ("聲音本", "sound_event", "audio event detection"),
        ("整體感本", "holistic", "LVLM clip"),
    ]
    for col, (name, key, tool) in zip(cols, notebook_specs):
        with col:
            st.subheader(name)
            st.caption(tool)
            st.metric("entries", counts.get(key, 0))


with tab_query:
    st.markdown("### Query")
    state = st.session_state.ingest_state
    if not state:
        st.info("先到「影片 ingest」分頁建立一個 ingest")
    else:
        st.caption(f"current ingest_id: `{state['ingest_id']}`")
        q = st.text_input("問題", placeholder="例：她在哪一段說『我會再想想』？")
        if st.button("送出", disabled=not q):
            with st.spinner("agent loop 中（Gemma 4 31B IT via Gemini API）..."):
                resp = client.post(
                    "/query",
                    json={"ingest_id": state["ingest_id"], "query": q},
                )
                if resp.status_code != 200:
                    st.error(f"query 失敗 ({resp.status_code}): {resp.json()}")
                else:
                    st.session_state.last_query_result = resp.json()

    result = st.session_state.last_query_result
    if result:
        st.divider()
        st.markdown("### Result")
        if result["status"] == "answered":
            st.success("answered")
            st.markdown(f"**Answer**: {result['answer']}")
            if result["cited_evidence"]:
                st.markdown("**Cited evidence**")
                for ev in result["cited_evidence"]:
                    st.markdown(
                        f"- `[{ev['index']}]` **{ev['channel']}** "
                        f"{ev['start_sec']:.2f}–{ev['end_sec']:.2f}s "
                        f"`{ev['text']}` _(via {ev['source_tool']})_"
                    )
        else:
            st.warning(f"abstain: {result['abstain_kind']}")
            st.markdown(f"**Reason**: {result['abstain_reason']}")


with tab_trace:
    st.markdown("### Evidence trace")
    st.caption("格式：claim ← evidence ← channel ← time。沒 trace 就 abstain。")

    result = st.session_state.last_query_result
    if not result:
        st.write("（尚未 query）")
    else:
        st.code(result["trace"], language="text")
