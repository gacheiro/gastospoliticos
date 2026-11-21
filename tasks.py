"""Tarefas do projeto (invoke).

O site é gerado diretamente com Jinja2 (ver ``gastospoliticos/site``) e
publicado no GitHub Pages a partir do diretório ``publish/``.
"""

import datetime
import functools
import http.server
import sys
import webbrowser
from pathlib import Path

from invoke import task

HERE = Path(__file__).parent

CONFIG = {
    # Diretório de saída do site
    "deploy_path": HERE / "publish",
    # Configuração do GitHub Pages
    "github_pages_branch": "gh-pages",
    "commit_message": f"'Publica site em {datetime.date.today().isoformat()}'",
    # Host e porta para `serve`
    "host": "localhost",
    "port": 8000,
}

OPEN_BROWSER_ON_SERVE = True


@task
def build(c):
    """Gera o site renderizando os templates Jinja2."""
    c.run(f"{sys.executable} -m gastospoliticos")


@task
def serve(c):
    """Serve o site em http://$HOST:$PORT/ (padrão: localhost:8000)."""
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler,
        directory=str(CONFIG["deploy_path"]),
    )

    class AddressReuseHTTPServer(http.server.ThreadingHTTPServer):
        allow_reuse_address = True

    server = AddressReuseHTTPServer((CONFIG["host"], CONFIG["port"]), handler)

    if OPEN_BROWSER_ON_SERVE:
        webbrowser.open("http://{host}:{port}".format(**CONFIG))

    sys.stderr.write("Servindo em {host}:{port} ...\n".format(**CONFIG))
    server.serve_forever()


@task
def reserve(c):
    """`build`, depois `serve`."""
    build(c)
    serve(c)


@task
def gh_pages(c):
    """Gera o site e publica no GitHub Pages."""
    build(c)
    c.run(
        "ghp-import -n -b {github_pages_branch} "
        "-m {commit_message} "
        "{deploy_path} -p".format(**CONFIG)
    )


@task
def exportar_dataframes(c):
    """Baixa deputados e despesas da API e salva em CSV."""
    from itertools import chain

    import pandas as pd

    from gastospoliticos.apidadosabertos import CamaraDadosAbertos
    from gastospoliticos.models import FonteDadosArquivo

    dataframes_dir = CONFIG["deploy_path"] / "dataframes"
    dataframes_dir.mkdir(parents=True, exist_ok=True)
    fonte_dados = FonteDadosArquivo(dataframes_dir)

    with CamaraDadosAbertos() as camara:
        dados_deputados = tuple(camara.buscar_deputados())
        dados_gastos = tuple(
            chain.from_iterable(
                camara.buscar_despesas(dep["id"]) for dep in dados_deputados
            )
        )

    fonte_dados.exportar_deputados(pd.DataFrame(dados_deputados))
    fonte_dados.exportar_gastos(pd.DataFrame(dados_gastos))
