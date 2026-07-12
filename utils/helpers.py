import re


def punct_mapping(text):
    punct_map = {
        "，": ",",
        "。": ".",
        "；": ";",
        "？": "?",
        "！": "!",
        "（": "(",
        "）": ")",
        "【": "{",
        "】": "}",
    }

    char_map = {ord(k): v for k, v in punct_map.items() if len(k) == 1 and len(v) == 1}
    text = text.translate(char_map)
    text = re.sub(r'[\r\n]+', '', text)

    return text
