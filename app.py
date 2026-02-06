import streamlit as st
import pandas as pd
import plotly.express as px
import os
import pytz
import json
import gspread
from datetime import datetime
import streamlit.components.v1 as components

# ==========================================
#      CONFIGURAÇÃO INICIAL
# ==========================================
st.set_page_config(page_title="Sistema Integrado Engage", page_icon="🚀", layout="wide")

# ==========================================
#      CONEXÃO GOOGLE SHEETS
# ==========================================
NOME_PLANILHA_GOOGLE = "Base_Atendimentos_Engage" 

def conectar_google_sheets():
    try:
        if "gcp_service_account" in st.secrets:
            secrets = st.secrets["gcp_service_account"]
            creds_dict = {
                "type": secrets["type"],
                "project_id": secrets["project_id"],
                "private_key_id": secrets["private_key_id"],
                "private_key": secrets["private_key"].replace("\\n", "\n"), 
                "client_email": secrets["client_email"],
                "client_id": secrets["client_id"],
                "auth_uri": secrets["auth_uri"],
                "token_uri": secrets["token_uri"],
                "auth_provider_x509_cert_url": secrets["auth_provider_x509_cert_url"],
                "client_x509_cert_url": secrets["client_x509_cert_url"]
            }
            client = gspread.service_account_from_dict(creds_dict)
            sheet = client.open(NOME_PLANILHA_GOOGLE).sheet1
            return sheet
        elif os.path.exists("credentials.json"):
            client = gspread.service_account(filename="credentials.json")
            sheet = client.open(NOME_PLANILHA_GOOGLE).sheet1
            return sheet
        else:
            st.error("🚨 Nenhuma credencial encontrada.")
            return None
    except Exception as e:
        st.error(f"Erro de Conexão: {e}")
        return None

def carregar_dados():
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

def obter_dia_semana_pt(dt):
    dias = {0: "Segunda-feira", 1: "Terça-feira", 2: "Quarta-feira", 3: "Quinta-feira", 4: "Sexta-feira", 5: "Sábado", 6: "Domingo"}
    return dias[dt.weekday()]

def salvar_registro(setor, colaborador, motivo, portal, nf, numero_pedido, motivo_crm, transportadora="-"):
    sheet = conectar_google_sheets()
    if sheet:
        agora = obter_data_hora_brasil()
        str_nf = str(nf)
        str_pedido = str(numero_pedido)
        dia_pt = obter_dia_semana_pt(agora)
        nova_linha = [agora.strftime("%d/%m/%Y"), agora.strftime("%H:%M:%S"), dia_pt, setor, colaborador, motivo, portal, str_nf, str_pedido, motivo_crm, transportadora]
        try:
            sheet.append_row(nova_linha)
            return True
        except Exception as e:
            st.error(f"Erro ao gravar: {e}")
            return False
    return False

def converter_para_excel_csv(df):
    df_export = df.copy()
    df_export['Nota_Fiscal'] = df_export['Nota_Fiscal'].astype(str)
    df_export['Numero_Pedido'] = df_export['Numero_Pedido'].astype(str)
    return df_export.to_csv(index=False, sep=';', encoding='utf-8-sig').encode('utf-8-sig')

def obter_data_hora_brasil():
    fuso_br = pytz.timezone('America/Sao_Paulo')
    return datetime.now(fuso_br)

def copiar_para_clipboard(texto):
    texto_json = json.dumps(texto)
    js = f"""<script>
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
    </script>"""
    components.html(js, height=0, width=0)

# ==========================================
#      DADOS E LISTAS
# ==========================================
colaboradores_pendencias = sorted(["Ana", "Mariana", "Gabriela", "Layra", "Maria Eduarda", "Akisia", "Marcelly", "Camilla", "Michelle"])
colaboradores_sac = sorted(["Ana Carolina", "Ana Victoria", "Eliane", "Cassia", "Juliana", "Tamara", "Rafaela", "Telliane", "Isadora", "Lorrayne", "Leticia", "Julia", "Sara", "Cauê", "Larissa"])
lista_transportadoras = sorted(["4ELOS", "ATUAL", "BRASIL WEB", "FAVORITA", "FRONTLOG", "GENEROSO", "JADLOG", "LOGAN", "MMA", "PAJUÇARA", "PATRUS", "REBOUÇAS", "REDE SUL", "RIO EXPRESS", "TJB", "TOTAL", "TRILOG"])
lista_portais = sorted(["ALIEXPRESS", "AMAZON - EXTREMA", "AMAZON | ENGAGE LOG", "AMAZON DBA", "AMERICANAS - EXTREMA", "B2W", "BRADESCO SHOP", "CARREFOUR", "CARREFOUR OUTLET", "CNOVA", "CNOVA - EXTREMA", "FAST SHOP", "KABUM", "LEROY - EXTREMA", "MADEIRA MADEIRA", "MAGALU - EXTREMA", "MAGALU ELETRO", "MAGALU INFO", "MARTINS", "MEGA B2B", "MELI OUTLET", "MERCADO LIVRE", "MERCADO LIVRE - EXTREMA", "O MAGAZINE", "PADRÃO", "SHOPEE", "SKYHUB", "TIKTOK", "WAPSTORE - ENGAGE", "WEBCONTINENTAL", "WINECOM - LOJA INTEGRADA", "ZEMA"])
lista_motivo_crm = sorted(["ACAREAÇÃO", "ACORDO CLIENTE", "ALTERAÇÃO DE NOTA FISCAL", "AREA DE RISCO", "AREA NÃO ATENDIDA", "ARREPENDIMENTO", "ARREPENDIMENTO - DEVOLUÇÃO AMAZON", "ARREPENDIMENTO POR QUALIDADE DO PRODUTO", "ATRASO NA ENTREGA", "ATRASO NA EXPEDIÇÃO", "AUSENTE", "AVARIA", "CANCELAMENTO FORÇADO PELO PORTAL", "CASO JURIDÍCO", "CORREÇÃO DE ENDEREÇO", "DEFEITO", "DESCONHECIDO", "DESCONTO", "DEVOLUÇÃO SEM INFORMAÇÃO", "ENDEREÇO NÃO LOCALIZADO", "ENTREGA C/ AVARIA FORÇADA", "ENTREGUE E CANCELADO", "ERRO DE CADASTRO", "ERRO DE EXPEDIÇÃO", "ERRO DE INTEGRAÇÃO DE FATURAMENTO", "ESTOQUE FALTANTE", "EXTRAVIO", "FALTA DE ETIQUETA ENVIAS", "INSUCESSO NA ENTREGA", "ITEM FALTANTE", "MERCADORIA RETIDA", "MUDOU-SE", "NOTA RETIDA", "PAGAMENTO/REEMBOLSO", "RECOBRANÇA DE CLIENTE", "RECUSA", "RETENÇÃO", "SEM ABERTURA DE CRM", "SEM RASTREIO", "SUSPEITA DE FRAUDE", "TROCA DE ETIQUETA", "ZONA RURAL"])

