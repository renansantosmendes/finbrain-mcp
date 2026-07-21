# Guia de Boas Práticas de Código

Este guia formaliza as convenções adotadas no projeto. Ele existe para que qualquer
skill, tool ou módulo novo siga o mesmo padrão dos demais.

## 1. Idioma

Regra geral: **código em inglês, negócio em português**.

| Elemento                                              | Idioma   |
|--------------------------------------------------------|----------|
| Nomes de pastas de skills (`skills/<nome>/`)            | Inglês   |
| Nomes de arquivos (`tools.py`, `SKILL.md`)               | Inglês (nomes já padronizados) |
| Nomes de funções e tools (`@tool def ...`)              | Inglês   |
| Nomes de variáveis                                      | Inglês   |
| Docstrings                                              | Inglês   |
| Conteúdo do `SKILL.md` (descrição, protocolo, formato)  | **Português** |
| Perguntas de exemplo / inputs de teste do usuário       | **Português** |

O `SKILL.md` é a única camada pensada para quem opera o agente no dia a dia
(negócio, suporte, produto), por isso permanece em português. Todo o resto é
código e segue convenção de engenharia (inglês).

## 2. Nomenclatura

- **Skills (pastas):** `snake_case` em inglês, nome do domínio.
  Ex.: `stock_analysis`, `technical_analysis`, `asset_comparison`.
- **Tools (funções `@tool`):** verbo + objeto, em inglês, `snake_case`.
  Ex.: `collect_technical_indicators`, `compare_assets`, `collect_yfinance_data`.
- **Variáveis:** inglês, `snake_case`, descritivas.
  Ex.: `filtered_data`, `closing_prices`, `current_price` (nunca `dados_filtrados`, `preco_atual`).
- **Funções privadas/auxiliares:** prefixo `_`, mesma convenção de nome.
  Ex.: `_calculate_rsi`.

## 3. Docstrings

- Sempre em inglês, no formato de resumo curto (o que a função faz + formato
  esperado de entrada, quando relevante).
- A docstring é a única explicação "oficial" da função — dispensa comentários
  inline redundantes.

```python
@tool
def collect_stock_data(ticker: str) -> str:
    """
    Collects real-time financial data and indicators for a stock using Yahoo Finance.
    The ticker format must follow Yahoo's standard (e.g. 'PETR4.SA' or 'AAPL').
    """
    ...
```

## 4. Comentários

- **Proibido** comentar o que o código já diz por si (ex.: `# soma os dois valores`
  acima de `total = a + b`). Se for preciso um comentário desses, o nome da
  variável/função está ruim — corrija o nome, não adicione o comentário.
- Comentários só são aceitáveis para:
  - Avisos de segurança ou limitação externa (ex.: rate limit de uma API).
  - Decisão de negócio não óbvia a partir do código (ex.: por que um limiar
    específico foi escolhido).
  - `TODO`/`FIXME` com contexto.

## 5. Type hints

- **Toda função** deve ter type hints nos parâmetros e no tipo de retorno.

```python
def _calculate_rsi(prices: pd.Series, period: int = 14) -> float:
    ...

@tool
def collect_technical_indicators(ticker: str, period: str = "3mo") -> str:
    ...
```

- **Não** anotar atribuições de variáveis locais — o tipo já fica claro pelo
  valor atribuído:

```python
# Correto
filtered_data = {"ticker": ticker, ...}

# Incorreto (não fazer)
filtered_data: dict = {"ticker": ticker, ...}
```

## 6. Estrutura de uma skill

Este repositório expõe apenas o servidor MCP: cada skill é uma pasta só com
`tools.py`, sem `SKILL.md` (esse arquivo é consumido pelo client deep-agent,
que vive em outro repositório, e é irrelevante para o servidor MCP).

```
skills/<nome_em_ingles>/
└── tools.py   # funções @tool em inglês, com docstring em inglês e type hints
```