import yfinance as yf
import json
import pandas as pd
from langchain_core.tools import tool


def _calculate_rsi(prices: pd.Series, period: int = 14) -> float | None:
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    average_gain = gain.rolling(window=period).mean()
    average_loss = loss.rolling(window=period).mean()
    rs = average_gain / average_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi.iloc[-1], 2) if not rsi.empty and pd.notna(rsi.iloc[-1]) else None


@tool
def collect_technical_indicators(ticker: str, period: str = "3mo") -> str:
    """
    Collect a stock's price history and compute technical indicators:
    moving averages (9, 21, 50 days), RSI (14 days) and MACD.
    The ticker format must follow the Yahoo standard (e.g. 'PETR4.SA' or 'AAPL').
    The period can be '1mo', '3mo', '6mo', '1y', etc.
    """
    try:
        stock = yf.Ticker(ticker)
        history = stock.history(period=period)

        if history.empty:
            return json.dumps({"error": f"No historical data for ticker {ticker}."})

        close = history["Close"]

        ma9 = close.rolling(window=9).mean().iloc[-1]
        ma21 = close.rolling(window=21).mean().iloc[-1]
        ma50 = close.rolling(window=50).mean().iloc[-1] if len(close) >= 50 else None

        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        macd_signal = macd_line.ewm(span=9, adjust=False).mean()

        data = {
            "ticker": ticker,
            "current_price": round(close.iloc[-1], 2),
            "moving_average_9": round(ma9, 2) if pd.notna(ma9) else None,
            "moving_average_21": round(ma21, 2) if pd.notna(ma21) else None,
            "moving_average_50": round(ma50, 2) if ma50 is not None and pd.notna(ma50) else None,
            "rsi_14": _calculate_rsi(close),
            "macd": round(macd_line.iloc[-1], 4),
            "macd_signal": round(macd_signal.iloc[-1], 4),
        }

        return json.dumps(data, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": f"Could not compute technical indicators for {ticker}. Reason: {str(e)}"})
