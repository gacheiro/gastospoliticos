"""Agregações dos dados de gastos usadas para gerar as páginas do site.

Tudo é calculado com pandas a partir dos DataFrames exportados da API,
uma única vez por build.
"""

import re
from dataclasses import dataclass, field

import pandas as pd

# Despesas acima deste valor entram em "Gastos mais recentes" na página inicial.
VALOR_MINIMO_RECENTES = 1000


def preparar_gastos(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza o DataFrame bruto de despesas da API."""
    df = df.drop_duplicates().copy()
    # valorLiquido da API vem com sinal invertido; recalcula (ver models.Gasto).
    df["valor"] = (df["valorDocumento"] - df["valorGlosa"].fillna(0)).round(2)
    df["data"] = pd.to_datetime(df["dataDocumento"].str[:10], errors="coerce")
    df["tipo"] = df["tipoDespesa"].map(normalizar_tipo)
    df["fornecedor"] = df["nomeFornecedor"].fillna("").str.strip()
    df["url"] = df["urlDocumento"].where(df["urlDocumento"].notna(), None)
    return df


def normalizar_tipo(tipo: str) -> str:
    """'COMBUSTÍVEIS E LUBRIFICANTES.' -> 'Combustíveis e lubrificantes'."""
    tipo = str(tipo).strip().rstrip(".").strip()
    tipo = re.sub(r"\s*,\s*", ", ", tipo)  # "HOSPEDAGEM ,EXCETO" -> "HOSPEDAGEM, EXCETO"
    return tipo[:1].upper() + tipo[1:].lower()


@dataclass
class Ranking:
    titulo: str
    itens: list[dict]  # {"deputado": dict, "total": float}

    @property
    def maximo(self) -> float:
        return max((i["total"] for i in self.itens), default=0) or 1


@dataclass
class PaginaDeputado:
    deputado: dict
    total_legislatura: float
    total_ano: float
    por_ano: list[tuple[int, float]]
    por_mes: list[tuple[int, float]]  # meses 1..12 do ano atual
    por_tipo: list[tuple[str, float]]
    despesas: list[dict] = field(default_factory=list)  # despesas do ano atual


class Painel:
    """Calcula os números e listas exibidos no site."""

    def __init__(self, df_deputados: pd.DataFrame, df_gastos: pd.DataFrame):
        self.deputados = df_deputados.set_index("id", drop=False)
        self.gastos = preparar_gastos(df_gastos)
        self.ano_atual = int(self.gastos["ano"].max())
        self._gastos_ano = self.gastos[self.gastos["ano"] == self.ano_atual]
        self._total_dep_leg = self.gastos.groupby("idDeputado")["valor"].sum()
        self._total_dep_ano = self._gastos_ano.groupby("idDeputado")["valor"].sum()

    # --- Página inicial ---------------------------------------------------

    @property
    def total_legislatura(self) -> float:
        return float(self.gastos["valor"].sum())

    @property
    def total_ano(self) -> float:
        return float(self._gastos_ano["valor"].sum())

    @property
    def anos(self) -> list[int]:
        return sorted(int(a) for a in self.gastos["ano"].unique())

    def deputado(self, id_deputado: int) -> dict:
        d = self.deputados.loc[id_deputado]
        return {
            "id": int(d["id"]),
            "nome": d["nome"],
            "partido": d["siglaPartido"],
            "uf": d["siglaUf"],
            "foto": d["urlFoto"],
            "email": d["email"],
        }

    def _ranking(self, totais: pd.Series, titulo: str, n: int) -> Ranking:
        top = totais.sort_values(ascending=False).head(n)
        return Ranking(
            titulo,
            [{"deputado": self.deputado(i), "total": float(v)} for i, v in top.items()],
        )

    def ranking_ano(self, n: int = 10) -> Ranking:
        return self._ranking(self._total_dep_ano, str(self.ano_atual), n)

    def ranking_legislatura(self, n: int = 10) -> Ranking:
        inicio, fim = self.anos[0], self.anos[-1]
        return self._ranking(self._total_dep_leg, f"{inicio}–{fim}", n)

    def por_tipo(self, df: pd.DataFrame | None = None) -> list[tuple[str, float]]:
        df = self._gastos_ano if df is None else df
        s = df.groupby("tipo")["valor"].sum().sort_values(ascending=False)
        return [(t, float(v)) for t, v in s.items() if v > 0]

    def recentes(self, n: int = 12) -> list[dict]:
        df = self.gastos[self.gastos["valor"] > VALOR_MINIMO_RECENTES]
        df = df.dropna(subset=["data"]).sort_values("data", ascending=False).head(n)
        return [
            {**self._despesa(r), "deputado": self.deputado(r["idDeputado"])}
            for r in df.to_dict(orient="records")
        ]

    # --- Lista de deputados -------------------------------------------------

    def lista_deputados(self) -> list[dict]:
        itens = []
        for id_dep in self.deputados.index:
            itens.append({
                **self.deputado(id_dep),
                "total_ano": float(self._total_dep_ano.get(id_dep, 0)),
                "total_legislatura": float(self._total_dep_leg.get(id_dep, 0)),
            })
        return sorted(itens, key=lambda d: d["total_ano"], reverse=True)

    @property
    def partidos(self) -> list[str]:
        return sorted(self.deputados["siglaPartido"].dropna().unique())

    @property
    def ufs(self) -> list[str]:
        return sorted(self.deputados["siglaUf"].dropna().unique())

    # --- Página de cada deputado -------------------------------------------

    def paginas_deputados(self):
        """Gera PaginaDeputado para cada deputado (uma passada pelos dados)."""
        por_dep = dict(tuple(self.gastos.groupby("idDeputado")))
        for id_dep in self.deputados.index:
            df = por_dep.get(id_dep, self.gastos.iloc[0:0])
            df_ano = df[df["ano"] == self.ano_atual]
            mensal = df_ano.groupby("mes")["valor"].sum()
            anual = df.groupby("ano")["valor"].sum()
            df_ano = df_ano.sort_values(["mes", "data"], ascending=False)
            yield PaginaDeputado(
                deputado=self.deputado(id_dep),
                total_legislatura=float(df["valor"].sum()),
                total_ano=float(df_ano["valor"].sum()),
                por_ano=[(a, float(anual.get(a, 0))) for a in self.anos],
                por_mes=[(m, float(mensal.get(m, 0))) for m in range(1, 13)],
                por_tipo=self.por_tipo(df_ano),
                despesas=[self._despesa(r) for r in df_ano.to_dict(orient="records")],
            )

    @staticmethod
    def _despesa(r: dict) -> dict:
        data = r["data"]
        return {
            "data": None if pd.isna(data) else data.date(),
            "mes": int(r["mes"]),
            "ano": int(r["ano"]),
            "tipo": r["tipo"],
            "valor": float(r["valor"]),
            "fornecedor": r["fornecedor"],
            "url": r["url"],
        }
