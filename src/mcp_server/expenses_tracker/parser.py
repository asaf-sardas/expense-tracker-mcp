from .config import DEFAULT_CURRENCY_SYMBOL


def to_agorot(shekels: float) -> int:
    return round(shekels * 100)


def to_shekels(agorot: int) -> float:
    return agorot / 100


def format_money(shekels: float, symbol: str = DEFAULT_CURRENCY_SYMBOL) -> str:
    """Amount for messages, e.g. '₪1,250.50' or '-₪5.00'."""
    sign = "-" if shekels < 0 else ""
    return f"{sign}{symbol}{abs(shekels):,.2f}"
