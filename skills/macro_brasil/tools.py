from bcb import sgs, PTAX, Expectativas
from langchain_core.tools import tool

CODIGOS_SGS = {
    "selic": 432,
    "ipca": 433,
    "cdi": 4391,
    "pib": 4380,
    "dolar_comercial": 1,
}


@tool
def get_bcb_series(nome_serie: str, start_date: str, end_date: str) -> str:
    """Busca uma série temporal econômica do Banco Central do Brasil (SGS).

    Séries disponíveis por nome: selic, ipca, cdi, pib, dolar_comercial.

    Args:
        nome_serie: nome da série (ex: "selic", "ipca").
        start_date: data inicial no formato "YYYY-MM-DD".
        end_date: data final no formato "YYYY-MM-DD".
    """
    codigo = CODIGOS_SGS.get(nome_serie.lower())
    if codigo is None:
        return f"Série '{nome_serie}' não reconhecida. Opções: {list(CODIGOS_SGS.keys())}"

    df = sgs.get({nome_serie: codigo}, start=start_date, end=end_date)
    return df.to_string()


@tool
def get_ptax_dolar_periodo(start_date: str, end_date: str) -> str:
    """Busca as cotações diárias de fechamento do dólar (PTAX) do Banco Central em um período.

    Args:
        start_date: data inicial no formato "MM-DD-YYYY".
        end_date: data final no formato "MM-DD-YYYY".
    """
    ptax = PTAX()
    endpoint = ptax.get_endpoint("CotacaoDolarPeriodo")
    df = (
        endpoint.query()
        .parameters(dataInicial=start_date, dataFinalCotacao=end_date)
        .collect()
    )
    return df.to_string()


@tool
def get_market_expectations(indicador: str, data_referencia: str) -> str:
    """Busca as expectativas de mercado (Boletim Focus) para um indicador macroeconômico brasileiro.

    Indicadores comuns: "IPCA", "Selic", "PIB Total", "Câmbio".

    Args:
        indicador: nome do indicador conforme usado no Focus (ex: "IPCA").
        data_referencia: ano de referência da expectativa (ex: "2026").
    """
    em = Expectativas()
    endpoint = em.get_endpoint("ExpectativasMercadoAnuais")
    df = (
        endpoint.query()
        .filter(endpoint.Indicador == indicador, endpoint.DataReferencia == data_referencia)
        .orderby(endpoint.Data.desc())
        .limit(5)
        .collect()
    )
    return df.to_string()