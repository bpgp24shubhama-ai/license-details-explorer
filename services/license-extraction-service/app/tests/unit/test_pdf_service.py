from app.services.pdf_service import PDFService


class FakePage:
    def __init__(self, text: str) -> None:
        self._text = text

    def get_text(self, _: str) -> str:
        return self._text


class FakeDocument:
    def __init__(self, pages: list[FakePage]) -> None:
        self._pages = pages

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def __iter__(self):
        return iter(self._pages)


def test_extract_page_texts(monkeypatch):
    fake_doc = FakeDocument([FakePage("Page One"), FakePage("Page Two")])
    monkeypatch.setattr("app.services.pdf_service.fitz.open", lambda **_: fake_doc)

    service = PDFService()
    pages = service.extract_page_texts(b"%PDF")

    assert len(pages) == 2
    assert pages[0].page_number == 1
    assert pages[0].text == "Page One"


def test_machine_readable_threshold():
    service = PDFService()
    from app.services.pdf_service import PageText

    result = service.has_machine_readable_text(
        [
            PageText(page_number=1, text=""),
            PageText(page_number=2, text="Long enough extracted text for readable page"),
        ]
    )
    assert result is True


def test_merge_page_texts():
    from app.services.pdf_service import PageText

    merged = PDFService.merge_page_texts(
        [
            PageText(page_number=1, text="A"),
            PageText(page_number=2, text="B"),
        ]
    )
    assert merged == "A\n\nB"
