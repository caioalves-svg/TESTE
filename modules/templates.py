import json
import os
import streamlit as st


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


@st.cache_data(show_spinner=False)
def carregar_templates(setor: str) -> dict:
    if setor == "pendencias":
        path = os.path.join(DATA_DIR, "templates_pendencias.json")
    else:
        path = os.path.join(DATA_DIR, "templates_sac.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def carregar_listas() -> dict:
    path = os.path.join(DATA_DIR, "lists.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def renderizar_template(template: str, dados: dict) -> str:
    """Substitui placeholders {chave} pelo valor correspondente.
    Placeholders sem valor ficam vazios — sem KeyError.
    """
    class DefaultDict(dict):
        def __missing__(self, key):
            return ""

    return template.format_map(DefaultDict(dados))
