from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from app.models import Chunk

# a lightweight, local stand-in for a hosted embedding model.
# TF-IDF needs no API key and no GPU, so ingestion and retrieval both run instantly and offline.
# swapping this for a real embedding model later only means changing this one file.


@dataclass
class ScoredChunk:
    chunk_id: str
    title: str
    content: str
    score: float


class ChunkIndex:
    def __init__(self) -> None:
        self._vectorizer: TfidfVectorizer | None = None
        self._matrix = None
        self._chunks: list[Chunk] = []

    def build(self, db: Session) -> None:
        self._chunks = db.query(Chunk).all()
        if not self._chunks:
            self._vectorizer = None
            self._matrix = None
            return
        texts = [chunk.content for chunk in self._chunks]
        self._vectorizer = TfidfVectorizer(stop_words="english", max_features=4000)
        self._matrix = self._vectorizer.fit_transform(texts)

    def search(self, query: str, top_k: int = 5) -> list[ScoredChunk]:
        if self._vectorizer is None or self._matrix is None:
            return []
        query_vector = self._vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, self._matrix)[0]
        ranked = sorted(zip(self._chunks, similarities), key=lambda pair: pair[1], reverse=True)
        return [
            ScoredChunk(
                chunk_id=chunk.id,
                title=chunk.title,
                content=chunk.content,
                score=round(float(score), 3),
            )
            for chunk, score in ranked[:top_k]
            if score > 0
        ]


_index = ChunkIndex()


def get_chunk_index() -> ChunkIndex:
    return _index
