import locale

locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")


def formatar_moeda(valor: int | float) -> str:
    """Formata um valor como BRL."""
    return locale.currency(valor, symbol=True, grouping=True)
