from functools import lru_cache


@lru_cache(maxsize=1)
def get_embedding_model(model_name: str):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name, device="cpu")


def embed_texts(texts: list[str], model_name: str) -> list[list[float]]:
    model = get_embedding_model(model_name)
    return model.encode(texts, batch_size=16, show_progress_bar=False, normalize_embeddings=True).tolist()
