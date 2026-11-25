from dataclasses import dataclass
from pathlib import Path

import fitz


class PdfValidationError(ValueError):
    pass


@dataclass(frozen=True)
class PdfPage:
    number: int
    text: str


def extract_pages(path: Path) -> tuple[int, list[PdfPage]]:
    try:
        with fitz.open(path) as pdf:
            if not pdf.is_pdf:
                raise PdfValidationError("The file is not a PDF.")
            if pdf.needs_pass:
                raise PdfValidationError("Encrypted PDFs are not supported.")
            if pdf.page_count == 0:
                raise PdfValidationError("The PDF has no pages.")
            pages = [PdfPage(index + 1, page.get_text().strip()) for index, page in enumerate(pdf)]
            if not any(page.text for page in pages):
                raise PdfValidationError("No selectable text was found. Image-only PDFs require OCR, which is not supported yet.")
            return len(pages), pages
    except (fitz.FileDataError, fitz.EmptyFileError) as exc:
        raise PdfValidationError("The PDF is corrupted or unreadable.") from exc
