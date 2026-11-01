from app.ingestion.embedder import collection, _model
from config import TOP_K_RETRIEVAL

def retrieve(query: str, top_k: int = TOP_K_RETRIEVAL,
             file_name: str | None = None) -> list[dict]:
    """Retrieve lecture material, optionally restricting results to one lecture."""
    if collection.count() == 0:
        return []
    q_emb = _model.encode([query]).tolist()[0]
    params = {"query_embeddings": [q_emb], "n_results": top_k}
    if file_name:
        params["where"] = {"file_name": file_name}
    res = collection.query(**params)
    out = []
    for i in range(len(res["ids"][0])):
        out.append({
            "chunk_id": res["ids"][0][i],
            "text": res["documents"][0][i],
            "metadata": res["metadatas"][0][i],
            "distance": res["distances"][0][i],
        })
    return out
