from typing import Literal, Protocol

InputType = Literal["document", "query"]


class EmbeddingClient(Protocol):
    async def embed(self, text: str, *, input_type: InputType = "document") -> list[float]: ...

    async def embed_batch(
            self, texts: list[str], *, input_type: InputType = "document"
    ) -> list[list[float]]: ...
