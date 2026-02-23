import hashlib
import json
import time

import streamlit as st
import streamlit.components.v1 as components

from modules.templates import carregar_templates, carregar_listas
from modules.sheets import salvar_registro
from modules.validation import validar_sac

_COOLDOWN = 60  # segundos mínimos entre registros idênticos


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


# Mapeamento de campos condicionais: motivo → lista de (label, key, tipo)
CAMPOS_EXTRAS: dict[str, list[tuple]] = {
    "SOLICITAÇÃO DE COLETA": [
        ("Endereço da coleta (Bairro/Cidade):", "end_coleta_sac", "text", "endereco_resumido"),
    ],
    "ASSISTÊNCIA TÉCNICA (DENTRO DOS 7 DIAS)": [
        ("Nome da Fabricante:", "fab_in_7", "text", "fabricante"),
        ("Endereço/Telefone/Infos:", "cont_assist_in_7", "area", "contato_assistencia"),
    ],
    "ASSISTÊNCIA TÉCNICA (FORA DOS 7 DIAS)": [
        ("Data da Compra:", "data_comp_out_7", "text", "data_compra"),
        ("Número da NF:", "nf_out_7", "text", "nota_fiscal"),
        ("Link do Posto Autorizado:", "link_out_7", "text", "link_posto"),
    ],
    "CÓDIGO POSTAL (LOGÍSTICA REVERSA)": [
        ("Código de Postagem:", "cod_post_sac", "text", "codigo_postagem"),
    ],
    "CÓDIGO COLETA DOMICILIAR": [
        ("Código de Coleta:", "cod_col_sac", "text", "codigo_coleta"),
    ],
    "CONFIRMAÇÃO DE ENTREGA": [
        ("Transportadora:", "tr_ent_sac_conf", "select_transp", "transportadora"),
        ("Data da Entrega:", "data_ent_sac", "text", "data_entrega"),
    ],
    "CONVERSÃO GLP/GNV": [
        ("Nome do Fabricante:", "fab_glp", "text", "fabricante"),
        ("Site/Contato:", "site_glp", "text", "site_fabricante"),
    ],
    "OFERECER DESCONTO POR AVARIA": [
        ("Valor do reembolso (R$):", "val_desc", "text", "valor_desconto"),
    ],
    "MERCADORIA EM TRÂNSITO": [
        ("Previsão de Entrega:", "prev_ent", "text", "previsao_entrega"),
        ("Link de Rastreio:", "link_rast", "text", "link_rastreio"),
        ("Nota Fiscal:", "nf_rast", "text", "nota_fiscal"),
        ("Transportadora:", "tr_trans_sac", "select_transp", "transportadora"),
    ],
    "FISCALIZAÇÃO": [
        ("Transportadora:", "tr_fisc_sac", "select_transp", "transportadora"),
    ],
    "INSUCESSO NA ENTREGA (SOLICITAR DADOS)": [
        ("Rua:", "rua_ins", "text", "rua"),
        ("CEP:", "cep_ins", "text", "cep"),
        ("Número:", "num_ins", "text", "numero"),
        ("Bairro:", "bair_ins", "text", "bairro"),
        ("Cidade:", "cid_ins", "text", "cidade"),
        ("Estado:", "uf_ins", "text", "estado"),
        ("Complemento (opcional):", "comp_ins", "text", "complemento"),
        ("Ponto de Referência (opcional):", "ref_ins", "text", "referencia"),
    ],
    "ENTREGA RECUSADA": [
        ("Data/Horário limite:", "data_limite_recusa", "text", "data_limite"),
    ],
    "PEDIDO CANCELADO (ENTREGUE)": [
        ("Data da Entrega:", "data_entrega_canc_ent", "text", "data_entrega"),
    ],
}

LISTA_LIVRE = [
    "OUTROS", "RECLAME AQUI", "INFORMAÇÃO SOBRE COLETA",
    "INFORMAÇÃO SOBRE ENTREGA", "INFORMAÇÃO SOBRE O PRODUTO",
    "INFORMAÇÃO SOBRE O REEMBOLSO",
]

SCRIPTS_MARTINS = [
    "CANCELAMENTO MARTINS (FRETE)",
    "CANCELAMENTO MARTINS (ESTOQUE)",
    "CANCELAMENTO MARTINS (PREÇO)",
]

