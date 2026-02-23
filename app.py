import os
import streamlit as st

st.set_page_config(
    page_title="Sistema Integrado Engage",
    page_icon="🚀",
    layout="wide",
)

# CSS
if os.path.exists("style.css"):
    with open("style.css", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from modules.auth import verificar_autenticacao
from modules.pendencias import pagina_pendencias
from modules.sac import pagina_sac
from modules.dashboard import pagina_dashboard

# ── Auth gate ──────────────────────────────────────────────────────────────
if not verificar_autenticacao():
    st.stop()

# ── Sidebar ────────────────────────────────────────────────────────────────
_usuario = st.session_state.get("usuario_logado", "")

if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)

st.sidebar.markdown(f"<p style='margin:0.5rem 0 0.1rem;font-weight:700;color:#1e293b'>👤 {_usuario}</p>", unsafe_allow_html=True)
st.sidebar.caption("MENU PRINCIPAL")

pagina = st.sidebar.radio(
    "Navegação:",
    ("Pendências Logísticas", "SAC / Atendimento", "📊 Dashboard Gerencial"),
    label_visibility="collapsed",
)
st.sidebar.markdown("---")

if st.sidebar.button("🚪 Sair"):
    st.session_state.clear()
    st.rerun()

# ── Roteamento ─────────────────────────────────────────────────────────────
if pagina == "Pendências Logísticas":
    pagina_pendencias()
elif pagina == "SAC / Atendimento":
    pagina_sac()
else:
    pagina_dashboard()
