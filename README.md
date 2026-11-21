# Gastos dos Políticos

Site estático sobre os gastos dos deputados federais, com dados da
[API Dados Abertos da Câmara](https://dadosabertos.camara.leg.br/swagger/api.html).
As páginas são renderizadas com Jinja2 e publicadas no GitHub Pages.

## Desenvolvimento

O projeto usa [uv](https://docs.astral.sh/uv/).

```bash
uv sync                              # cria .venv e instala dependências (inclui dev)
uv run invoke exportar-dataframes    # baixa deputados e despesas para publish/dataframes
uv run invoke build                  # gera publish/index.html
uv run invoke serve                  # serve o site em http://localhost:8000
uv run invoke gh-pages               # gera e publica no branch gh-pages
```

A legislatura consultada fica em `LEGISLATURA_ATUAL`
(`gastospoliticos/apidadosabertos.py`) e deve ser atualizada quando uma nova
legislatura começar.
