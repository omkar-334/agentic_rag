import os

from dotenv import load_dotenv
from qdrant_client import QdrantClient

load_dotenv()


class HybridClient:
    DENSE_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    SPARSE_MODEL = "prithivida/Splade_PP_en_v1"

    def __init__(self):
        self.qdrant_client = QdrantClient(
            url="https://e8c7892c-84a5-4b73-9281-27d52258c6d8.europe-west3-0.gcp.cloud.qdrant.io:6333",
            api_key=os.getenv("QDRANT_API_KEY"),
        )
        self.qdrant_client.set_model(self.DENSE_MODEL)
        self.qdrant_client.set_sparse_model(self.SPARSE_MODEL)

    def create(self, collection: str):
        if not self.qdrant_client.collection_exists(collection):
            self.create_collection(
                collection_name=collection,
                vectors_config=self.qdrant_client.get_fastembed_vector_params(),
                sparse_vectors_config=self.qdrant_client.get_fastembed_sparse_vector_params(),
            )
            return collection
        return None

    def insert(self, collection, chunks):
        documents = []
        for chunk in chunks:
            documents.append(chunk.pop("text"))

        self.qdrant_client.add(
            collection_name=collection,
            documents=documents,
            metadata=chunks,
            parallel=0,
        )

    def search(self, collection, text: str, limit: int = 10):
        search_result = self.qdrant_client.query(
            collection_name=collection,
            query_text=text,
            query_filter=None,
            limit=limit,
        )
        # Select and return metadata
        # metadata = [hit.metadata for hit in search_result]
        return search_result
