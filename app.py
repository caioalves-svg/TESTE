import streamlit as st
import pandas as pd
import plotly.express as px
import os
import pytz
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import streamlit.components.v1 as components

# ==========================================
#      CONFIGURAÇÃO INICIAL
# ==========================================
st.set_page_config(page_title="Sistema Integrado Engage", page_icon="🚀", layout="wide")

# ==========================================
#      CONEXÃO GOOGLE SHEETS (HÍBRIDA & SEGURA)
# ==========================================
NOME_PLANILHA_GOOGLE = "Base_Atendimentos_Engage" 

def conectar_google_sheets():
    """
    Conecta ao Google Sheets.
    PRIORIDADE: Tenta ler dos Secrets do Streamlit Cloud (Recomendado).
    SECUNDÁRIO: Tenta ler arquivo local (Apenas para testes no PC).
    """
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = None

    # 1. TENTATIVA: Ler dos Secrets (Configuração da Nuvem)
    if "gcp_service_account" in st.secrets:
        try:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        except Exception as e:
            st.warning(f"Erro ao ler Secrets: {e}")

    # 2. TENTATIVA: Ler arquivo local (Se não achou secrets)
    if creds is None:
        if os.path.exists("credentials.json"):
            creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        else:
            st.error("🚨 ERRO DE CONEXÃO: Credenciais não encontradas.")
            st.info("Passo a Passo para corrigir no Streamlit Cloud:")
            st.markdown("1. Vá no painel do seu App no Streamlit.")
            st.markdown("2. Clique em 'Settings' > 'Secrets'.")
            st.markdown("3. Cole o conteúdo do seu JSON lá (veja o formato abaixo do código).")
            return None

    # Conectar
    try:
        client = gspread.authorize(creds)
        sheet = client.open(NOME_PLANILHA_GOOGLE).sheet1
        return sheet
    except gspread.SpreadsheetNotFound:
        st.error(f"⚠️ Planilha '{NOME_PLANILHA_GOOGLE}' não encontrada. Verifique se você compartilhou a planilha com o e-mail do robô.")
        return None
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return None

def carregar_dados():
    """Lê os dados diretamente do Google Sheets."""
    sheet = conectar_google_sheets()
    if sheet:
        try:
            dados = sheet.get_all_records()
            if dados:
                return pd.DataFrame(dados)
            else:
                return pd.DataFrame(columns=["Data", "Hora", "Dia_Semana", "Setor", "Colaborador", "Motivo", "Portal", "Nota_Fiscal", "Numero_Pedido", "Motivo_CRM", "Transportadora"])
        except Exception as e:
            st.error(f"Erro ao ler dados: {e}")
    return pd.DataFrame()

def salvar_registro(setor, colaborador, motivo, portal, nf, numero_pedido, motivo_crm, transportadora="-"):
    """Salva uma nova linha no Google Sheets."""
    sheet = conectar_google_sheets()
    if sheet:
        agora = obter_data_hora_brasil()
        
        # Força conversão para string para evitar erros no Excel depois
        str_nf = str(nf)
        str_pedido = str(numero_pedido)

        nova_linha = [
            agora.strftime("%d/%m/%Y"),      # Data
            agora.strftime("%H:%M:%S"),      # Hora
            agora.strftime("%A"),            # Dia da Semana
            setor,
            colaborador,
            motivo,
            portal,
            str_nf,                          # Salva como Texto
            str_pedido,                      # Salva como Texto
            motivo_crm,
            transportadora
        ]
        try:
            sheet.append_row(nova_linha)
            return True
        except Exception as e:
            st.error(f"Erro ao gravar no Google Sheets: {e}")
            return False
    return False

def converter_para_excel_csv(df):
    """Converte DF para CSV forçando colunas numéricas a serem texto."""
    df_export = df.copy()
    # Adiciona um caractere invisível ou força string para o Excel não comer o número
    df_export['Nota_Fiscal'] = df_export['Nota_Fiscal'].astype(str)
    df_export['Numero_Pedido'] = df_export['Numero_Pedido'].astype(str)
    return df_export.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')

# ==========================================
#      DADOS E LISTAS
# ==========================================

colaboradores_pendencias = sorted(["Ana", "Mariana", "Gabriela", "Layra", "Maria Eduarda", "Akisia", "Marcelly", "Camilla"])
colaboradores_sac = sorted(["Ana Carolina", "Ana Victoria", "Eliane", "Cassia", "Juliana", "Tamara", "Rafaela", "Telliane", "Isadora", "Lorrayne", "Leticia", "Julia"])

