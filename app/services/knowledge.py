"""참고 자료 검색(RAG): customize/knowledge/*.md 를 '## 제목' 단위로 쪼개 임베딩하고 코사인 유사도로 검색."""
import hashlib
import json
import math
from pathlib import Path

from ..hcx import HCXClient


def split_sections(path: Path) -> list[dict]:
    """'## 제목' 단위로 자르기. 첫 '##' 앞의 글은 파일 이름을 제목으로 사용."""
    chunks, title, lines = [], path.stem, []

    def flush():
        body = "\n".join(lines).strip()
        if body:
            chunks.append({"id": f"{path.stem}#{len(chunks)}", "source": path.name,
                           "title": title, "text": f"{title}\n{body}"})

    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.startswith("## "):
            flush()
            title, lines = line[3:].strip(), []
        elif not line.startswith("# "):  # 문서 제목(#)은 건너뜀
            lines.append(line)
    flush()
    return chunks


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / norm if norm else 0.0


class KnowledgeBase:
    def __init__(self, hcx: HCXClient, root: Path, data_dir: Path):
        self.hcx = hcx
        self.root = Path(root)
        self.data_dir = Path(data_dir)

    def chunks(self) -> list[dict]:
        # '_'로 시작하는 파일은 형식 예시라 제외
        files = sorted(p for p in self.root.glob("*.md") if not p.name.startswith("_"))
        return [chunk for path in files for chunk in split_sections(path)]

    def _index_path(self) -> Path:
        # MOCK 벡터와 실제 벡터는 섞이면 안 되므로 파일 분리
        return self.data_dir / f"knowledge_index_{'mock' if self.hcx.settings.mock else 'live'}.json"

    async def _vectors(self, chunks: list[dict]) -> dict[str, list[float]]:
        """조각별 벡터. 이미 임베딩한 글은 JSON 캐시에서 꺼냄 (내용이 바뀐 조각만 다시 임베딩)."""
        path = self._index_path()
        index = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        changed = False
        for chunk in chunks:
            key = hashlib.sha256(chunk["text"].encode()).hexdigest()
            chunk["key"] = key
            if key not in index:
                index[key] = (await self.hcx.embed("knowledge_index", chunk["text"])).data
                changed = True
        if changed:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(index), encoding="utf-8")
        return index

    async def search(self, query: str, k: int = 3) -> list[dict]:
        chunks = self.chunks()
        if not chunks or not query.strip():
            return []  # 자료가 없으면 임베딩 호출도 안 함
        index = await self._vectors(chunks)
        query_vec = (await self.hcx.embed("knowledge_query", query)).data
        for chunk in chunks:
            chunk["score"] = round(cosine(query_vec, index[chunk.pop("key")]), 4)
        return sorted(chunks, key=lambda c: c["score"], reverse=True)[:k]


def format_references(hits: list[dict]) -> str:
    return "\n\n".join(f"[{h['title']}]\n{h['text'].split(chr(10), 1)[-1]}" for h in hits)
