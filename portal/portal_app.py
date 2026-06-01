import streamlit as st
import json
import time
from pathlib import Path

# Page config
st.set_page_config(
    page_title="GIULIA AI - RAG Ecosystem Portal",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS + JS auto-scroll via anchor ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

html, body, [data-testid="stApp"] {
    background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%) !important;
    font-family: 'Inter', sans-serif;
}

[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] { background: rgba(15, 23, 42, 0.9) !important; }

.project-card {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(12px);
    border-radius: 16px;
    padding: 22px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    margin-bottom: 18px;
    transition: all 0.25s ease;
    min-height: 200px;
}
.project-card:hover {
    border-color: rgba(99, 102, 241, 0.6);
    background: rgba(99, 102, 241, 0.08);
    transform: translateY(-3px);
    box-shadow: 0 8px 32px rgba(99, 102, 241, 0.2);
}
.project-card h3 { color: #a5b4fc; margin: 0 0 4px; font-size: 13px; font-weight: 600; letter-spacing: 1px; }
.project-card h4 { color: #e2e8f0; margin: 0 0 10px; font-size: 16px; font-weight: 600; }
.project-card p  { color: #94a3b8; font-size: 13px; line-height: 1.5; margin: 0; }

.badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}
.badge-concluido      { background: #065f46; color: #6ee7b7; border: 1px solid #059669; }
.badge-em_desenvolvim { background: #78350f; color: #fde68a; border: 1px solid #d97706; }
.badge-backlog        { background: #1e293b; color: #94a3b8; border: 1px solid #475569; }

.detail-panel {
    background: rgba(99, 102, 241, 0.06);
    border: 1px solid rgba(99, 102, 241, 0.25);
    border-radius: 20px;
    padding: 30px;
    margin-top: 10px;
}
.detail-title {
    font-size: 22px;
    font-weight: 700;
    color: #e2e8f0;
    margin-bottom: 6px;
}
.detail-sub {
    font-size: 13px;
    color: #94a3b8;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# --- Helper functions ---
def load_projects():
    for path in [
        Path("../../../REGISTRY/projects.json"),
        Path("REGISTRY/projects.json"),
    ]:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return {"projetos": {}}

def get_metrics():
    for path in [
        Path("../../../INFRA/logs/rag_metrics.json"),
        Path("INFRA/logs/rag_metrics.json"),
    ]:
        if path.exists():
            try:
                raw = path.read_text(encoding="utf-8").strip()
                parsed = json.loads(raw)
                # Pode ser array ou dict
                if isinstance(parsed, list):
                    return parsed[-10:]
                elif isinstance(parsed, dict):
                    return [parsed]
            except Exception:
                # Tenta JSON Lines como fallback
                valid = []
                for l in path.read_text().splitlines():
                    l = l.strip()
                    if not l or l in ("null", "[", "]"):
                        continue
                    l = l.rstrip(",")
                    try:
                        valid.append(json.loads(l))
                    except Exception:
                        pass
                return valid[-10:]
    return []

def load_snapshot(pid: str, filename: str) -> str | None:
    pattern = f"../../../DEV/{pid}_*/project_context/{filename}"
    found = next(Path(".").glob(pattern), None)
    if found:
        return found.read_text(encoding="utf-8")
    return None

def badge_html(status: str) -> str:
    label_map = {
        "concluido": "✅ Concluído",
        "em_desenvolvimento": "🔧 Em Desenvolvimento",
        "backlog": "💤 Backlog",
    }
    cls_map = {
        "concluido": "badge-concluido",
        "em_desenvolvimento": "badge-em_desenvolvim",
        "backlog": "badge-backlog",
    }
    label = label_map.get(status, status)
    cls   = cls_map.get(status, "badge-backlog")
    return f'<span class="badge {cls}">{label}</span>'

# --- Port map ---
PORT_MAP = {
    "PRJ-01": 8501, "PRJ-02": 8502, "PRJ-03": 8503,
    "PRJ-04": 8504, "PRJ-05": 8505, "PRJ-06": 8506,
    "PRJ-07": 8507, "PRJ-08": 8508, "PRJ-09": 8500,
}

# --- Load data ---
data = load_projects()
projects = data.get("projetos", {})

# --- Sidebar ---
with st.sidebar:
    st.markdown("### 🤖 GIULIA AI")
    st.markdown("**RAG Ecosystem**")
    st.divider()

    metrics = get_metrics()
    if metrics:
        avg_lat = sum(m.get("total_latency", 0) for m in metrics) / len(metrics)
        st.metric("⚡ Avg Latency", f"{avg_lat:.2f}s")
    else:
        st.info("Observatory sem dados recentes.")

    st.divider()
    done = sum(1 for p in projects.values() if p["status"] == "concluido")
    st.metric("📦 Projetos Concluídos", f"{done} / {len(projects)}")

    st.divider()
    st.caption("Portal v3.0 — GARE-92")

# --- Header ---
st.title("🚀 RAG Portfolio Command Center")
st.markdown("Explore a evolução da arquitetura RAG em 9 implementações progressivas. Clique num projeto para ver os detalhes.")

st.divider()

# --- Project grid ---
cols = st.columns(3)
for i, (pid, info) in enumerate(projects.items()):
    with cols[i % 3]:
        status = info.get("status", "backlog")
        tasks_done  = info.get("tasks", {}).get("concluidas", 0)
        tasks_total = info.get("tasks", {}).get("total", 0)

        st.markdown(f"""
        <div class="project-card">
            <h3>{pid}</h3>
            <h4>{info['nome']}</h4>
            <p>{info.get('descricao','')[:110]}…</p>
            <div style="margin-top:14px; display:flex; justify-content:space-between; align-items:center;">
                {badge_html(status)}
                <span style="font-size:11px; color:#64748b;">Tasks {tasks_done}/{tasks_total}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button(f"🔍 Explorar {pid}", key=f"btn_{pid}", use_container_width=True):
            st.session_state.selected_project = pid
            # Inject JS to scroll to the anchor after rerun
            st.session_state.scroll_to_details = True
            st.rerun()

# --- Auto-scroll anchor ---
# Place the anchor BEFORE the detail panel
st.markdown('<div id="project-details-anchor"></div>', unsafe_allow_html=True)

# Inject JS scroll if flag is set
if st.session_state.get("scroll_to_details"):
    st.session_state.scroll_to_details = False
    st.markdown("""
    <script>
        window.parent.document.getElementById('project-details-anchor')
            ?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    </script>
    """, unsafe_allow_html=True)

# --- Detail panel ---
if "selected_project" in st.session_state:
    pid  = st.session_state.selected_project
    info = projects.get(pid, {})
    port = PORT_MAP.get(pid, 8500)
    status = info.get("status", "backlog")

    st.markdown(f"""
    <div class="detail-panel">
        <div class="detail-title">🔍 {pid} — {info.get('nome','')}</div>
        <div class="detail-sub">
            {badge_html(status)}
            &nbsp;&nbsp;|&nbsp;&nbsp;
            <code>{info.get('tecnica','')}</code>
        </div>
        <p style="color:#cbd5e1;">{info.get('descricao','')}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")

    col_left, col_right = st.columns([2, 1])

    with col_left:
        tab_mem, tab_arch, tab_ops = st.tabs(["🧠 Memória Operacional", "🏗️ Arquitetura", "🔧 Ops & Manutenção"])

        with tab_mem:
            content = load_snapshot(pid, "01_OPERATIONAL_MEMORY.md")
            if content:
                st.markdown(content)
            else:
                st.warning("Snapshot de memória não encontrado. Rode: `python INFRA/start_project.py --snapshot " + pid + "`")

        with tab_arch:
            content = load_snapshot(pid, "02_ARCHITECTURE_LOG.md")
            if content:
                st.markdown(content)
            else:
                st.warning("Log de arquitetura não encontrado.")

        with tab_ops:
            content = load_snapshot(pid, "03_MAINTENANCE_GUIDE.md")
            if content:
                st.markdown(content)
            else:
                st.info("Guia de manutenção não gerado ainda.")

            st.divider()
            st.markdown("**Comando Docker para este projeto:**")
            pid_lower = pid.lower().replace("-", "")
            st.code(f"cd DEV/PRJ-09_Deploy_Cloud && docker-compose up {pid_lower}-api {pid_lower}-ui", language="bash")

    with col_right:
        # --- Live App Access ---
        st.markdown("### 🚀 Acesso Direto")
        st.link_button(
            f"Abrir Interface Live → Porta {port}",
            f"http://localhost:{port}",
            use_container_width=True,
        )
        st.caption(f"Suba o projeto antes de acessar: `streamlit run frontend/app.py --server.port {port}`")

        st.divider()

        # --- Jira ---
        st.markdown("### 🎫 Jira")
        st.markdown(f"**Epic:** `{info.get('jira_epico', 'N/A')}`")
        st.markdown(f"**Tasks:** `{info.get('jira_tasks_range', 'N/A')}`")

        st.divider()

        # --- Lessons Learned snippet ---
        st.markdown("### 💡 Lições")
        content = load_snapshot(pid, "06_LESSONS_LEARNED.md")
        if content:
            # Show just first 600 chars
            st.markdown(content[:600] + "…")
        else:
            st.caption("Sem lições registradas ainda.")

# --- Footer ---
st.divider()
st.markdown(
    "<p style='text-align:center;color:#334155;font-size:12px;'>"
    "GIULIA AI Ecosystem © 2026 · Developed by Wemerson Souza · PRJ-09 Deploy Cloud"
    "</p>",
    unsafe_allow_html=True,
)
