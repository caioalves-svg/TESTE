import streamlit as st
import pandas as pd
import plotly.express as px
import os
import pytz
import json
import streamlit.components.v1 as components
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Sistema Integrado", page_icon="✨", layout="wide")

# Nome do arquivo de dados
ARQUIVO_DADOS = "historico_atendimentos.csv"

# ==========================================
#      FUNÇÕES DE BANCO DE DADOS
# ==========================================
def obter_data_hora_brasil():
    fuso_br = pytz.timezone('America/Sao_Paulo')
    return datetime.now(fuso_br)

def inicializar_banco():
    if not os.path.exists(ARQUIVO_DADOS):
        df = pd.DataFrame(columns=["Data", "Hora", "Setor", "Colaborador", "Motivo", "Transportadora"])
        df.to_csv(ARQUIVO_DADOS, index=False, sep=';', encoding='utf-8-sig')

def salvar_registro(setor, colaborador, motivo, transportadora="-"):
    inicializar_banco()
    agora = obter_data_hora_brasil()
    
    nova_linha = {
        "Data": agora.strftime("%d/%m/%Y"),
        "Hora": agora.strftime("%H:%M:%S"),
        "Setor": setor,
        "Colaborador": colaborador,
        "Motivo": motivo,
        "Transportadora": transportadora
    }
    
    try:
        df = pd.read_csv(ARQUIVO_DADOS, sep=';', encoding='utf-8-sig')
        df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
        df.to_csv(ARQUIVO_DADOS, index=False, sep=';', encoding='utf-8-sig')
    except Exception as e:
        st.error(f"Erro ao salvar: {e}. Tente apagar o arquivo .csv antigo.")

def carregar_dados():
    inicializar_banco()
    try:
        return pd.read_csv(ARQUIVO_DADOS, sep=';', encoding='utf-8-sig')
    except:
        return pd.DataFrame()

def restaurar_backup(arquivo_upload):
    try:
        df_backup = pd.read_csv(arquivo_upload, sep=';', encoding='utf-8-sig')
        df_backup.to_csv(ARQUIVO_DADOS, index=False, sep=';', encoding='utf-8-sig')
        return True
    except Exception as e:
        st.error(f"Erro ao restaurar: {e}")
        return False

def converter_para_excel_csv(df):
    return df.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')

