import hashlib
import json
import time

import streamlit as st
import streamlit.components.v1 as components

from modules.templates import carregar_templates, carregar_listas
from modules.sheets import salvar_registro
from modules.validation import validar_pendencia

# Segundos mínimos entre dois registros idênticos (mesmo colaborador + pedido + NF)
_COOLDOWN = 60


def _copiar_para_clipboard(texto: str):
    texto_json = json.dumps(texto)
    js = f"""<script>
    (function() {{
        const text = {texto_json};
        const el = document.createElement("textarea");
        el.value = text;
        el.style.position = "fixed";
        el.style.left = "-9999px";
        document.body.appendChild(el);
        el.focus();
        el.select();
        try {{ document.execCommand('copy'); }} catch(e) {{}}
        document.body.removeChild(el);
    }})();
    </script>"""
    components.html(js, height=0, width=0)


def _hash_ticket_p() -> str:
    """Hash dos campos que identificam unicamente um atendimento de Pendência."""
    colab = st.session_state.get("colab_p", "")
    ped   = st.session_state.get("ped_p", "")
    nf    = st.session_state.get("nf_p", "")
    chave = f"{colab}|{ped}|{nf}"
    return hashlib.md5(chave.encode()).hexdigest()


def _callback_registrar(texto_final: str):
    sufixo = "_p"
    st.session_state[f"texto_persistente{sufixo}"] = texto_final

    # ── Anti-duplicata ────────────────────────────────────────────────────
    hash_atual   = _hash_ticket_p()
    ultimo_hash  = st.session_state.get("_ultimo_hash_p", "")
    ultimo_tempo = st.session_state.get("_ultimo_save_p", 0.0)
    decorrido    = time.time() - ultimo_tempo

    if hash_atual == ultimo_hash and decorrido < _COOLDOWN:
        restante = int(_COOLDOWN - decorrido)
        st.session_state["_aviso_dup_p"] = restante
        return  # Bloqueia sem salvar

    # ── Double-submit (cliques simultâneos) ───────────────────────────────
    if st.session_state.get("_salvando_p"):
        return
    st.session_state["_salvando_p"] = True

    dados = {
        "setor":          "Pendência",
        "colaborador":    st.session_state.get("colab_p", ""),
        "motivo":         st.session_state.get("msg_p", ""),
        "portal":         st.session_state.get("portal_p", ""),
        "nota_fiscal":    st.session_state.get("nf_p", ""),
        "numero_pedido":  st.session_state.get("ped_p", ""),
        "motivo_crm":     st.session_state.get("crm_p", ""),
        "transportadora": st.session_state.get("transp_p", "-"),
    }

    sucesso = salvar_registro(dados)
    st.session_state["_salvando_p"] = False

    if sucesso:
        # Registra hash e tempo para bloquear re-envio imediato
        st.session_state["_ultimo_hash_p"] = hash_atual
        st.session_state["_ultimo_save_p"] = time.time()
        st.session_state["sucesso_recente_p"] = True
        for campo in ["cliente_p", "nf_p", "ped_p"]:
            if campo in st.session_state:
                st.session_state[campo] = ""
    else:
        st.session_state["erro_recente_p"] = True


def _limpar_campos_p():
    campos = ["cliente_p", "nf_p", "ped_p"]
    for campo in campos:
        if campo in st.session_state:
            st.session_state[campo] = ""
    # Limpar também o hash para não bloquear o próximo registro legítimo
    st.session_state.pop("_ultimo_hash_p", None)
    st.session_state.pop("_ultimo_save_p", None)
    st.session_state.pop("texto_persistente_p", None)


