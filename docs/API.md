# FinBrain API Documentation

FinBrain exposes its functionality as a single **MCP (Model Context
Protocol)** server mounted on a FastAPI application, using the
**Streamable HTTP** transport. It does not expose conventional per-resource
REST routes (e.g. `/stocks`, `/crypto/{symbol}`); instead, every capability
is implemented as an MCP *tool*, discovered and invoked through one HTTP
endpoint via the MCP JSON-RPC protocol.

- Local base URL: `http://localhost:8000`
- Production base URL: `https://finbrain-mcp.vercel.app`

## HTTP endpoint

| Method | Path | Description |
|---|---|---|
| `POST` | `/mcp` | Main MCP endpoint. Handles JSON-RPC requests: `initialize`, `tools/list`, `tools/call`, etc. |
| `GET` | `/mcp` | Opens a server-sent events (SSE) stream for the MCP session, used for server-initiated messages. |
| `DELETE` | `/mcp` | Terminates an MCP session. |

The server runs with `stateless_http=True`, so no session state is kept
between requests on the server side — each request is handled
independently and no `Mcp-Session-Id` continuity is required across calls.

There are no other application routes: the FastAPI app (`mcp_server.py`)
only mounts the MCP ASGI app at the root path (`/`), and FastMCP registers
its single `Route("/mcp", ...)` on top of that.

### Calling a tool

Clients should use an MCP client SDK (e.g. `mcp.client.streamable_http`) or
speak the MCP JSON-RPC protocol directly against `POST /mcp`. Example flow:

1. `initialize` — negotiate protocol version and capabilities.
2. `tools/list` — discover available tools, their JSON schemas and
   descriptions.
3. `tools/call` — invoke a tool by name with its arguments.

See [`list_mcp_tools.py`](../list_mcp_tools.py) in the repository root for a
minimal Python client example that connects to the server and lists all
available tools.

## Tools reference

All tools return a plain string (JSON-encoded or formatted plain text,
depending on the tool). Every tool call is automatically traced as a
Langfuse `tool` observation when Langfuse credentials are configured (see
the root `README.md`).

### Stock analysis (`skills/stock_analysis`)

#### `collect_yfinance_data`

Collects real-time financial data, indicators, and price history for a
stock using Yahoo Finance.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `ticker` | `str` | — | Ticker in Yahoo Finance format (e.g. `PETR4.SA`, `AAPL`). |
| `period` | `str` | `"1mo"` | History window: `1d`, `5d`, `1mo`, `3mo`, `6mo`, `1y`, etc. |
| `interval` | `str` | `"1d"` | Candle interval: `1m`, `5m`, `15m`, `1h`, `1d`, `1wk`, `1mo`, etc. |

**Returns:** JSON string with `ticker`, `name`, `current_price`,
`previous_close`, `fifty_day_average`, `current_volume`, `average_volume`,
`currency`, `market_time`, `day_change` (%) and `history` (list of OHLCV
candles).

### Fundamental analysis (`skills/fundamental_analysis`)

#### `collect_fundamental_indicators`

Collects fundamental indicators for a stock using Yahoo Finance.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `ticker` | `str` | — | Ticker in Yahoo Finance format (e.g. `PETR4.SA`, `AAPL`). |

**Returns:** JSON string with `ticker`, `name`, `sector`, `pe_ratio`
(P/E), `pb_ratio` (P/B), `roe`, `net_margin`, `dividend_yield`,
`debt_to_equity`, `earnings_per_share`, `market_cap`, `currency`.

### Technical analysis (`skills/technical_analysis`)

#### `collect_technical_indicators`

Collects a stock's price history and computes technical indicators.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `ticker` | `str` | — | Ticker in Yahoo Finance format (e.g. `PETR4.SA`, `AAPL`). |
| `period` | `str` | `"3mo"` | History window: `1mo`, `3mo`, `6mo`, `1y`, etc. |

**Returns:** JSON string with `ticker`, `current_price`,
`moving_average_9`, `moving_average_21`, `moving_average_50` (`null` if
fewer than 50 data points), `rsi_14` (14-day RSI), `macd` and
`macd_signal`.

### Asset comparison (`skills/asset_comparison`)

#### `compare_assets`

Compares multiple assets side by side.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `tickers` | `str` | — | Comma-separated tickers in Yahoo Finance format (e.g. `PETR4.SA,VALE3.SA,ITUB4.SA`). |

**Returns:** JSON array, one object per ticker, with `ticker`, `name`,
`current_price`, `day_change` (%), `pe_ratio`, `dividend_yield`,
`currency` — or `{"ticker": ..., "error": ...}` for tickers that failed to
resolve.

### Brazilian macroeconomics (`skills/macro_brasil`)

#### `get_bcb_series`

Fetches an economic time series from the Central Bank of Brazil (SGS).

