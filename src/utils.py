from textwrap import fill


def printf(text: str) -> str:
    print(fill(text, 79))
    return text
