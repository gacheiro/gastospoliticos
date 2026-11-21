import datetime
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .utils import (
    formatar_moeda,
    mes_abrev,
    moeda_curta,
    nome_mes,
    porcentagem,
    sem_acento,
)

HERE = Path(__file__).parent

DEFAULT_TEMPLATE_DIR = HERE / "templates"
DEFAULT_STATIC_DIR = HERE / "static"
DEFAULT_OUTPUT_DIR = (HERE / "../../publish").resolve()


class SiteRenderer:
    """Renderiza templates e dados em páginas HTML."""

    def __init__(self, jinja_env, output_dir, static_dir=DEFAULT_STATIC_DIR):
        self.jinja_env = jinja_env
        self.output_dir = Path(output_dir)
        self.static_dir = Path(static_dir)

    def render_template(self, template_path, context) -> str:
        template = self.jinja_env.get_template(template_path)
        return template.render(context)

    def save_html(self, content, filename) -> None:
        output_path = self.output_dir / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

    def render(self, template_path, filename, context) -> None:
        """Renderiza `template_path` e salva em `filename` (relativo ao output)."""
        # Prefixo para links relativos: "deputado/1.html" -> "../"
        raiz = "../" * filename.count("/")
        self.save_html(self.render_template(template_path, {**context, "raiz": raiz}), filename)

    def copy_static(self) -> None:
        shutil.copytree(self.static_dir, self.output_dir / "static", dirs_exist_ok=True)


env = Environment(
    loader=FileSystemLoader(DEFAULT_TEMPLATE_DIR),
    autoescape=select_autoescape(["html"]),
    trim_blocks=True,
    lstrip_blocks=True,
)

# Filtros para formatação
env.filters["formatar_moeda"] = formatar_moeda
env.filters["moeda"] = formatar_moeda
env.filters["moeda_curta"] = moeda_curta
env.filters["nome_mes"] = nome_mes
env.filters["mes_abrev"] = mes_abrev
env.filters["sem_acento"] = sem_acento
env.filters["porcentagem"] = porcentagem

env.globals["atualizado_em"] = datetime.date.today()

default_renderer = SiteRenderer(env, DEFAULT_OUTPUT_DIR)
