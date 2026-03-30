from abc import ABC, abstractmethod


class TranslationProvider(ABC):
    @abstractmethod
    async def translate_to_english(self, text: str) -> str:
        raise NotImplementedError
