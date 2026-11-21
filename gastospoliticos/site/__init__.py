from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from .utils import formatar_moeda

HERE = Path(__file__).parent

DEFAULT_TEMPLATE_DIR = HERE / "templates"
DEFAULT_OUTPUT_DIR = HERE / "../../publish"


class SiteRenderer:
    """Renderiza templates e dados em páginas HTML."""

    def __init__(self, jinja_env, output_dir):
        self.jinja_env = jinja_env
        self.output_dir = output_dir

    def render_template(self, template_path, context) -> str:
        template = self.jinja_env.get_template(template_path)
        return template.render(context)

    def save_html(self, content, filename) -> None:
        output_path = Path(self.output_dir) / filename
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)


env = Environment(loader=FileSystemLoader(DEFAULT_TEMPLATE_DIR))

# Adiciona filtros úteis para formatação e processamento
env.filters["formatar_moeda"] = formatar_moeda

default_renderer = SiteRenderer(env, DEFAULT_OUTPUT_DIR)
