"""Integração com a API Dados Abertos da Câmera Federal."""

import logging
import typing as t

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("APIDadosAbertos")

URL_BASE = "https://dadosabertos.camara.leg.br/api/v2"

# Legislatura atual da Câmara dos Deputados (57ª: 2023–2027).
# Atualizar quando uma nova legislatura começar (58ª em fev/2027).
# A API de despesas precisa deste valor explicitamente; sem ele retorna
# apenas os últimos meses. Ver:
# https://github.com/CamaraDosDeputados/dados-abertos/issues/383
LEGISLATURA_ATUAL = 57
HEADERS = {
    "accept": "application/json",
    "User-Agent": "GastosPolíticos/1.0",
}


class CamaraDadosAbertos:
    """Integração com a API Dados Abertos da Câmara Federal."""

    def __init__(
        self,
        url_base: str = URL_BASE,
        headers: dict[str, str] | None = None,
        session: requests.Session | None = None,
        log: logging.Logger = logger,
    ):
        self.url_base = url_base.rstrip("/")
        self.headers = headers or HEADERS
        self.session = session or requests.Session()
        self.session.headers.update(self.headers)
        self.logger = logger

    def buscar_deputados(self) -> t.Generator[dict[str, t.Any], None, None]:
        """Retorna os deputados da legislação atual"""
        self.logger.info("Buscando deputados da legislação atual.")

        response = self.session.get(f"{self.url_base}/deputados")
        response.raise_for_status()

        self.logger.info(
            "%d deputados retornados para a legislação atual.",
            len(response.json().get("dados", [])),
        )

        for dep_dict in response.json().get("dados", []):
            yield dep_dict

    def buscar_despesas(
        self,
        id_deputado: int,
        mes: int | None = None,
        ano: int | None = None,
        id_legislatura: int = LEGISLATURA_ATUAL,
    ) -> t.Generator[dict[str, t.Any], None, None]:
        """Retorna os gastos do deputado na legislatura informada."""
        params: dict[str, t.Any] = {
            "idLegislatura": id_legislatura,
            "ordem": "DESC",
            "ordenarPor": "dataDocumento",
            "itens": 100,
        }
        if ano is not None:
            params["ano"] = ano
            if mes is not None:
                params["mes"] = mes

        url = f"{self.url_base}/deputados/{id_deputado}/despesas"

        yield from self._paginar_despesas(url, id_deputado, params)

    def _paginar_despesas(
        self,
        url: str,
        id_deputado: int,
        params: dict[str, t.Any],
    ) -> t.Generator[dict[str, t.Any], None, None]:
        """Itera através de todas as páginas de resultados."""
        while url:
            response = self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            for despesa in data.get("dados", []):
                despesa["idDeputado"] = id_deputado
                yield despesa

            # Prepara para próxima página
            url = self._extrair_url_proxima(data)  # type: ignore[assignment]
            params = {}  # Params só são usados na primeira requisição

    @staticmethod
    def _extrair_url_proxima(data: dict[str, t.Any]) -> str | None:
        """Extrai a URL da próxima página dos links de paginação."""
        for link in data.get("links", []):
            if link.get("rel") == "next":
                return link.get("href")
        return None

    def fechar(self) -> None:
        """Fecha a sessão de requisições."""
        self.session.close()

    def __enter__(self):
        """Entrada do context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Saída do context manager."""
        self.fechar()
