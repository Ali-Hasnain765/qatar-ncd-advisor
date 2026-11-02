"""Minimal RAG pipeline: extract a PDF's text per page, embed each paragraph with
Gemini's embedding model, store the vectors in an in-memory Chroma collection, and
retrieve the top-k most relevant paragraphs for a query at generation time.

Everything here is ephemeral (per Streamlit session, in-memory only) — no guideline
text or embeddings are written to disk, consistent with the project's "nothing is
persisted" privacy stance.
"""
import io

import chromadb
from google.genai import types
from pypdf import PdfReader

EMBED_MODEL = "gemini-embedding-001"
MIN_CHUNK_CHARS = 40


def extract_pdf_chunks(file_bytes: bytes, source_id: str):
    """Returns a list of {"id", "page", "text"} paragraph chunks from a PDF, in order."""
    reader = PdfReader(io.BytesIO(file_bytes))
    chunks = []
    for page_num, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if not text:
            continue
        paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) >= MIN_CHUNK_CHARS]
        if not paragraphs:
            paragraphs = [text]
        for i, para in enumerate(paragraphs):
            chunks.append({"id": f"{source_id}-p{page_num}-{i}", "page": page_num, "text": para})
    return chunks


def _embed(genai_client, texts, task_type):
    result = genai_client.models.embed_content(
        model=EMBED_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(task_type=task_type),
    )
    return [e.values for e in result.embeddings]


def build_index(genai_client, chunks, collection_name):
    """Embeds all chunks and loads them into a fresh, in-memory Chroma collection."""
    chroma_client = chromadb.EphemeralClient()
    collection = chroma_client.get_or_create_collection(collection_name)
    embeddings = _embed(genai_client, [c["text"] for c in chunks], task_type="RETRIEVAL_DOCUMENT")
    collection.add(
        ids=[c["id"] for c in chunks],
        embeddings=embeddings,
        documents=[c["text"] for c in chunks],
        metadatas=[{"page": c["page"]} for c in chunks],
    )
    return collection


def retrieve(genai_client, collection, query, k=4):
    """Returns the top-k most relevant {"id", "page", "text"} chunks for a query."""
    query_embedding = _embed(genai_client, [query], task_type="RETRIEVAL_QUERY")[0]
    results = collection.query(query_embeddings=[query_embedding], n_results=k)
    if not results["ids"][0]:
        return []
    return [
        {"id": id_, "page": meta["page"], "text": doc}
        for id_, meta, doc in zip(results["ids"][0], results["metadatas"][0], results["documents"][0])
    ]
