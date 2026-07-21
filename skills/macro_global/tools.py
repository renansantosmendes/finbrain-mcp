import wbdata
from langchain_core.tools import tool


@tool
def get_world_bank_indicator(indicator_code: str, countries: list[str], start_year: int, end_year: int) -> str:
    """Busca um indicador macroeconômico do Banco Mundial para uma lista de países, em um intervalo de anos.

    Indicadores comuns:
    - NY.GDP.MKTP.CD: PIB (US$ correntes)
    - NY.GDP.PCAP.CD: PIB per capita
    - FP.CPI.TOTL.ZG: Inflação anual (%)
    - SL.UEM.TOTL.ZS: Taxa de desemprego (%)
    - SP.POP.TOTL: População total

    Args:
        indicator_code: código do indicador (ex: "FP.CPI.TOTL.ZG").
        countries: lista de códigos de país ISO (ex: ["BRA", "USA", "CHN"]).
        start_year: ano inicial.
        end_year: ano final.
    """
    df = wbdata.get_dataframe(
        {indicator_code: "valor"},
        country=countries,
        date=(f"{start_year}", f"{end_year}"),
    )
    df = df.dropna().sort_index()
    return df.to_string()


@tool
def search_world_bank_indicator(query: str) -> str:
    """Busca indicadores do Banco Mundial por palavra-chave, retornando código e descrição.

    Use quando não souber o código exato do indicador (ex: query="inflação" ou "gdp").
    """
    resultados = wbdata.search_indicators(query)
    linhas = [f"{r['id']}: {r['name']}" for r in list(resultados)[:15]]
    return "\n".join(linhas) if linhas else f"Nenhum indicador encontrado para '{query}'."


@tool
def compare_countries_latest(indicator_code: str, countries: list[str]) -> str:
    """Compara o valor mais recente disponível de um indicador entre vários países, ordenado do maior para o menor.

    Args:
        indicator_code: código do indicador do Banco Mundial (ex: "NY.GDP.PCAP.CD").
        countries: lista de códigos de país ISO (ex: ["BRA", "ARG", "USA"]).
    """
    df = wbdata.get_dataframe({indicator_code: "valor"}, country=countries)
    ultimos = df.dropna().groupby(level="country").apply(lambda g: g.sort_index().iloc[-1])
    ultimos = ultimos.sort_values("valor", ascending=False)
    return ultimos.to_string()