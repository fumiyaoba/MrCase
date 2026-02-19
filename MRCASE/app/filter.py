# MRCASE/app/filter.py

from typing import Iterable, List
from MRCASE.models.slack_message import SlackMessage


def normalize(text: str) -> str:
    """比較用に正規化（空白除去＋trim）"""
    return text.replace(" ", "").strip()


def filter_by_first_line(
    messages: Iterable[SlackMessage],
    keyword: str,
) -> List[SlackMessage]:
    """
    メッセージの先頭行が keyword と一致するものを返す
    （keyword は env 側から渡す）
    """
    key = normalize(keyword)

    result: List[SlackMessage] = []
    for m in messages:
        if not m.text:
            continue

        first_line = m.text.splitlines()[0]
        if normalize(first_line) == key:
            result.append(m)

    return result
