def to_agorot(shekels: float) -> int:
    return round(shekels * 100)


def to_shekels(agorot: int) -> float:
    return agorot / 100
