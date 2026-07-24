"""
EvalBench AI - Evaluation & Benchmarking Dashboard (Light Professional Theme)
Talks only to the local FastAPI backend at http://localhost:8001 - fully offline.
"""
import requests
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

API = "http://localhost:8001"

st.set_page_config(page_title="EvalBench AI", page_icon="📊", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"]  { font-family: 'Inter', -apple-system, sans-serif; }
    .stApp { background: linear-gradient(180deg, #f7f9fc 0%, #eef1f8 100%); }
    .main-header { font-size: 2.3rem; font-weight: 800; color: #1a1f36; margin-bottom: 0; letter-spacing: -0.02em; }
    .sub-header { color: #6b7280; font-size: 0.98rem; margin-top: 0.25rem; font-weight: 500; }
    .header-badge {
        display: inline-block; background: #eef2ff; color: #4338ca;
        font-size: 0.72rem; font-weight: 700; padding: 4px 12px; border-radius: 20px;
        letter-spacing: 0.03em; text-transform: uppercase; margin-left: 10px; vertical-align: middle;
    }
    .metric-card {
        background: #ffffff; border: 1px solid #e8ebf3; border-radius: 16px;
        padding: 20px 22px; box-shadow: 0 1px 3px rgba(16,24,40,0.04), 0 4px 12px rgba(16,24,40,0.03);
        transition: box-shadow 0.2s ease;
    }
    .metric-card:hover { box-shadow: 0 4px 12px rgba(16,24,40,0.08), 0 8px 24px rgba(16,24,40,0.06); }
    .metric-label { color: #6b7280; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.06em; font-weight: 700; margin-bottom: 6px; }
    .metric-value { color: #111827; font-size: 2rem; font-weight: 800; letter-spacing: -0.02em; }
    section[data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e8ebf3; }
    section[data-testid="stSidebar"] .stMarkdown h3 { color: #1a1f36; font-weight: 700; font-size: 0.95rem; }
    button[data-baseweb="tab"] { font-weight: 600; color: #6b7280; font-size: 0.95rem; }
    button[data-baseweb="tab"][aria-selected="true"] { color: #4338ca !important; }
    div[data-baseweb="tab-highlight"] { background-color: #4338ca !important; }
    div[data-baseweb="tab-border"] { background-color: #e8ebf3 !important; }
    div[data-testid="stExpander"] { background: #ffffff; border: 1px solid #e8ebf3; border-radius: 12px; }
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
        border-radius: 10px !important; border: 1px solid #d5d9e2 !important; background-color: #ffffff !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #4338ca !important; box-shadow: 0 0 0 3px rgba(67,56,202,0.1) !important;
    }
    .stButton button {
        border-radius: 10px !important; font-weight: 600 !important;
        border: 1px solid #d5d9e2 !important; color: #1a1f36 !important;
        background-color: #ffffff !important; transition: all 0.15s ease !important;
    }
    .stButton button:hover { border-color: #4338ca !important; color: #4338ca !important; }
    .stButton button[kind="primary"] {
        background: linear-gradient(135deg, #4338ca 0%, #6366f1 100%) !important;
        border: none !important; color: #ffffff !important; box-shadow: 0 1px 2px rgba(67,56,202,0.3) !important;
    }
    .stButton button[kind="primary"]:hover { opacity: 0.92 !important; color: #ffffff !important; }
    div[data-testid="stDataFrame"] { border: 1px solid #e8ebf3; border-radius: 12px; overflow: hidden; }
    hr { border-color: #e8ebf3 !important; }
    .section-title { font-size: 1.15rem; font-weight: 700; color: #1a1f36; margin-bottom: 4px; }
    .section-caption { color: #9ca3af; font-size: 0.85rem; margin-bottom: 16px; }
</style>
""", unsafe_allow_html=True)


def api_get(path, **params):
    try:
        r = requests.get(f"{API}{path}", params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.session_state["api_error"] = str(e)
        return None


def api_post(path, json_body=None, timeout=180):
    try:
        r = requests.post(f"{API}{path}", json=json_body, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return None


CHART_COLORS = ["#4338ca", "#6366f1", "#a5b4fc", "#f97316", "#10b981", "#f43f5e"]

def style_chart(fig, height=350, title=None):
    fig.update_layout(
        paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
        font_color="#374151", font_family="Inter",
        height=height, margin=dict(l=10, r=10, t=50 if title else 20, b=10),
        title=dict(text=title, font=dict(size=15, color="#1a1f36")) if title else None,
        xaxis=dict(gridcolor="#f1f3f9", linecolor="#e8ebf3"),
        yaxis=dict(gridcolor="#f1f3f9", linecolor="#e8ebf3"),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    return fig

col_a, col_b = st.columns([5, 1])
with col_a:
    st.markdown('<div class="main-header">📊 EvalBench AI <span class="header-badge">100% Local</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">LLM Evaluation & Benchmarking Platform — Zero Cloud Dependency</div>', unsafe_allow_html=True)
with col_b:
    st.markdown(f"<div style='text-align:right; color:#9ca3af; padding-top:24px; font-weight:600;'>{datetime.now().strftime('%H:%M:%S')}</div>", unsafe_allow_html=True)

st.markdown("---")

with st.sidebar:
    st.markdown("### ⚙️ System")
    st.caption("Backend · FastAPI @ :8001")
    st.caption("LLM Judge · Ollama (phi3) — local")
    st.caption("Embeddings · sentence-transformers — local")
    st.caption("Hallucination check · LLM + lexical fallback")
    st.markdown("---")

    st.markdown("### ➕ New Prompt Version")
    with st.form("new_prompt"):
        p_name = st.text_input("Prompt name", placeholder="e.g. support-agent-v1")
        p_template = st.text_area("Template", placeholder="Answer the question: {input}\n\nContext: {context}")
        p_system = st.text_area("System prompt (optional)")
        if st.form_submit_button("Save Prompt", use_container_width=True, type="primary"):
            if p_name and p_template:
                api_post("/prompts", {"name": p_name, "template": p_template, "system_prompt": p_system or None})
                st.success("Prompt saved")

    st.markdown("### ➕ New Dataset")
    with st.form("new_dataset"):
        d_name = st.text_input("Dataset name", placeholder="e.g. support-qa-eval")
        d_desc = st.text_input("Description")
        if st.form_submit_button("Create Dataset", use_container_width=True, type="primary"):
            if d_name:
                api_post("/datasets", {"name": d_name, "description": d_desc})
                st.success("Dataset created")

tab_runs, tab_data, tab_results, tab_ab, tab_analytics = st.tabs(
    ["🚀 Run Evaluation", "📚 Datasets", "📈 Run Results", "⚔️ A/B Testing", "📊 Analytics"]
)

prompts = api_get("/prompts") or []
datasets = api_get("/datasets") or []
runs = api_get("/runs") or []

prompt_opts = {p["id"]: f"{p['name']} v{p['version']}" for p in prompts}
dataset_opts = {d["id"]: d["name"] for d in datasets}
run_opts = {r["id"]: r["name"] for r in runs}

with tab_runs:
    st.markdown('<div class="section-title">Configure Evaluation Run</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-caption">Pick a prompt, a dataset, and a local model, then run generation + judging end to end.</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        run_name = st.text_input("Run name", placeholder="e.g. support-agent-v1-eval")
        sel_prompt = st.selectbox("Prompt", options=list(prompt_opts.keys()) or [None],
                                   format_func=lambda x: prompt_opts.get(x, "No prompts yet"))
    with c2:
        sel_dataset = st.selectbox("Dataset", options=list(dataset_opts.keys()) or [None],
                                    format_func=lambda x: dataset_opts.get(x, "No datasets yet"))
        model_name = st.selectbox("Local model", ["phi3", "llama3", "mistral", "gemma2"])
    with c3:
        rag_mode = st.checkbox("Enable RAG metrics (needs context per example)")
        st.caption("RAG mode computes context precision/recall, faithfulness, and answer relevancy.")

    if st.button("🚀 Run Evaluation", type="primary", use_container_width=True):
        if run_name and sel_prompt and sel_dataset:
            with st.spinner("Running evaluation locally (generation + judging)... this may take a while"):
                result = api_post("/runs", {"name": run_name, "prompt_id": sel_prompt,
                                             "dataset_id": sel_dataset, "model_name": model_name,
                                             "rag_mode": rag_mode})
            if result:
                st.success(f"Run #{result['run_id']} completed — {result['num_results']} examples evaluated")
                st.rerun()
        else:
            st.warning("Fill in run name, prompt, and dataset first.")

    st.markdown("---")
    st.markdown('<div class="section-title">Run History</div>', unsafe_allow_html=True)
    if runs:
        df = pd.DataFrame(runs)[["id", "name", "model_name", "status", "created_at"]]
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.caption("No runs yet.")

with tab_data:
    st.markdown('<div class="section-title">Add Examples to a Dataset</div>', unsafe_allow_html=True)
    sel_ds = st.selectbox("Dataset", options=list(dataset_opts.keys()) or [None],
                           format_func=lambda x: dataset_opts.get(x, "No datasets yet"), key="ds_examples")
    with st.form("new_example"):
        ex_input = st.text_area("Input / question")
        ex_ref = st.text_area("Reference answer (optional)")
        ex_context = st.text_area("Context (optional, for RAG eval)")
        if st.form_submit_button("Add Example", type="primary"):
            if sel_ds and ex_input:
                api_post(f"/datasets/{sel_ds}/examples",
                         {"input_text": ex_input, "reference_answer": ex_ref or None, "context": ex_context or None})
                st.success("Example added")
                st.rerun()

    st.markdown('<div class="section-title">Bulk Upload</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-caption">CSV columns: input_text, reference_answer, context</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded and sel_ds:
        df_upload = pd.read_csv(uploaded)
        if st.button("Import CSV into dataset"):
            examples = df_upload.fillna("").to_dict(orient="records")
            payload = [{"input_text": r.get("input_text", ""), "reference_answer": r.get("reference_answer") or None,
                        "context": r.get("context") or None} for r in examples]
            api_post(f"/datasets/{sel_ds}/examples/bulk", payload)
            st.success(f"Imported {len(payload)} examples")
            st.rerun()

    if sel_ds:
        st.markdown('<div class="section-title">Current Examples</div>', unsafe_allow_html=True)
        examples = api_get(f"/datasets/{sel_ds}/examples") or []
        if examples:
            st.dataframe(pd.DataFrame(examples)[["id", "input_text", "reference_answer", "context"]],
                         use_container_width=True, hide_index=True)
        else:
            st.caption("No examples yet.")

with tab_results:
    sel_run = st.selectbox("Select run", options=list(run_opts.keys()) or [None],
                            format_func=lambda x: run_opts.get(x, "No runs yet"))
    if sel_run:
        summary = api_get(f"/runs/{sel_run}/summary")
        if summary and summary.get("num_results"):
            cols = st.columns(4)
            metrics = [
                ("Avg Judge Score", f"{summary['avg_judge_score']}/10" if summary['avg_judge_score'] is not None else "N/A"),
                ("Avg Hallucination Score", summary["avg_hallucination_score"] if summary["avg_hallucination_score"] is not None else "N/A"),
                ("Hallucination Flag Rate", f"{summary['hallucination_flag_rate']*100:.1f}%"),
                ("Avg Latency", f"{summary['avg_latency_ms']:.0f} ms" if summary["avg_latency_ms"] else "N/A"),
            ]
            for col, (label, value) in zip(cols, metrics):
                col.markdown(f"""<div class="metric-card"><div class="metric-label">{label}</div>
                             <div class="metric-value">{value}</div></div>""", unsafe_allow_html=True)

            st.markdown("---")
            results = api_get(f"/runs/{sel_run}/results") or []
            df = pd.DataFrame(results)
            display_cols = ["input_text", "generated_output", "judge_score", "correctness",
                             "relevance", "coherence", "hallucination_score", "hallucination_flag",
                             "latency_ms", "error", "judge_reasoning"]
            display_cols = [c for c in display_cols if c in df.columns]
            st.markdown('<div class="section-title">Per-Example Results</div>', unsafe_allow_html=True)
            st.dataframe(df[display_cols], use_container_width=True, hide_index=True, height=400)

            with st.expander("View flagged hallucinations"):
                flagged = df[df.get("hallucination_flag", False) == True] if "hallucination_flag" in df else pd.DataFrame()
                if not flagged.empty:
                    st.dataframe(flagged[["input_text", "generated_output", "unsupported_claims", "hallucination_score"]],
                                 use_container_width=True, hide_index=True)
                else:
                    st.caption("No hallucinations flagged in this run.")
        else:
            st.caption("No results yet for this run.")

with tab_ab:
    st.markdown('<div class="section-title">Compare Two Runs</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        ab_name = st.text_input("Test name", placeholder="e.g. prompt-v1-vs-v2")
        run_a = st.selectbox("Run A", options=list(run_opts.keys()) or [None],
                              format_func=lambda x: run_opts.get(x, "—"), key="run_a")
    with c2:
        run_b = st.selectbox("Run B", options=list(run_opts.keys()) or [None],
                              format_func=lambda x: run_opts.get(x, "—"), key="run_b")

    if st.button("⚔️ Run A/B Comparison", type="primary"):
        if ab_name and run_a and run_b and run_a != run_b:
            with st.spinner("Comparing runs..."):
                result = api_post("/ab-tests", {"name": ab_name, "run_a_id": run_a, "run_b_id": run_b})
            if result:
                fig = go.Figure(data=[go.Bar(
                    x=["Run A", "Run B"], y=[result["mean_score_a"], result["mean_score_b"]],
                    marker_color=[CHART_COLORS[0], CHART_COLORS[3]], width=0.5
                )])
                fig = style_chart(fig, title=f"Mean Judge Score (p≈{result['p_value_estimate']})")
                st.plotly_chart(fig, use_container_width=True)
                st.markdown(f"**Winner: {result['winner']}**")
                st.info(result["summary"])
        else:
            st.warning("Select two different runs and a test name.")

    st.markdown("---")
    st.markdown('<div class="section-title">A/B Test History</div>', unsafe_allow_html=True)
    ab_tests = api_get("/ab-tests") or []
    if ab_tests:
        st.dataframe(pd.DataFrame(ab_tests)[["id", "name", "winner", "created_at"]],
                     use_container_width=True, hide_index=True)

with tab_analytics:
    st.markdown('<div class="section-title">Cross-Run Analytics</div>', unsafe_allow_html=True)
    if runs:
        all_summaries = []
        for r in runs:
            s = api_get(f"/runs/{r['id']}/summary")
            if s and s.get("num_results"):
                s["run_name"] = r["name"]
                all_summaries.append(s)
        if all_summaries:
            df = pd.DataFrame(all_summaries)

            fig1 = px.bar(df, x="run_name", y="avg_judge_score", color_discrete_sequence=[CHART_COLORS[0]])
            st.plotly_chart(style_chart(fig1, title="Average Judge Score by Run"), use_container_width=True)

            fig2 = px.bar(df, x="run_name", y="hallucination_flag_rate", color_discrete_sequence=[CHART_COLORS[3]])
            st.plotly_chart(style_chart(fig2, title="Hallucination Flag Rate by Run"), use_container_width=True)

            fig3 = px.bar(df, x="run_name", y="avg_latency_ms", color_discrete_sequence=[CHART_COLORS[4]])
            st.plotly_chart(style_chart(fig3, title="Average Latency (ms) by Run"), use_container_width=True)
        else:
            st.caption("No completed runs with results yet.")
    else:
        st.caption("No runs yet.")
