import calendar
import locale
import unicodedata

locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")


def formatar_moeda(valor: float) -> str:
    """Formata um valor como BRL."""
    return locale.currency(valor, symbol=True, grouping=True)


def moeda_curta(valor: float) -> str:
    """Formato compacto: 2_349_389 -> 'R$ 2,3 mi'; 52_300 -> 'R$ 52 mil'."""
    for limite, sufixo in ((1e9, "bi"), (1e6, "mi"), (1e3, "mil")):
        if abs(valor) >= limite:
            numero = valor / limite
            casas = 1 if abs(numero) < 100 else 0
            texto = locale.format_string(f"%.{casas}f", numero, grouping=True)
            return f"R$ {texto} {sufixo}"
    return formatar_moeda(valor)


def nome_mes(mes: int) -> str:
    """1 -> 'janeiro'."""
    try:
        return calendar.month_name[int(mes)]
    except (ValueError, IndexError, TypeError):
        return ""


def mes_abrev(mes: int) -> str:
    """1 -> 'jan'."""
    try:
        return calendar.month_abbr[int(mes)].rstrip(".")
    except (ValueError, IndexError, TypeError):
        return ""


def sem_acento(texto: str) -> str:
    """Normaliza para busca: 'Acácio Favacho' -> 'acacio favacho'."""
    decomposto = unicodedata.normalize("NFD", str(texto))
    return "".join(c for c in decomposto if not unicodedata.combining(c)).lower()


def porcentagem(valor: float, maximo: float) -> str:
    """Largura de barra em %, com 2 casas, para usar em CSS."""
    if not maximo:
        return "0"
    return f"{max(0.0, min(100.0, valor / maximo * 100)):.2f}"
