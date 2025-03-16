from rag.document_loader import DocumentLoader
from rag.indexing import DocumentIndexer
from rag.language_model import LanguageModel
import json
import os

def test_language_model():
    """Test the language model with retrieved documents."""
    print("\n=== Testing Language Model ===")
    
    # Load sample documents
    loader = DocumentLoader()
    documents = loader.load_text_file("data/sample.txt")
    print(f"Loaded {len(documents)} document chunks")
    
    # Create sample indexer to retrieve documents
    indexer = DocumentIndexer()
    indexer.add_documents(documents)
    
    # Perform a search to get relevant documents
    query = "What are the benefits of RAG?"
    results = indexer.search(query, top_k=2)
    print(f"Retrieved {len(results)} documents for query: '{query}'")
    
    # Initialize language model
    language_model = LanguageModel()
    
    # Generate response
    print("\nGenerating response...")
    response_data = language_model.generate_response(query, results)
    
    # Print results
    print(f"\nUsing LLM: {response_data.get('using_llm', False)}")
    if response_data.get('using_llm', False):
        print(f"Model: {response_data.get('model', 'unknown')}")
    
    print("\nGenerated Response:")
    print("-" * 50)
    print(response_data["response"])
    print("-" * 50)
    
    # Save response to file for inspection
    with open("data/llm_response_sample.json", "w") as f:
        json.dump(response_data, f, indent=2)
    print("\nSaved response to data/llm_response_sample.json")
    
    return response_data

if __name__ == "__main__":
    print("Testing Language Model integration...\n")
    
    # Test language model
    response_data = test_language_model()
    
    print("\nTest completed.") 