from abc import ABC, abstractmethod

from app.models.schemas import Action


class AIProvider(ABC):
    name: str

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        model: str,
        api_key: str,
    ) -> list[Action]:
        ...
