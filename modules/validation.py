CAMPOS_PENDENCIAS = [
    "colaborador", "nome_cliente", "portal",
    "numero_pedido", "motivo_crm", "transportadora",
]

CAMPOS_SAC_BASE = [
    "colaborador", "nome_cliente", "portal", "motivo", "motivo_crm",
]

CAMPOS_CONDICIONAIS_SAC: dict[str, list[str]] = {
    "SOLICITAÇÃO DE COLETA": ["endereco_resumido"],
    "MERCADORIA EM TRÂNSITO": ["previsao_entrega", "link_rastreio"],
    "ASSISTÊNCIA TÉCNICA (DENTRO DOS 7 DIAS)": ["fabricante", "contato_assistencia"],
    "ASSISTÊNCIA TÉCNICA (FORA DOS 7 DIAS)": ["data_compra", "nota_fiscal", "link_posto"],
    "CONFIRMAÇÃO DE ENTREGA": ["transportadora", "data_entrega"],
    "CONVERSÃO GLP/GNV": ["fabricante", "site_fabricante"],
    "OFERECER DESCONTO POR AVARIA": ["valor_desconto"],
    "ENTREGA RECUSADA": ["data_limite"],
    "PEDIDO CANCELADO (ENTREGUE)": ["data_entrega"],
    "CÓDIGO POSTAL (LOGÍSTICA REVERSA)": ["codigo_postagem"],
    "CÓDIGO COLETA DOMICILIAR": ["codigo_coleta"],
    "INSUCESSO NA ENTREGA (SOLICITAR DADOS)": ["rua", "cep", "numero", "bairro", "cidade", "estado"],
    "FISCALIZAÇÃO": ["transportadora"],
}

MOTIVOS_SEM_PEDIDO = [
    "SAUDAÇÃO", "AGRADECIMENTO", "AGRADECIMENTO 2", "PRÉ-VENDA",
    "BARRAR ENTREGA NA TRANSPORTADORA", "ALTERAÇÃO DE ENDEREÇO (SOLICITAÇÃO DE DADOS)",
    "ESTOQUE FALTANTE", "COMPROVANTE DE ENTREGA (MARTINS)", "PEDIDO AMAZON FBA",
    "BAIXA ERRÔNEA", "COBRANÇA INDEVIDA", "INFORMAÇÃO EMBALAGEM",
    "RETIRADA DE ENTREGA", "ENCERRAMENTO DE CHAT", "SOLICITAÇÃO DE COLETA",
    "OUTROS", "RECLAME AQUI", "INFORMAÇÃO SOBRE COLETA", "INFORMAÇÃO SOBRE ENTREGA",
    "INFORMAÇÃO SOBRE O PRODUTO", "INFORMAÇÃO SOBRE O REEMBOLSO",
]


def validar_campos(dados: dict, campos: list[str]) -> list[str]:
    """Retorna lista de nomes de campos obrigatórios que estão vazios."""
    faltando = []
    for campo in campos:
        valor = dados.get(campo, "")
        if not str(valor).strip():
            faltando.append(campo.replace("_", " ").title())
    return faltando


def validar_pendencia(dados: dict) -> list[str]:
    return validar_campos(dados, CAMPOS_PENDENCIAS)


def validar_sac(dados: dict, motivo: str) -> list[str]:
    faltando = validar_campos(dados, CAMPOS_SAC_BASE)
    extras = CAMPOS_CONDICIONAIS_SAC.get(motivo.upper(), [])
    faltando += validar_campos(dados, extras)
    return faltando
