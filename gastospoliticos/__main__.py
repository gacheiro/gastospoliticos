from itertools import chain
from pathlib import Path

import pandas as pd

from gastospoliticos.apidadosabertos import CamaraDadosAbertos
from gastospoliticos.models import CamaraRepositorio, FonteDadosArquivo
from gastospoliticos.site.utils import formatar_moeda

from gastospoliticos.site import default_renderer

if __name__ == "__main__":
    # dadosabertos = DadosAbertos()
    # deputados = dadosabertos.buscar_deputados()
    # for d in deputados:
    #     reembolsos = list(dadosabertos.buscar_despesas(d.id))
    #     print(
    #         f"Deputado(a) {d.nome} pediu {len(reembolsos)} reembolso(s), "
    #         f"totalizando R${sum(r.valor for r in reembolsos):,.2f}"
    #     )

    # deputados: pd.DataFrame = extrair_deputados()
    # novo = deputados[deputados["siglaPartido"] == "NOVO"]
    # despesas: pd.DataFrame = extrair_despesas(novo["id"])
    # breakpoint()

    # with CamaraDadosAbertos() as camara:
    #     dados_deputados = tuple(camara.buscar_deputados())
    #     dados_gastos = tuple(
    #         chain.from_iterable(
    #             camara.buscar_despesas(dep_dict["id"]) for dep_dict in dados_deputados
    #         )
    #     )

    fonte_dados = FonteDadosArquivo(Path(__file__).parent / "../publish/dataframes")
    # fonte_dados.exportar_deputados(pd.DataFrame(dados_deputados))
    # fonte_dados.exportar_gastos(pd.DataFrame(dados_gastos))

    repo = CamaraRepositorio(fonte_dados)
    deputados = repo.deputados()
    deputados = sorted(deputados, key=lambda d: d.total_gasto, reverse=True)
    gastos = repo.gastos()
    gastos = sorted(gastos, key=lambda g: g.valor_liquido, reverse=True)

    html_gerado = default_renderer.render_template(
        "index_neo.html",
        context={
            "titulo": "Gastos dos Políticos",
            "deputados": deputados[:9],
            "gastos": gastos[:10],
        },
    )

    default_renderer.save_html(html_gerado, "index.html")
