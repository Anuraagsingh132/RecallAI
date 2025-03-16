from rag.document_loader import DocumentLoader
import json

def test_text_file_loading():
    """Test loading text from a file."""
    loader = DocumentLoader()
    
    try:
        # Test loading the sample text file
        documents = loader.load_text_file("data/sample.txt")
        
        print("\n=== Text File Loading Test ===")
        print(f"Successfully loaded {len(documents)} document chunks")
        print(f"First chunk preview: {documents[0]['text'][:100]}...")
        print(f"Metadata: {documents[0]['metadata']}")
        
        return documents
    except Exception as e:
        print(f"Error loading text file: {e}")
        return None

def test_wikipedia_loading():
    """Test loading text from Wikipedia."""
    loader = DocumentLoader()
    
    try:
        # Test loading from Wikipedia
        documents = loader.load_wikipedia("Retrieval Augmented Generation")
        
        print("\n=== Wikipedia Loading Test ===")
        print(f"Successfully loaded {len(documents)} document chunks")
        
        if documents:
            print(f"First chunk preview: {documents[0]['text'][:100]}...")
            print(f"Metadata: {documents[0]['metadata']}")
        else:
            print("No documents were retrieved from Wikipedia")
        
        return documents
    except Exception as e:
        print(f"Error loading from Wikipedia: {e}")
        return None

if __name__ == "__main__":
    print("Testing DocumentLoader functionality directly...\n")
    
    # Test text file loading
    text_docs = test_text_file_loading()
    
    # Test Wikipedia loading
    wiki_docs = test_wikipedia_loading()
    
    # Save sample results to a file for inspection
    if text_docs:
        with open("data/text_docs_sample.json", "w") as f:
            json.dump(text_docs[:2], f, indent=2)
            print("\nSaved text document samples to data/text_docs_sample.json")
    
    if wiki_docs:
        with open("data/wiki_docs_sample.json", "w") as f:
            json.dump(wiki_docs[:2], f, indent=2)
            print("Saved Wikipedia document samples to data/wiki_docs_sample.json")
            
    print("\nAll tests completed.") 