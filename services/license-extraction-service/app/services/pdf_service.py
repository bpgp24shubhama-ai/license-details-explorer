from dataclasses import dataclass

import fitz


@dataclass
class PageText:
    page_number: int
    text: str


class PDFService:
    def extract_page_texts(self, pdf_bytes: bytes) -> list[PageText]:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
            return [
                PageText(page_number=index + 1, text=page.get_text("text").strip())
                for index, page in enumerate(document)
            ]

    def render_pages_to_images(self, pdf_bytes: bytes) -> list[bytes]:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
            images: list[bytes] = []
            for page in document:
                pixmap = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
                images.append(pixmap.tobytes("png"))
            return images

    @staticmethod
    def has_machine_readable_text(page_texts: list[PageText], min_chars: int = 20) -> bool:
        readable_pages = sum(1 for page in page_texts if len(page.text.strip()) >= min_chars)
        if not page_texts:
            return False
        return readable_pages / len(page_texts) >= 0.5

    @staticmethod
    def merge_page_texts(page_texts: list[PageText]) -> str:
        return "\n\n".join(page.text for page in page_texts if page.text.strip())
