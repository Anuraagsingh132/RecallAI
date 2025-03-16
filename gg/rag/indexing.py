import os
import pickle
import numpy as np
from typing import List, Dict, Any, Optional
import faiss
from sentence_transformers import SentenceTransformer

class DocumentIndexer:
    """Class for embedding and indexing documents for retrieval."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", vector_dim: int = 384):
        """
        Initialize the DocumentIndexer.
        
        Args:
            model_name: Name of the sentence transformer model to use
            vector_dim: Dimension of the embedding vectors
        """
        self.model = SentenceTransformer(model_name)
        self.vector_dim = vector_dim
        self.index = None
        self.documents = []
        
    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        Add documents to the index.
        
        Args:
            documents: List of document chunks with text and metadata
        """
        # Store documents in memory
        start_idx = len(self.documents)
        self.documents.extend(documents)
        
        # Extract text from documents
        texts = [doc["text"] for doc in documents]
        
        # Compute embeddings
        embeddings = self.model.encode(texts, show_progress_bar=True)
        
        # Create or update FAISS index
        if self.index is None:
            self.index = faiss.IndexFlatL2(self.vector_dim)
            
        # Add embeddings to index with IDs starting from start_idx
        faiss.normalize_L2(embeddings)  # Normalize vectors for cosine similarity
        self.index.add(embeddings)
        
        print(f"Added {len(documents)} documents to index. Total: {len(self.documents)}")
        
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for documents similar to the query.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of document chunks with text, metadata, and similarity score
        """
        if self.index is None or len(self.documents) == 0:
            return []
            
        # Compute query embedding
        query_embedding = self.model.encode([query])[0]
        query_embedding = query_embedding.reshape(1, -1)
        faiss.normalize_L2(query_embedding)
        
        # Search in FAISS index
        distances, indices = self.index.search(query_embedding, min(top_k, len(self.documents)))
        
        # Convert distances to similarity scores (1 - distance for L2 distance)
        similarities = 1 - distances[0]
        
        # Return relevant documents
        results = []
        for idx, similarity in zip(indices[0], similarities):
            if idx < len(self.documents):  # Safeguard against out-of-bounds indices
                doc = self.documents[idx].copy()
                doc["similarity"] = float(similarity)
                results.append(doc)
        
        return results

    def save(self, directory: str) -> None:
        """
        Save the index and documents to disk.
        
        Args:
            directory: Directory to save the index and documents
        """
        os.makedirs(directory, exist_ok=True)
        
        # Save FAISS index
        if self.index is not None:
            faiss.write_index(self.index, os.path.join(directory, "faiss_index.bin"))
            
        # Save documents
        with open(os.path.join(directory, "documents.pkl"), "wb") as f:
            pickle.dump(self.documents, f)
            
        print(f"Index saved to {directory}")
        
    def load(self, directory: str) -> bool:
        """
        Load the index and documents from disk.
        
        Args:
            directory: Directory to load the index and documents from
            
        Returns:
            True if successful, False otherwise
        """
        index_path = os.path.join(directory, "faiss_index.bin")
        docs_path = os.path.join(directory, "documents.pkl")
        
        if not os.path.exists(index_path) or not os.path.exists(docs_path):
            return False
            
        try:
            # Load FAISS index
            self.index = faiss.read_index(index_path)
            
            # Load documents
            with open(docs_path, "rb") as f:
                self.documents = pickle.load(f)
                
            print(f"Loaded index with {len(self.documents)} documents")
            return True
        except Exception as e:
            print(f"Error loading index: {e}")
            return False 