lista_transportadoras = sorted(["4ELOS", "ATUAL", "BRASIL WEB", "FAVORITA", "FRONTLOG", "GENEROSO", "JADLOG", "LOGAN", "MMA", "PAJUÇARA", "PATRUS", "REBOUÇAS", "REDE SUL", "RIO EXPRESS", "TJB", "TOTAL", "TRILOG"])

lista_portais = sorted([
    "ALIEXPRESS", "AMAZON - EXTREMA", "AMAZON | ENGAGE LOG", "AMAZON DBA", "AMERICANAS - EXTREMA",
    "B2W", "BRADESCO SHOP", "CARREFOUR", "CARREFOUR OUTLET", "CNOVA", "CNOVA - EXTREMA",
    "FAST SHOP", "KABUM", "LEROY - EXTREMA", "MADEIRA MADEIRA", "MAGALU - EXTREMA",
    "MAGALU ELETRO", "MAGALU INFO", "MARTINS", "MEGA B2B", "MELI OUTLET", "MERCADO LIVRE",
    "MERCADO LIVRE - EXTREMA", "O MAGAZINE", "PADRÃO", "SHOPEE", "SKYHUB", "TIKTOK",
    "WAPSTORE - ENGAGE", "WEBCONTINENTAL", "WINECOM - LOJA INTEGRADA", "ZEMA"
])

lista_motivo_crm = sorted([
    "ACAREAÇÃO", "ACORDO CLIENTE", "ALTERAÇÃO DE NOTA FISCAL", "AREA DE RISCO", "AREA NÃO ATENDIDA",
    "ARREPENDIMENTO", "ARREPENDIMENTO - DEVOLUÇÃO AMAZON", "ARREPENDIMENTO POR QUALIDADE DO PRODUTO",
    "ATRASO NA ENTREGA", "ATRASO NA EXPEDIÇÃO", "AUSENTE", "AVARIA", "CANCELAMENTO FORÇADO PELO PORTAL",
    "CASO JURIDÍCO", "CORREÇÃO DE ENDEREÇO", "DEFEITO", "DESCONHECIDO", "DESCONTO",
    "DEVOLUÇÃO SEM INFORMAÇÃO", "ENDEREÇO NÃO LOCALIZADO", "ENTREGA C/ AVARIA FORÇADA",
    "ENTREGUE E CANCELADO", "ERRO DE CADASTRO", "ERRO DE EXPEDIÇÃO", "ERRO DE INTEGRAÇÃO DE FATURAMENTO",
    "ESTOQUE FALTANTE", "EXTRAVIO", "FALTA DE ETIQUETA ENVIAS", "INSUCESSO NA ENTREGA",
    "ITEM FALTANTE", "MERCADORIA RETIDA", "MUDOU-SE", "NOTA RETIDA", "PAGAMENTO/REEMBOLSO",
    "RECOBRANÇA DE CLIENTE", "RECUSA", "RETENÇÃO", "SEM ABERTURA DE CRM", "SEM RASTREIO", "SUSPEITA DE FRAUDE",
    "TROCA DE ETIQUETA", "ZONA RURAL"
])