EXCECOES_NF = [
    "SAUDAÇÃO", "AGRADECIMENTO", "AGRADECIMENTO 2", "PRÉ-VENDA",
    "BARRAR ENTREGA NA TRANSPORTADORA", "ALTERAÇÃO DE ENDEREÇO (SOLICITAÇÃO DE DADOS)",
    "ESTOQUE FALTANTE", "COMPROVANTE DE ENTREGA (MARTINS)", "PEDIDO AMAZON FBA",
    "BAIXA ERRÔNEA", "COBRANÇA INDEVIDA", "INFORMAÇÃO EMBALAGEM",
    "RETIRADA DE ENTREGA", "ENCERRAMENTO DE CHAT", "SOLICITAÇÃO DE COLETA",
] + LISTA_LIVRE


def _hash_ticket_s() -> str:
    """Hash dos campos que identificam unicamente um atendimento de SAC."""
    colab  = st.session_state.get("colab_s", "")
    ped    = st.session_state.get("ped_s", "")
    nf     = st.session_state.get("nf_s", "")
    motivo = st.session_state.get("msg_s", "")
    chave  = f"{colab}|{ped}|{nf}|{motivo}"
    return hashlib.md5(chave.encode()).hexdigest()


def _callback_registrar(texto_final: str, transp_extra: str):
    sufixo = "_s"
    st.session_state[f"texto_persistente{sufixo}"] = texto_final

    # ── Anti-duplicata ────────────────────────────────────────────────────
    hash_atual   = _hash_ticket_s()
    ultimo_hash  = st.session_state.get("_ultimo_hash_s", "")
    ultimo_tempo = st.session_state.get("_ultimo_save_s", 0.0)
    decorrido    = time.time() - ultimo_tempo

    if hash_atual == ultimo_hash and decorrido < _COOLDOWN:
        restante = int(_COOLDOWN - decorrido)
        st.session_state["_aviso_dup_s"] = restante
        return  # Bloqueia sem salvar

    # ── Double-submit (cliques simultâneos) ───────────────────────────────
    if st.session_state.get("_salvando_s"):
        return
    st.session_state["_salvando_s"] = True

    dados = {
        "setor":          "SAC",
        "colaborador":    st.session_state.get("colab_s", ""),
        "motivo":         st.session_state.get("msg_s", ""),
        "portal":         st.session_state.get("portal_s", ""),
        "nota_fiscal":    st.session_state.get("nf_s", ""),
        "numero_pedido":  st.session_state.get("ped_s", ""),
        "motivo_crm":     st.session_state.get("crm_s", ""),
        "transportadora": transp_extra or "-",
    }

    sucesso = salvar_registro(dados)
    st.session_state["_salvando_s"] = False

    if sucesso:
        st.session_state["_ultimo_hash_s"] = hash_atual
        st.session_state["_ultimo_save_s"] = time.time()
        st.session_state["sucesso_recente_s"] = True
        for campo in ["cliente_s", "nf_s", "ped_s"]:
            if campo in st.session_state:
                st.session_state[campo] = ""
        for campo in [
            "end_coleta_sac", "fab_in_7", "cont_assist_in_7", "data_comp_out_7",
            "nf_out_7", "link_out_7", "cod_post_sac", "cod_col_sac", "data_ent_sac",
            "fab_glp", "site_glp", "val_desc", "prev_ent", "link_rast", "nf_rast",
            "rua_ins", "cep_ins", "num_ins", "bair_ins", "cid_ins", "uf_ins",
            "comp_ins", "ref_ins", "data_limite_recusa", "data_entrega_canc_ent",
        ]:
            if campo in st.session_state:
                st.session_state[campo] = ""
    else:
        st.session_state["erro_recente_s"] = True


def _limpar_campos_s():
    campos = [
        "cliente_s", "nf_s", "ped_s",
        "end_coleta_sac", "fab_in_7", "cont_assist_in_7", "data_comp_out_7",
        "nf_out_7", "link_out_7", "cod_post_sac", "cod_col_sac", "data_ent_sac",
        "fab_glp", "site_glp", "val_desc", "prev_ent", "link_rast", "nf_rast",
        "rua_ins", "cep_ins", "num_ins", "bair_ins", "cid_ins", "uf_ins",
        "comp_ins", "ref_ins", "data_limite_recusa", "data_entrega_canc_ent",
        "texto_livre_s",
    ]
    for campo in campos:
        if campo in st.session_state:
            st.session_state[campo] = ""
    st.session_state.pop("_ultimo_hash_s", None)
    st.session_state.pop("_ultimo_save_s", None)
    if "texto_persistente_s" in st.session_state:
        del st.session_state["texto_persistente_s"]