# ==========================================
#      MÁGICA DE CÓPIA (JS)
# ==========================================
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
        try {{
            document.execCommand('copy');
        }} catch (err) {{}}
        document.body.removeChild(textArea);
    }}
    copyToClipboard();
    </script>
    """
    components.html(js, height=0, width=0)

# ==========================================
#      DESIGN CLEAN (SIDEBAR BRANCA)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    .stApp { background-color: #f8fafc; font-family: 'Inter', sans-serif; }

    /* Sidebar Branca */
    section[data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 1px solid #e2e8f0; }
    section[data-testid="stSidebar"] * { color: #334155 !important; }
    
    h1, h2, h3 { color: #0f172a !important; font-weight: 700; }

    /* Inputs Limpos */
    .stSelectbox div[data-baseweb="select"] > div, .stTextInput input, .stDateInput input, .stTextArea textarea {
        background-color: #ffffff !important; border: 1px solid #94a3b8 !important; border-radius: 8px !important; color: #1e293b !important;
    }
    
    /* Caixa de Visualização */
    .preview-box {
        background-color: #ffffff; border-left: 5px solid #3b82f6; border: 1px solid #e2e8f0; border-radius: 4px; padding: 20px;
        color: #334155; white-space: pre-wrap; margin-top: 10px; font-size: 14px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    /* Botão Registrar */
    .botao-registrar .stButton button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important; color: white !important;
        border: none; padding: 0.8rem 2rem; border-radius: 8px; font-weight: 600; width: 100%;
        box-shadow: 0 4px 6px rgba(16, 185, 129, 0.2);
    }
    .botao-registrar .stButton button:hover { transform: translateY(-2px); box-shadow: 0 6px 8px rgba(16, 185, 129, 0.3); }

    /* Botão Download */
    .stDownloadButton button {
        background-color: #3b82f6 !important; color: white !important;
        border: none !important; border-radius: 8px; font-weight: 600; width: 100%;
    }
    .stDownloadButton button:hover { background-color: #2563eb !important; }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
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
#      DADOS (Listas)
# ==========================================
colaboradores_pendencias = sorted(["Ana", "Mariana", "Gabriela", "Layra", "Maria Eduarda", "Akisia", "Marcelly", "Camilla"])
lista_transportadoras = sorted(["4ELOS", "ATUAL", "BRASIL WEB", "FAVORITA", "FRONTLOG", "GENEROSO", "JADLOG", "LOGAN", "MMA", "PAJUÇARA", "PATRUS", "REBOUÇAS", "REDE SUL", "RIO EXPRESS", "TJB", "TOTAL", "TRILOG"])
colaboradores_sac = sorted(["Ana Carolina", "Ana Victoria", "Eliane", "Cassia", "Juliana", "Tamara", "Rafaela", "Telliane", "Isadora", "Lorrayne", "Leticia", "Julia"])

# ==========================================
#      MENSAGENS PENDÊNCIAS
# ==========================================
modelos_pendencias = {
    "Ausente": """Olá, {cliente}! Tudo bem? Esperamos que sim!\n\nA transportadora {transportadora} tentou realizar a entrega de sua mercadoria no endereço cadastrado, porém, o responsável pelo recebimento estava ausente.\n\nPara solicitarmos uma nova tentativa de entrega à transportadora, poderia por gentileza, nos confirmar dados abaixo?\n\nRua: \nNúmero: \nBairro: \nCEP: \nCidade: \nEstado: \nPonto de Referência: \nRecebedor: \nTelefone: \n\nApós a confirmação dos dados acima, iremos solicitar que a transportadora realize uma nova tentativa de entrega que irá ocorrer no prazo de até 3 a 5 dias úteis. Caso não tenhamos retorno, o produto será devolvido ao nosso Centro de Distribuição e seguiremos com o cancelamento da compra.\n\nQualquer dúvida, estamos à disposição!\n\nAtenciosamente,\n{colaborador}""",
    "Solicitação de Contato": """Olá, {cliente}! Tudo bem? Esperamos que sim!\n\nPara facilitar a entrega da sua mercadoria e não ter desencontros com a transportadora {transportadora}, o senhor pode por gentileza nos enviar um número de telefone ativo para alinharmos a entrega?\n\nAguardo o retorno!\n\nAtenciosamente,\n{colaborador}""",
    "Endereço Não Localizado": """Olá, {cliente}! Tudo bem? Esperamos que sim!\n\nA transportadora {transportadora} tentou realizar a entrega de sua mercadoria, porém, não localizou o endereço.\n\nPara solicitarmos uma nova tentativa de entrega à transportadora, poderia por gentileza, nos confirmar dados abaixo:\n\nRua:\nNúmero:\nBairro:\nCEP:\nCidade:\nEstado:\nPonto de Referência:\nRecebedor:\nTelefone:\n\nApós a confirmação dos dados acima, iremos solicitar que a transportadora realize uma nova tentativa de entrega que irá ocorrer no prazo de até 3 a 5 dias úteis. Caso não tenhamos retorno, o produto será devolvido ao nosso Centro de Distribuição e seguiremos com o cancelamento da compra.\n\nAtenciosamente,\n{colaborador}""",
    "Área de Risco": """Olá, {cliente}! Tudo bem? Espero que sim!\n\nA transportadora {transportadora}, informou que está com dificuldades para realizar a entrega no endereço cadastrado no portal. Dessa forma, peço por gentileza que nos informe um endereço alternativo e também telefones ativos para melhor comunicação.\n\nCaso não possua um outro endereço, sua mercadoria ficará disponível para retirada da base da transportadora.\n\nQualquer dúvida me coloco à disposição para ajudá-lo!\n\nAtenciosamente,\n{colaborador}""",
    "Extravio / Avaria": """Olá, {cliente}! Tudo bem? Espero que sim!\n\nInfelizmente fomos informados pela transportadora {transportadora} que sua mercadoria foi furtada/avariada em transporte. Antes de tudo, pedimos desculpas pelo ocorrido e por todo transtorno causado.\n\nGostaríamos de saber se o senhor aceita o envio de uma nova mercadoria? O prazo para entrega é de 5 a 7 dias úteis, podendo ocorrer antes.\n\nNovamente, pedimos desculpas. Qualquer dúvida me coloco à disposição para ajudá-lo!\n\nAtenciosamente,\n{colaborador}""",
    "Recusa de Entrega": """Prezado cliente,\n\nA transportadora {transportadora} informou que a entrega foi recusada. Houve algum problema com a apresentação da carga? O senhor deseja o cancelamento da compra?\n\nCaso não tenhamos retorno e o produto seja devolvido ao nosso estoque, seguiremos com o cancelamento da compra.\n\nQualquer dúvida me coloco à disposição para ajudá-lo!\n\nAtenciosamente,\n{colaborador}""",
    "Solicitação de Barramento": """Olá, {cliente}! Tudo bem? Esperamos que sim!\n\nSolicitamos à transportadora {transportadora} que barre a entrega da sua mercadoria. Caso tentem realizar a entrega, gentileza recusar o recebimento.\n\nAssim que a mercadoria der entrada em nosso estoque, liberamos o estorno.\n\nAtenciosamente,\n{colaborador}""",
    "Garantia de A a Z (Amazon)": """Olá, {cliente}! Tudo bem? Esperamos que sim!\n\nDiante da abertura da Garantia A a Z, solicitamos à transportadora {transportadora} responsável que barre a entrega e aguardaremos a confirmação da suspensão da entrega, a fim de possibilitar a liberação do reembolso pela plataforma.\n\nAtenciosamente,\n{colaborador}""",
    "Em caso de Reembolso": """Olá, {cliente}! Tudo bem? Esperamos que sim!\n\nO cancelamento foi liberado conforme solicitado. O reembolso é realizado de acordo com a forma de pagamento da compra:\n\nPara pagamentos com boleto, o reembolso será feito na conta bancária especificada pelo cliente ou como um vale-presente. Se todos os dados da sua conta bancária estiverem corretos, o reembolso pode levar até 3 dias úteis para constar na conta.\n\nCaso você tenha pago com cartão de crédito, dependendo da data de fechamento e vencimento do seu cartão, o reembolso pode levar de uma a duas faturas.\n\nPara pagamento em PIX, o reembolso será realizado na conta PIX em um dia útil.\n\nAtenciosamente,\n{colaborador}""",
    "Mercadoria sem Estoque": """Olá, {cliente}! Tudo bem? Esperamos que sim!\n\nHouve um erro no sistema que vendeu um item a mais e o lojista não possui a mercadoria disponível em estoque no momento. Verificamos com o nosso fornecedor, e infelizmente não tem a previsão de entrega de um novo lote.\n\nPedimos desculpas pelo transtorno causado.\n\nGostaríamos de saber se podemos seguir com o cancelamento do pedido para que a loja da compra possa realizar o estorno total.\n\nAtenciosamente,\n{colaborador}""",
    "Endereço em Zona Rural": """Olá, {cliente}! Tudo bem? Esperamos que sim!\n\nA transportadora {transportadora} nos informou que está com dificuldades para realizar a entrega no endereço cadastrado no portal.\n\nPeço por gentileza que nos informe um endereço alternativo e também telefones ativos para melhor comunicação. Caso o senhor não possua um outro endereço, sua mercadoria ficará disponível para retirada a base da transportadora.\n\nAtenciosamente,\n{colaborador}""",
    "Reenvio de Produto": """Olá, {cliente}! Tudo bem? Esperamos que sim!\n\nConforme solicitado, realizamos o envio de um novo produto ao senhor. Em até 48h você terá acesso a sua nova nota fiscal e poderá acompanhar os passos de sua entrega:\n\nLink: https://ssw.inf.br/2/rastreamento_pf?\n(Necessário inserir o CPF)\n\nNovamente peço desculpas por todo transtorno causado.\n\nAtenciosamente,\n{colaborador}"""
}

