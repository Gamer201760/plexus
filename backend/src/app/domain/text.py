def normalize_name(text: str) -> str:
    return " ".join(text.replace("ё", "е").replace("Ё", "Е").casefold().split())