# ==========================================
#      SCRIPTS (MENSAGENS PENDÊNCIAS)
# ==========================================
modelos_pendencias = {
    "ATENDIMENTO DIGISAC": "", 
    "2° TENTATIVA DE CONTATO": "", 
    "3° TENTATIVA DE CONTATO": "",
    "CANCELAMENTO MARTINS (FRETE)": """Olá, {nome_cliente}!\n\nIdentificamos que, devido à localização de entrega, o valor do frete excedeu o limite operacional permitido para esta transação. Por este motivo, solicitamos a gentileza de seguir com o cancelamento do pedido.\n\nAtenciosamente, {colaborador} | Equipe de Atendimento Engage Eletro.""",
    "CANCELAMENTO MARTINS (ESTOQUE)": """Olá, {nome_cliente}!\n\nDevido a uma indisponibilidade pontual em nosso estoque logístico, não conseguiremos processar o envio do seu pedido desta vez. Para evitar maiores transtornos, pedimos que realize o cancelamento da compra.\n\nAtenciosamente, {colaborador} | Equipe de Atendimento Engage Eletro.""",
    "CANCELAMENTO MARTINS (PREÇO)": """Olá, {nome_cliente}!\n\nIdentificamos uma divergência no valor do produto devido a um erro técnico na transmissão de nossa tabela de precificação. Em razão disso, solicitamos o cancelamento do pedido para que possamos regularizar a situação.\n\nAtenciosamente, {colaborador} | Equipe de Atendimento Engage Eletro.""",
    "AUSENTE": """Olá, (Nome do cliente)! Tudo bem? Esperamos que sim!\n\nA transportadora {transportadora} tentou realizar a entrega de sua mercadoria no endereço cadastrado, porém, o responsável pelo recebimento estava ausente.\n\nPara solicitarmos uma nova tentativa de entrega à transportadora, poderia por gentileza, nos confirmar dados abaixo?\n\nRua: \nNúmero: \nBairro: \nCEP: \nCidade: \nEstado: \nPonto de Referência: \nRecebedor: \nTelefone: \n\nApós a confirmação dos dados acima, iremos solicitar que a transportadora realize uma nova tentativa de entrega que irá ocorrer no prazo de até 3 a 5 dias úteis. Caso não tenhamos retorno, o produto será devolvido ao nosso Centro de Distribuição e seguiremos com o cancelamento da compra.\n\nQualquer dúvida, estamos à disposição!\n\nAtenciosamente,\n{colaborador}""",
    "SOLICITAÇÃO DE CONTATO": """Olá, (Nome do cliente)! Tudo bem? Esperamos que sim!\n\nPara facilitar a entrega da sua mercadoria e não ter desencontros com a transportadora {transportadora}, o senhor pode por gentileza nos enviar um número de telefone ativo para alinharmos a entrega?\n\nAguardo o retorno!\n\nAtenciosamente,\n{colaborador}""",
    "ENDEREÇO NÃO LOCALIZADO": """Olá, (Nome do cliente)! Tudo bem? Esperamos que sim!\n\nA transportadora {transportadora} tentou realizar a entrega de sua mercadoria, porém, não localizou o endereço.\n\nPara solicitarmos uma nova tentativa de entrega à transportadora, poderia por gentileza, nos confirmar dados abaixo:\n\nRua:\nNúmero:\nBairro:\nCEP:\nCidade:\nEstado:\nPonto de Referência:\nRecebedor:\nTelefone:\n\nApós a confirmação dos dados acima, iremos solicitar que a transportadora realize uma nova tentativa de entrega que irá ocorrer no prazo de até 3 a 5 dias úteis. Caso não tenhamos retorno, o produto será devolvido ao nosso Centro de Distribuição e seguiremos com o cancelamento da compra.\n\nAtenciosamente,\n{colaborador}""",
    "ÁREA DE RISCO": """Olá, (Nome do cliente)! Tudo bem? Espero que sim!\n\nA transportadora {transportadora}, informou que está com dificuldades para realizar a entrega no endereço cadastrado no portal. Dessa forma, peço por gentileza que nos informe um endereço alternativo e também telefones ativos para melhor comunicação.\n\nCaso não possua um outro endereço, sua mercadoria ficará disponível para retirada da base da transportadora.\n\nQualquer dúvida me coloco à disposição para ajudá-lo!\n\nAtenciosamente,\n{colaborador}""",
    "EXTRAVIO / AVARIA": """Olá, (Nome do cliente)! Tudo bem? Espero que sim!\n\nInfelizmente fomos informados pela transportadora {transportadora} que sua mercadoria foi furtada/avariada em transporte. Antes de tudo, pedimos desculpas pelo ocorrido e por todo transtorno causado.\n\nGostaríamos de saber se o senhor aceita o envio de uma nova mercadoria? O prazo para entrega é de 5 a 7 dias úteis, podendo ocorrer antes.\n\nNovamente, pedimos desculpas. Qualquer dúvida me coloco à disposição para ajudá-lo!\n\nAtenciosamente,\n{colaborador}""",
    "RECUSA DE ENTREGA": """Olá, (Nome do cliente)!\n\nA transportadora {transportadora} informou que a entrega foi recusada. Houve algum problema com a apresentação da carga? O senhor deseja o cancelamento da compra?\n\nCaso não tenhamos retorno e o produto seja devolvido ao nosso estoque, seguiremos com o cancelamento da compra.\n\nQualquer dúvida me coloco à disposição para ajudá-lo!\n\nAtenciosamente,\n{colaborador}""",
    "SOLICITAÇÃO DE BARRAMENTO": """Olá, (Nome do cliente)! Tudo bem? Esperamos que sim!\n\nSolicitamos à transportadora {transportadora} que barre a entrega da sua mercadoria. Caso tentem realizar a entrega, gentileza recusar o recebimento.\n\nAssim que a mercadoria der entrada em nosso estoque, liberamos o estorno.\n\nAtenciosamente,\n{colaborador}""",
    "GARANTIA DE A A Z (AMAZON)": """Olá, (Nome do cliente)! Tudo bem? Esperamos que sim!\n\nDiante da abertura da Garantia A a Z, solicitamos à transportadora {transportadora} responsável que barre a entrega e aguardaremos a confirmação da suspensão da entrega, a fim de possibilitar a liberação do reembolso pela plataforma.\n\nAtenciosamente,\n{colaborador}""",
    "EM CASO DE REEMBOLSO": """Olá, (Nome do cliente)! Tudo bem? Esperamos que sim!\n\nO cancelamento foi liberado conforme solicitado. O reembolso é realizado de acordo com a forma de pagamento da compra:\n\nPara pagamentos com boleto, o reembolso será feito na conta bancária especificada pelo cliente ou como um vale-presente. Se todos os dados da sua conta bancária estiverem corretos, o reembolso pode levar até 3 dias úteis para constar na conta.\n\nCaso você tenha pago com cartão de crédito, dependendo da data de fechamento e vencimento do seu cartão, o reembolso pode levar de uma a duas faturas.\n\nPara pagamento em PIX, o reembolso será realizado na conta PIX em um dia útil.\n\nAtenciosamente,\n{colaborador}""",
    "MERCADORIA SEM ESTOQUE": """Olá, (Nome do cliente)! Tudo bem? Esperamos que sim!\n\nHouve um erro no sistema que vendeu um item a mais e o lojista não possui a mercadoria disponível em estoque no momento. Verificamos com o nosso fornecedor, e infelizmente não tem a previsão de entrega de um novo lote.\n\nPedimos desculpas pelo transtorno causado.\n\nGostaríamos de saber se podemos seguir com o cancelamento do pedido para que a loja da compra possa realizar o estorno total.\n\nAtenciosamente,\n{colaborador}""",
    "ENDEREÇO EM ZONA RURAL": """Olá, (Nome do cliente)! Tudo bem? Esperamos que sim!\n\nA transportadora {transportadora} nos informou que está com dificuldades para realizar a entrega no endereço cadastrado no portal.\n\nPeço por gentileza que nos informe um endereço alternativo e também telefones ativos para melhor comunicação. Caso o senhor não possua um outro endereço, sua mercadoria ficará disponível para retirada a base da transportadora.\n\nAtenciosamente,\n{colaborador}""",
    "REENVIO DE PRODUTO": """Olá, (Nome do cliente)! Tudo bem? Esperamos que sim!\n\nConforme solicitado, realizamos o envio de um novo produto ao senhor. Em até 48h você terá acesso a sua nova nota fiscal e poderá acompanhar os passos de sua entrega:\n\nLink: https://ssw.inf.br/2/rastreamento_pf?\n(Necessário inserir o CPF)\n\nNovamente peço desculpas por todo transtorno causado.\n\nAtenciosamente,\n{colaborador}"""
}

