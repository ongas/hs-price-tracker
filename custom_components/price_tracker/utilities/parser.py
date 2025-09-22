from bs4 import BeautifulSoup


def parse_bool(value: any) -> bool:
    if isinstance(value, bool):
        return value
    elif isinstance(value, str):
        return value.lower() in [
            "true",
            "yes",
            "y",
            "はい",
            "예",
            "ok",
            "1",
            "on",
            "enable",
            "enabled",
            "active",
            "activated",
            "open",
            "opened",
            "unlock",
            "unlocked",
        ]
    return bool(value)


def parse_float(value: any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, float):
        return value
    if isinstance(value, int):
        return float(value)
    s = str(value)
    # Remove all currency symbols and whitespace
    s = (
        s.replace(",", "")
        .replace(" ", "")
        .replace("円", "")
        .replace("¥", "")
        .replace("￦", "")
        .replace("₩", "")
        .replace("$", "")
        .replace("\t", "")
        .replace("원", "")
        .replace("USD", "")
        .replace("AUD", "")
        .replace("EUR", "")
        .replace("NZD", "")
        .replace("GBP", "")
    )
    # Remove any trailing/leading non-numeric chars
    import re
    s = re.sub(r"[^0-9.\-]+", "", s)
    try:
        return float(s)
    except (ValueError, TypeError):
        return 0.0


def parse_number(value: any) -> int:
    if value is None:
        return 0

    try:
        return int(
            str(value)
            .replace(",", "")
            .replace(" ", "")
            .replace("円", "")
            .replace("¥", "")
            .replace("￦", "")
            .replace("\t", "")
            .replace("원", "")
            .replace("free", "0")
        )
    except (ValueError, TypeError):
        return 0


def parse_html(text: str):
    return BeautifulSoup(text, "html.parser")


def parse_engine_id(item: any) -> str:
    if isinstance(item, dict):
        return "_".join(item.values())

    return str(item)
