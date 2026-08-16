# FinBrain MCP

FinBrain é um servidor **MCP (Model Context Protocol)** que expõe um conjunto de
ferramentas (skills) de análise financeira — ações, criptomoedas e
macroeconomia — para qualquer cliente compatível com MCP (agentes de IA,
IDEs, deep agents, etc.). O servidor é construído sobre o `FastMCP`
(SDK oficial do MCP) e é hospedado como uma aplicação **FastAPI**, o que
permite rodá-lo tanto localmente via `uvicorn` quanto como função serverless
na **Vercel**.

Em outras palavras: o FinBrain não é uma API REST tradicional com múltiplas
rotas de negócio — é um único endpoint MCP (`/mcp`) por onde qualquer cliente
descobre e chama as ferramentas disponíveis usando o protocolo MCP
(JSON-RPC sobre HTTP/SSE).

## Índice

- [Arquitetura](#arquitetura)
- [Skills e ferramentas disponíveis](#skills-e-ferramentas-disponíveis)
- [Como rodar localmente](#como-rodar-localmente)
- [Variáveis de ambiente](#variáveis-de-ambiente)
- [Deploy](#deploy)
- [Observabilidade (Langfuse)](#observabilidade-langfuse)
- [Testando o servidor](#testando-o-servidor)
- [Convenções de código](#convenções-de-código)
- [Documentação da API](#documentação-da-api)

## Arquitetura

```
mcp_server.py        -> monta o servidor MCP (FastMCP) dentro de uma app FastAPI
api/index.py          -> entrypoint usado pela Vercel (functions/api/index.py)
skills/<nome>/tools.py -> cada skill é uma pasta com as tools (funções) que ela expõe
list_mcp_tools.py      -> script utilitário para listar as tools de um servidor MCP remoto
vercel.json            -> configuração de deploy serverless na Vercel
```

- Cada **skill** é uma pasta em `skills/` contendo um `tools.py` com uma ou
  mais funções decoradas com `@tool` (do `langchain_core.tools`).
- O `mcp_server.py` importa essas funções e as registra no `FastMCP` via
  `mcp.tool(...)`, envolvendo cada chamada com rastreamento (tracing) do
  Langfuse.
- O `FastMCP` gera uma aplicação ASGI (`streamable_http_app`) que é montada
  na raiz da aplicação FastAPI (`app.mount("/", mcp_asgi_app)`), expondo o
  protocolo MCP via **Streamable HTTP** no caminho `/mcp`.
- Não há rotas REST de negócio (ex.: `/stocks`, `/crypto`) — todas as
  capacidades são acessadas como *tools* MCP através do único endpoint
  `/mcp`. Veja a seção [Documentação da API](#documentação-da-api).

## Skills e ferramentas disponíveis

| Skill | Pasta | O que faz |
|---|---|---|
| Análise de ações | `skills/stock_analysis` | Dados em tempo real e histórico de preços via Yahoo Finance |
| Análise fundamentalista | `skills/fundamental_analysis` | Indicadores fundamentalistas (P/L, P/VP, ROE, margem líquida, dividend yield, etc.) |
| Análise técnica | `skills/technical_analysis` | Médias móveis, RSI e MACD calculados a partir do histórico de preços |
| Comparação de ativos | `skills/asset_comparison` | Compara múltiplos tickers lado a lado |
| Macroeconomia Brasil | `skills/macro_brasil` | Séries do Banco Central (SGS), PTAX e expectativas de mercado (Boletim Focus) |
| Macroeconomia global | `skills/macro_global` | Indicadores do Banco Mundial, busca de indicadores e comparação entre países |
| Criptomoedas | `skills/cripto` | Preço, candles (OHLCV) e order book via `ccxt`, em múltiplas exchanges |
| Séries sintéticas | `skills/synthetic_series` | Gera N séries temporais sintéticas de preços via modelo GARCH(1,1) (`arch`) |

Cada skill expõe uma ou mais *tools* MCP. A lista completa de tools, seus
parâmetros e formatos de retorno está documentada em inglês em
[`docs/API.md`](docs/API.md), conforme convenção do projeto (código e
documentação técnica em inglês, camada de negócio em português — ver
[`AGENTS.md`](AGENTS.md)).

## Como rodar localmente

Pré-requisitos: Python 3.11+.

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

pip install -r requirements.txt
cp .env.example .env          # preencha as chaves do Langfuse (opcional)

python mcp_server.py
```

O servidor sobe em `http://0.0.0.0:8000`, com o endpoint MCP disponível em
`http://localhost:8000/mcp`.

## Variáveis de ambiente

Definidas em `.env` (veja `.env.example`):

| Variável | Obrigatória | Descrição |
|---|---|---|
| `LANGFUSE_PUBLIC_KEY` | Não | Chave pública do Langfuse, usada para tracing das chamadas de tools |
| `LANGFUSE_SECRET_KEY` | Não | Chave secreta do Langfuse |
| `LANGFUSE_HOST` | Não | Host da instância Langfuse (cloud ou self-hosted) |

Sem essas variáveis o servidor continua funcionando normalmente; apenas o
tracing das tools fica desabilitado/sem efeito.

## Deploy

O projeto está preparado para deploy serverless na **Vercel**:

- `api/index.py` importa a app FastAPI de `mcp_server.py` e a expõe como
  função serverless.
- A Vercel detecta automaticamente a app FastAPI (zero-config) e roteia
  todas as rotas para ela — **não** use `rewrites` no `vercel.json` para
  isso: em projetos com framework de backend detectado, a Vercel passa o
  path de destino do rewrite como o path interno da requisição, então um
  rewrite `"/(.*)" -> "/api/index"` faz toda rota chegar na app como
  `/api/index`, quebrando o roteamento (foi a causa de um 404 em produção
  em todas as rotas, inclusive `/mcp`).
- `vercel.json` só define `maxDuration: 30` segundos para a função
  (`functions["api/index.py"]`).
- Caches que normalmente seriam escritos no diretório do usuário
  (`wbdata`, `yfinance`) são redirecionados para `/tmp`, único diretório
  gravável em runtimes serverless como a Vercel.

Deploy: `vercel --prod` (ou via integração automática com o repositório
Git).

## Observabilidade (Langfuse)

Todas as tools são automaticamente instrumentadas com
[Langfuse](https://langfuse.com/) via o decorator `observe`. Cada chamada de
tool gera uma observação do tipo `tool`, com flush síncrono ao final da
execução — útil em ambientes serverless, onde o processo pode ser encerrado
logo após a resposta.

## Testando o servidor

O script `list_mcp_tools.py` conecta-se a um servidor MCP (local ou remoto)
e lista as tools disponíveis:

```bash
python list_mcp_tools.py                                   # usa o deploy de produção
python list_mcp_tools.py http://localhost:8000/mcp          # usa o servidor local
```

Testes unitários (`pytest`) cobrem as skills que possuem lógica própria além
de chamadas diretas a APIs externas, como `skills/synthetic_series`:

```bash
pip install -r requirements-dev.txt   # instala requirements.txt + pytest
python -m pytest tests/
```

`pytest` fica isolado em `requirements-dev.txt` (não vai para o deploy da
Vercel, que usa apenas `requirements.txt`).

## Convenções de código

As convenções de nomenclatura, idioma, docstrings e estrutura de skills
estão formalizadas em [`AGENTS.md`](AGENTS.md). Resumo: **código em inglês,
negócio em português** — nomes de funções, variáveis e docstrings em
inglês; qualquer camada voltada a quem opera o agente no dia a dia, em
português.

## Documentação da API

A documentação técnica completa dos endpoints HTTP e de todas as tools MCP
(nome, parâmetros, tipos e retorno) está em [`docs/API.md`](docs/API.md),
escrita em inglês.
