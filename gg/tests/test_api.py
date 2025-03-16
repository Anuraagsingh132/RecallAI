#!/usr/bin/env python3
import requests
import json
import os
import time

API_BASE_URL = "http://localhost:5000"

def test_index_endpoint():
    """Test the index endpoint."""
    print("\n=== Testing Index Endpoint ===")
    
    response = requests.get(f"{API_BASE_URL}/")
    data = response.json()
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(data, indent=2)}")
    
    return response.status_code == 200

def test_load_text_document():
    """Test loading a text document."""
    print("\n=== Testing Load Text Document ===")
    
    payload = {
        "source": "text",
        "path": "data/sample.txt"
    }
    
    response = requests.post(f"{API_BASE_URL}/load", json=payload)
    data = response.json()
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(data, indent=2)}")
    
    return response.status_code == 200

def test_search_endpoint():
    """Test the search endpoint."""
    print("\n=== Testing Search Endpoint ===")
    
    payload = {
        "query": "What are the benefits of RAG?",
        "top_k": 3
    }
    
    response = requests.post(f"{API_BASE_URL}/search", json=payload)
    data = response.json()
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(data, indent=2)}")
    
    return response.status_code == 200

def test_chat_endpoint():
    """Test the chat endpoint."""
    print("\n=== Testing Chat Endpoint ===")
    
    payload = {
        "query": "Explain how RAG works"
    }
    
    response = requests.post(f"{API_BASE_URL}/chat", json=payload)
    data = response.json()
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(data, indent=2)}")
    
    return response.status_code == 200

def test_wikipedia_load():
    """Test loading from Wikipedia."""
    print("\n=== Testing Wikipedia Loading ===")
    
    payload = {
        "source": "wikipedia",
        "query": "Transformer models in NLP"
    }
    
    response = requests.post(f"{API_BASE_URL}/load", json=payload)
    data = response.json()
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(data, indent=2)}")
    
    return response.status_code == 200

def main():
    """Run all tests."""
    print("Starting API Tests...")
    
    # Give Flask server time to start
    time.sleep(2)
    
    tests = [
        ("Index Endpoint", test_index_endpoint),
        ("Load Text Document", test_load_text_document),
        ("Search Endpoint", test_search_endpoint),
        ("Chat Endpoint", test_chat_endpoint),
        ("Wikipedia Load", test_wikipedia_load)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"Error in {test_name}: {str(e)}")
            results.append((test_name, False))
    
    print("\n=== Test Results ===")
    for test_name, success in results:
        status = "PASSED" if success else "FAILED"
        print(f"{test_name}: {status}")

if __name__ == "__main__":
    main() 