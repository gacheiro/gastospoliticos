"""Gera o site estático em publish/ a partir dos CSVs exportados da API."""

import logging
import time
from pathlib import Path

from gastospoliticos.apidadosabertos import LEGISLATURA_ATUAL
from gastospoliticos.models import FonteDadosArquivo
from gastospoliticos.site import default_renderer as site
from gastospoliticos.site.dados import VALOR_MINIMO_RECENTES, Painel

logger = logging.getLogger("gastospoliticos")


def gerar_site() -> None:
    inicio = time.perf_counter()
    fonte = FonteDadosArquivo(Path(__file__).parent / "../publish/dataframes")
    painel = Painel(fonte.obter_deputados(), fonte.obter_gastos())
    deputados = painel.lista_deputados()

    comum = {
        "ano": painel.ano_atual,
        "anos": painel.anos,
        "legislatura": LEGISLATURA_ATUAL,
        "n_deputados": len(deputados),
        "ufs": painel.ufs,
        "partidos": painel.partidos,
    }

    site.copy_static()

    site.render("index.html", "index.html", {
        **comum,
        "pagina": "inicio",
        "total_ano": painel.total_ano,
        "total_legislatura": painel.total_legislatura,
        "ranking_ano": painel.ranking_ano(),
        "ranking_legislatura": painel.ranking_legislatura(),
        "recentes": painel.recentes(),
        "valor_minimo_recentes": VALOR_MINIMO_RECENTES,
        "por_tipo": painel.por_tipo(),
        "deputados": deputados,
    })
    site.render("deputados.html", "deputados.html", {
        **comum, "pagina": "deputados", "deputados": deputados,
    })
    site.render("sobre.html", "sobre.html", {**comum, "pagina": "sobre"})

    posicoes = {d["id"]: i for i, d in enumerate(deputados, start=1)}
    for pagina in painel.paginas_deputados():
        id_dep = pagina.deputado["id"]
        site.render("deputado.html", f"deputado/{id_dep}.html", {
            **comum, "pagina": "deputados", "p": pagina, "posicao": posicoes[id_dep],
        })

    logger.info(
        "Site gerado: %d páginas de deputados em %.1fs.",
        len(deputados), time.perf_counter() - inicio,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    gerar_site()
