"""Extract plain text from uploaded study materials."""

from __future__ import annotations

import io


SUPPORTED_EXTENSIONS = (".pdf", ".docx", ".txt", ".md")


def _extract_pdf(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    parts: list[str] = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n\n".join(p for p in parts if p.strip())


def _extract_docx(data: bytes) -> str:
    from docx import Document

    doc = Document(io.BytesIO(data))
    paragraphs = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
    # Also pull cell text from any tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text and cell.text.strip():
                    paragraphs.append(cell.text)
    return "\n\n".join(paragraphs)


def _extract_text(data: bytes) -> str:
    return data.decode("utf-8", errors="ignore")


def extract_text(uploaded_file) -> tuple[str, str | None]:
    """Pull text out of a Streamlit UploadedFile. Returns (text, error_message)."""
    name = (uploaded_file.name or "").lower()
    data = uploaded_file.read()

    try:
        if name.endswith(".pdf"):
            return _extract_pdf(data), None
        if name.endswith(".docx"):
            return _extract_docx(data), None
        if name.endswith(".txt") or name.endswith(".md"):
            return _extract_text(data), None
    except Exception as exc:  # noqa: BLE001
        return "", f"Couldn't read this {name.rsplit('.', 1)[-1].upper()} file: {exc}"

    return "", (
        f"Unsupported file type: '{uploaded_file.name}'. "
        "Please upload a PDF, DOCX, TXT, or MD file."
    )