# Ordena a lista de chaves (Motivos do Contato) para o Dropdown
lista_motivos_contato = sorted([k for k in modelos_sac.keys() if k != "OUTROS"])
lista_motivos_contato.append("OUTROS")

# ==========================================
#      FUNÇÕES DE BANCO DE DADOS
# ==========================================
def obter_data_hora_brasil():
    fuso_br = pytz.timezone('America/Sao_Paulo')
    return datetime.now(fuso_br)

def copiar_para_clipboard(texto):
    texto_json = json.dumps(texto)
    js = f"""
    <script>
    function copyToClipboard() {{
        const text = {texto_json};
        const textArea = document.createElement("textarea");
        textArea.value = text;
        textArea.style.position = "fixed";
        textArea.style.left = "-9999px";
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        try {{ document.execCommand('copy'); }} catch (err) {{}}
        document.body.removeChild(textArea);
    }}
    copyToClipboard();
    </script>
    """
    components.html(js, height=0, width=0)

# ==========================================
#      DESIGN CLEAN
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    .stApp { background-color: #f8fafc !important; font-family: 'Inter', sans-serif; }
    section[data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 1px solid #e2e8f0; }
    .stApp, .stApp * { color: #334155 !important; }
    h1, h2, h3, h4, h5, h6 { color: #0f172a !important; font-weight: 700; }
    
    .stSelectbox div[data-baseweb="select"] > div, 
    .stTextInput input, .stDateInput input, .stTextArea textarea {
        background-color: #ffffff !important; 
        border: 1px solid #94a3b8 !important; 
        border-radius: 8px !important; 
        color: #1e293b !important;
    }
    ::placeholder { color: #94a3b8 !important; opacity: 1; }

    .preview-box { 
        background-color: #f1f5f9 !important; border-left: 5px solid #3b82f6; 
        border-radius: 4px; padding: 20px; color: #334155 !important; 
        white-space: pre-wrap; margin-top: 10px; font-size: 14px; 
    }

    .botao-registrar .stButton button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important; 
        color: white !important; border: none; padding: 0.8rem 2rem; 
        border-radius: 8px; font-weight: 600; width: 100%; 
        box-shadow: 0 4px 6px rgba(16, 185, 129, 0.2);
    }
    .botao-registrar .stButton button:hover { transform: translateY(-2px); }

    .stDownloadButton button { background-color: #3b82f6 !important; color: white !important; border: none !important; border-radius: 8px; font-weight: 600; width: 100%; }
    .stDownloadButton button:hover { background-color: #2563eb !important; }
    
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] { gap: 0rem; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
#           MENU LATERAL
# ==========================================
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", width=180)
    st.sidebar.markdown("##")

st.sidebar.caption("MENU PRINCIPAL")
pagina_escolhida = st.sidebar.radio(
    "Navegação:",
    ("Pendências Logísticas", "SAC / Atendimento", "📊 Dashboard Gerencial"),
    label_visibility="collapsed"
)
st.sidebar.markdown("---")

# ==========================================
#           PÁGINA PENDÊNCIAS
# ==========================================
def pagina_pendencias():
    st.title("🚚 Pendências Logísticas")
    st.markdown("---")
    
    col1, col2 = st.columns([1, 1.5], gap="medium")
    
    with col1:
        st.subheader("1. Configuração")
        colab = st.selectbox("👤 Colaborador:", colaboradores_pendencias, key="colab_p")
        nome_cliente = st.text_input("👤 Nome do Cliente:", key="cliente_p")
        
        portal = st.selectbox("🛒 Portal:", lista_portais, key="portal_p")
        nota_fiscal = st.text_input("📄 Nota Fiscal:", key="nf_p")
        numero_pedido = st.text_input("📦 Número do Pedido:", key="ped_p")
        motivo_crm = st.selectbox("📂 Motivo CRM:", lista_motivo_crm, key="crm_p")
        
        transp = st.selectbox("🚛 Qual a transportadora?", lista_transportadoras, key="transp_p")
        
        st.markdown("---")
        st.subheader("2. Motivo")
        opcao = st.selectbox("Selecione o caso:", list(modelos_pendencias.keys()), key="msg_p")

    with col2:
        st.subheader("3. Visualização")
        texto_cru = modelos_pendencias[opcao]
        
        nome_cliente_str = nome_cliente if nome_cliente else "(Nome do cliente)"
        assinatura_nome = colab

        if "AMAZON" in portal:
            assinatura_nome = ""

        # Substituições Gerais
        texto_base = texto_cru.replace("{transportadora}", transp)\
                              .replace("{colaborador}", assinatura_nome)\
                              .replace("{nome_cliente}", nome_cliente_str)\
                              .replace("(Nome do cliente)", nome_cliente_str)

        # Regra Via Varejo: Mantém o "Olá" (Pedido atualizado)
        if portal in ["CNOVA", "CNOVA - EXTREMA", "PONTO", "CASAS BAHIA"]:
             # Apenas garante que começa com Olá e Nome
             pass 

        motivos_sem_texto = ["ATENDIMENTO DIGISAC", "2° TENTATIVA DE CONTATO", "3° TENTATIVA DE CONTATO"]
        scripts_martins = ["CANCELAMENTO MARTINS (FRETE)", "CANCELAMENTO MARTINS (ESTOQUE)", "CANCELAMENTO MARTINS (PREÇO)"]
        
        if opcao not in motivos_sem_texto:
            if opcao in scripts_martins:
                texto_final = texto_base
            else:
                ped_str = numero_pedido if numero_pedido else "..."
                frase_pedido = f"O atendimento é referente ao seu pedido de número {ped_str}..."
                
                if "\n" in texto_base:
                    partes = texto_base.split("\n", 1)
                    texto_final = f"{partes[0]}\n\n{frase_pedido}\n{partes[1]}"
                else:
                    texto_final = f"{frase_pedido}\n\n{texto_base}"
        else:
            texto_final = ""
        
        st.markdown(f'<div class="preview-box">{texto_final}</div>', unsafe_allow_html=True)
        
        st.write("")
        st.markdown('<div class="botao-registrar">', unsafe_allow_html=True)
        if st.button("✅ Registrar e Copiar", key="btn_save_pend"):
            sucesso = salvar_registro("Pendência", colab, opcao, portal, nota_fiscal, numero_pedido, motivo_crm, transp)
            if sucesso:
                st.toast("Registrado com sucesso na Nuvem! ☁️", icon="✨")
                copiar_para_clipboard(texto_final)
                st.code(texto_final, language="text")
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
#           PÁGINA SAC
# ==========================================
def pagina_sac():
    st.title("🎧 SAC / Atendimento")
    st.markdown("---")
    
    col1, col2 = st.columns([1, 1.5], gap="medium")
    dados = {}
    
    with col1:
        st.subheader("1. Configuração Obrigatória")
        
        colab = st.selectbox("👤 Colaborador:", colaboradores_sac, key="colab_s")
        nome_cliente = st.text_input("👤 Nome do Cliente:", key="cliente_s")
        portal = st.selectbox("🛒 Portal:", lista_portais, key="portal_s")
        nota_fiscal = st.text_input("📄 Nota Fiscal:", key="nf_s")
        numero_pedido = st.text_input("📦 Número do Pedido:", key="ped_s")
        motivo_crm = st.selectbox("📂 Motivo CRM:", lista_motivo_crm, key="crm_s")
        
        st.markdown("---")
        
        opcao = st.selectbox("💬 Qual o motivo do contato?", lista_motivos_contato, key="msg_s")
        
        # === CORREÇÃO DOS ERROS DE ID (Adicionei key= em todos) ===
        op_upper = opcao.upper()
        if "SOLICITAÇÃO DE COLETA" in op_upper:
            st.info("🚚 Endereço")
            dados["{endereco_resumido}"] = st.text_input("Endereço da coleta (Bairro/Cidade):", key="end_coleta_sac")
        elif "ASSISTÊNCIA TÉCNICA (DENTRO DOS 7 DIAS)" in op_upper:
            st.info("🔧 Dados da Assistência")
            dados["{fabricante}"] = st.text_input("Nome da Fabricante:", key="fab_in_7")
            dados["{contato_assistencia}"] = st.text_area("Endereço/Telefone/Infos:", key="cont_assist_in_7")
        elif "ASSISTÊNCIA TÉCNICA (FORA DOS 7 DIAS)" in op_upper:
            st.info("📅 Dados da Compra")
            # --- Correção do ID Duplicado Aqui ---
            dados["{data_compra}"] = st.text_input("Data da Compra:", key="data_comp_out_7")
            dados["{nota_fiscal}"] = st.text_input("Número da NF (Repetir se necessário):", key="nf_out_7")
            dados["{link_posto}"] = st.text_input("Link do Posto Autorizado:", key="link_out_7")
        elif "CÓDIGO POSTAL" in op_upper or "CÓDIGO COLETA" in op_upper:
            st.info("📮 Código de Postagem")
            k = "{codigo_postagem}" if "CÓDIGO POSTAL" in op_upper else "{codigo_coleta}"
            dados[k] = st.text_input("Código de Coleta/Postagem:", key="cod_post_sac")
        elif "CONFIRMAÇÃO DE ENTREGA" in op_upper:
            st.info("🚚 Dados da Entrega")
            dados["{transportadora}"] = st.selectbox("Transportadora:", lista_transportadoras, key="tr_ent_sac_conf")
            dados["{data_entrega}"] = st.text_input("Data da Entrega:", key="data_ent_sac")
        elif "CONVERSÃO GLP" in op_upper:
            st.info("🔥 Dados do Fabricante")
            dados["{fabricante}"] = st.text_input("Nome do Fabricante:", key="fab_glp")
            dados["{site_fabricante}"] = st.text_input("Site/Contato:", key="site_glp")
        elif "OFERECER DESCONTO" in op_upper:
            st.info("💰 Proposta de Valor")
            dados["{valor_desconto}"] = st.text_input("Valor do reembolso (R$):", key="val_desc")
        elif "MERCADORIA EM TRÂNSITO" in op_upper:
            st.info("📦 Rastreamento")
            dados["{previsao_entrega}"] = st.text_input("Previsão de Entrega:", key="prev_ent")
            dados["{link_rastreio}"] = st.text_input("Link de Rastreio:", key="link_rast")
            dados["{nota_fiscal}"] = st.text_input("Nota Fiscal:", key="nf_rast")
            dados["{transportadora}"] = st.selectbox("Transportadora:", lista_transportadoras, key="tr_trans_sac")
        elif "FISCALIZAÇÃO" in op_upper:
            st.info("🛑 Fiscalização")
            dados["{transportadora}"] = st.selectbox("Transportadora:", lista_transportadoras, key="tr_fisc_sac")
        elif "INSUCESSO NA ENTREGA" in op_upper:
            st.info("🏠 Endereço para Confirmar")
            dados["{rua}"] = st.text_input("Rua:", key="rua_ins")
            dados["{cep}"] = st.text_input("CEP:", key="cep_ins")
            dados["{numero}"] = st.text_input("Número:", key="num_ins")
            dados["{bairro}"] = st.text_input("Bairro:", key="bair_ins")
            dados["{cidade}"] = st.text_input("Cidade:", key="cid_ins")
            dados["{estado}"] = st.text_input("Estado:", key="uf_ins")
            dados["{complemento}"] = st.text_input("Complemento (opcional):", value="", key="comp_ins")
            dados["{referencia}"] = st.text_input("Ponto de Referência (opcional):", value="", key="ref_ins")

    with col2:
        st.subheader("2. Visualização")
        
        if opcao == "OUTROS":
            texto_base = st.text_area("Digite a mensagem personalizada:", height=200)
            if texto_base:
                texto_base += f"\n\nEquipe de atendimento Engage Eletro.\n{{colaborador}}"
        else:
            texto_base = modelos_sac.get(opcao, "")

        nome_cliente_str = nome_cliente if nome_cliente else "(Nome do cliente)"
        texto_base = texto_base.replace("(Nome do cliente)", nome_cliente_str)

        # Regra Via Varejo ATUALIZADA (Olá! Nome)
        if portal in ["CNOVA", "CNOVA - EXTREMA", "PONTO", "CASAS BAHIA"]:
             texto_base = texto_base.replace(f"Olá, {nome_cliente_str}", f"Olá, {nome_cliente_str}!")

        # Regra Frase Pedido
        excecoes_nf = ["SAUDAÇÃO", "AGRADECIMENTO", "AGRADECIMENTO 2", "PRÉ-VENDA", "OUTROS"]
        
        if opcao not in excecoes_nf:
            ped_str = numero_pedido if numero_pedido else "..."
            frase_pedido = f"O atendimento é referente ao seu pedido de número {ped_str}..."
            
            if "\n" in texto_base:
                partes = texto_base.split("\n", 1)
                texto_final = f"{partes[0]}\n\n{frase_pedido}\n{partes[1]}"
            else:
                texto_final = f"{frase_pedido}\n\n{texto_base}"
        else:
            texto_final = texto_base

        assinatura_nome = colab
        if "AMAZON" in portal:
            assinatura_nome = "" 
        
        texto_final = texto_final.replace("{colaborador}", assinatura_nome)
        
        for chave, valor in dados.items():
            substituto = valor if valor else "................"
            texto_final = texto_final.replace(chave, substituto)
        
        st.markdown(f'<div class="preview-box">{texto_final}</div>', unsafe_allow_html=True)

        st.write("")
        st.markdown('<div class="botao-registrar">', unsafe_allow_html=True)
        
        transp_usada = "-"
        if "{transportadora}" in dados:
            transp_usada = dados["{transportadora}"]
            
        if st.button("✅ Registrar e Copiar", key="btn_save_sac"):
            sucesso = salvar_registro("SAC", colab, opcao, portal, nota_fiscal, numero_pedido, motivo_crm, transp_usada)
            if sucesso:
                st.toast("Registrado com sucesso na Nuvem! ☁️", icon="✨")
                copiar_para_clipboard(texto_final)
                st.code(texto_final, language="text")
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
#           DASHBOARD
# ==========================================
def pagina_dashboard():
    st.title("📊 Dashboard Gerencial (Nuvem)")
    st.markdown("Visão estratégica em tempo real.")
    st.markdown("---")

    # Verifica se existem credenciais (local ou nuvem)
    tem_secrets = "gcp_service_account" in st.secrets
    tem_arquivo = os.path.exists("credentials.json")

    if not tem_secrets and not tem_arquivo:
        st.error("🚨 Credenciais não encontradas. Configure as 'Secrets' no Streamlit Cloud.")
        return

    try:
        df = carregar_dados()
        if df.empty:
            st.warning("A planilha do Google Sheets está vazia.")
            return

        df["Data_Filtro"] = pd.to_datetime(df["Data"], format="%d/%m/%Y", errors='coerce')
        
        st.sidebar.markdown("---")
        st.sidebar.subheader("Filtros do Painel")
        
        data_min = df["Data_Filtro"].min().date() if not df["Data_Filtro"].isnull().all() else datetime.today()
        data_max = df["Data_Filtro"].max().date() if not df["Data_Filtro"].isnull().all() else datetime.today()
        
        c_data1, c_data2 = st.sidebar.columns(2)
        data_inicial = c_data1.date_input("Início", data_min, format="DD/MM/YYYY")
        data_final = c_data2.date_input("Fim", data_max, format="DD/MM/YYYY")
        
        mask = (df["Data_Filtro"].dt.date >= data_inicial) & (df["Data_Filtro"].dt.date <= data_final)
        df_filtrado = df.loc[mask]
        
        if df_filtrado.empty:
            st.warning("Nenhum dado encontrado para o período.")
            return

        # KPIs
        total = len(df_filtrado)
        sac_total = len(df_filtrado[df_filtrado["Setor"] == "SAC"])
        pend_total = len(df_filtrado[df_filtrado["Setor"] == "Pendência"])
        
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("Total", total, border=True)
        kpi2.metric("SAC", sac_total, border=True)
        kpi3.metric("Pendências", pend_total, border=True)

        st.markdown("##")

        # GRÁFICOS NOVOS
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("📈 Tendência Diária")
            trend = df_filtrado.groupby("Data_Filtro").size().reset_index(name='Atendimentos')
            fig = px.line(trend, x="Data_Filtro", y="Atendimentos", markers=True, 
                          title="Volume de Atendimentos por Dia", line_shape="spline",
                          color_discrete_sequence=['#10b981'])
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            st.subheader("⏰ Picos de Demanda (Horário)")
            df_filtrado['Hora_Int'] = pd.to_datetime(df_filtrado['Hora'], format='%H:%M:%S', errors='coerce').dt.hour
            heatmap_data = df_filtrado.groupby('Hora_Int').size().reset_index(name='Atendimentos')
            fig = px.bar(heatmap_data, x='Hora_Int', y='Atendimentos', 
                         title="Volume por Faixa Horária",
                         labels={'Hora_Int': 'Hora do Dia'},
                         color_discrete_sequence=['#3b82f6'])
            fig.update_layout(xaxis=dict(tickmode='linear', dtick=1))
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        
        # LINHA 2
        c3, c4 = st.columns(2)
        
        df_pend_dash = df_filtrado[df_filtrado["Setor"] == "Pendência"]
        
        with c3:
            st.subheader("🚚 Transportadoras (Detalhado)")
            if not df_pend_dash.empty:
                # CORREÇÃO: Gráfico Stacked + Text Auto para mostrar números dentro das barras
                fig = px.histogram(df_pend_dash, x="Transportadora", color="Motivo", 
                                   title="Ocorrências por Transportadora",
                                   barmode='stack', text_auto=True)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sem dados de Pendências.")

        with c4:
            st.subheader("📊 Motivos CRM")
            df_crm = df_filtrado[df_filtrado["Motivo_CRM"].notna() & (df_filtrado["Motivo_CRM"] != "-")]
            if not df_crm.empty:
                contagem = df_crm['Motivo_CRM'].value_counts().reset_index()
                contagem.columns = ['Motivo CRM', 'Quantidade']
                fig = px.bar(contagem.head(10).sort_values('Quantidade', ascending=True), 
                             x='Quantidade', y='Motivo CRM', orientation='h', text='Quantidade', 
                             title="Top Motivos CRM",
                             color_discrete_sequence=['#f43f5e'])
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sem dados de CRM.")

        st.markdown("---")
        st.subheader("📥 Exportação Geral")
        
        # Botão de Download com a correção de formato TEXTO
        csv = converter_para_excel_csv(df_filtrado)
        st.download_button(
            label="Baixar Dados Filtrados (.csv)",
            data=csv,
            file_name="relatorio_geral_google_sheets.csv",
            mime='text/csv',
        )
        
        st.dataframe(df_filtrado.drop(columns=["Data_Filtro", "Hora_Int"], errors='ignore').sort_values(by=["Data", "Hora"], ascending=False).head(50), use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Erro no Dashboard: {e}")

# ==========================================
#           ROTEAMENTO
# ==========================================
if pagina_escolhida == "Pendências Logísticas":
    pagina_pendencias()
elif pagina_escolhida == "SAC / Atendimento":
    pagina_sac()
else:
    pagina_dashboard()