| Parameter | Type | Default | Description |
|---|---|---|---|
| `nome_serie` | `str` | — | Series name. One of: `selic`, `ipca`, `cdi`, `pib`, `dolar_comercial`. |
| `start_date` | `str` | — | Start date, format `YYYY-MM-DD`. |
| `end_date` | `str` | — | End date, format `YYYY-MM-DD`. |

**Returns:** Plain-text table (`DataFrame.to_string()`) of the series, or
an error message listing valid series names if `nome_serie` is not
recognized.

#### `get_ptax_dolar_periodo`

Fetches daily USD/BRL closing rates (PTAX) from the Central Bank of Brazil
for a date range.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `start_date` | `str` | — | Start date, format `MM-DD-YYYY`. |
| `end_date` | `str` | — | End date, format `MM-DD-YYYY`. |

**Returns:** Plain-text table of daily PTAX quotes.

#### `get_market_expectations`

Fetches market expectations (Focus Bulletin) for a Brazilian
macroeconomic indicator.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `indicador` | `str` | — | Indicator name as used in the Focus bulletin (e.g. `IPCA`, `Selic`, `PIB Total`, `Câmbio`). |
| `data_referencia` | `str` | — | Reference year for the expectation (e.g. `2026`). |

**Returns:** Plain-text table with the 5 most recent expectation entries
matching the indicator and reference year.

### Global macroeconomics (`skills/macro_global`)

#### `get_world_bank_indicator`

Fetches a World Bank macroeconomic indicator for a list of countries over
a year range.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `indicator_code` | `str` | — | World Bank indicator code (e.g. `NY.GDP.MKTP.CD`, `FP.CPI.TOTL.ZG`). |
| `countries` | `list[str]` | — | ISO country codes (e.g. `["BRA", "USA", "CHN"]`). |
| `start_year` | `int` | — | Start year. |
| `end_year` | `int` | — | End year. |

**Returns:** Plain-text table indexed by country/date, sorted by date,
with `NaN` rows dropped.

#### `search_world_bank_indicator`

Searches World Bank indicators by keyword.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `query` | `str` | — | Free-text search query (e.g. `"inflação"`, `"gdp"`). |

**Returns:** Up to 15 lines of `"<indicator_code>: <indicator_name>"`, or a
"not found" message.

#### `compare_countries_latest`

Compares the latest available value of an indicator across multiple
countries.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `indicator_code` | `str` | — | World Bank indicator code (e.g. `NY.GDP.PCAP.CD`). |
| `countries` | `list[str]` | — | ISO country codes (e.g. `["BRA", "ARG", "USA"]`). |

**Returns:** Plain-text table with the most recent value per country,
sorted descending.

### Cryptocurrency (`skills/cripto`)

#### `get_crypto_price`

Fetches the current ticker price of a cryptocurrency on a given exchange.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `exchange_name` | `str` | — | Lowercase exchange id supported by `ccxt` (e.g. `binance`, `coinbase`, `kraken`). |
| `symbol` | `str` | — | Trading pair, `BASE/QUOTE` format (e.g. `BTC/USDT`). |

**Returns:** Formatted text with last price, 24h high/low, 24h % change
and 24h volume; or an error message.

#### `get_crypto_ohlcv`

Fetches OHLCV candle history for a cryptocurrency.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `exchange_name` | `str` | — | Exchange id (e.g. `binance`). |
| `symbol` | `str` | — | Trading pair (e.g. `BTC/USDT`). |
| `timeframe` | `str` | `"1d"` | Candle interval (e.g. `1m`, `1h`, `1d`, `1w`). |
| `limit` | `int` | `10` | Number of most recent candles to return. |

**Returns:** Plain-text table with columns `timestamp`, `open`, `high`,
`low`, `close`, `volume`.

#### `get_crypto_order_book`

Fetches the order book (best bid/ask levels) for a cryptocurrency.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `exchange_name` | `str` | — | Exchange id (e.g. `binance`). |
| `symbol` | `str` | — | Trading pair (e.g. `BTC/USDT`). |
| `limit` | `int` | `5` | Number of price levels to return per side. |

**Returns:** Formatted text with best bid, best ask, spread, and the top
`limit` bids/asks.

#### `list_available_exchanges`

Lists all cryptocurrency exchanges supported by the `ccxt` library.

No parameters.

**Returns:** Comma-separated list of exchange ids.

## Error handling

Tools generally do not raise exceptions across the MCP boundary; instead
they catch errors internally and return a string describing the failure
(e.g. `{"error": "Could not collect data for ticker XYZ. Reason: ..."}` or
a plain-text `"Erro ao buscar ..."` message), so a bad ticker, unknown
exchange or invalid indicator surfaces as tool output rather than an MCP
protocol-level error.