# ==========================================
#      MENSAGENS SAC
# ==========================================
modelos_sac = {
    "Solicitação de Coleta": """Olá, {cliente}!\n\nVerificamos que o seu pedido está dentro do prazo para troca/cancelamento. Sendo assim, já solicitamos ao setor responsável a emissão da Nota Fiscal de coleta e o acionamento da transportadora para realizar o recolhimento da mercadoria.\n\nInstruções de devolução:\n- Por favor, devolva as mercadorias em suas embalagens originais ou similares, devidamente protegidas.\n- A transportadora realizará a coleta no endereço de entrega nos próximos 15/20 dias úteis: {endereco_resumido}\n- É necessário colocar dentro da embalagem uma cópia da Nota Fiscal.\n\nRessaltamos que, assim que a coleta for confirmada, daremos continuidade ao seu atendimento conforme solicitado.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "Barrar Entrega na Transportadora": """Olá, {cliente}!\n\nSolicitamos à transportadora responsável o bloqueio da entrega. No entanto, caso haja alguma tentativa de entrega no local, pedimos a gentileza de recusar o recebimento no ato.\n\nAssim que o produto retornar ao centro de distribuição da Engage Eletro, seguiremos imediatamente com as tratativas de troca ou reembolso, conforme nossa política.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "Assistência Técnica (Dentro dos 7 dias)": """Olá, {cliente}!\n\nInformamos que o processo de troca via loja possui um prazo total de até 20 dias úteis (contando a partir da data de coleta).\n\nPara solucionar o seu problema de forma muito mais rápida, recomendamos acionar diretamente a assistência técnica da fabricante {fabricante}, que possui prioridade no atendimento. Seguem as informações de contato:\n{contato_assistencia}\n\nCaso a assistência técnica não consiga resolver ou seja inviável, por favor, nos informe. Verificaremos a possibilidade de troca diretamente conosco, mediante a disponibilidade em nosso estoque.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "Prazos de Reembolso": """Olá, {cliente}!\n\nA devolução do valor será realizada na mesma forma de pagamento utilizada na compra:\n\n- Boleto Bancário: O reembolso será feito em conta bancária de mesma titularidade ou via vale-presente. Se os dados informados estiverem corretos, o crédito ocorre em até 3 dias úteis.\n- Cartão de Crédito: O estorno será processado pela operadora do cartão e, dependendo da data de fechamento da sua fatura, poderá ser visualizado em uma ou duas faturas subsequentes.\n- PIX: O reembolso será realizado na conta de origem do PIX em até um dia útil.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "Assistência Técnica (Fora dos 7 dias)": """Olá, {cliente}!\n\nVerificamos que a sua compra foi realizada no dia {data_compra}, referente à NF-{nota_fiscal}. Desta forma, o pedido encontra-se fora do prazo de 7 dias para cancelamento ou troca direta com a loja. No entanto, seu produto está amparado pela garantia do fabricante, que cobre defeitos de funcionamento.\n\nPara agilizar o reparo, segue o link para localizar o posto autorizado mais próximo de sua residência: {link_posto}\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "Troca de Modelo (Dentro de 7 dias)": """Olá, {cliente}!\n\nEsclarecemos que a troca direta é realizada em casos de divergência de pedido, defeito ou avaria. Não efetuamos trocas por insatisfação de modelo, cor ou voltagem após o envio correto.\n\nNeste caso, como prefere prosseguir? Você deseja permanecer com o produto recebido ou prefere seguir com o cancelamento e reembolso da compra?\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "Código Postal (Logística Reversa)": """Olá, {cliente}!\n\nSegue abaixo o código de postagem para a logística reversa. Para utilizá-lo, dirija-se a uma agência dos Correios com o produto devidamente embalado e apresente o código:\n{codigo_postagem}\n\nImportante:\n- O processo não gera custo para você.\n- Não é necessário endereçar a embalagem (remetente/destinatário), pois o código já vincula todos os dados.\n- Leve o Código de Autorização anotado ou no celular.\n\nApós o retorno do produto ao nosso Centro de Distribuição, seguiremos com a tratativa solicitada.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "Reenvio Solicitado": """Olá, {cliente}!\n\nTemos boas notícias! O seu novo envio já foi solicitado. O pedido será liberado para transporte em até 72h úteis. Assim que tivermos o novo rastreio, informaremos você.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "Acareação": """Olá, {cliente}!\n\nAbriremos um chamado de acareação junto à transportadora responsável. Neste procedimento, a transportadora retornará ao local de entrega para identificar quem recebeu a mercadoria e confrontar as informações.\n\nO prazo para a conclusão desta tratativa é de até 7 dias úteis. Pedimos que aguarde nosso retorno com a resolução.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "Confirmação de Entrega": """Olá, {cliente}!\n\nDe acordo com o sistema da transportadora {transportadora}, o seu pedido consta como entregue no dia {data_entrega}. Segue em anexo o comprovante de entrega: (QUANDO ESTIVER DISPONÍVEL E ASSINADO)\n\nCaso você não reconheça este recebimento, por favor, nos informe imediatamente para que possamos iniciar a acareação e as buscas pela mercadoria junto à transportadora.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "Conversão GLP/GNV": """Olá, {cliente}!\n\nInformamos que sua mercadoria sai de fábrica ajustada para GLP (gás de botijão). A conversão para Gás Natural (GNV) deve ser feita conforme as orientações do manual de instruções.\n\nAtenção: Quando a conversão é realizada pela rede de assistência autorizada da fabricante, o produto mantém a garantia original intacta.\n\nDados da Fabricante para agendamento: {fabricante}\nSite: {site_fabricante}\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "Solicitação de Dados Bancários": """Olá, {cliente}!\n\nPara que possamos processar o seu reembolso, por favor, informe os dados bancários do titular da compra:\n\nNome do titular da compra:\nCPF do titular da compra:\nNome do banco:\nChave Pix:\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "Oferecer Desconto por Avaria": """Olá, {cliente}!\n\nLamentamos sinceramente pelo ocorrido. Gostaríamos de propor uma solução ágil.\nPrimeiramente, o produto está funcionando normalmente (apesar da avaria estética)?\n\nCaso o funcionamento esteja perfeito e você tenha interesse em permanecer com o item, podemos oferecer um reembolso parcial no valor de R$ {valor_desconto} como desconto pela avaria.\n\n- O produto continuará com a garantia total de funcionamento pela fabricante.\n\nSe aceitar esta proposta, por favor, nos informe os dados abaixo para pagamento:\nNome do titular da compra:\nCPF do titular da compra:\nNome do banco:\nChave Pix:\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "Insucesso na Entrega (Solicitar Dados)": """Olá, {cliente}!\n\nA transportadora nos informou que está com dificuldades para localizar o endereço ou finalizar a entrega. Para evitar a devolução, por favor, confirme os dados abaixo e nos forneça telefones atualizados:\n\nRua: {rua}\nCEP: {cep}\nNúmero: {numero}\nBairro: {bairro}\nCidade: {cidade}\nEstado: {estado}\nComplemento: {complemento}\nPonto de Referência: {referencia}\n2 telefones ativos (com DDD):\n\nAtenção: Caso não tenhamos retorno breve, o produto retornará ao nosso estoque e seguiremos com o reembolso.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "Nova Tentativa de Entrega": """Olá, {cliente}!\n\nJá repassamos as informações para a transportadora. Uma nova tentativa de entrega será realizada no prazo de 5 a 7 dias úteis, podendo ocorrer antes. Estamos acompanhando para garantir que você receba seu pedido o quanto antes.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "Mercadoria em Trânsito": """Olá, {cliente}!\n\nConsultamos o rastreio e seu pedido segue em trânsito normal, com previsão de entrega até o dia {previsao_entrega}, podendo chegar antes.\n\nVocê pode acompanhar a entrega através dos dados abaixo:\nLink: {link_rastreio}\nNota fiscal: {nota_fiscal}\nTransportadora: {transportadora}\n\nPara rastrear, utilize o CPF do titular da compra.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "Erro de Integração": """Olá, {cliente}!\n\nPedimos sinceras desculpas pelo transtorno. Identificamos um erro de integração sistêmica que afetou alguns pedidos, incluindo o seu. Nossa equipe de TI já está atuando na correção e a liberação do seu pedido ocorrerá em breve.\n\nAgradecemos sua paciência e estamos à disposição.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "Erro de Integração com Atraso": """Olá, {cliente}!\n\nPedimos desculpas pela demora. Devido a uma falha de integração em nosso sistema, tivemos um impacto na operação de envios. No entanto, já solicitamos prioridade máxima para o seu pedido, a fim de que ele seja despachado o mais rápido possível.\n\nContamos com a sua compreensão e lamentamos o inconveniente.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "Extravio Aguardar Confirmação": """Olá, {cliente}!\n\nA transportadora nos sinalizou uma possível situação de extravio com o seu pedido. Estamos em contato direto com eles para tentar localizar a mercadoria com urgência.\n\nPedimos a gentileza de aguardar um prazo de 48 horas para que possamos confirmar a situação e dar um retorno definitivo. Fique tranquilo(a): caso o pedido não seja localizado neste prazo, iniciaremos imediatamente os procedimentos de reenvio ou reembolso para garantir sua satisfação.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "Extravio com Opção de Reenvio": """Olá, {cliente}!\n\nLamentamos pelo transtorno causado. Confirmamos junto à transportadora que houve o extravio de sua mercadoria durante o trajeto. Para resolvermos isso rapidamente, gostaríamos de saber como prefere prosseguir:\n\nVocê deseja o reenvio de um novo produto ou o reembolso total da compra?\n\nAguardamos seu retorno para seguir com a opção escolhida.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "Fiscalização": """Olá, {cliente}!\n\nIdentificamos que seu pedido está retido na fiscalização (SEFAZ). Não se preocupe, já estamos em contato com a transportadora {transportadora} para providenciar a liberação o mais rápido possível.\n\nDevido a este trâmite fiscal, a entrega poderá sofrer um pequeno atraso. Assim que a mercadoria for liberada, solicitaremos prioridade na rota de entrega.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "Item Faltante": """Olá, {cliente}!\n\nSentimos muito pelo ocorrido. Já acionamos o nosso estoque e a expedição para verificar a disponibilidade do item faltante e providenciar o envio separado para você.\n\nRetornaremos com uma posição em breve.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "Atraso na Entrega": """Olá, {cliente}!\n\nLamentamos pelo atraso na entrega do seu pedido. Estamos em contato ativo com a transportadora para entender o motivo e cobramos uma nova previsão de entrega com urgência e prioridade de finalização. Manteremos você informado(a).\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "Entrega (Serviços não inclusos)": """Olá, {cliente}!\n\nGostaríamos de esclarecer alguns pontos sobre a entrega: O serviço contratado pela Engage Eletro junto às transportadoras parceiras cobre a entrega do produto até a entrada (porta ou portaria) do endereço indicado. O serviço não inclui: montagem/desmontagem, subida de escadas (se não houver elevador ou se o produto não couber), içamento por guincho ou instalação.\n\nAs entregas ocorrem de segunda a sexta-feira, em horário comercial.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "Agradecimento": """Olá, {cliente}!\n\nQue ótima notícia! Fico muito feliz que tenha dado tudo certo. Sempre que tiver dúvidas, sugestões ou precisar de ajuda, não hesite em nos contatar. Estamos aqui para garantir a sua melhor experiência.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "Código Coleta Domiciliar": """Olá, {cliente}!\n\nSegue abaixo o código para a logística reversa (coleta domiciliar). Para que a coleta seja efetuada com sucesso, o produto deve estar devidamente embalado quando a transportadora chegar.\n\nCódigo de Coleta: {codigo_coleta}\n\nObservações:\n- O processo não gera custos para o cliente.\n- Não é necessário preencher dados de remetente/destinatário na caixa, o código já contém as informações.\n\nAssim que o produto retornar ao nosso Centro de Distribuição, seguiremos com a tratativa solicitada.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "Embalagem Similar": """Olá, {cliente}!\n\nPara garantir que o produto chegue intacto ao nosso centro de distribuição e seu processo seja finalizado sem problemas, reforçamos a importância da embalagem:\nRecomendamos envolver o produto em plástico bolha e utilizar uma caixa de papelão resistente (pode ser reutilizada, desde que sem rótulos antigos). Isso evita danos adicionais no transporte.\n\nAgradecemos sua colaboração.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "Termo para Troca Casada": """Olá, {cliente}!\n\nPara agilizar o processo e tentar realizar a entrega do novo produto no mesmo momento da coleta do antigo, propomos a formalização de um Termo de Acordo Extrajudicial.\n\nO procedimento é simples:\n- Enviaremos o termo pelo nosso Jurídico.\n- Você deve assinar todas as páginas (conforme seu documento de identificação).\n- Envie o termo assinado + foto do documento (RG ou CNH) em até 48 horas.\n- Após validação jurídica, seguiremos com o envio e coleta simultânea.\n\nPodemos seguir com este procedimento?\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "Recusa de Troca (Avaria)": """Olá, {cliente}!\n\nConforme informamos, a troca do produto avariado é necessária agora para evitar problemas futuros, uma vez que o prazo de reclamação por danos físicos é limitado.\n\nRespeitamos sua decisão, mas entendemos que, ao recusar a troca neste momento, o(a) senhor(a) está ciente e assume o risco de permanecer com um produto com avaria estética, isentando a loja de reclamações futuras sobre este dano específico.\n\nReforçamos que seu produto continua coberto pela garantia do fabricante exclusivamente para defeitos funcionais, conforme a lei. Avarias físicas não são cobertas pela garantia de fábrica posteriormente.\n\nPermanecemos à disposição.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "Rastreio Indisponível (Jadlog)": """Olá, {cliente}!\n\nGostaríamos de tranquilizá-lo(a): seu pedido foi despachado regularmente e segue dentro do prazo de entrega. No momento, o sistema de rastreamento da transportadora apresenta uma instabilidade técnica temporária, impedindo a visualização do status em tempo real.\n\nJá notificamos a transportadora parceira e estamos monitorando o restabelecimento do sistema. Seu pedido continua em movimento normalmente.\n\nAgradecemos a compreensão.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "Solicitação de Fotos e Vídeos (Avaria)": """Olá, {cliente}!\n\nPedimos sinceras desculpas pelos transtornos causados com a chegada do seu produto. Entendemos sua frustração e queremos resolver isso o mais rápido possível.\n\nPara darmos continuidade ao atendimento e agilizarmos a solução junto ao setor responsável, precisamos que nos envie, por gentileza:\n· Fotos nítidas do produto e da embalagem onde consta a avaria;\n· Um breve vídeo mostrando o detalhe do dano (se possível).\n\nAssim que recebermos as evidências, faremos a análise imediata para prosseguir com as tratativas de resolução.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}"""
}

