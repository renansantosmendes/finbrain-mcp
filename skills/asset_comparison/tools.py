import yfinance as yf
import json
from langchain_core.tools import tool


@tool
def compare_assets(tickers: str) -> str:
    """
    Compare multiple assets side by side (price, day change, P/E and dividend yield).
    Pass the tickers separated by commas, in Yahoo Finance format
    (e.g. 'PETR4.SA,VALE3.SA,ITUB4.SA' or 'AAPL,MSFT,GOOGL').
    """
    ticker_list = [t.strip() for t in tickers.split(",") if t.strip()]
    results = []

    for ticker in ticker_list:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            current_price = info.get("currentPrice") or info.get("regularMarketPrice")
            previous_close = info.get("previousClose")
            change = None
            if current_price and previous_close:
                change = round(((current_price - previous_close) / previous_close) * 100, 2)

            results.append({
                "ticker": ticker,
                "name": info.get("longName", "N/A"),
                "current_price": current_price,
                "day_change": change,
                "pe_ratio": info.get("trailingPE"),
                "dividend_yield": info.get("dividendYield"),
                "currency": info.get("currency", "BRL"),
            })
        except Exception as e:
            results.append({"ticker": ticker, "error": str(e)})

    return json.dumps(results, ensure_ascii=False)
