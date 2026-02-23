import time
import os

import gspread
import pandas as pd
import pytz
import streamlit as st
from datetime import datetime


NOME_PLANILHA = "Base_Atendimentos_Engage"
COLUNAS = ["Data", "Hora", "Dia_Semana", "Setor", "Colaborador", "Motivo",
           "Portal", "Nota_Fiscal", "Numero_Pedido", "Motivo_CRM", "Transportadora"]


def _obter_data_hora_brasil():
    fuso = pytz.timezone("America/Sao_Paulo")
    return datetime.now(fuso)


def _dia_semana_pt(dt) -> str:
    dias = {0: "Segunda-feira", 1: "Terça-feira", 2: "Quarta-feira",
            3: "Quinta-feira", 4: "Sexta-feira", 5: "Sábado", 6: "Domingo"}
    return dias[dt.weekday()]


@st.cache_resource(ttl=300, show_spinner=False)
def _conectar() -> gspread.Worksheet | None:
    try:
        if "gcp_service_account" in st.secrets:
            secrets = st.secrets["gcp_service_account"]
            creds = {
                "type": secrets["type"],
                "project_id": secrets["project_id"],
                "private_key_id": secrets["private_key_id"],
                "private_key": secrets["private_key"].replace("\\n", "\n"),
                "client_email": secrets["client_email"],
                "client_id": secrets["client_id"],
                "auth_uri": secrets["auth_uri"],
                "token_uri": secrets["token_uri"],
                "auth_provider_x509_cert_url": secrets["auth_provider_x509_cert_url"],
                "client_x509_cert_url": secrets["client_x509_cert_url"],
            }
            client = gspread.service_account_from_dict(creds)
        elif os.path.exists("credentials.json"):
            client = gspread.service_account(filename="credentials.json")
        else:
            return None
        return client.open(NOME_PLANILHA).sheet1
    except Exception:
        return None


def salvar_registro(dados: dict) -> bool:
    """Grava uma linha na planilha com 3 tentativas e backoff exponencial."""
    agora = _obter_data_hora_brasil()
    linha = [
        agora.strftime("%d/%m/%Y"),
        agora.strftime("%H:%M:%S"),
        _dia_semana_pt(agora),
        dados.get("setor", ""),
        dados.get("colaborador", ""),
        dados.get("motivo", ""),
        dados.get("portal", ""),
        str(dados.get("nota_fiscal", "")),
        str(dados.get("numero_pedido", "")),
        dados.get("motivo_crm", ""),
        dados.get("transportadora", "-"),
    ]
    for tentativa in range(3):
        try:
            sheet = _conectar()
            if sheet is None:
                return False
            sheet.append_row(linha)
            return True
        except Exception:
            if tentativa < 2:
                time.sleep(0.5 * (2 ** tentativa))
    return False


@st.cache_data(ttl=60, show_spinner=False)
def carregar_dados_dashboard() -> pd.DataFrame:
    sheet = _conectar()
    if sheet is None:
        return pd.DataFrame()
    try:
        registros = sheet.get_all_records()
        if registros:
            return pd.DataFrame(registros)
        return pd.DataFrame(columns=COLUNAS)
    except Exception:
        return pd.DataFrame()
