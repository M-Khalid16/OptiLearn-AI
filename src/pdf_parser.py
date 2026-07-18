"""PDF lecture-note text extraction utilities for OptiLearn AI."""

from dataclasses import dataclass
from pathlib import PurePath
import re
from typing import Any

import fitz


MAX_PDF_SIZE_BYTES = 25 * 1024 * 1024
MAX_PDF_PAGES = 300
SPARSE_TEXT_CHARACTER_THRESHOLD = 40
LIKELY_SCANNED_SPARSE_PAGE_RATIO = 0.8

PDF_OPEN_ERRORS = tuple(
    error_type
    for error_name in (
        "FileDataError",
        "EmptyFileError",
        "FileNotFoundError",
        "PDFSyntaxError",
    )
    if isinstance((error_type := getattr(fitz, error_name, None)), type)
)


@dataclass(frozen=True)
class PDFPage:
    """Normalized text and statistics for one PDF page."""

    page_number: int
    text: str
    character_count: int
    word_count: int
    is_text_sparse: bool


@dataclass(frozen=True)
class PDFDocument:
    """Complete result for one reproducible PDF text extraction."""

    filename: str
    page_count: int
    pages: tuple[PDFPage, ...]
    full_text: str
    character_count: int
    word_count: int
    nonempty_page_count: int
    sparse_page_count: int
    title: str | None
    author: str | None
    subject: str | None
    keywords: str | None
    is_likely_scanned: bool


def normalize_extracted_text(text: str) -> str:
    """Normalize extracted text while preserving paragraph structure."""
    normalized_text = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized_text = normalized_text.replace("\u00a0", " ").replace("\x00", "")
    normalized_text = "\n".join(
        line.rstrip() for line in normalized_text.split("\n")
    )
    normalized_text = re.sub(r"\n{3,}", "\n\n", normalized_text)

    return normalized_text.strip()


def count_words(text: str) -> int:
    """Count normalized whitespace tokens, not linguistic word units."""
    return len(normalize_extracted_text(text).split())


def validate_pdf_bytes(
    pdf_bytes: bytes,
    filename: str,
    max_size_bytes: int = MAX_PDF_SIZE_BYTES,
) -> None:
    """Validate application-level PDF upload constraints."""
    if not isinstance(pdf_bytes, bytes):
        raise ValueError("Uploaded PDF content must be provided as bytes.")
    if not filename or not filename.strip():
        raise ValueError("The uploaded file must have a filename.")
    if PurePath(filename).suffix.lower() != ".pdf":
        raise ValueError("Please upload a file with a .pdf extension.")
    if not pdf_bytes:
        raise ValueError("The uploaded PDF is empty.")
    if len(pdf_bytes) > max_size_bytes:
        size_mib = max_size_bytes / (1024 * 1024)
        raise ValueError(f"The uploaded PDF must be {size_mib:.0f} MiB or smaller.")


def _clean_metadata_value(value: Any) -> str | None:
    """Return stripped metadata text or None for missing values."""
    if value is None:
        return None

    normalized_value = normalize_extracted_text(str(value))
    return normalized_value or None


def _build_page(page_number: int, text: str) -> PDFPage:
    """Create page-level statistics from normalized page text."""
    character_count = len(text)
    word_count = count_words(text)
    non_whitespace_character_count = sum(
        1 for character in text if not character.isspace()
    )

    return PDFPage(
        page_number=page_number,
        text=text,
        character_count=character_count,
        word_count=word_count,
        is_text_sparse=(
            non_whitespace_character_count < SPARSE_TEXT_CHARACTER_THRESHOLD
        ),
    )


def _build_full_text(pages: tuple[PDFPage, ...]) -> str:
    """Join pages with visible one-based provenance separators."""
    return "\n\n".join(
        f"===== Page {page.page_number} =====\n\n{page.text}" for page in pages
    )


def extract_pdf_document(
    pdf_bytes: bytes,
    filename: str,
    max_pages: int = MAX_PDF_PAGES,
) -> PDFDocument:
    """Extract normalized page text and metadata from an in-memory PDF."""
    validate_pdf_bytes(pdf_bytes=pdf_bytes, filename=filename)

    document = None
    try:
        document = fitz.open(stream=pdf_bytes, filetype="pdf")
    except PDF_OPEN_ERRORS as error:
        raise ValueError(
            "The uploaded file could not be opened as a readable PDF."
        ) from error

    try:
        if document.needs_pass:
            raise ValueError(
                "This PDF is encrypted or password-protected and cannot be "
                "processed without credentials."
            )

        page_count = document.page_count
        if page_count == 0:
            raise ValueError("The uploaded PDF does not contain any pages.")
        if page_count > max_pages:
            raise ValueError(
                f"The uploaded PDF has {page_count} pages, which exceeds the "
                f"{max_pages}-page application limit."
            )

        pages = tuple(
            _build_page(
                page_number=page_index + 1,
                text=normalize_extracted_text(document[page_index].get_text("text")),
            )
            for page_index in range(page_count)
        )
        full_text = _build_full_text(pages)
        metadata = document.metadata or {}

        character_count = sum(page.character_count for page in pages)
        word_count = sum(page.word_count for page in pages)
        nonempty_page_count = sum(1 for page in pages if page.text)
        sparse_page_count = sum(1 for page in pages if page.is_text_sparse)
        sparse_page_ratio = sparse_page_count / page_count
        is_likely_scanned = (
            nonempty_page_count == 0
            or sparse_page_ratio >= LIKELY_SCANNED_SPARSE_PAGE_RATIO
        )

        return PDFDocument(
            filename=filename,
            page_count=page_count,
            pages=pages,
            full_text=full_text,
            character_count=character_count,
            word_count=word_count,
            nonempty_page_count=nonempty_page_count,
            sparse_page_count=sparse_page_count,
            title=_clean_metadata_value(metadata.get("title")),
            author=_clean_metadata_value(metadata.get("author")),
            subject=_clean_metadata_value(metadata.get("subject")),
            keywords=_clean_metadata_value(metadata.get("keywords")),
            is_likely_scanned=is_likely_scanned,
        )
    except PDF_OPEN_ERRORS as error:
        raise ValueError(
            "The PDF opened, but text extraction failed for this document."
        ) from error
    finally:
        document.close()
