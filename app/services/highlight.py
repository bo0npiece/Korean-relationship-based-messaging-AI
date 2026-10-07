"""문제 구간(quote)을 원문에서 찾아 start/end 오프셋을 붙임 (프론트 하이라이트용)."""
import re

STRIP_CHARS = " \t\n\"'“”‘’「」『』"


def _candidates(text: str, quote: str):
    # 1) 그대로 2) 앞뒤 따옴표·공백 제거 3) 공백 차이 무시
    yield from ((m.start(), m.end()) for m in re.finditer(re.escape(quote), text))
    stripped = quote.strip(STRIP_CHARS)
    if stripped and stripped != quote:
        yield from ((m.start(), m.end()) for m in re.finditer(re.escape(stripped), text))
    words = stripped.split()
    if len(words) > 1:
        loose = r"\s+".join(re.escape(w) for w in words)
        yield from ((m.start(), m.end()) for m in re.finditer(loose, text))


def locate_spans(text: str, issues: list[dict]) -> list[dict]:
    """issues 각각에 start/end 추가. 못 찾으면 None."""
    used = set()
    for issue in issues:
        issue["start"] = issue["end"] = None
        quote = issue.get("quote") or ""
        if not quote.strip():
            continue
        for start, end in _candidates(text, quote):
            if start not in used:  # 같은 문장이 여러 번 나오면 다음 위치 사용
                used.add(start)
                issue["start"], issue["end"] = start, end
                break
    return issues


def first_sentence(text: str) -> str:
    match = re.match(r"\s*(.+?[.!?。]|.+)", text, flags=re.S)
    return match.group(1).strip() if match else text
