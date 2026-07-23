import os


def parse_file(file_path: str) -> str:
    ext = file_path.split(".")[-1].lower()

    if ext == "pdf":
        return _parse_pdf(file_path)
    elif ext == "txt":
        return _parse_text(file_path)
    elif ext in ("docx", "doc"):
        return _parse_docx(file_path)
    elif ext in ("xlsx", "xls"):
        return _parse_excel(file_path)
    elif ext == "md":
        return _parse_text(file_path)
    elif ext == "csv":
        return _parse_text(file_path)
    else:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()


def _parse_pdf(file_path: str) -> str:
    try:
        from pypdf import PdfReader

        reader = PdfReader(file_path)
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        return "\n\n".join(text_parts)
    except ImportError:
        raise ImportError("Установите pypdf: pip install pypdf")


def _parse_text(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def _parse_docx(file_path: str) -> str:
    try:
        from docx import Document

        doc = Document(file_path)
        return "\n\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    except ImportError:
        raise ImportError("Установите python-docx: pip install python-docx")


def _parse_excel(file_path: str) -> str:
    try:
        import pandas as pd

        df = pd.read_excel(file_path)
        return df.to_string()
    except ImportError:
        raise ImportError("Установите openpyxl: pip install openpyxl pandas")
