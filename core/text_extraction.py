import os
from typing import Tuple

def from_pdf(path: str) -> str:
    try:
        import fitz
        doc = fitz.open(path)
        text = ""
        for p in doc:
            text += p.get_text()
        doc.close()
        return text
    except Exception:
        try:
            import pdfplumber
            text = ""
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
            return text
        except Exception as e:
            raise RuntimeError(f"PDF parsing failed: {e}")

def from_docx(path: str) -> str:
    try:
        import docx
        doc = docx.Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        raise RuntimeError(f"DOCX parsing failed: {e}")

def from_txt(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def extract_text(path: str) -> Tuple[str, str]:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return from_pdf(path), "pdf"
    if ext in [".docx", ".doc"]:
        return from_docx(path), "docx"
    if ext in [".txt", ".md"]:
        return from_txt(path), "txt"
    raise RuntimeError(f"Unsupported file type: {ext}")