def pagina_sac():
    if st.session_state.pop("sucesso_recente_s", False):
        st.toast("Registrado e Limpo!", icon="✅")
    if st.session_state.pop("erro_recente_s", False):
        st.error("⚠️ Falha ao salvar. Tente novamente.")

    restante = st.session_state.pop("_aviso_dup_s", None)
    if restante is not None:
        st.warning(
            f"⚠️ **Registro duplicado bloqueado.** Este atendimento já foi registrado "
            f"há menos de {restante} segundos. Mude o número do pedido ou NF para "
            f"continuar, ou aguarde antes de registrar o mesmo atendimento novamente."
        )

    st.markdown("""
    <div style="background:linear-gradient(135deg,#0369a1 0%,#0ea5e9 55%,#059669 100%);
                border-radius:20px;padding:1.75rem 2rem;margin-bottom:1.25rem;color:white">
        <h1 style="margin:0;color:white;font-size:1.9rem;font-weight:800;letter-spacing:-0.5px">
            🎧 SAC / Atendimento
        </h1>
        <p style="margin:0.35rem 0 0;opacity:0.85;font-size:0.9rem">
            Gere mensagens padronizadas e registre atendimentos ao cliente
        </p>
    </div>""", unsafe_allow_html=True)

    listas = carregar_listas()
    colabs = listas["colaboradores_sac"]
    portais = listas["lista_portais"]
    transportadoras = listas["lista_transportadoras"]
    motivos_crm = listas["lista_motivo_crm"]
    modelos = carregar_templates("sac")

    lista_motivos = sorted([k for k in modelos if k != "OUTROS"])
    lista_motivos.append("OUTROS")

    # Pré-preenche colaborador com usuário logado e trava
    usuario   = st.session_state.get("usuario_logado", colabs[0])
    idx_colab = colabs.index(usuario) if usuario in colabs else 0
    travado   = bool(usuario)

    st.markdown("""<div style="border-left:4px solid #0ea5e9;padding:0.1rem 0 0.1rem 0.9rem;margin-bottom:0.9rem">
        <span style="font-size:1rem;font-weight:700;color:#1e293b">1. Configuração Obrigatória</span>
    </div>""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        colab = st.selectbox("👤 Colaborador:", colabs, index=idx_colab, key="colab_s", disabled=travado)
    with c2:
        nome_cliente = st.text_input("👤 Nome do Cliente:", key="cliente_s")
    with c3:
        portal = st.selectbox("🛒 Portal:", portais, key="portal_s")

    c4, c5, c6 = st.columns(3)
    with c4:
        nota_fiscal = st.text_input("📄 Nota Fiscal:", key="nf_s")
    with c5:
        numero_pedido = st.text_input("📦 Número do Pedido:", key="ped_s")
    with c6:
        motivo_crm = st.selectbox("📂 Motivo CRM:", motivos_crm, key="crm_s")

    st.markdown("---")

    opcao = st.selectbox("💬 Qual o motivo do contato?", lista_motivos, key="msg_s")

    # ── Campos condicionais ───────────────────────────────────────────────
    dados_extras: dict[str, str] = {}
    transp_extra = ""

    campos_motivo = CAMPOS_EXTRAS.get(opcao, [])
    if campos_motivo:
        st.info(f"📋 Dados adicionais para: {opcao}")
        for label, key, tipo, placeholder in campos_motivo:
            if tipo == "text":
                dados_extras[placeholder] = st.text_input(label, key=key)
            elif tipo == "area":
                dados_extras[placeholder] = st.text_area(label, key=key)
            elif tipo == "select_transp":
                val = st.selectbox(label, transportadoras, key=key)
                dados_extras[placeholder] = val
                transp_extra = val

    st.markdown("<hr style='margin:0.75rem 0;border-color:#e2e8f0'>", unsafe_allow_html=True)
    st.markdown("""<div style="border-left:4px solid #059669;padding:0.1rem 0 0.1rem 0.9rem;margin-bottom:0.9rem">
        <span style="font-size:1rem;font-weight:700;color:#1e293b">2. Visualização da Mensagem</span>
    </div>""", unsafe_allow_html=True)

    # ── Livre escrita ─────────────────────────────────────────────────────
    if opcao in LISTA_LIVRE:
        if opcao == "RECLAME AQUI":
            label_texto = "Digite a resposta do Reclame Aqui:"
        elif "INFORMAÇÃO" in opcao:
            label_texto = f"Detalhes sobre {opcao}:"
        else:
            label_texto = "Digite a mensagem personalizada:"
        texto_base = st.text_area(label_texto, height=200, key="texto_livre_s")
        if texto_base:
            texto_base += f"\n\nEquipe de atendimento Engage Eletro.\n{{colaborador}}"
    else:
        texto_base = modelos.get(opcao, "")

    # ── Substituições base ────────────────────────────────────────────────
    nome_str = nome_cliente if nome_cliente else "(Nome do cliente)"
    ped_str = numero_pedido if numero_pedido else "......"

    texto_base = texto_base.replace("(Nome do cliente)", nome_str)

    # Casos especiais de montagem do texto
    if opcao in SCRIPTS_MARTINS:
        texto_final = texto_base.replace("{nome_cliente}", nome_str)

    elif opcao == "RETIRADA DE ENTREGA":
        texto_final = texto_base.replace("{numero_pedido}", ped_str).replace("(Nome do cliente)", nome_str)

    elif opcao == "SOLICITAÇÃO DE COLETA":
        end_res = dados_extras.get("endereco_resumido", "................")
        texto_final = (texto_base
                       .replace("{numero_pedido}", ped_str)
                       .replace("{endereco_resumido}", end_res or "................"))

    elif opcao == "ENCERRAMENTO DE CHAT":
        texto_final = texto_base

    elif opcao == "ESTOQUE FALTANTE":
        texto_final = texto_base.replace("{portal}", str(portal))

    elif opcao == "COMPROVANTE DE ENTREGA (MARTINS)":
        texto_final = ""

    elif opcao == "BARRAR ENTREGA NA TRANSPORTADORA":
        corpo = modelos["BARRAR ENTREGA NA TRANSPORTADORA"].replace("Olá, (Nome do cliente)!", "").strip()
        texto_final = f"Olá, {nome_str}!\nO atendimento é referente ao seu pedido de número {ped_str}\n\n{corpo}"

    elif opcao == "ALTERAÇÃO DE ENDEREÇO (SOLICITAÇÃO DE DADOS)":
        corpo = modelos["ALTERAÇÃO DE ENDEREÇO (SOLICITAÇÃO DE DADOS)"].replace("Olá, (Nome do cliente)!", "").strip()
        texto_final = f"Olá, {nome_str}!\nO atendimento é referente ao seu pedido de número {ped_str}\n\n{corpo}"

    elif opcao in EXCECOES_NF or opcao in LISTA_LIVRE:
        texto_final = texto_base

    else:
        frase = f"O atendimento é referente ao seu pedido de número {ped_str}..."
        if "\n" in texto_base:
            partes = texto_base.split("\n", 1)
            texto_final = f"{partes[0]}\n\n{frase}\n{partes[1]}"
        else:
            texto_final = f"{frase}\n\n{texto_base}"

    # Assinatura
    assinatura = colab if "AMAZON" not in portal else ""
    texto_final = texto_final.replace("{colaborador}", assinatura)

    # Substitui todos os campos extras
    for chave, valor in dados_extras.items():
        texto_final = texto_final.replace(f"{{{chave}}}", valor if valor else "................")

    st.markdown(f'<div class="preview-box">{texto_final}</div>', unsafe_allow_html=True)
    st.write("")

    # Validação
    dados_validar = {
        "colaborador": colab,
        "nome_cliente": nome_cliente,
        "portal": portal,
        "motivo": opcao,
        "motivo_crm": motivo_crm,
        **dados_extras,
    }
    faltando = validar_sac(dados_validar, opcao)
    if faltando:
        st.error(f"⚠️ Campos obrigatórios: {', '.join(faltando)}")

    # ── Detecta se este ticket foi salvo recentemente ─────────────────────
    hash_atual   = _hash_ticket_s()
    ultimo_hash  = st.session_state.get("_ultimo_hash_s", "")
    ultimo_tempo = st.session_state.get("_ultimo_save_s", 0.0)
    ja_registrado = (
        hash_atual == ultimo_hash
        and bool(numero_pedido or nota_fiscal)
        and (time.time() - ultimo_tempo) < _COOLDOWN
    )

    if ja_registrado:
        restante_btn = int(_COOLDOWN - (time.time() - ultimo_tempo))
        st.info(f"🔒 Atendimento já registrado. Altere o pedido/NF ou aguarde {restante_btn}s para re-registrar.")

    col_btn1, col_btn2 = st.columns([3, 1])
    with col_btn1:
        st.markdown('<div class="botao-registrar">', unsafe_allow_html=True)
        st.button(
            "✅ Registrar e Copiar",
            key="btn_save_sac",
            on_click=_callback_registrar,
            args=(texto_final, transp_extra),
            disabled=bool(faltando) or ja_registrado,
        )
        st.markdown("</div>", unsafe_allow_html=True)
    with col_btn2:
        st.button(
            "🗑️ Limpar Campos",
            key="btn_limpar_sac",
            on_click=_limpar_campos_s,
            use_container_width=True,
        )

    if "texto_persistente_s" in st.session_state:
        st.markdown("---")
        st.info("📝 Último texto registrado (Cópia Segura):")
        st.code(st.session_state["texto_persistente_s"], language="text")
        _copiar_para_clipboard(st.session_state["texto_persistente_s"])
