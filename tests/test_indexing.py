from rag.document_loader import DocumentLoader
from rag.indexing import DocumentIndexer
import json
import os

def test_document_indexing():
    """Test document indexing and search."""
    # Create the vector store directory if it doesn't exist
    vector_store_dir = "data/vector_store"
    os.makedirs(vector_store_dir, exist_ok=True)
    
    # Load documents
    loader = DocumentLoader()
    documents = loader.load_text_file("data/sample.txt")
    
    print(f"\n=== Document Loading ===")
    print(f"Loaded {len(documents)} document chunks")
    
    # Create indexer
    indexer = DocumentIndexer()
    
    # Add documents to index
    print(f"\n=== Document Indexing ===")
    indexer.add_documents(documents)
    
    # Save index
    indexer.save(vector_store_dir)
    print(f"Index saved to {vector_store_dir}")
    
    # Test search
    print(f"\n=== Document Search ===")
    query = "What are the benefits of RAG?"
    results = indexer.search(query, top_k=2)
    
    print(f"Query: '{query}'")
    print(f"Found {len(results)} relevant documents")
    
    for i, result in enumerate(results):
        print(f"\nResult {i+1} (Similarity: {result['similarity']:.4f})")
        print(f"Text preview: {result['text'][:100]}...")
    
    # Save search results for inspection
    with open("data/search_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved search results to data/search_results.json")
    
    return indexer

def test_index_loading():
    """Test loading an existing index."""
    vector_store_dir = "data/vector_store"
    
    print(f"\n=== Index Loading ===")
    
    # Load index
    indexer = DocumentIndexer()
    success = indexer.load(vector_store_dir)
    
    if success:
        print(f"Successfully loaded index with {len(indexer.documents)} documents")
        
        # Test search on loaded index
        query = "What are the components of a RAG system?"
        results = indexer.search(query, top_k=2)
        
        print(f"\nQuery on loaded index: '{query}'")
        print(f"Found {len(results)} relevant documents")
        
        for i, result in enumerate(results):
            print(f"\nResult {i+1} (Similarity: {result['similarity']:.4f})")
            print(f"Text preview: {result['text'][:100]}...")
    else:
        print("Failed to load index")
    
    return indexer

if __name__ == "__main__":
    print("Testing document indexing functionality...\n")
    
    # Test indexing
    indexer = test_document_indexing()
    
    # Test loading
    loaded_indexer = test_index_loading()
    
    print("\nAll tests completed.") 