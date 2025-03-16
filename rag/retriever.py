from typing import List, Dict, Any, Optional
from .indexing import DocumentIndexer

class DocumentRetriever:
    """Class for retrieving relevant document chunks based on a query."""
    
    def __init__(self, indexer: DocumentIndexer, top_k: int = 5):
        """
        Initialize the DocumentRetriever.
        
        Args:
            indexer: The document indexer to use for retrieval
            top_k: Number of documents to retrieve
        """
        self.indexer = indexer
        self.top_k = top_k
        
    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        """
        Retrieve relevant document chunks based on the query.
        
        Args:
            query: Search query
            
        Returns:
            List of document chunks with text, metadata, and similarity score
        """
        return self.indexer.search(query, top_k=self.top_k)
    
    def format_context(self, documents: List[Dict[str, Any]]) -> str:
        """
        Format retrieved documents into a string context.
        
        Args:
            documents: List of retrieved documents
            
        Returns:
            Formatted context string
        """
        if not documents:
            return ""
            
        # Sort by similarity score (highest first)
        sorted_docs = sorted(documents, key=lambda x: x.get("similarity", 0), reverse=True)
        
        context_parts = []
        
        for i, doc in enumerate(sorted_docs):
            # Format source information
            source_info = doc.get("metadata", {}).get("source", "Unknown source")
            if "title" in doc.get("metadata", {}):
                source_info = f"{doc['metadata']['title']} ({source_info})"
                
            # Format the document chunk
            context_part = f"[Document {i+1}] Source: {source_info}\n\n{doc['text']}\n\n"
            context_parts.append(context_part)
            
        return "".join(context_parts) 