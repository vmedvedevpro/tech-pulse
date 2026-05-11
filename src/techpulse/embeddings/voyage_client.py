import voyageai

from techpulse.embeddings.protocols import InputType


class VoyageEmbeddingClient:
    def __init__(self, api_key: str, model: str) -> None:
        self._model = model
        self._client = voyageai.AsyncClient(api_key=api_key)

    async def embed(self, text: str, *, input_type: InputType = "document") -> list[float]:
        result = await self._client.embed([text], model=self._model, input_type=input_type)
        return result.embeddings[0]

    async def embed_batch(
            self, texts: list[str], *, input_type: InputType = "document"
    ) -> list[list[float]]:
        result = await self._client.embed(texts, model=self._model, input_type=input_type)
        return result.embeddings
