import io
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from modules.sheets import carregar_dados_dashboard

# ── Paleta consistente ────────────────────────────────────────────────────────
COR_SAC      = "#2563eb"
COR_PEND     = "#7c3aed"
COR_POSITIVO = "#059669"
COR_ALERTA   = "#f59e0b"
COR_NEUTRO   = "#64748b"

_CHART_LAYOUT = dict(
    template="plotly_white",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#334155"),
    margin=dict(l=12, r=12, t=40, b=12),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _card_html(icone: str, valor: str, titulo: str, gradiente: str, subtitulo: str = "") -> str:
    """Gera card HTML com altura mínima uniforme independente do subtítulo."""
    sub = f'<div style="font-size:0.72rem;opacity:0.8;margin-top:3px;min-height:1rem">{subtitulo}</div>'
    return (
        f'<div style="background:{gradiente};border-radius:18px;padding:1.4rem 1rem 1.2rem;'
        f'box-shadow:0 8px 24px -6px rgba(0,0,0,0.18);color:white;text-align:center;'
        f'min-height:150px;display:flex;flex-direction:column;justify-content:center;">'
        f'<div style="font-size:1.9rem;line-height:1">{icone}</div>'
        f'<div style="font-size:2.1rem;font-weight:800;line-height:1.15;margin-top:0.3rem">{valor}</div>'
        f'{sub}'
        f'<div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:0.07em;opacity:0.85;margin-top:0.5rem">{titulo}</div>'
        f'</div>'
    )


def _secao(titulo: str, descricao: str = ""):
    desc = f'<p style="color:#475569;font-size:0.92rem;font-weight:500;margin:0.3rem 0 0;line-height:1.4">{descricao}</p>' if descricao else ""
    st.markdown(
        f'<div style="border-left:5px solid {COR_SAC};padding:0.2rem 0 0.2rem 1rem;margin:1.75rem 0 0.9rem;'
        f'background:linear-gradient(90deg,rgba(37,99,235,0.04) 0%,transparent 100%);border-radius:0 8px 8px 0">'
        f'<h3 style="margin:0;color:#0f172a;font-size:1.25rem;font-weight:800;letter-spacing:-0.2px">{titulo}</h3>'
        f'{desc}</div>',
        unsafe_allow_html=True,
    )


def _exportar_excel(df: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    df_dados = df.copy().drop(columns=["Data_Filtro", "Hora_Int"], errors="ignore")
    df_dados["Nota_Fiscal"]    = df_dados["Nota_Fiscal"].astype(str)
    df_dados["Numero_Pedido"]  = df_dados["Numero_Pedido"].astype(str)

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_dados.to_excel(writer, sheet_name="Dados", index=False)

        total    = len(df_dados)
        sac      = len(df_dados[df_dados["Setor"] == "SAC"]) if "Setor" in df_dados else 0
        pend     = len(df_dados[df_dados["Setor"] == "Pendência"]) if "Setor" in df_dados else 0
        taxa     = f"{sac / total * 100:.1f}%" if total else "0%"
        top_port = df_dados["Portal"].mode()[0] if "Portal" in df_dados and not df_dados.empty else "-"

        resumo = pd.DataFrame({
            "Métrica": ["Total de Atendimentos", "SAC", "Pendências", "Taxa SAC/Total", "Portal Mais Ativo"],
            "Valor":   [total, sac, pend, taxa, top_port],
        })
        resumo.to_excel(writer, sheet_name="Resumo", index=False)

        if "Colaborador" in df_dados and "Setor" in df_dados:
            pivot = df_dados.pivot_table(
                index="Colaborador", columns="Setor", aggfunc="size", fill_value=0
            ).reset_index()
            pivot["Total"] = pivot.select_dtypes("number").sum(axis=1)
            pivot.to_excel(writer, sheet_name="Por Colaborador", index=False)

    return buffer.getvalue()


# ── Página principal ──────────────────────────────────────────────────────────

def pagina_dashboard():
    usuario_logado = st.session_state.get("usuario_logado", "")

    st.markdown(
        '<div style="background:linear-gradient(135deg,#1e40af 0%,#2563eb 60%,#7c3aed 100%);'
        'border-radius:20px;padding:2rem 2.5rem;margin-bottom:1.5rem;color:white">'
        '<h1 style="margin:0;color:white;font-size:2rem;letter-spacing:-0.5px">📊 Dashboard Gerencial</h1>'
        '<p style="margin:0.4rem 0 0;opacity:0.85;font-size:0.95rem">Visão estratégica dos atendimentos · atualização a cada 60 s</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    df_raw = carregar_dados_dashboard()
    if df_raw.empty:
        st.warning("⚠️ Planilha vazia ou sem conexão com o Google Sheets.")
        return

    df_raw["Data_Filtro"] = pd.to_datetime(df_raw["Data"], format="%d/%m/%Y", errors="coerce")
    total_na_base = len(df_raw)

    # ── Filtros na sidebar ────────────────────────────────────────────────────
    st.sidebar.markdown("---")
    st.sidebar.markdown("**🔍 Filtros do painel**")

    d_min = df_raw["Data_Filtro"].min().date() if not df_raw["Data_Filtro"].isnull().all() else datetime.today().date()
    d_max = df_raw["Data_Filtro"].max().date() if not df_raw["Data_Filtro"].isnull().all() else datetime.today().date()

    c1, c2 = st.sidebar.columns(2)
    ini = c1.date_input("Início", d_min, format="DD/MM/YYYY")
    fim = c2.date_input("Fim",    d_max, format="DD/MM/YYYY")

    setores  = sorted(df_raw["Setor"].dropna().unique().tolist())
    f_setor  = st.sidebar.multiselect("Setor:", options=setores, default=setores)
    if not f_setor:
        f_setor = setores

    mask = (
        (df_raw["Data_Filtro"].dt.date >= ini)
        & (df_raw["Data_Filtro"].dt.date <= fim)
        & (df_raw["Setor"].isin(f_setor))
    )
    df = df_raw.loc[mask].copy()

    if df.empty:
        st.warning("Nenhum dado para o período/filtro selecionado.")
        return

    # Nota de transparência
    st.sidebar.caption(f"📦 {total_na_base} registros na base · {len(df)} exibidos")

    # Coluna de hora (necessária para cálculos de velocidade)
    df["Hora_Int"] = pd.to_datetime(df["Hora"], format="%H:%M:%S", errors="coerce").dt.hour

    # ── KPIs ──────────────────────────────────────────────────────────────────
    total      = len(df)
    sac        = len(df[df["Setor"] == "SAC"])
    pend       = len(df[df["Setor"] == "Pendência"])
    taxa_sac   = f"{sac / total * 100:.1f}%" if total else "0%"
    top_portal = df["Portal"].mode()[0] if "Portal" in df and not df.empty else "-"

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.markdown(_card_html("📋", str(total), "Total de Atendimentos",
            "linear-gradient(135deg,#1e40af,#2563eb)"), unsafe_allow_html=True)
    with k2:
        st.markdown(_card_html("🎧", str(sac), "SAC",
            "linear-gradient(135deg,#0369a1,#0ea5e9)"), unsafe_allow_html=True)
    with k3:
        st.markdown(_card_html("🚚", str(pend), "Pendências",
            "linear-gradient(135deg,#6d28d9,#7c3aed)"), unsafe_allow_html=True)
    with k4:
        st.markdown(_card_html("🛒", top_portal, "Portal Mais Ativo",
            "linear-gradient(135deg,#b45309,#f59e0b)"), unsafe_allow_html=True)
    with k5:
        st.markdown(_card_html("📊", taxa_sac, "Taxa SAC / Total",
            "linear-gradient(135deg,#065f46,#059669)"), unsafe_allow_html=True)

    # ── Seu Desempenho ────────────────────────────────────────────────────────
    st.markdown("<div style='margin-top:1.5rem'></div>", unsafe_allow_html=True)
    _secao("⭐ Seu Desempenho", "Seus números em contexto — período selecionado")

    # Atendimentos/dia por colaborador
    atend_por_dia = (
        df.groupby("Colaborador")
        .agg(total_atend=("Colaborador", "count"),
             dias=("Data_Filtro", lambda x: x.dt.date.nunique()))
        .assign(taxa=lambda t: t["total_atend"] / t["dias"].clip(lower=1))
    )
    media_time     = atend_por_dia["total_atend"].mean() if not atend_por_dia.empty else 0
    taxa_media_dia = atend_por_dia["taxa"].mean() if not atend_por_dia.empty else 0

    meu_total = int(atend_por_dia["total_atend"].get(usuario_logado, 0)) if usuario_logado else 0
    minha_taxa_dia = float(atend_por_dia["taxa"].get(usuario_logado, 0.0)) if usuario_logado else 0.0

    # Semana atual vs anterior
    hoje       = datetime.today().date()
    ini_sem    = hoje - timedelta(days=hoje.weekday())
    ini_sem_ant= ini_sem - timedelta(days=7)
    df_sem_at  = df[df["Data_Filtro"].dt.date >= ini_sem]
    df_sem_ant = df[(df["Data_Filtro"].dt.date >= ini_sem_ant) & (df["Data_Filtro"].dt.date < ini_sem)]
    minha_sem_at  = int((df_sem_at["Colaborador"] == usuario_logado).sum()) if usuario_logado else 0
    minha_sem_ant = int((df_sem_ant["Colaborador"] == usuario_logado).sum()) if usuario_logado else 0

    delta_semana  = minha_sem_at - minha_sem_ant
    sinal_sem     = ("▲ +" if delta_semana > 0 else ("▼ " if delta_semana < 0 else "= ")) + str(abs(delta_semana)) + " vs sem. passada"

    delta_media  = meu_total - media_time
    sinal_media  = ("▲ +" if delta_media > 0 else ("▼ " if delta_media < 0 else "= ")) + f"{abs(delta_media):.0f} vs média do time"

    # Cor baseada em performance vs média
    if meu_total >= media_time * 1.1:
        cor_voce = "linear-gradient(135deg,#065f46,#059669)"
    elif meu_total >= media_time * 0.9:
        cor_voce = "linear-gradient(135deg,#b45309,#d97706)"
    else:
        cor_voce = "linear-gradient(135deg,#9f1239,#e11d48)"

    nome_exibicao = usuario_logado if usuario_logado else "Você"

    d1, d2, d3 = st.columns(3)
    with d1:
        st.markdown(_card_html(
            "🎯", str(meu_total), f"{nome_exibicao} · Total do período",
            cor_voce, subtitulo=sinal_media
        ), unsafe_allow_html=True)
    with d2:
        st.markdown(_card_html(
            "📅", str(minha_sem_at), "Esta semana",
            "linear-gradient(135deg,#0369a1,#0ea5e9)", subtitulo=sinal_sem
        ), unsafe_allow_html=True)
    with d3:
        taxa_str  = f"{minha_taxa_dia:.1f}" if minha_taxa_dia else "—"
        media_str = f"média do time: {taxa_media_dia:.1f}/dia"
        st.markdown(_card_html(
            "⚡", taxa_str, "Atend./dia (você)",
            "linear-gradient(135deg,#5b21b6,#7c3aed)", subtitulo=media_str
        ), unsafe_allow_html=True)

    st.markdown("<div style='margin-top:2rem'></div>", unsafe_allow_html=True)

    # ── Gráfico 1: Tendência diária ───────────────────────────────────────────
    _secao("📈 Tendência Diária", "Volume total de atendimentos por dia")
    trend = df.groupby("Data_Filtro").size().reset_index(name="Atendimentos")
    fig1  = px.area(
        trend, x="Data_Filtro", y="Atendimentos",
        markers=True, line_shape="spline", text="Atendimentos",
        color_discrete_sequence=[COR_SAC],
    )
    fig1.update_traces(
        textposition="top center",
        fillcolor="rgba(37,99,235,0.12)",
        line=dict(width=2.5),
    )
    fig1.update_xaxes(tickformat="%d/%m", dtick="D1", gridcolor="#e2e8f0")
    fig1.update_yaxes(gridcolor="#e2e8f0")
    fig1.update_layout(**_CHART_LAYOUT)
    st.plotly_chart(fig1, use_container_width=True)

    # ── Evolução semanal: você vs média do time ───────────────────────────────
    _secao("📆 Sua Evolução Semanal", "Seus atendimentos por semana comparado à média do time")
    df["Semana"] = df["Data_Filtro"].dt.to_period("W").dt.start_time

    # Média semanal do time
    evo_time = (
        df.groupby(["Semana", "Colaborador"]).size()
        .reset_index(name="Atendimentos")
        .groupby("Semana")["Atendimentos"].mean()
        .reset_index()
        .rename(columns={"Atendimentos": "Media_Time"})
    )

    # Linha do usuário logado
    if usuario_logado:
        evo_user = (
            df[df["Colaborador"] == usuario_logado]
            .groupby("Semana").size()
            .reset_index(name="Atendimentos")
        )
    else:
        evo_user = pd.DataFrame(columns=["Semana", "Atendimentos"])

    evo_merged = pd.merge(evo_time, evo_user, on="Semana", how="left").fillna(0)

    fig_evo = go.Figure()
    fig_evo.add_trace(go.Scatter(
        x=evo_merged["Semana"], y=evo_merged["Media_Time"].round(1),
        name="Média do time", mode="lines+markers",
        line=dict(color=COR_NEUTRO, width=2, dash="dot"),
        marker=dict(size=6),
        hovertemplate="Média do time<br>Semana: %{x|%d/%m}<br>Atend.: %{y:.1f}<extra></extra>",
    ))
    if usuario_logado:
        fig_evo.add_trace(go.Scatter(
            x=evo_merged["Semana"], y=evo_merged["Atendimentos"],
            name=usuario_logado, mode="lines+markers+text",
            text=evo_merged["Atendimentos"].astype(int),
            textposition="top center",
            line=dict(color=COR_SAC, width=3),
            marker=dict(size=8),
            fill="tozeroy",
            fillcolor="rgba(37,99,235,0.07)",
            hovertemplate=f"{usuario_logado}<br>Semana: %{{x|%d/%m}}<br>Atend.: %{{y}}<extra></extra>",
        ))
    fig_evo.update_xaxes(tickformat="%d/%m", gridcolor="#e2e8f0")
    fig_evo.update_yaxes(gridcolor="#e2e8f0")
    fig_evo.update_layout(**_CHART_LAYOUT)
    st.plotly_chart(fig_evo, use_container_width=True)

    # ── Distribuição por Portal ───────────────────────────────────────────────
    _secao("🗺️ Distribuição por Portal", "Participação de cada marketplace no total de atendimentos")
    portais = df["Portal"].value_counts().reset_index()
    portais.columns = ["Portal", "Qtd"]
    portais["Pct"] = (portais["Qtd"] / portais["Qtd"].sum() * 100).round(1)
    portais["Label"] = portais.apply(lambda r: f"{r['Qtd']}  ({r['Pct']}%)", axis=1)
    portais = portais.sort_values("Qtd")  # crescente → maior fica no topo do eixo Y
    altura_portais = max(320, len(portais) * 42)
    fig4 = px.bar(
        portais, x="Qtd", y="Portal", orientation="h",
        text="Label",
        color="Qtd",
        color_continuous_scale=["#bfdbfe", COR_SAC],
    )
    fig4.update_traces(textposition="outside", textfont_size=13)
    fig4.update_layout(
        height=altura_portais,
        xaxis=dict(visible=False),
        yaxis=dict(tickfont=dict(size=13), gridcolor="#e2e8f0"),
        coloraxis_showscale=False,
        **_CHART_LAYOUT,
    )
    st.plotly_chart(fig4, use_container_width=True)

    # ── Gráficos lado a lado 2 ────────────────────────────────────────────────
    col_c, col_d = st.columns(2)

    with col_c:
        _secao("📂 Top Motivos CRM")
        df_crm = df[df["Motivo_CRM"].notna() & (df["Motivo_CRM"] != "-")]
        if not df_crm.empty:
            crm = df_crm["Motivo_CRM"].value_counts().head(12).reset_index()
            crm.columns = ["Motivo", "Qtd"]
            fig5 = px.bar(
                crm, x="Qtd", y="Motivo", orientation="h", text="Qtd",
                color="Qtd",
                color_continuous_scale=["#fde68a", "#f59e0b"],
            )
            fig5.update_traces(textposition="outside")
            fig5.update_layout(
                height=max(380, len(crm) * 38),
                yaxis={"categoryorder": "total ascending"},
                coloraxis_showscale=False,
                **_CHART_LAYOUT,
            )
            st.plotly_chart(fig5, use_container_width=True)
        else:
            st.info("Sem dados de CRM no período.")

    with col_d:
        _secao("⏰ Picos de Demanda por Hora")
        total_sec = df.groupby("Setor").size().reset_index(name="Total_Setor")
        heat      = df.groupby(["Hora_Int", "Setor"]).size().reset_index(name="Atendimentos")
        heat      = pd.merge(heat, total_sec, on="Setor")
        heat["Pct"] = (heat["Atendimentos"] / heat["Total_Setor"]) * 100
        fig2 = px.line(
            heat, x="Hora_Int", y="Pct", color="Setor", markers=True,
            labels={"Hora_Int": "Hora", "Pct": "% do setor"},
            color_discrete_map={"Pendência": COR_PEND, "SAC": COR_SAC},
        )
        fig2.update_traces(line=dict(width=2.5))
        fig2.update_layout(
            xaxis=dict(tickmode="linear", dtick=1, gridcolor="#e2e8f0"),
            yaxis=dict(ticksuffix="%", gridcolor="#e2e8f0"),
            **_CHART_LAYOUT,
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Motivos por setor ─────────────────────────────────────────────────────
    _secao("📊 Top Motivos CRM por Setor")
    df_mot = df[df["Motivo_CRM"].notna() & (df["Motivo_CRM"] != "-")]
    if not df_mot.empty:
        top10   = df_mot["Motivo_CRM"].value_counts().head(10).index.tolist()
        mot_set = df_mot[df_mot["Motivo_CRM"].isin(top10)].groupby(["Motivo_CRM", "Setor"]).size().reset_index(name="Qtd")
        fig7 = px.bar(
            mot_set, x="Motivo_CRM", y="Qtd", color="Setor", barmode="stack",
            color_discrete_map={"Pendência": COR_PEND, "SAC": COR_SAC},
            text="Qtd",
        )
        fig7.update_traces(textposition="inside")
        fig7.update_xaxes(tickangle=-28, gridcolor="#e2e8f0")
        fig7.update_yaxes(gridcolor="#e2e8f0")
        fig7.update_layout(**_CHART_LAYOUT)
        st.plotly_chart(fig7, use_container_width=True)

    # ── Exportação ────────────────────────────────────────────────────────────
    _secao("📥 Exportação de Dados")
    df_export = df.drop(columns=["Data_Filtro", "Hora_Int"], errors="ignore").copy()
    csv = df_export.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")

    col_e1, col_e2, col_e3 = st.columns([1, 1, 2])
    col_e1.download_button(
        "⬇️ CSV", data=csv,
        file_name="relatorio_engage.csv", mime="text/csv",
        use_container_width=True,
    )
    try:
        excel = _exportar_excel(df)
        col_e2.download_button(
            "📊 Excel (3 abas)", data=excel,
            file_name="relatorio_engage.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    except Exception as e:
        col_e2.warning(f"Excel: {e}")

    # ── Tabela ────────────────────────────────────────────────────────────────
    _secao("📋 Registros Recentes", "Últimos 100 atendimentos registrados")
    df_display = df.sort_values(by=["Data_Filtro", "Hora"], ascending=False).head(100)
    st.data_editor(
        df_display.drop(columns=["Data_Filtro", "Hora_Int"], errors="ignore"),
        use_container_width=True,
        hide_index=True,
        disabled=True,
    )