# ==========================================
#      SCRIPTS PENDÊNCIAS
# ==========================================
modelos_pendencias = {
    "ATENDIMENTO DIGISAC": "", "2° TENTATIVA DE CONTATO": "", "3° TENTATIVA DE CONTATO": "",
    "REENTREGA": "", "AGUARDANDO TRANSPORTADORA": "",
    
    "ACAREAÇÃO": """Olá, (Nome do cliente)! Tudo bem?\n\nIdentificamos uma divergência na entrega do seu pedido e, por isso, abrimos um chamado de acareação com a transportadora.\n\nNeste procedimento, o motorista retorna ao local para identificar quem recebeu a mercadoria e validar as informações fornecidas. O prazo para a conclusão desta análise é de até 7 dias úteis.\n\nAssim que tivermos o parecer final, entraremos em contato imediatamente com a resolução.\n\nAtenciosamente,\n{colaborador}""",
    
    "DEVOLUÇÃO INDEVIDA": """Olá, (Nome do cliente)! Tudo bem?\n\nLamentamos informar que o seu pedido retornou indevidamente ao nosso centro de distribuição por um erro operacional.\n\nPara resolvermos da melhor forma para você, como prefere seguir?\n\nReenvio: Geramos um novo envio prioritário da sua mercadoria.\nCancelamento: Realizamos o estorno integral do valor pago.\n\nPedimos sinceras desculpas pelo transtorno. Ficamos no aguardo da sua escolha para prosseguir.\n\nAtenciosamente,\n{colaborador}""",
    
    "SOLICITAÇÃO DE CONTATO": """Olá, (Nome do cliente)! Tudo bem?\n\nQueremos garantir que sua mercadoria chegue com agilidade e sem novos desencontros.\n\nPor gentileza, você poderia nos informar um número de telefone atualizado (com DDD)? Assim, podemos alinhar os detalhes diretamente com a transportadora e facilitar o acesso ao seu endereço.\n\nAguardamos seu retorno!\n\nAtenciosamente,\n{colaborador}""",
    
    "EXTRAVIO / AVARIA (SEM ESTOQUE)": """Olá, (Nome do cliente)! Tudo bem?\n\nDurante o transporte, fomos notificados de que sua mercadoria sofreu um imprevisto (extravio/avaria). Infelizmente, verificamos que este item não está mais disponível em nosso estoque para reposição imediata.\n\nDevido a isso, seguiremos com o cancelamento da compra e o reembolso total do valor.\n\nSentimos muito por não conseguir entregar o seu produto desta vez e pedimos desculpas por qualquer frustração causada. Se houver algo mais que possamos fazer, estamos à disposição.\n\nAtenciosamente,\n{colaborador}""",

    "AUSENTE": """Olá, (Nome do cliente)! Tudo bem? Esperamos que sim!\n\nA transportadora {transportadora} tentou realizar a entrega de sua mercadoria no endereço cadastrado, porém, o responsável pelo recebimento estava ausente.\n\nPara solicitarmos uma nova tentativa de entrega à transportadora, poderia por gentileza, nos confirmar dados abaixo?\n\nRua: \nNúmero: \nBairro: \nCEP: \nCidade: \nEstado: \nPonto de Referência: \nRecebedor: \nTelefone: \n\nApós a confirmação dos dados acima, iremos solicitar que a transportadora realize uma nova tentativa de entrega que irá ocorrer no prazo de até 3 a 5 dias úteis. Caso não tenhamos retorno, o produto será devolvido ao nosso Centro de Distribuição e seguiremos com o cancelamento da compra.\n\nQualquer dúvida, estamos à disposição!\n\nAtenciosamente,\n{colaborador}""",
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

# ==========================================
#      SCRIPTS SAC
# ==========================================
modelos_sac = {
    "OUTROS": "", 
    "RECLAME AQUI": "",
    "INFORMAÇÃO SOBRE COLETA": "", 
    "INFORMAÇÃO SOBRE ENTREGA": "", 
    "INFORMAÇÃO SOBRE O PRODUTO": "", 
    "INFORMAÇÃO SOBRE O REEMBOLSO": "", 
    "COMPROVANTE DE ENTREGA (MARTINS)": "", # Novo (apenas registro)

    "ESTOQUE FALTANTE": """Olá, (Nome do cliente)!\n\nGostaríamos de pedir sinceras desculpas, mas tivemos um erro técnico em nosso anúncio e, infelizmente, o produto que você comprou está temporariamente fora de estoque.\n\nPara sua segurança e comodidade, a {portal} processará o seu reembolso automaticamente nos próximos dias.\n\nLamentamos muito pelo transtorno e já estamos trabalhando para que isso não ocorra novamente.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    
    "SAUDAÇÃO": """Olá, (Nome do cliente)!\n\nMe chamo {colaborador} e vou prosseguir com o seu atendimento.\nComo posso ajudar?""",
    
    "ALTERAÇÃO DE ENDEREÇO (SOLICITAÇÃO DE DADOS)": """Olá, (Nome do cliente)!\n\nPodemos verificar a possibilidade de alteração de endereço desde que não haja uma mudança referente a CIDADE ou ESTADO. Gentileza encaminhar o endereço completo no formato abaixo:\n\nRua:\nCep:\nNúmero:\nBairro:\nCidade:\nEstado:\nComplemento:\nPonto de Referência:\n2 telefones ativos:\n\nApós o envio dos dados, estaremos gerando uma Carta de Correção de Endereço e encaminhando para a transportadora para verificamos a possibilidade de entrega no local indicado.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",

    "BARRAR ENTREGA NA TRANSPORTADORA": """Olá, (Nome do cliente)!\n\nSolicitamos à transportadora responsável o bloqueio da entrega. No entanto, caso haja alguma tentativa de entrega no local, pedimos a gentileza de recusar o recebimento no ato.\n\nGostaríamos de informar que o pedido de barragem é definitivo. Por questões logísticas, após essa solicitação, não conseguimos reverter o processo para seguir com a entrega novamente.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "ENTREGA RECUSADA": """Olá, (Nome do cliente). Tudo bem?\n\nRecebemos uma notificação da transportadora informando que a entrega do seu pedido foi recusada no endereço de destino.\n\nHouve algum problema na tentativa de entrega ou avaria na embalagem?\n\n· Se deseja receber o produto: Por gentileza, nos confirme o endereço e pontos de referência.\n· Se deseja cancelar: Nos informe por aqui para agilizarmos o processo.\n\nAtenção:\nCaso não tenhamos retorno até {data_limite}, o produto retornará ao nosso estoque e seguiremos com o cancelamento automático.\n\nAguardo seu retorno!\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "AGUARDANDO RETORNO (FOLLOW UP)": """Olá, (Nome do cliente).\n\nPassando para informar que seu caso continua sendo tratado como prioridade por nossa equipe.\n\nJá acionamos o setor responsável/transportadora e estamos apenas aguardando a formalização da resposta para lhe posicionar com a solução definitiva. Não se preocupe, estou acompanhando pessoalmente o seu pedido.\n\nAssim que tiver o retorno, entro em contato imediatamente. Obrigado pela paciência!\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "PEDIDO EM EXPEDIÇÃO": """Olá, (Nome do cliente).\n\nTrago boas notícias! O seu pedido já foi aprovado e encontra-se atualmente em processo de expedição (separação e embalagem).\n\nEsta etapa garante que tudo chegue perfeito para você e pode levar até 72 horas úteis. Assim que o pacote for coletado pela transportadora, o código de rastreio será gerado e enviado para você acompanhar a rota de entrega.\n\nQualquer dúvida, estou à disposição!\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "SOLICITAÇÃO DE BARRAR EXPEDIÇÃO": """Olá, (Nome do cliente).\n\nRecebemos sua solicitação de cancelamento. Informo que já acionei nosso estoque solicitando o bloqueio imediato da expedição do pedido.\n\nEstamos aguardando apenas a confirmação da equipe logística de que o produto não foi coletado. Assim que confirmado, seguiremos com o reembolso conforme nossa política.\n\nTe aviso assim que tiver o "OK" do estoque!\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "PEDIDO CANCELADO (ENTREGUE)": """Olá, (Nome do cliente).\n\nNotamos pelo rastreio que o pedido foi entregue com sucesso no dia {data_entrega}.\n\nComo a plataforma Amazon já havia processado o reembolso deste pedido anteriormente, precisamos regularizar a situação. Por uma questão de ética e transparência, gostaríamos de confirmar como prefere prosseguir:\n\n1. Autorizar uma nova cobrança (Retrocharge) e ficar com o produto?\n2. Realizar a devolução do item? (Enviaremos um código de postagem sem custos).\n\nAguardamos seu retorno para finalizar este atendimento.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "PEDIDO CANCELADO (EM TRÂNSITO)": """Olá, (Nome do cliente).\n\nVerificamos que a plataforma já seguiu com o seu reembolso integral.\n\nComo o pedido ainda consta em rota, já solicitamos à transportadora que suspenda a entrega. No entanto, caso o entregador compareça ao seu endereço antes da atualização do sistema, orientamos que recuse o recebimento no ato da entrega.\n\nIsso garantirá que o pacote retorne ao nosso estoque automaticamente, finalizando o processo de forma correta.\n\nAgradecemos a compreensão!\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "CANCELAMENTO MARTINS (FRETE)": """Olá, {nome_cliente}!\n\nIdentificamos que, devido à localização de entrega, o valor do frete excedeu o limite operacional permitido para esta transação. Por este motivo, solicitamos a gentileza de seguir com o cancelamento do pedido.\n\nAtenciosamente, {colaborador} | Equipe de Atendimento Engage Eletro.""",
    "CANCELAMENTO MARTINS (ESTOQUE)": """Olá, {nome_cliente}!\n\nDevido a uma indisponibilidade pontual em nosso estoque logístico, não conseguiremos processar o envio do seu pedido desta vez. Para evitar maiores transtornos, pedimos que realize o cancelamento da compra.\n\nAtenciosamente, {colaborador} | Equipe de Atendimento Engage Eletro.""",
    "CANCELAMENTO MARTINS (PREÇO)": """Olá, {nome_cliente}!\n\nIdentificamos uma divergência no valor do produto devido a um erro técnico na transmissão de nossa tabela de precificação. Em razão disso, solicitamos o cancelamento do pedido para que possamos regularizar a situação.\n\nAtenciosamente, {colaborador} | Equipe de Atendimento Engage Eletro.""",
    "ENVIO DE NF": """Olá, (Nome do cliente)!\n\nSegue anexo a sua nota fiscal,\n\nFicamos à disposição para qualquer esclarecimento.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "ENVIO DE 2° VIA NF": """Olá, (Nome do cliente)\n\nSegue em anexo a segunda via da nota fiscal solicitada.\nFico à disposição para qualquer esclarecimento.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "CANCELAMENTO": """Olá, (Nome do cliente)\n\nRecebemos sua solicitação de cancelamento e lamentamos que tenha decidido não permanecer com a compra.\nGostaríamos de entender melhor o motivo da sua decisão antes de iniciarmos o processo de cancelamento.\nSeu feedback é essencial para que possamos melhorar continuamente nossos produtos e serviços.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "COMPROVANTE DE ENTREGA": """Olá, (Nome do cliente)\n\nSolicitamos, junto à transportadora responsável, o comprovante de entrega devidamente assinado para conferência, visto que não há reconhecimento do recebimento.\nPermanecemos no aguardo.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "AGRADECIMENTO": """Olá, (Nome do cliente)!\n\nQue ótima notícia! Fico muito feliz que tenha dado tudo certo. Sempre que tiver dúvidas, sugestões ou precisar de ajuda, não hesite em nos contatar. Estamos aqui para garantir a sua melhor experiência.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "AGRADECIMENTO 2": """Disponha!\n\nPermanecemos disponíveis para esclarecer quaisquer dúvidas.\nSempre que precisar de ajuda, tiver sugestões ou necessitar de esclarecimentos adicionais, não hesite em nos contatar.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "PRÉ-VENDA": """Olá, (Nome do cliente)!\n\n(Insira o texto de pré-venda aqui)\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "SOLICITAÇÃO DE COLETA": """Olá, (Nome do cliente)!\n\nVerificamos que o seu pedido está dentro do prazo para troca/cancelamento. Sendo assim, já solicitamos ao setor responsável a emissão da Nota Fiscal de coleta e o acionamento da transportadora para realizar o recolhimento da mercadoria.\n\nInstruções de devolução:\n- Por favor, devolva as mercadorias em suas embalagens originais ou similares, devidamente protegidas.\n- A transportadora realizará a coleta no endereço de entrega nos próximos 15/20 dias úteis: {endereco_resumido}\n- É necessário colocar dentro da embalagem uma cópia da Nota Fiscal.\n\nRessaltamos que, assim que a coleta for confirmada, daremos continuidade ao seu atendimento conforme solicitado.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "BARRAR ENTREGA NA TRANSPORTADORA": """Olá, (Nome do cliente)!\n\nSolicitamos à transportadora responsável o bloqueio da entrega. No entanto, caso haja alguma tentativa de entrega no local, pedimos a gentileza de recusar o recebimento no ato.\n\nAssim que o produto retornar ao centro de distribuição da Engage Eletro, seguiremos imediatamente com as tratativas de troca ou reembolso, conforme nossa política.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "ASSISTÊNCIA TÉCNICA (DENTRO DOS 7 DIAS)": """Olá, (Nome do cliente)!\n\nInformamos que o processo de troca via loja possui um prazo total de até 20 dias úteis (contando a partir da data de coleta).\n\nPara solucionar o seu problema de forma muito mais rápida, recomendamos acionar diretamente a assistência técnica da fabricante {fabricante}, que possui prioridade no atendimento. Seguem as informações de contato:\n{contato_assistencia}\n\nCaso a assistência técnica não consiga resolver ou seja inviável, por favor, nos informe. Verificaremos a possibilidade de troca diretamente conosco, mediante a disponibilidade em nosso estoque.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "PRAZOS DE REEMBOLSO": """Olá, (Nome do cliente)!\n\nA devolução do valor será realizada na mesma forma de pagamento utilizada na compra:\n\n- Boleto Bancário: O reembolso será feito em conta bancária de mesma titularidade ou via vale-presente. Se os dados informados estiverem corretos, o crédito ocorre em até 3 dias úteis.\n- Cartão de Crédito: O estorno será processado pela operadora do cartão e, dependendo da data de fechamento da sua fatura, poderá ser visualizado em uma ou duas faturas subsequentes.\n- PIX: O reembolso será realizado na conta de origem do PIX em até um dia útil.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "ASSISTÊNCIA TÉCNICA (FORA DOS 7 DIAS)": """Olá, (Nome do cliente)!\n\nVerificamos que a sua compra foi realizada no dia {data_compra}, referente à NF-{nota_fiscal}. Desta forma, o pedido encontra-se fora do prazo de 7 dias para cancelamento ou troca direta com a loja. No entanto, seu produto está amparado pela garantia do fabricante, que cobre defeitos de funcionamento.\n\nPara agilizar o reparo, segue o link para localizar o posto autorizado mais próximo de sua residência: {link_posto}\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "TROCA DE MODELO (DENTRO DE 7 DIAS)": """Olá, (Nome do cliente)!\n\nEsclarecemos que a troca direta é realizada em casos de divergência de pedido, defeito ou avaria. Não efetuamos trocas por insatisfação de modelo, cor ou voltagem após o envio correto.\n\nNeste caso, como prefere prosseguir? Você deseja permanecer com o produto recebido ou prefere seguir com o cancelamento e reembolso da compra?\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "CÓDIGO POSTAL (LOGÍSTICA REVERSA)": """Olá, (Nome do cliente)!\n\nSegue abaixo o código de postagem para a logística reversa. Para utilizá-lo, dirija-se a uma agência dos Correios com o produto devidamente embalado e apresente o código:\n{codigo_postagem}\n\nImportante:\n- O processo não gera custo para você.\n- Não é necessário endereçar a embalagem (remetente/destinatário), pois o código já vincula todos os dados.\n- Leve o Código de Autorização anotado ou no celular.\n\nApós o retorno do produto ao nosso Centro de Distribuição, seguiremos com a tratativa solicitada.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "REENVIO SOLICITADO": """Olá, (Nome do cliente)!\n\nTemos boas notícias! O seu novo envio já foi solicitado. O pedido será liberado para transporte em até 72h úteis. Assim que tivermos o novo rastreio, informaremos você.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "ACAREAÇÃO": """Olá, (Nome do cliente)!\n\nAbriremos um chamado de acareação junto à transportadora responsável. Neste procedimento, a transportadora retornará ao local de entrega para identificar quem recebeu a mercadoria e confrontar as informações.\n\nO prazo para a conclusão desta tratativa é de até 7 dias úteis. Pedimos que aguarde nosso retorno com a resolução.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "CONFIRMAÇÃO DE ENTREGA": """Olá, (Nome do cliente)!\n\nDe acordo com o sistema da transportadora {transportadora}, o seu pedido consta como entregue no dia {data_entrega}. Segue em anexo o comprovante de entrega: (QUANDO ESTIVER DISPONÍVEL E ASSINADO)\n\nCaso você não reconheça este recebimento, por favor, nos informe imediatamente para que possamos iniciar a acareação e as buscas pela mercadoria junto à transportadora.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "CONVERSÃO GLP/GNV": """Olá, (Nome do cliente)!\n\nInformamos que sua mercadoria sai de fábrica ajustada para GLP (gás de botijão). A conversão para Gás Natural (GNV) deve ser feita conforme as orientações do manual de instruções.\n\nAtenção: Quando a conversão é realizada pela rede de assistência autorizada da fabricante, o produto mantém a garantia original intacta.\n\nDados da Fabricante para agendamento: {fabricante}\nSite: {site_fabricante}\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "SOLICITAÇÃO DE DADOS BANCÁRIOS": """Olá, (Nome do cliente)!\n\nPara que possamos processar o seu reembolso, por favor, informe os dados bancários do titular da compra:\n\nNome do titular da compra:\nCPF do titular da compra:\nNome do banco:\nChave Pix:\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "OFERECER DESCONTO POR AVARIA": """Olá, (Nome do cliente)!\n\nLamentamos sinceramente pelo ocorrido. Gostaríamos de propor uma solução ágil.\nPrimeiramente, o produto está funcionando normalmente (apesar da avaria estética)?\n\nCaso o funcionamento esteja perfeito e você tenha interesse em permanecer com o item, podemos oferecer um reembolso parcial no valor de R$ {valor_desconto} como desconto pela avaria.\n\n- O produto continuará com a garantia total de funcionamento pela fabricante.\n\nSe aceitar esta proposta, por favor, nos informe os dados abaixo para pagamento:\nNome do titular da compra:\nCPF do titular da compra:\nNome do banco:\nChave Pix:\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "INSUCESSO NA ENTREGA (SOLICITAR DADOS)": """Olá, (Nome do cliente)!\n\nA transportadora nos informou que está com dificuldades para localizar o endereço ou finalizar a entrega. Para evitar a devolução, por favor, confirme os dados abaixo e nos forneça telefones atualizados:\n\nRua: {rua}\nCEP: {cep}\nNúmero: {numero}\nBairro: {bairro}\nCidade: {cidade}\nEstado: {estado}\nComplemento: {complemento}\nPonto de Referência: {referencia}\n2 telefones ativos (com DDD):\n\nAtenção: Caso não tenhamos retorno breve, o produto retornará ao nosso estoque e seguiremos com o reembolso.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "NOVA TENTATIVA DE ENTREGA": """Olá, (Nome do cliente)!\n\nJá repassamos as informações para a transportadora. Uma nova tentativa de entrega será realizada no prazo de 5 a 7 dias úteis, podendo ocorrer antes. Estamos acompanhando para garantir que você receba seu pedido o quanto antes.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "MERCADORIA EM TRÂNSITO": """Olá, (Nome do cliente)!\n\nConsultamos o rastreio e seu pedido segue em trânsito normal, com previsão de entrega até o dia {previsao_entrega}, podendo chegar antes.\n\nVocê pode acompanhar a entrega através dos dados abaixo:\nLink: {link_rastreio}\nNota fiscal: {nota_fiscal}\nTransportadora: {transportadora}\n\nPara rastrear, utilize o CPF do titular da compra.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "ERRO DE INTEGRAÇÃO": """Olá, (Nome do cliente)!\n\nPedimos sinceras desculpas pelo transtorno. Identificamos um erro de integração sistêmica que afetou alguns pedidos, incluindo o seu. Nossa equipe de TI já está atuando na correção e a liberação do seu pedido ocorrerá em breve.\n\nAgradecemos sua paciência e estamos à disposição.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "ERRO DE INTEGRAÇÃO COM ATRASO": """Olá, (Nome do cliente)!\n\nPedimos desculpas pela demora. Devido a uma falha de integração em nosso sistema, tivemos um impacto na operação de envios. No entanto, já solicitamos prioridade máxima para o seu pedido, a fim de que ele seja despachado o mais rápido possível.\n\nContamos com a sua compreensão e lamentamos o inconveniente.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "EXTRAVIO AGUARDAR CONFIRMAÇÃO": """Olá, (Nome do cliente)!\n\nA transportadora nos sinalizou uma possível situação de extravio com o seu pedido. Estamos em contato direto com eles para tentar localizar a mercadoria com urgência.\n\nPedimos a gentileza de aguardar um prazo de 48 horas para que possamos confirmar a situação e dar um retorno definitivo. Fique tranquilo(a): caso o pedido não seja localizado neste prazo, iniciaremos imediatamente os procedimentos de reenvio ou reembolso para garantir sua satisfação.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "EXTRAVIO COM OPÇÃO DE REENVIO": """Olá, (Nome do cliente)!\n\nLamentamos pelo transtorno causado. Confirmamos junto à transportadora que houve o extravio de sua mercadoria durante o trajeto. Para resolvermos isso rapidamente, gostaríamos de saber como prefere prosseguir:\n\nVocê deseja o reenvio de um novo produto ou o reembolso total da compra?\n\nAguardamos seu retorno para seguir com a opção escolhida.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "FISCALIZAÇÃO": """Olá, (Nome do cliente)!\n\nIdentificamos que seu pedido está retido na fiscalização (SEFAZ). Não se preocupe, já estamos em contato com a transportadora {transportadora} para providenciar a liberação o mais rápido possível.\n\nDevido a este trâmite fiscal, a entrega poderá sofrer um pequeno atraso. Assim que a mercadoria for liberada, solicitaremos prioridade na rota de entrega.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "ITEM FALTANTE": """Olá, (Nome do cliente)!\n\nSentimos muito pelo ocorrido. Já acionamos o nosso estoque e a expedição para verificar a disponibilidade do item faltante e providenciar o envio separado para você.\n\nRetornaremos com uma posição em breve.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "ATRASO NA ENTREGA": """Olá, (Nome do cliente)!\n\nLamentamos pelo atraso na entrega do seu pedido. Estamos em contato ativo com a transportadora para entender o motivo e cobramos uma nova previsão de entrega com urgência e prioridade de finalização. Manteremos você informado(a).\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "ENTREGA (SERVIÇOS NÃO INCLUSOS)": """Olá, (Nome do cliente)!\n\nGostaríamos de esclarecer alguns pontos sobre a entrega: O serviço contratado pela Engage Eletro junto às transportadoras parceiras cobre a entrega do produto até a entrada (porta ou portaria) do endereço indicado. O serviço não inclui: montagem/desmontagem, subida de escadas (se não houver elevador ou se o produto não couber), içamento por guincho ou instalação.\n\nAs entregas ocorrem de segunda a sexta-feira, em horário comercial.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "CÓDIGO COLETA DOMICILIAR": """Olá, (Nome do cliente)!\n\nSegue abaixo o código para a logística reversa (coleta domiciliar). Para que a coleta seja efetuada com sucesso, o produto deve estar devidamente embalado quando a transportadora chegar.\n\nCódigo de Coleta: {codigo_coleta}\n\nObservações:\n- O processo não gera custos para o cliente.\n- Não é necessário preencher dados de remetente/destinatário na caixa, o código já contém as informações.\n\nAssim que o produto retornar ao nosso Centro de Distribuição, seguiremos com a tratativa solicitada.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "EMBALAGEM SIMILAR": """Olá, (Nome do cliente)!\n\nPara garantir que o produto chegue intacto ao nosso centro de distribuição e seu processo seja finalizado sem problemas, reforçamos a importância da embalagem:\n\nRecomendamos envolver o produto em plástico bolha e utilizar uma caixa de papelão resistente (pode ser reutilizada, desde que sem rótulos antigos). Isso evita danos adicionais no transporte.\n\nAgradecemos sua colaboração.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "TERMO PARA TROCA CASADA": """Olá, (Nome do cliente)!\n\nPara agilizar o processo e tentar realizar a entrega do novo produto no mesmo momento da coleta do antigo, propomos a formalização de um Termo de Acordo Extrajudicial.\n\nO procedimento é simples:\n- Enviaremos o termo pelo nosso Jurídico.\n- Você deve assinar todas as páginas (conforme seu documento de identificação).\n- Envie o termo assinado + foto do documento (RG ou CNH) em até 48 horas.\n- Após validação jurídica, seguiremos com o envio e coleta simultânea.\n\nPodemos seguir com este procedimento?\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "RECUSA DE TROCA (AVARIA)": """Olá, (Nome do cliente)!\n\nConforme informamos, a troca do produto avariado é necessária agora para evitar problemas futuros, uma vez que o prazo de reclamação por danos físicos é limitado.\n\nRespeitamos sua decisão, mas entendemos que, ao recusar a troca neste momento, o(a) senhor(a) está ciente e assume o risco de permanecer com um produto com avaria estética, isentando a loja de reclamações futuras sobre este dano específico.\n\nReforçamos que seu produto continua coberto pela garantia do fabricante exclusivamente para defeitos funcionais, conforme a lei. Avarias físicas não são cobertas pela garantia de fábrica posteriormente.\n\nPermanecemos à disposição.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "RASTREIO INDISPONÍVEL (JADLOG)": """Olá, (Nome do cliente)!\n\nGostaríamos de tranquilizá-lo(a): seu pedido foi despachado regularmente e segue dentro do prazo de entrega. No momento, o sistema de rastreamento da transportadora apresenta uma instabilidade técnica temporária, impedindo a visualização do status em tempo real.\n\nJá notificamos a transportadora parceira e estamos monitorando o restabelecimento do sistema. Seu pedido continua em movimento normalmente.\n\nAgradecemos a compreensão.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}""",
    "SOLICITAÇÃO DE FOTOS E VÍDEOS (AVARIA)": """Olá, (Nome do cliente)!\n\nPedimos sinceras desculpas pelos transtornos causados com a chegada do seu produto. Entendemos sua frustração e queremos resolver isso o mais rápido possível.\n\nPara darmos continuidade ao atendimento e agilizarmos a solução junto ao setor responsável, precisamos que nos envie, por gentileza:\n· Fotos nítidas do produto e da embalagem onde consta a avaria;\n· Um breve vídeo mostrando o detalhe do dano (se possível).\n\nAssim que recebermos as evidências, faremos a análise imediata para prosseguir com as tratativas de resolução.\n\nEquipe de atendimento Engage Eletro.\n{colaborador}"""
}

# ORDENAÇÃO DE LISTA
lista_motivos_contato = sorted([k for k in modelos_sac.keys() if k not in ["OUTROS", "RECLAME AQUI", "INFORMAÇÃO SOBRE COLETA", "INFORMAÇÃO SOBRE ENTREGA", "INFORMAÇÃO SOBRE O PRODUTO", "INFORMAÇÃO SOBRE O REEMBOLSO", "COMPROVANTE DE ENTREGA (MARTINS)"]])
lista_motivos_contato.extend(["INFORMAÇÃO SOBRE COLETA", "INFORMAÇÃO SOBRE ENTREGA", "INFORMAÇÃO SOBRE O PRODUTO", "INFORMAÇÃO SOBRE O REEMBOLSO", "RECLAME AQUI", "COMPROVANTE DE ENTREGA (MARTINS)", "OUTROS"])

# ==========================================
#           DESIGN
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    .stApp { background-color: #f8fafc !important; font-family: 'Inter', sans-serif; }
    section[data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 1px solid #e2e8f0; }
    .stApp, .stApp * { color: #334155 !important; }
    h1, h2, h3, h4, h5, h6 { color: #0f172a !important; font-weight: 700; }
    .stSelectbox div[data-baseweb="select"] > div, .stTextInput input, .stDateInput input, .stTextArea textarea {
        background-color: #ffffff !important; border: 1px solid #94a3b8 !important; border-radius: 8px !important; color: #1e293b !important;
    }
    .preview-box { background-color: #f1f5f9 !important; border-left: 5px solid #3b82f6; border-radius: 4px; padding: 20px; color: #334155 !important; white-space: pre-wrap; margin-top: 10px; font-size: 14px; }
    .botao-registrar .stButton button { background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important; color: white !important; border: none; padding: 0.8rem 2rem; border-radius: 8px; font-weight: 600; width: 100%; box-shadow: 0 4px 6px rgba(16, 185, 129, 0.2); }
    .botao-registrar .stButton button:hover { transform: translateY(-2px); }
    .stDownloadButton button { background-color: #3b82f6 !important; color: white !important; border: none !important; border-radius: 8px; font-weight: 600; width: 100%; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
#           MENU
# ==========================================
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", width=180)
st.sidebar.caption("MENU PRINCIPAL")
pagina_escolhida = st.sidebar.radio("Navegação:", ("Pendências Logísticas", "SAC / Atendimento", "📊 Dashboard Gerencial"), label_visibility="collapsed")
st.sidebar.markdown("---")

# ==========================================
#           CALLBACKS (LÓGICA SEGURA)
# ==========================================
def registrar_e_limpar(setor, texto_pronto):
    # Salva o texto pronto na memória persistente ANTES de limpar os campos
    sufixo = "_p" if setor == "Pendência" else "_s"
    st.session_state[f'texto_persistente{sufixo}'] = texto_pronto
    
    # Recupera dados do Session State para salvar no Sheets
    colab = st.session_state.get(f"colab{sufixo}")
    motivo_opcao = st.session_state.get(f"msg{sufixo}")
    portal = st.session_state.get(f"portal{sufixo}")
    nf = st.session_state.get(f"nf{sufixo}")
    pedido = st.session_state.get(f"ped{sufixo}")
    crm = st.session_state.get(f"crm{sufixo}")
    
    transp = st.session_state.get(f"transp_p") if setor == "Pendência" else st.session_state.get("tr_ent_sac_conf", "-")
    if setor == "SAC" and transp == "-":
        transp = st.session_state.get("tr_trans_sac", st.session_state.get("tr_fisc_sac", "-"))

    sucesso = salvar_registro(setor, colab, motivo_opcao, portal, nf, pedido, crm, transp)
    
    if sucesso:
        st.session_state[f'sucesso_recente{sufixo}'] = True
        
        # Limpa campos
        campos_para_limpar = [f"cliente{sufixo}", f"nf{sufixo}", f"ped{sufixo}"]
        if setor == "SAC":
            campos_para_limpar.extend(["end_coleta_sac", "fab_in_7", "cont_assist_in_7", "data_comp_out_7", "nf_out_7", "link_out_7", "cod_post_sac", "tr_ent_sac_conf", "data_ent_sac", "fab_glp", "site_glp", "val_desc", "prev_ent", "link_rast", "nf_rast", "tr_trans_sac", "tr_fisc_sac", "rua_ins", "cep_ins", "num_ins", "bair_ins", "cid_ins", "uf_ins", "comp_ins", "ref_ins", "data_limite_recusa", "data_entrega_canc_ent"])
            
        for campo in campos_para_limpar:
            if campo in st.session_state:
                st.session_state[campo] = ""

# ==========================================
#           PÁGINA PENDÊNCIAS
# ==========================================
def pagina_pendencias():
    if st.session_state.get('sucesso_recente_p'):
        st.toast("Registrado e Limpo!", icon="✅")
        st.session_state['sucesso_recente_p'] = False

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
        assinatura_nome = colab if "AMAZON" not in portal else ""
        texto_base = texto_cru.replace("{transportadora}", transp).replace("{colaborador}", assinatura_nome).replace("{nome_cliente}", nome_cliente_str).replace("(Nome do cliente)", nome_cliente_str)
        if portal in ["CNOVA", "CNOVA - EXTREMA", "PONTO", "CASAS BAHIA"]: texto_base = texto_base.replace(f"Olá, {nome_cliente_str}", f"Olá, {nome_cliente_str}!")
        
        # ATUALIZADO: Inclui os novos motivos sem texto
        motivos_sem_texto = ["ATENDIMENTO DIGISAC", "2° TENTATIVA DE CONTATO", "3° TENTATIVA DE CONTATO", "REENTREGA", "AGUARDANDO TRANSPORTADORA"]
        
        if opcao not in motivos_sem_texto:
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
        
        # Passa o texto_final calculado como argumento
        st.button("✅ Registrar e Copiar", key="btn_save_pend", on_click=registrar_e_limpar, args=("Pendência", texto_final))
        st.markdown('</div>', unsafe_allow_html=True)

        if 'texto_persistente_p' in st.session_state:
            st.markdown("---")
            st.info("📝 Último texto registrado (Cópia Segura):")
            st.code(st.session_state['texto_persistente_p'], language="text")
            copiar_para_clipboard(st.session_state['texto_persistente_p'])

# ==========================================
#           PÁGINA SAC
# ==========================================
def pagina_sac():
    if st.session_state.get('sucesso_recente_s'):
        st.toast("Registrado e Limpo!", icon="✅")
        st.session_state['sucesso_recente_s'] = False

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
        elif "ENTREGA RECUSADA" in op_upper:
            st.info("📅 Dados de Prazo")
            dados["{data_limite}"] = st.text_input("Data/Horário limite:", key="data_limite_recusa")
        elif "PEDIDO CANCELADO (ENTREGUE)" in op_upper:
            st.info("📅 Dados da Entrega")
            dados["{data_entrega}"] = st.text_input("Data da Entrega:", key="data_entrega_canc_ent")

    with col2:
        st.subheader("2. Visualização")
        
        lista_livre_escrita = ["OUTROS", "RECLAME AQUI", "INFORMAÇÃO SOBRE COLETA", "INFORMAÇÃO SOBRE ENTREGA", "INFORMAÇÃO SOBRE O PRODUTO", "INFORMAÇÃO SOBRE O REEMBOLSO"]
        
        if opcao in lista_livre_escrita:
            label_texto = "Digite a mensagem personalizada:"
            if opcao == "RECLAME AQUI": label_texto = "Digite a resposta do Reclame Aqui:"
            elif "INFORMAÇÃO" in opcao: label_texto = f"Detalhes sobre {opcao}:"
            texto_base = st.text_area(label_texto, height=200)
            if texto_base: texto_base += f"\n\nEquipe de atendimento Engage Eletro.\n{{colaborador}}"
        else:
            texto_base = modelos_sac.get(opcao, "")

        nome_cliente_str = nome_cliente if nome_cliente else "(Nome do cliente)"
        texto_base = texto_base.replace("(Nome do cliente)", nome_cliente_str)
        if portal in ["CNOVA", "CNOVA - EXTREMA", "PONTO", "CASAS BAHIA"]: texto_base = texto_base.replace(f"Olá, {nome_cliente_str}", f"Olá, {nome_cliente_str}!")
        
        excecoes_nf = ["SAUDAÇÃO", "AGRADECIMENTO", "AGRADECIMENTO 2", "PRÉ-VENDA", "BARRAR ENTREGA NA TRANSPORTADORA", "ALTERAÇÃO DE ENDEREÇO (SOLICITAÇÃO DE DADOS)", "COMPROVANTE DE ENTREGA (MARTINS)"] + lista_livre_escrita
        scripts_martins = ["CANCELAMENTO MARTINS (FRETE)", "CANCELAMENTO MARTINS (ESTOQUE)", "CANCELAMENTO MARTINS (PREÇO)"]
        
        if opcao not in excecoes_nf and opcao not in scripts_martins:
            ped_str = numero_pedido if numero_pedido else "..."
            frase_pedido = f"O atendimento é referente ao seu pedido de número {ped_str}..."
            if "\n" in texto_base:
                partes = texto_base.split("\n", 1)
                texto_final = f"{partes[0]}\n\n{frase_pedido}\n{partes[1]}"
            else:
                texto_final = f"{frase_pedido}\n\n{texto_base}"
        elif opcao == "BARRAR ENTREGA NA TRANSPORTADORA":
             raw_text = modelos_sac["BARRAR ENTREGA NA TRANSPORTADORA"]
             corpo_mensagem = raw_text.replace("Olá, (Nome do cliente)!", "").strip()
             ped_str = numero_pedido if numero_pedido else "......"
             texto_final = f"Olá, {nome_cliente_str}!\nO atendimento é referente ao seu pedido de número {ped_str}\n\n{corpo_mensagem}"
        elif opcao == "ALTERAÇÃO DE ENDEREÇO (SOLICITAÇÃO DE DADOS)":
             raw_text = modelos_sac["ALTERAÇÃO DE ENDEREÇO (SOLICITAÇÃO DE DADOS)"]
             corpo_mensagem = raw_text.replace("Olá, (Nome do cliente)!", "").strip()
             ped_str = numero_pedido if numero_pedido else "......"
             texto_final = f"Olá, {nome_cliente_str}!\nO atendimento é referente ao seu pedido de número {ped_str}\n\n{corpo_mensagem}"
        elif opcao == "ESTOQUE FALTANTE":
             # Lógica para substituir o {portal}
             texto_final = texto_base.replace("{portal}", portal)
        elif opcao == "COMPROVANTE DE ENTREGA (MARTINS)":
             texto_final = ""
        elif opcao in scripts_martins:
            texto_final = texto_base.replace("{nome_cliente}", nome_cliente_str)
        else:
            texto_final = texto_base

        assinatura_nome = colab if "AMAZON" not in portal else ""
        texto_final = texto_final.replace("{colaborador}", assinatura_nome)
        
        for chave, valor in dados.items():
            substituto = valor if valor else "................"
            texto_final = texto_final.replace(chave, substituto)
        
        st.markdown(f'<div class="preview-box">{texto_final}</div>', unsafe_allow_html=True)
        st.write("")
        st.markdown('<div class="botao-registrar">', unsafe_allow_html=True)
        
        transp_usada = dados.get("{transportadora}", "-")
        if st.button("✅ Registrar e Copiar", key="btn_save_sac"):
            sucesso = salvar_registro("SAC", colab, opcao, portal, nota_fiscal, numero_pedido, motivo_crm, transp_usada)
            if sucesso:
                st.session_state['ultimo_texto_s'] = texto_final
                st.session_state['sucesso_recente_s'] = True
                
                # LIMPEZA SEGURA DOS CAMPOS
                keys_clean = ["cliente_s", "nf_s", "ped_s", "end_coleta_sac", "fab_in_7", "cont_assist_in_7", "data_comp_out_7", "nf_out_7", "link_out_7", "cod_post_sac", "tr_ent_sac_conf", "data_ent_sac", "fab_glp", "site_glp", "val_desc", "prev_ent", "link_rast", "nf_rast", "tr_trans_sac", "tr_fisc_sac", "rua_ins", "cep_ins", "num_ins", "bair_ins", "cid_ins", "uf_ins", "comp_ins", "ref_ins", "data_limite_recusa", "data_entrega_canc_ent"]
                for key in keys_clean:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        if 'texto_persistente_s' in st.session_state:
            st.markdown("---")
            st.info("📝 Último texto registrado (Cópia Segura):")
            st.code(st.session_state['texto_persistente_s'], language="text")
            copiar_para_clipboard(st.session_state['texto_persistente_s'])

# ==========================================
#           DASHBOARD
# ==========================================
def pagina_dashboard():
    st.title("📊 Dashboard Gerencial (Nuvem)")
    st.markdown("Visão estratégica em tempo real.")
    st.markdown("---")

    if not ("gcp_service_account" in st.secrets or os.path.exists("credentials.json")):
        st.error("🚨 Credenciais não encontradas.")
        return

    try:
        df = carregar_dados()
        if df.empty:
            st.warning("A planilha do Google Sheets está vazia.")
            uploaded_file = st.file_uploader("📂 Restaurar Backup (CSV Antigo)", type="csv")
            if uploaded_file and st.button("⬆️ Carregar para Nuvem"):
                df_upload = pd.read_csv(uploaded_file, sep=";", encoding='utf-8-sig')
                sheet = conectar_google_sheets()
                if sheet:
                    if "Dia_Semana" not in df_upload.columns: df_upload.insert(2, "Dia_Semana", "-")
                    sheet.append_rows(df_upload.astype(str).values.tolist())
                    st.success("Backup restaurado!")
            return

        df["Data_Filtro"] = pd.to_datetime(df["Data"], format="%d/%m/%Y", errors='coerce')
        
        st.sidebar.markdown("---")
        st.sidebar.subheader("Filtros do Painel")
        
        d_min = df["Data_Filtro"].min().date() if not df["Data_Filtro"].isnull().all() else datetime.today().date()
        d_max = df["Data_Filtro"].max().date() if not df["Data_Filtro"].isnull().all() else datetime.today().date()
        
        c_d1, c_d2 = st.sidebar.columns(2)
        ini = c_d1.date_input("Início", d_min, format="DD/MM/YYYY")
        fim = c_d2.date_input("Fim", d_max, format="DD/MM/YYYY")
        
        lst_setores = sorted(list(df["Setor"].unique()))
        f_setor = st.sidebar.multiselect("Filtrar por Setor:", options=lst_setores, default=lst_setores)
        if not f_setor: f_setor = lst_setores
        
        mask = (df["Data_Filtro"].dt.date >= ini) & (df["Data_Filtro"].dt.date <= fim) & (df["Setor"].isin(f_setor))
        df_f = df.loc[mask]
        
        if df_f.empty:
            st.warning("Nenhum dado encontrado.")
            return

        k1, k2, k3 = st.columns(3)
        k1.metric("Total", len(df_f), border=True)
        k2.metric("SAC", len(df_f[df_f["Setor"] == "SAC"]), border=True)
        k3.metric("Pendências", len(df_f[df_f["Setor"] == "Pendência"]), border=True)

        st.markdown("##")
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("📈 Tendência Diária")
            trend = df_f.groupby("Data_Filtro").size().reset_index(name='Atendimentos')
            fig = px.line(trend, x="Data_Filtro", y="Atendimentos", markers=True, title="Volume Diário", line_shape="spline", color_discrete_sequence=['#10b981'], text='Atendimentos')
            fig.update_traces(textposition="top center")
            fig.update_xaxes(tickformat="%d/%m", dtick="D1")
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            st.subheader("⏰ Picos de Demanda (Horário)")
            df_f['Hora_Int'] = pd.to_datetime(df_f['Hora'], format='%H:%M:%S', errors='coerce').dt.hour
            total_sec = df_f.groupby('Setor').size().reset_index(name='Total_Setor')
            heat = df_f.groupby(['Hora_Int', 'Setor']).size().reset_index(name='Atendimentos')
            heat = pd.merge(heat, total_sec, on='Setor')
            heat['Pct'] = (heat['Atendimentos'] / heat['Total_Setor']) * 100
            
            fig = px.line(heat, x='Hora_Int', y='Pct', title="Volume por Faixa Horária (% do Setor)", labels={'Hora_Int': 'Hora', 'Pct': '%'}, color='Setor', markers=True, text='Pct', color_discrete_map={'Pendência': '#3b82f6', 'SAC': '#10b981'})
            fig.update_traces(texttemplate='%{y:.1f}%', textposition='top center')
            fig.update_layout(xaxis=dict(tickmode='linear', dtick=1))
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("📊 Motivos CRM")
        df_crm = df_f[df_f["Motivo_CRM"].notna() & (df_f["Motivo_CRM"] != "-")]
        if not df_crm.empty:
            cont = df_crm['Motivo_CRM'].value_counts().reset_index()
            cont.columns = ['Motivo', 'Qtd']
            max_y = cont['Qtd'].max()
            fig = px.bar(cont.head(15), x='Motivo', y='Qtd', text='Qtd', title="Top Motivos CRM", color_discrete_sequence=['#f43f5e'])
            fig.update_traces(textposition='outside', cliponaxis=False)
            fig.update_layout(yaxis_range=[0, max_y * 1.2])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados de CRM.")

        st.markdown("---")
        st.subheader("📥 Exportação Geral")
        st.download_button(label="Baixar CSV", data=converter_para_excel_csv(df_f), file_name="relatorio_engage.csv", mime='text/csv')
        df_display = df_f.sort_values(by=["Data_Filtro", "Hora"], ascending=False).head(50)
        st.dataframe(df_display.drop(columns=["Data_Filtro", "Hora_Int"], errors='ignore'), use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Erro no Dashboard: {e}")

if pagina_escolhida == "Pendências Logísticas": pagina_pendencias()
elif pagina_escolhida == "SAC / Atendimento": pagina_sac()
else: pagina_dashboard()
