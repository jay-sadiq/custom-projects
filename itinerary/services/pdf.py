from io import BytesIO

from pypdf import PdfReader


def extract_text_from_pdf(uploaded_file) -> str:
    uploaded_file.seek(0)
    reader = PdfReader(BytesIO(uploaded_file.read()))
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            pages.append(text.strip())
    uploaded_file.seek(0)
    return "\n\n".join(pages)