# ==========================================
#           PÁGINA PENDÊNCIAS
# ==========================================
def pagina_pendencias():
    st.title("🚚 Pendências Logísticas")
    st.markdown("---")
    
    col1, col2 = st.columns([1, 1.5], gap="medium")
    
    with col1:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("1. Configuração")
        colab = st.selectbox("👤 Colaborador:", colaboradores_pendencias, key="colab_p")
        # NOME DO CLIENTE OBRIGATÓRIO (SERÁ VALIDADO NO BOTÃO)
        nome_cliente = st.text_input("Nome do Cliente:", key="nome_cliente_p")
        transp = st.selectbox("🚛 Qual a transportadora?", lista_transportadoras, key="transp_p")
        
        st.markdown("---")
        st.subheader("2. Motivo")
        opcao = st.selectbox("Selecione o caso:", list(modelos_pendencias.keys()), key="msg_p")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("3. Visualização")
        texto_cru = modelos_pendencias[opcao]
        
        nome_cliente_final = nome_cliente if nome_cliente else "[NOME DO CLIENTE]"
        
        texto_final = texto_cru.replace("{transportadora}", transp)\
                               .replace("{colaborador}", colab)\
                               .replace("{cliente}", nome_cliente_final)
        
        st.markdown(f'<div class="preview-box">{texto_final}</div>', unsafe_allow_html=True)
        
        st.write("")
        st.markdown('<div class="botao-registrar">', unsafe_allow_html=True)
        # LÓGICA DE VALIDAÇÃO (FEATURE 5)
        if st.button("✅ Registrar e Copiar", key="btn_save_pend"):
            if not nome_cliente.strip():
                st.error("⚠️ Por favor, preencha o Nome do Cliente antes de registrar.")
            else:
                salvar_registro("Pendência", colab, opcao, transp)
                st.toast("Registrado com sucesso!", icon="✨")
                copiar_para_clipboard(texto_final)
                st.code(texto_final, language="text")
        st.markdown('</div>', unsafe_allow_html=True)
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
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("1. Configuração")
        colab = st.selectbox("👤 Colaborador:", colaboradores_sac, key="colab_s")
        nome_cliente = st.text_input("Nome do Cliente:", key="nome_cliente_s")
        opcao = st.selectbox("Qual o motivo do contato?", list(modelos_sac.keys()), key="msg_s")
        
        if "Solicitação de Coleta" in opcao:
            st.info("🚚 Endereço")
            dados["{endereco_resumido}"] = st.text_input("Endereço da coleta (Bairro/Cidade):")
        elif "Assistência Técnica (Dentro dos 7 dias)" in opcao:
            st.info("🔧 Dados da Assistência")
            dados["{fabricante}"] = st.text_input("Nome da Fabricante:")
            dados["{contato_assistencia}"] = st.text_area("Endereço/Telefone/Infos:")
        elif "Assistência Técnica (Fora dos 7 dias)" in opcao:
            st.info("📅 Dados da Compra")
            dados["{data_compra}"] = st.text_input("Data da Compra:")
            dados["{nota_fiscal}"] = st.text_input("Número da NF:")
            dados["{link_posto}"] = st.text_input("Link do Posto Autorizado:")
        elif "Código Postal" in opcao or "Código Coleta" in opcao:
            st.info("📮 Código de Postagem")
            k = "{codigo_postagem}" if "Código Postal" in opcao else "{codigo_coleta}"
            dados[k] = st.text_input("Código de Coleta/Postagem:")
        elif "Confirmação de Entrega" in opcao:
            st.info("🚚 Dados da Entrega")
            dados["{transportadora}"] = st.selectbox("Transportadora:", lista_transportadoras, key="tr_ent_sac")
            dados["{data_entrega}"] = st.text_input("Data da Entrega:")
        elif "Conversão GLP" in opcao:
            st.info("🔥 Dados do Fabricante")
            dados["{fabricante}"] = st.text_input("Nome do Fabricante:")
            dados["{site_fabricante}"] = st.text_input("Site/Contato:")
        elif "Oferecer Desconto" in opcao:
            st.info("💰 Proposta de Valor")
            dados["{valor_desconto}"] = st.text_input("Valor do reembolso (R$):")
        elif "Mercadoria em Trânsito" in opcao:
            st.info("📦 Rastreamento")
            dados["{previsao_entrega}"] = st.text_input("Previsão de Entrega:")
            dados["{link_rastreio}"] = st.text_input("Link de Rastreio:")
            dados["{nota_fiscal}"] = st.text_input("Nota Fiscal:")
            dados["{transportadora}"] = st.selectbox("Transportadora:", lista_transportadoras, key="tr_trans_sac")
        elif "Fiscalização" in opcao:
            st.info("🛑 Fiscalização")
            dados["{transportadora}"] = st.selectbox("Transportadora:", lista_transportadoras, key="tr_fisc_sac")
        elif "Insucesso na Entrega" in opcao:
            st.info("🏠 Endereço para Confirmar")
            dados["{rua}"] = st.text_input("Rua:")
            dados["{cep}"] = st.text_input("CEP:")
            dados["{numero}"] = st.text_input("Número:")
            dados["{bairro}"] = st.text_input("Bairro:")
            dados["{cidade}"] = st.text_input("Cidade:")
            dados["{estado}"] = st.text_input("Estado:")
            dados["{complemento}"] = st.text_input("Complemento (opcional):", value="")
            dados["{referencia}"] = st.text_input("Ponto de Referência (opcional):", value="")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("2. Visualização")
        texto_cru = modelos_sac[opcao]
        
        nome_cliente_final = nome_cliente if nome_cliente else "[NOME DO CLIENTE]"
        
        texto_final = texto_cru.replace("{colaborador}", colab)\
                               .replace("{cliente}", nome_cliente_final)
                               
        for chave, valor in dados.items():
            substituto = valor if valor else "................"
            texto_final = texto_final.replace(chave, substituto)
        
        st.markdown(f'<div class="preview-box">{texto_final}</div>', unsafe_allow_html=True)

        st.write("")
        st.markdown('<div class="botao-registrar">', unsafe_allow_html=True)
        transp_usada = "-"
        if "{transportadora}" in dados:
            transp_usada = dados["{transportadora}"]
            
        # LÓGICA DE VALIDAÇÃO (FEATURE 5)
        if st.button("✅ Registrar e Copiar", key="btn_save_sac"):
            if not nome_cliente.strip():
                st.error("⚠️ Por favor, preencha o Nome do Cliente antes de registrar.")
            else:
                salvar_registro("SAC", colab, opcao, transp_usada)
                st.toast("Registrado com sucesso!", icon="✨")
                copiar_para_clipboard(texto_final)
                st.code(texto_final, language="text")
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
#           DASHBOARD
# ==========================================
def pagina_dashboard():
    st.title("📊 Dashboard Gerencial")
    st.markdown("Visão estratégica dos atendimentos.")
    st.markdown("---")

    # RESTAURAÇÃO DE BACKUP
    with st.expander("📂 Backup e Restauração"):
        st.info("O sistema reseta ao atualizar o código. Use isso para restaurar seus dados.")
        arquivo_backup = st.file_uploader("Carregar histórico antigo (.csv)", type=["csv"])
        if arquivo_backup is not None:
            if st.button("Restaurar Dados"):
                if restaurar_backup(arquivo_backup):
                    st.success("Histórico recuperado! Atualize a página.")
                    st.rerun()

    df = carregar_dados()

    # --- EXPORTAÇÃO ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("📥 Exportação")
    
    tipo_export = st.sidebar.selectbox("Filtrar planilha por:", ["Geral (Todos)", "Apenas SAC", "Apenas Pendências"])
    
    if not df.empty:
        df_export = df.copy()
        if tipo_export == "Apenas SAC":
            df_export = df_export[df_export["Setor"] == "SAC"]
        elif tipo_export == "Apenas Pendências":
            df_export = df_export[df_export["Setor"] == "Pendência"]
            
        csv = converter_para_excel_csv(df_export)
        nome_arquivo = f'relatorio_{tipo_export.split()[0].lower()}_{datetime.now().strftime("%d-%m-%Y")}.csv'
        
        st.sidebar.download_button(
            label=f"Baixar Planilha ({tipo_export})",
            data=csv,
            file_name=nome_arquivo,
            mime='text/csv',
        )
    else:
        st.sidebar.info("Sem dados para exportar.")

    # --- FILTROS VISUAIS ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filtros do Painel")
    
    if not df.empty:
        df["Data_Filtro"] = pd.to_datetime(df["Data"], format="%d/%m/%Y", errors='coerce')
        data_min = df["Data_Filtro"].min().date()
        data_max = df["Data_Filtro"].max().date()
    else:
        data_min = datetime.now().date()
        data_max = datetime.now().date()
    
    c_data1, c_data2 = st.sidebar.columns(2)
    data_inicial = c_data1.date_input("Início", data_min, format="DD/MM/YYYY")
    data_final = c_data2.date_input("Fim", data_max, format="DD/MM/YYYY")
    
    if df.empty:
        st.warning("Ainda não há dados registrados.")
        return

    mask = (df["Data_Filtro"].dt.date >= data_inicial) & (df["Data_Filtro"].dt.date <= data_final)
    df_filtrado = df.loc[mask]
    
    if df_filtrado.empty:
        st.warning("Nenhum dado encontrado para o período.")
        total, sac_total, pend_total = 0, 0, 0
    else:
        total = len(df_filtrado)
        sac_total = len(df_filtrado[df_filtrado["Setor"] == "SAC"])
        pend_total = len(df_filtrado[df_filtrado["Setor"] == "Pendência"])

    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Total", total, border=True)
    kpi2.metric("SAC", sac_total, border=True)
    kpi3.metric("Pendências", pend_total, border=True)

    st.markdown("##")

    # GRÁFICOS
    if not df_filtrado.empty:
        # NOVO GRÁFICO (FEATURE 3): Análise de Transportadoras
        st.subheader("🚚 Análise de Transportadoras (Ofensores)")
        # Filtra apenas onde tem transportadora válida
        df_transp = df_filtrado[df_filtrado['Transportadora'].notnull() & (df_filtrado['Transportadora'] != "-")]
        
        if not df_transp.empty:
            # Agrupa por Transportadora e Motivo
            df_grouped = df_transp.groupby(['Transportadora', 'Motivo']).size().reset_index(name='Quantidade')
            
            fig_transp = px.bar(
                df_grouped, 
                x="Transportadora", 
                y="Quantidade", 
                color="Motivo", 
                title="Problemas por Transportadora (Visão Geral)",
                text_auto=True
            )
            fig_transp.update_layout(height=500)
            st.plotly_chart(fig_transp, use_container_width=True)
        else:
            st.info("Nenhum dado de transportadora registrado neste período.")

        st.markdown("---")

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📊 Motivos - SAC")
            df_sac = df_filtrado[df_filtrado["Setor"] == "SAC"]
            if not df_sac.empty:
                contagem = df_sac['Motivo'].value_counts().reset_index()
                contagem.columns = ['Motivo', 'Quantidade']
                fig_sac = px.bar(contagem.sort_values('Quantidade', ascending=True), x='Quantidade', y='Motivo', orientation='h', text='Quantidade', color_discrete_sequence=['#3b82f6'])
                fig_sac.update_layout(xaxis_title=None, yaxis_title=None, height=400)
                st.plotly_chart(fig_sac, use_container_width=True)
            else:
                st.info("Sem dados de SAC.")

        with c2:
            st.subheader("📊 Motivos - Pendências")
            df_pend = df_filtrado[df_filtrado["Setor"] == "Pendência"]
            if not df_pend.empty:
                contagem_p = df_pend['Motivo'].value_counts().reset_index()
                contagem_p.columns = ['Motivo', 'Quantidade']
                fig_pend = px.bar(contagem_p.sort_values('Quantidade', ascending=True), x='Quantidade', y='Motivo', orientation='h', text='Quantidade', color_discrete_sequence=['#0ea5e9'])
                fig_pend.update_layout(xaxis_title=None, yaxis_title=None, height=400)
                st.plotly_chart(fig_pend, use_container_width=True)
            else:
                st.info("Sem dados de Pendências.")

        st.markdown("---")
        st.subheader("📋 Base de Dados (Últimos 50 registros)")
        df_show = df_filtrado.drop(columns=["Data_Filtro"], errors='ignore')
        st.dataframe(df_show.sort_values(by=["Data", "Hora"], ascending=False).head(50), use_container_width=True, hide_index=True)

# ==========================================
#           ROTEAMENTO
# ==========================================
if pagina_escolhida == "Pendências Logísticas":
    pagina_pendencias()
elif pagina_escolhida == "SAC / Atendimento":
    pagina_sac()
else:
    pagina_dashboard()
