import os

from dotenv import load_dotenv
from qdrant_client import QdrantClient, models

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
            self.qdrant_client.create_collection(
                collection_name=collection,
                vectors_config=self.qdrant_client.get_fastembed_vector_params(),
                sparse_vectors_config=self.qdrant_client.get_fastembed_sparse_vector_params(),
                quantization_config=models.ScalarQuantization(
                    scalar=models.ScalarQuantizationConfig(
                        type=models.ScalarType.INT8,
                        quantile=0.99,
                        always_ram=False,
                    ),
                ),
            )
            print(f"--- {collection} collection created")
            return collection
        return None

    def insert(self, collection, chunks):
        documents = []
        for chunk in chunks:
            documents.append(chunk.pop("text"))
            chunk.pop("color")
            chunk.pop("size")

        self.qdrant_client.add(
            collection_name=collection,
            documents=documents,
            metadata=chunks,
            parallel=0,
        )
        print("--- pdf inserted")

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

    def get_chapter_name(self, collection: str):
        points = self.qdrant_client.retrieve(collection_name=collection, ids=[0])
        return points[0]
