"""Knowledge base: Markdown files with front matter → section chunks with metadata → FAISS index.

Every `##` section of a document becomes one chunk, because a section answers one question and can be
cited as «документ / раздел». Long sections are split further with an overlap.
Documents in config.ALWAYS_ON go into every request whole; config.NOT_INDEXED stay out of search.
"""

from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from echo import config

META_KEYS = ("doc_id", "title", "topic", "type")
MAX_CHUNK_CHARS = 1500
_splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=150)


def parse_doc(text: str) -> tuple[dict, str]:
    lines = text.lstrip("﻿").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("документ должен начинаться с front matter (---)")
    end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    meta = {}
    for line in lines[1:end]:
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip().strip("'\"")  # doc_id is quoted so YAML keeps "05" a string
    missing = [k for k in META_KEYS if k not in meta]
    if missing:
        raise ValueError(f"в front matter нет ключей: {', '.join(missing)}")
    return meta, "\n".join(lines[end + 1:])


def sections(body: str) -> list[tuple[str, str]]:
    out, heading, buf = [], None, []
    for line in body.splitlines():
        if line.startswith("## "):
            if heading is not None:
                out.append((heading, "\n".join(buf).strip()))
            heading, buf = line[3:].strip(), []
        elif heading is not None:  # text before the first «##» is only the «#» title and the purpose line
            buf.append(line)
    if heading is not None:
        out.append((heading, "\n".join(buf).strip()))
    return [(h, t) for h, t in out if t]


def split_doc(meta: dict, body: str) -> list[Document]:
    chunks = []
    for heading, text in sections(body):
        parts = [text] if len(text) <= MAX_CHUNK_CHARS else _splitter.split_text(text)
        for part in parts:
            chunks.append(Document(
                page_content=f"{meta['title']}\n## {heading}\n{part}",
                metadata={**meta, "section": heading, "source": f"{meta['title']} / {heading}"}))
    return chunks


def doc_paths(kb_dir: Path = config.KB_DIR) -> list[Path]:
    return sorted(kb_dir.glob("[0-9][0-9]_*.md"))


def load_docs(kb_dir: Path = config.KB_DIR) -> list[tuple[dict, str]]:
    return [({**m, "path": p.name}, b) for p in doc_paths(kb_dir) for m, b in [parse_doc(p.read_text(encoding="utf-8"))]]


def get_doc(doc_id: str, kb_dir: Path = config.KB_DIR) -> tuple[dict, str] | None:
    return next(((m, b) for m, b in load_docs(kb_dir) if m["doc_id"] == doc_id), None)


def load_chunks(kb_dir: Path = config.KB_DIR) -> list[Document]:
    return [c for m, b in load_docs(kb_dir) if m["doc_id"] not in config.ALWAYS_ON + config.NOT_INDEXED
            for c in split_doc(m, b)]


def always_on_docs(kb_dir: Path = config.KB_DIR) -> list[Document]:
    """Whole documents that go into every request; cited like any fragment."""
    out = []
    for m, b in load_docs(kb_dir):
        if m["doc_id"] in config.ALWAYS_ON:
            out.append(Document(page_content=f"{m['title']}\n{b.strip()}",
                                metadata={**m, "section": "весь документ", "source": m["title"]}))
    return out


def embeddings() -> OpenAIEmbeddings:
    # OpenRouter takes raw text; token arrays (the default) are an OpenAI-only shortcut
    return OpenAIEmbeddings(model=config.EMBED_MODEL, base_url=config.BASE_URL, api_key=config.api_key(),
                            check_embedding_ctx_length=False)


def build_index(chunks: list[Document]) -> FAISS:
    return FAISS.from_documents(chunks, embeddings())


def load_index(index_dir: Path = config.INDEX_DIR) -> FAISS:
    # the index is built by our own ingest.py, so unpickling it is safe
    return FAISS.load_local(str(index_dir), embeddings(), allow_dangerous_deserialization=True)


def search(index: FAISS, query: str, k: int = config.TOP_K, doc_type: str | None = None,
           exclude_type: str | None = None) -> list[tuple[Document, float]]:
    def flt(m: dict) -> bool:
        return (doc_type is None or m["type"] == doc_type) and (exclude_type is None or m["type"] != exclude_type)
    # the index is small (about a hundred chunks), so filter over all of it instead of a fetch_k sample
    return index.similarity_search_with_score(query, k=k, filter=flt, fetch_k=index.index.ntotal)
