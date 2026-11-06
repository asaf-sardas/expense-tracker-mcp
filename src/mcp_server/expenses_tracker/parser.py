from .config import settings


def to_agorot(shekels: float) -> int:
    return round(shekels * 100)


def to_shekels(agorot: int) -> float:
    return agorot / 100


def format_money(shekels: float) -> str:
    """Amount for messages, e.g. '₪1,250.50' or '-₪5.00'."""
    sign = "-" if shekels < 0 else ""
    return f"{sign}{settings.currency_symbol}{abs(shekels):,.2f}"
