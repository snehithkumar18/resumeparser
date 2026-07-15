import os
from pathlib import Path
from pypdf import PdfReader
from docx import Document

def read_pdf(file_path: Path | str) -> str:
    """Reads a PDF file and extracts text from all pages."""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")
    
    text = []
    reader = PdfReader(file_path)
    for idx, page in enumerate(reader.pages):
        page_text = page.extract_text()
        if page_text:
            text.append(page_text)
    return "\n".join(text)

def read_docx(file_path: Path | str) -> str:
    """Reads a Word document (.docx) and extracts text from paragraphs and tables."""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"DOCX file not found: {file_path}")
    
    doc = Document(file_path)
    text = []
    
    # Extract text from paragraphs
    for paragraph in doc.paragraphs:
        if paragraph.text:
            text.append(paragraph.text)
            
    # Extract text from tables
    for table in doc.tables:
        for row in table.rows:
            row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if row_text:
                text.append(" | ".join(row_text))
                
    return "\n".join(text)

def read_document(file_path: Path | str) -> str:
    """Reads a document (PDF, DOCX, TXT) and returns its text content."""
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()
    
    if suffix == ".pdf":
        return read_pdf(file_path)
    elif suffix == ".docx":
        return read_docx(file_path)
    elif suffix in (".txt", ".md"):
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported file format: {suffix}. Only PDF, DOCX, and TXT are supported.")
