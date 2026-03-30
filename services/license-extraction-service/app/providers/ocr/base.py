from abc import ABC, abstractmethod

from pydantic import BaseModel


class OCRPageResult(BaseModel):
    page_number: int
    text: str


class OCRProvider(ABC):
    provider_name: str

    @abstractmethod
    async def extract_text(self, page_images: list[bytes]) -> list[OCRPageResult]:
        raise NotImplementedError
