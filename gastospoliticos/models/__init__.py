"""Define dataclasses para os dados da aplicação."""

from dataclasses import dataclass, field, replace
from datetime import date, datetime
from pathlib import Path
from os import PathLike
import typing as t

import pandas as pd


def _parse_data(valor: t.Any) -> date | None:
    """Converte "AAAA-MM-DD..." em date; retorna None se ausente (a API às vezes omite)."""
    if not isinstance(valor, str) or not valor:
        return None
    return datetime.strptime(valor[:10], "%Y-%m-%d").date()


def _valor_ou_zero(valor: t.Any) -> float:
    """Retorna o valor numérico, ou 0 se ausente/NaN."""
    return 0.0 if valor is None or pd.isna(valor) else float(valor)


@dataclass(frozen=True)
class Gasto:
    id_deputado: int
    cod_documento: int
    num_documento: str
    tipo: str
    tipo_documento: str
    mes: int
    ano: int
    data: date | None
    valor: float
    valor_liquido: float
    uri_documento: str | None
    nome_fornecedor: str
    id_fornecedor: str

    @staticmethod
    def de_json(json):
        return Gasto(
            id_deputado=json["idDeputado"],
            cod_documento=json["codDocumento"],
            num_documento=json["numDocumento"],
            tipo_documento=json["tipoDocumento"],
            tipo=json["tipoDespesa"],
            ano=json["ano"],
            mes=json["mes"],
            data=_parse_data(json.get("dataDocumento")),
            valor=json["valorDocumento"],
            # Calculado em vez de usar json["valorLiquido"]: desde 2026 a API
            # retorna esse campo com o sinal invertido na maioria das despesas.
            valor_liquido=round(json["valorDocumento"] - _valor_ou_zero(json.get("valorGlosa")), 2),
            uri_documento=json["urlDocumento"],
            nome_fornecedor=json["nomeFornecedor"],
            id_fornecedor=json["cnpjCpfFornecedor"],
        )


@dataclass(frozen=True)
class Deputado:
    id: int
    nome: str
    email: str
    sigla_partido: str
    uf: str
    legislatura: int
    uri_foto: str
    gastos: tuple[Gasto, ...] = field(default_factory=tuple)

    @property
    def total_gasto(self) -> float:
        """Retorna o total dos gastos assoaciados à esta instância de deputado."""
        return sum(g.valor_liquido for g in self.gastos)

    @staticmethod
    def de_json(json):
        return Deputado(
            id=json["id"],
            nome=json["nome"],
            email=json["email"],
            sigla_partido=json["siglaPartido"],
            uf=json["siglaUf"],
            legislatura=json["idLegislatura"],
            uri_foto=json["urlFoto"],
        )

    def com_gastos(self, gastos: tuple[Gasto, ...] = ()):
        """Retorna uma cópia do deputado com seus gastos adicionados."""
        return replace(self, gastos=tuple(gastos))
    

class FonteDados(t.Protocol):
    """Interface para fonte de dados."""

    def obter_deputados(self) -> pd.DataFrame: ...

    def obter_gastos(self) -> pd.DataFrame: ...


class FonteDadosArquivo(FonteDados):
    """Implementação que lê arquivos e escrever arquivos CSV."""

    def __init__(self, dir: str | PathLike):
        self.dir = dir

    @property
    def caminho_dep(self) -> Path:
        return Path(self.dir) / "deputados.csv"

    @property
    def caminho_gas(self) -> Path:
        return Path(self.dir) / "gastos.csv.gz"  # comprimido: o CSV passa do limite de 100 MB do GitHub

    def obter_deputados(self) -> pd.DataFrame:
        return pd.read_csv(self.caminho_dep)

    def obter_gastos(self) -> pd.DataFrame:
        return pd.read_csv(self.caminho_gas)

    def exportar_deputados(self, df_deputados: pd.DataFrame) -> None:
        df_deputados.to_csv(self.caminho_dep, index=False)

    def exportar_gastos(self, df_gastos: pd.DataFrame) -> None:
        df_gastos.to_csv(self.caminho_gas, index=False)


class CamaraRepositorio:
    """Repositório agnóstico à fonte de dados."""

    def __init__(self, fonte: FonteDados):
        self.fonte = fonte
        self._df_deputados = fonte.obter_deputados()
        self._df_gastos = fonte.obter_gastos()

    def deputado_por_id(self, id_deputado: int) -> Deputado | None:
        """Retorna um deputado específico ou None."""
        matching = self._df_deputados[self._df_deputados["id"] == id_deputado]
        if matching.empty:
            return None
        dep_dict = matching.iloc[0].to_dict()
        return Deputado.de_json(dep_dict).com_gastos(self.gastos(id_deputado))

    def deputados(self) -> tuple[Deputado]:
        """Retorna tupla de instâncias Deputado com gastos associados."""
        return tuple(
            Deputado.de_json(dep_dict).com_gastos(self.gastos(dep_dict["id"]))
            for _, dep_dict in self._df_deputados.iterrows()
        )

    def gastos(self, id_deputado: int | None = None) -> tuple[Gasto, ...]:
        """Retorna tupla de instâncias Gasto, opcionalmente filtradas."""
        df = self._df_gastos
        if id_deputado is not None:
            df = df[df["idDeputado"] == id_deputado]

        return tuple(
            Gasto.de_json(gasto_dict) for gasto_dict in df.to_dict(orient="records")
        )
