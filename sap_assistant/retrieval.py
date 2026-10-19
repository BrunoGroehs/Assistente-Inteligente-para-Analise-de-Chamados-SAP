from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re
import unicodedata

from sqlalchemy import select
from sqlalchemy.orm import Session

from .contracts import Evidence
from .database import Chunk

ROOT = Path(__file__).resolve().parents[1]
STOPWORDS = {"a", "o", "as", "os", "de", "do", "da", "em", "e", "que", "para", "no", "na", "um", "uma", "com"}


def tokens(text):
    normalized = unicodedata.normalize("NFKD", text.lower()).encode("ascii", "ignore").decode()
    return [x for x in re.findall(r"[a-z0-9_]+", normalized) if len(x) > 1 and x not in STOPWORDS]


def synchronize_knowledge(store, directory=None):
    directory = directory or ROOT / "conhecimento"
    catalog = json.loads((directory / "catalogo.json").read_text(encoding="utf-8"))
    with store.transaction() as db:
        existing = {row.id: row for row in db.scalars(select(Chunk))}
        ids = []
        for entry in catalog:
            path = (directory / entry["file"]).resolve()
            if path.parent != directory.resolve() or path.suffix != ".md":
                raise ValueError("Caminho de conhecimento inválido.")
            content = path.read_text(encoding="utf-8")
            content_hash = hashlib.sha256((content + json.dumps(entry, sort_keys=True)).encode()).hexdigest()
            row = existing.get(entry["id"])
            if row is None:
                row = Chunk(id=entry["id"], title=entry["title"], content=content,
                            attributes=entry, content_hash=content_hash)
                db.add(row)
            elif row.content_hash != content_hash:
                row.title, row.content, row.attributes = entry["title"], content, entry
                row.content_hash, row.embedding, row.embedding_model = content_hash, None, None
            ids.append(entry["id"])
        for key, row in existing.items():
            if key not in ids:
                db.delete(row)
    return len(catalog)


def cosine(a, b):
    if len(a) != len(b):
        raise ValueError("Dimensões de embeddings incompatíveis.")
    denominator = math.sqrt(sum(x*x for x in a) * sum(x*x for x in b))
    return sum(x*y for x, y in zip(a, b)) / denominator if denominator else 0


class Retriever:
    def __init__(self, store, provider):
        self.store, self.provider = store, provider

    def ensure_embeddings(self):
        with Session(self.store.engine) as db:
            rows = db.scalars(select(Chunk).order_by(Chunk.id)).all()
            missing = [(r.id, r.content_hash, r.title + "\n" + r.content) for r in rows
                       if r.embedding is None or r.embedding_model != self.provider.embedding_model]
        if missing:
            vectors = self.provider.embed([x[2] for x in missing])
            with self.store.transaction() as db:
                for (key, content_hash, _), vector in zip(missing, vectors, strict=True):
                    row = db.get(Chunk, key)
                    if row is not None and row.content_hash == content_hash:
                        row.embedding, row.embedding_model = vector, self.provider.embedding_model
        return len(missing)

    def search(self, query, limit=4):
        created = self.ensure_embeddings()
        with Session(self.store.engine) as db:
            rows = db.scalars(select(Chunk).where(Chunk.embedding_model == self.provider.embedding_model)).all()
        if not rows:
            return [], {"method": "hibrida_rrf", "embedding_model": self.provider.embedding_model,
                        "new_document_embeddings": created, "selected_ids": []}
        vector = self.provider.embed([query])[0]
        with Session(self.store.engine) as db:
            if any(len(r.embedding) != len(vector) for r in rows):
                raise ValueError("Dimensão do modelo mudou. Reindexe o conhecimento.")
            terms = Counter(tokens(query))
            lexical = sorted(rows, key=lambda r: (-sum(min(n, Counter(tokens(r.title+' '+r.content))[t])
                                                     for t, n in terms.items()), r.id))
            lexical = [r for r in lexical if set(terms) & set(tokens(r.title+' '+r.content))]
            if self.store.engine.dialect.name == "postgresql":
                semantic = db.scalars(select(Chunk).where(Chunk.embedding_model == self.provider.embedding_model)
                                      .order_by(Chunk.embedding.cosine_distance(vector)).limit(limit*2)).all()
            else:
                semantic = sorted(rows, key=lambda r: (-cosine(vector, r.embedding), r.id))
            scores = Counter()
            for ranking in (lexical, semantic):
                for rank, row in enumerate(ranking, 1):
                    scores[row.id] += 1 / (60 + rank)
            ordered = sorted([r for r in rows if r.attributes["kind"] == "sintese_de_fonte_oficial"],
                             key=lambda r: (-scores[r.id], r.id))[:limit]
            policies = sorted([r for r in rows if r.attributes["kind"] == "politica_da_simulacao"], key=lambda r: r.id)
            ordered.extend(policies)
            evidence = [Evidence(id=r.id, title=r.title, content=r.content, kind=r.attributes["kind"],
                                 source_url=r.attributes.get("source_url"), version=r.attributes["version"])
                        for r in ordered]
            return evidence, {"method": "hibrida_rrf", "embedding_model": self.provider.embedding_model,
                              "new_document_embeddings": created, "selected_ids": [x.id for x in evidence]}
