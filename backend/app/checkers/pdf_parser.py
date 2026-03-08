from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass, field
from io import BytesIO

import pdfplumber

logger = logging.getLogger(__name__)

POINTS_TO_MM = 1 / 2.835


@dataclass
class TextBlock:
    text: str
    font_name: str
    font_size: float
    is_bold: bool
    is_italic: bool
    bbox: tuple[float, float, float, float]
    alignment: str | None = None


@dataclass
class ImageInfo:
    page_number: int
    bbox: tuple[float, float, float, float]
    width: float
    height: float


@dataclass
class TableInfo:
    page_number: int
    bbox: tuple[float, float, float, float]
    rows: int
    cols: int


@dataclass
class HeadingInfo:
    text: str
    level: int
    page_number: int


@dataclass
class ParsedPage:
    number: int
    width_mm: float
    height_mm: float
    text_blocks: list[TextBlock] = field(default_factory=list)
    images: list[ImageInfo] = field(default_factory=list)
    tables: list[TableInfo] = field(default_factory=list)
    lines: list[str] = field(default_factory=list)


@dataclass
class ParsedPDF:
    pages: list[ParsedPage] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    headings: list[HeadingInfo] = field(default_factory=list)
    page_count: int = 0
    fonts_used: set[str] = field(default_factory=set)


def _build_text_blocks(chars: list[dict]) -> list[TextBlock]:
    if not chars:
        return []

    blocks: list[TextBlock] = []
    current_chars: list[dict] = [chars[0]]

    for ch in chars[1:]:
        prev = current_chars[-1]
        same_line = abs(ch.get("top", 0) - prev.get("top", 0)) < 2
        same_font = ch.get("fontname") == prev.get("fontname") and abs(ch.get("size", 0) - prev.get("size", 0)) < 0.5
        if same_line and same_font:
            current_chars.append(ch)
        else:
            blocks.append(_chars_to_block(current_chars))
            current_chars = [ch]

    if current_chars:
        blocks.append(_chars_to_block(current_chars))
    return blocks


def _chars_to_block(chars: list[dict]) -> TextBlock:
    text = "".join(ch.get("text", "") for ch in chars)
    font_name = chars[0].get("fontname", "")
    font_size = chars[0].get("size", 0.0)
    x0 = min(ch.get("x0", 0) for ch in chars)
    top = min(ch.get("top", 0) for ch in chars)
    x1 = max(ch.get("x1", 0) for ch in chars)
    bottom = max(ch.get("bottom", 0) for ch in chars)
    is_bold = "Bold" in font_name or "bold" in font_name
    is_italic = "Italic" in font_name or "italic" in font_name or "Oblique" in font_name
    return TextBlock(
        text=text,
        font_name=font_name,
        font_size=font_size,
        is_bold=is_bold,
        is_italic=is_italic,
        bbox=(x0, top, x1, bottom),
    )


def parse_pdf(data: bytes) -> ParsedPDF:
    pages: list[ParsedPage] = []
    all_fonts: set[str] = set()
    all_text_blocks: list[tuple[int, TextBlock]] = []

    with pdfplumber.open(BytesIO(data)) as pdf:
        metadata = pdf.metadata or {}

        for page_num, page in enumerate(pdf.pages, start=1):
            try:
                width_mm = (page.width or 0) * POINTS_TO_MM
                height_mm = (page.height or 0) * POINTS_TO_MM

                chars = page.chars or []
                text_blocks = _build_text_blocks(chars)
                for tb in text_blocks:
                    all_fonts.add(tb.font_name)
                    all_text_blocks.append((page_num, tb))

                images: list[ImageInfo] = []
                for img in page.images or []:
                    x0, top, x1, bottom = (
                        img.get("x0", 0),
                        img.get("top", 0),
                        img.get("x1", 0),
                        img.get("bottom", 0),
                    )
                    images.append(
                        ImageInfo(
                            page_number=page_num,
                            bbox=(x0, top, x1, bottom),
                            width=x1 - x0,
                            height=bottom - top,
                        )
                    )

                tables: list[TableInfo] = []
                for tbl in page.find_tables() or []:
                    bbox = tbl.bbox
                    cells = tbl.cells or []
                    rows_set: set[float] = set()
                    cols_set: set[float] = set()
                    for cell in cells:
                        rows_set.add(round(cell[1], 1))
                        cols_set.add(round(cell[0], 1))
                    tables.append(
                        TableInfo(
                            page_number=page_num,
                            bbox=bbox,
                            rows=len(rows_set),
                            cols=len(cols_set),
                        )
                    )

                raw_text = page.extract_text() or ""
                lines = raw_text.split("\n")

                pages.append(
                    ParsedPage(
                        number=page_num,
                        width_mm=width_mm,
                        height_mm=height_mm,
                        text_blocks=text_blocks,
                        images=images,
                        tables=tables,
                        lines=lines,
                    )
                )
            except Exception:
                logger.warning("Failed to parse page %d, skipping", page_num, exc_info=True)
                pages.append(ParsedPage(number=page_num, width_mm=0, height_mm=0))

    font_sizes = [tb.font_size for _, tb in all_text_blocks if tb.font_size > 0]
    common_size = Counter(round(s, 1) for s in font_sizes).most_common(1)
    baseline = common_size[0][0] if common_size else 12.0

    headings: list[HeadingInfo] = []
    for page_num, tb in all_text_blocks:
        if tb.is_bold and tb.font_size > baseline + 0.5 and tb.text.strip():
            level = 1 if tb.font_size >= baseline + 4 else 2
            headings.append(HeadingInfo(text=tb.text.strip(), level=level, page_number=page_num))

    return ParsedPDF(
        pages=pages,
        metadata=metadata,
        headings=headings,
        page_count=len(pages),
        fonts_used=all_fonts,
    )
