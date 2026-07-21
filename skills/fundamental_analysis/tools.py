import yfinance as yf
import json
from langchain_core.tools import tool


@tool
def collect_fundamental_indicators(ticker: str) -> str:
    """
    Collect fundamental indicators for a stock (P/E, P/B, ROE, net margin,
    dividend yield, debt-to-equity) using Yahoo Finance.
    The ticker format must follow the Yahoo standard (e.g. 'PETR4.SA' for Petrobras or 'AAPL' for Apple).
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        filtered_data = {
            "ticker": ticker,
            "name": info.get("longName", "N/A"),
            "sector": info.get("sector", "N/A"),
            "pe_ratio": info.get("trailingPE"),
            "pb_ratio": info.get("priceToBook"),
            "roe": info.get("returnOnEquity"),
            "net_margin": info.get("profitMargins"),
            "dividend_yield": info.get("dividendYield"),
            "debt_to_equity": info.get("debtToEquity"),
            "earnings_per_share": info.get("trailingEps"),
            "market_cap": info.get("marketCap"),
            "currency": info.get("currency", "BRL"),
        }

        return json.dumps(filtered_data, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": f"Could not collect indicators for ticker {ticker}. Reason: {str(e)}"})
