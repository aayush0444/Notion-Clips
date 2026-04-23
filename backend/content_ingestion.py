from __future__ import annotations

from typing import Tuple

import fitz
from newspaper import Article


def extract_text_from_pdf(file_bytes: bytes) -> Tuple[str, str]:
    """
    Returns (title, full_text) from a PDF byte stream.
    - title: first non-empty line or "Untitled Document"
    - full_text: concatenated page text (max 50k chars)
    """
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        pages = []
        for page in doc:
            pages.append(page.get_text())
        full_text = "\n".join(pages).strip()

    lines = [line.strip() for line in full_text.split("\n") if line.strip()]
    title = lines[0][:100] if lines else "Untitled Document"

    if len(full_text) > 50000:
        full_text = full_text[:50000] + "\n\n[Content truncated — document too long]"

    return title, full_text


def extract_text_from_url(url: str) -> Tuple[str, str]:
    """
    Returns (title, full_text) from an article URL using newspaper3k.
    Raises ValueError if extraction fails or content is too thin.
    """
    article = Article(url)
    article.download()
    article.parse()

    text = (article.text or "").strip()
    if not text or len(text) < 100:
        raise ValueError(f"Could not extract readable content from {url}")

    title = (article.title or "Untitled Article").strip() or "Untitled Article"
    if len(text) > 30000:
        text = text[:30000] + "\n\n[Content truncated]"

    return title, text