def pagina_pendencias():
    if st.session_state.pop("sucesso_recente_p", False):
        st.toast("Registrado e Limpo!", icon="✅")
    if st.session_state.pop("erro_recente_p", False):
        st.error("⚠️ Falha ao salvar no Google Sheets. Tente novamente.")

    # Aviso de duplicata
    restante = st.session_state.pop("_aviso_dup_p", None)
    if restante is not None:
        st.warning(
            f"⚠️ **Registro duplicado bloqueado.** Este pedido já foi registrado "
            f"há menos de {restante} segundos. Mude o número do pedido ou NF para "
            f"continuar, ou aguarde antes de registrar o mesmo atendimento novamente."
        )

    st.markdown("""
    <div style="background:linear-gradient(135deg,#6d28d9 0%,#7c3aed 50%,#2563eb 100%);
                border-radius:20px;padding:1.75rem 2rem;margin-bottom:1.25rem;color:white">
        <h1 style="margin:0;color:white;font-size:1.9rem;font-weight:800;letter-spacing:-0.5px">
            🚚 Pendências Logísticas
        </h1>
        <p style="margin:0.35rem 0 0;opacity:0.85;font-size:0.9rem">
            Registre ocorrências e copie mensagens prontas para o cliente
        </p>
    </div>""", unsafe_allow_html=True)

    listas         = carregar_listas()
    colabs         = listas["colaboradores_pendencias"]
    portais        = listas["lista_portais"]
    transportadoras = listas["lista_transportadoras"]
    motivos_crm    = listas["lista_motivo_crm"]
    modelos        = carregar_templates("pendencias")

    tipo_fluxo = st.radio("Tipo de Registro:", ["Pendência", "Atraso", "Devolução"], horizontal=True)
    st.markdown("<hr style='margin:0.5rem 0 1rem;border-color:#e2e8f0'>", unsafe_allow_html=True)

    # ── Pendência principal ───────────────────────────────────────────────
    if tipo_fluxo == "Pendência":
        st.markdown("""<div style="border-left:4px solid #7c3aed;padding:0.1rem 0 0.1rem 0.9rem;margin-bottom:0.9rem">
            <span style="font-size:1rem;font-weight:700;color:#1e293b">1. Configuração</span>
        </div>""", unsafe_allow_html=True)

        usuario   = st.session_state.get("usuario_logado", colabs[0])
        idx_colab = colabs.index(usuario) if usuario in colabs else 0
        travado   = bool(usuario)

        c1, c2, c3 = st.columns(3)
        with c1:
            colab = st.selectbox("👤 Colaborador:", colabs, index=idx_colab, key="colab_p", disabled=travado)
        with c2:
            nome_cliente = st.text_input("👤 Nome do Cliente:", key="cliente_p")
        with c3:
            portal = st.selectbox("🛒 Portal:", portais, key="portal_p")

        c4, c5, c6, c7 = st.columns(4)
        with c4:
            nota_fiscal   = st.text_input("📄 Nota Fiscal:", key="nf_p")
        with c5:
            numero_pedido = st.text_input("📦 Número do Pedido:", key="ped_p")
        with c6:
            motivo_crm = st.selectbox("📂 Motivo CRM:", motivos_crm, key="crm_p")
        with c7:
            transp = st.selectbox("🚛 Transportadora:", transportadoras, key="transp_p")

        st.markdown("<hr style='margin:0.75rem 0;border-color:#e2e8f0'>", unsafe_allow_html=True)
        st.markdown("""<div style="border-left:4px solid #2563eb;padding:0.1rem 0 0.1rem 0.9rem;margin-bottom:0.9rem">
            <span style="font-size:1rem;font-weight:700;color:#1e293b">2. Motivo e Visualização</span>
        </div>""", unsafe_allow_html=True)

        opcao = st.selectbox("Selecione o caso:", sorted(modelos.keys()), key="msg_p")

        # Renderização do texto
        texto_cru = modelos[opcao]
        nome_str  = nome_cliente if nome_cliente else "(Nome do cliente)"
        assinatura = colab if "AMAZON" not in portal else ""
        texto_base = (texto_cru
                      .replace("{transportadora}", str(transp))
                      .replace("{colaborador}", assinatura)
                      .replace("{nome_cliente}", nome_str)
                      .replace("(Nome do cliente)", nome_str))

        motivos_sem_texto = [
            "ATENDIMENTO DIGISAC", "2° TENTATIVA DE CONTATO", "3° TENTATIVA DE CONTATO",
            "REENTREGA", "AGUARDANDO TRANSPORTADORA",
        ]
        if opcao not in motivos_sem_texto:
            ped_str = numero_pedido if numero_pedido else "..."
            frase   = f"O atendimento é referente ao seu pedido de número {ped_str}..."
            if "\n" in texto_base:
                partes = texto_base.split("\n", 1)
                texto_final = f"{partes[0]}\n\n{frase}\n{partes[1]}"
            else:
                texto_final = f"{frase}\n\n{texto_base}"
        else:
            texto_final = ""

        st.markdown(f'<div class="preview-box">{texto_final}</div>', unsafe_allow_html=True)
        st.write("")

        # ── Validação de campos obrigatórios ─────────────────────────────
        dados_validar = {
            "colaborador":    colab,
            "nome_cliente":   nome_cliente,
            "portal":         portal,
            "numero_pedido":  numero_pedido,
            "motivo_crm":     motivo_crm,
            "transportadora": transp,
        }
        faltando = validar_pendencia(dados_validar)
        if faltando:
            st.error(f"⚠️ Campos obrigatórios: {', '.join(faltando)}")

        # ── Detecta se este ticket foi salvo recentemente ─────────────────
        hash_atual   = _hash_ticket_p()
        ultimo_hash  = st.session_state.get("_ultimo_hash_p", "")
        ultimo_tempo = st.session_state.get("_ultimo_save_p", 0.0)
        ja_registrado = (
            hash_atual == ultimo_hash
            and bool(numero_pedido or nota_fiscal)   # ignora campos vazios
            and (time.time() - ultimo_tempo) < _COOLDOWN
        )

        if ja_registrado:
            restante_btn = int(_COOLDOWN - (time.time() - ultimo_tempo))
            st.info(f"🔒 Pedido já registrado. Altere o pedido/NF ou aguarde {restante_btn}s para re-registrar.")

        col_btn1, col_btn2 = st.columns([3, 1])
        with col_btn1:
            st.markdown('<div class="botao-registrar">', unsafe_allow_html=True)
            st.button(
                "✅ Registrar e Copiar",
                key="btn_save_pend",
                on_click=_callback_registrar,
                args=(texto_final,),
                disabled=bool(faltando) or ja_registrado,
            )
            st.markdown("</div>", unsafe_allow_html=True)
        with col_btn2:
            st.button(
                "🗑️ Limpar Campos",
                key="btn_limpar_pend",
                on_click=_limpar_campos_p,
                use_container_width=True,
            )

        if "texto_persistente_p" in st.session_state:
            st.markdown("---")
            st.info("📝 Último texto registrado (Cópia Segura):")
            st.code(st.session_state["texto_persistente_p"], language="text")
            _copiar_para_clipboard(st.session_state["texto_persistente_p"])

    # ── Atraso ────────────────────────────────────────────────────────────
    elif tipo_fluxo == "Atraso":
        st.subheader("Registro de Atraso")
        with st.form("form_atraso", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                colab  = st.selectbox("👤 Colaborador:", colabs)
                nf     = st.text_input("📄 Nota Fiscal:")
                pedido = st.text_input("📦 Número do Pedido:")
            with c2:
                transp = st.selectbox("🚛 Transportadora:", transportadoras)
                status = st.selectbox("Status:", ["ENTREGUE", "CANCELADO", "COBRADO"])
            submitted = st.form_submit_button("✅ Registrar Atraso")
            if submitted:
                salvar_registro({
                    "setor": "Pendência", "colaborador": colab,
                    "motivo": f"ATRASO - {status}", "portal": "-",
                    "nota_fiscal": nf, "numero_pedido": pedido,
                    "motivo_crm": "-", "transportadora": transp,
                })
                st.toast("Atraso registrado!", icon="✅")

    # ── Devolução ─────────────────────────────────────────────────────────
    elif tipo_fluxo == "Devolução":
        st.subheader("Registro de Devolução")
        with st.form("form_devolucao", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                colab  = st.selectbox("👤 Colaborador:", colabs)
                nf     = st.text_input("📄 Nota Fiscal:")
                pedido = st.text_input("📦 Número do Pedido:")
            with c2:
                transp = st.selectbox("🚛 Transportadora:", transportadoras)
                status = st.selectbox("Status:", ["DEVOLVIDO", "COBRADO"])
            submitted = st.form_submit_button("✅ Registrar Devolução")
            if submitted:
                salvar_registro({
                    "setor": "Pendência", "colaborador": colab,
                    "motivo": f"DEVOLUÇÃO - {status}", "portal": "-",
                    "nota_fiscal": nf, "numero_pedido": pedido,
                    "motivo_crm": "-", "transportadora": transp,
                })
                st.toast("Devolução registrada!", icon="✅")
