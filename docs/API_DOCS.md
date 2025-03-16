# RecallAI API Documentation

This document provides detailed information about the API endpoints available in the RecallAI.

## Base URL

All endpoints are relative to the base URL of your RecallAI deployment:

```
http://<host>:<port>/
```

## Authentication

Currently, the API does not require authentication.

## Endpoints

### 1. Chat

Send a query to the chatbot and receive a response.

**Endpoint:** `/chat`  
**Method:** `POST`  
**Content-Type:** `application/json`

**Request Body:**

```json
{
  "query": "What are the key features of RAG systems?"
}
```

**Response:**

```json
{
  "status": "success",
  "response": "RAG (Retrieval-Augmented Generation) systems combine information retrieval with text generation. Key features include: 1) Document retrieval using semantic search, 2) Context-based response generation, 3) Ability to reference external knowledge sources, 4) Reduced hallucinations compared to pure LLM approaches, and 5) Transparency through source citations.",
  "using_llm": true,
  "model": "gemini-2.0-flash",
  "sources": [
    {
      "source": "Introduction to RAG.pdf",
      "similarity": 0.92,
      "title": "Understanding RAG Systems"
    },
    {
      "source": "Vector Search Techniques.txt",
      "similarity": 0.85,
      "title": null
    }
  ]
}
```

### 2. Load Documents

Load documents from various sources into the vector store.

**Endpoint:** `/load`  
**Method:** `POST`  
**Content-Type:** `application/json`

**Request Body:**

For text files:
```json
{
  "source": "text",
  "path": "data/uploads/document.txt"
}
```

For PDF files:
```json
{
  "source": "pdf",
  "path": "data/uploads/document.pdf"
}
```

For Wikipedia articles:
```json
{
  "source": "wikipedia",
  "query": "Retrieval Augmented Generation"
}
```

**Response:**

```json
{
  "status": "success",
  "message": "Loaded 24 document chunks",
  "document_count": 24
}
```

### 3. Search Documents

Directly search the document index without generating a response.

**Endpoint:** `/search`  
**Method:** `POST`  
**Content-Type:** `application/json`

**Request Body:**

```json
{
  "query": "vector database techniques",
  "top_k": 3
}
```

**Response:**

```json
{
  "status": "success",
  "message": "Found 3 relevant documents",
  "results": [
    {
      "text": "Vector databases store embeddings as high-dimensional vectors and enable efficient similarity search...",
      "metadata": {
        "source": "Vector Search Techniques.txt",
        "type": "text"
      },
      "similarity": 0.94
    },
    {
      "text": "FAISS (Facebook AI Similarity Search) is a library for efficient similarity search...",
      "metadata": {
        "source": "Database Comparison.pdf",
        "page": 12,
        "type": "pdf"
      },
      "similarity": 0.88
    },
    {
      "text": "Approximate nearest neighbor algorithms trade exact results for speed...",
      "metadata": {
        "source": "Wikipedia: Vector Database",
        "type": "wikipedia"
      },
      "similarity": 0.82
    }
  ]
}
```

### 4. Upload Files

Upload files to be indexed.

#### Text Files

**Endpoint:** `/upload-text`  
**Method:** `POST`  
**Content-Type:** `multipart/form-data`

**Form Fields:**
- `file`: The text file to upload

**Response:**

```json
{
  "status": "success",
  "message": "File uploaded successfully",
  "path": "data/uploads/document.txt"
}
```

#### PDF Files

**Endpoint:** `/upload-pdf`  
**Method:** `POST`  
**Content-Type:** `multipart/form-data`

**Form Fields:**
- `file`: The PDF file to upload

**Response:**

```json
{
  "status": "success",
  "message": "File uploaded successfully",
  "path": "data/uploads/document.pdf"
}
```

### 5. Chat History

Retrieve chat history.

**Endpoint:** `/history`  
**Method:** `GET`

**Response:**

```json
{
  "status": "success",
  "history": [
    {
      "query": "What are RAG systems?",
      "response": "RAG (Retrieval-Augmented Generation) systems are...",
      "sources": [
        {
          "source": "Introduction to RAG.pdf",
          "similarity": 0.92
        }
      ],
      "timestamp": "2023-06-15T10:30:45"
    },
    {
      "query": "How do vector embeddings work?",
      "response": "Vector embeddings transform text into numerical vectors...",
      "sources": [
        {
          "source": "Vector Search Techniques.txt",
          "similarity": 0.89
        }
      ],
      "timestamp": "2023-06-15T10:31:20"
    }
  ]
}
```

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200 OK`: Request was successful
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server-side error

Error responses include a descriptive message:

```json
{
  "status": "error",
  "message": "Invalid request: missing required parameter 'query'"
}
```

## Rate Limiting

Currently, there are no rate limits implemented.

## Versioning

The current API version is v1. Future versions may be introduced with a version prefix in the URL path. 