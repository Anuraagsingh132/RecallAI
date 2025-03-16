# RecallAI: Technical Documentation

This document provides a comprehensive technical overview of the RecallAI system, explaining its architecture, components, and internal workings.

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [RAG Implementation](#rag-implementation)
4. [Data Flow](#data-flow)
5. [Component Details](#component-details)
   - [Document Processing](#document-processing)
   - [Indexing and Retrieval](#indexing-and-retrieval)
   - [Language Model Integration](#language-model-integration)
   - [API Layer](#api-layer)
   - [Frontend](#frontend)
6. [Security Considerations](#security-considerations)
7. [Deployment Options](#deployment-options)
8. [Performance Optimization](#performance-optimization)
9. [Known Limitations](#known-limitations)
10. [Future Enhancements](#future-enhancements)

## System Overview

RecallAI is a Retrieval-Augmented Generation (RAG) system built with Flask and Google's Gemini API. It allows users to upload documents (text, PDF) or import content from Wikipedia, and then ask questions about that content. The system retrieves relevant information from the documents and generates human-like responses based on the retrieved context.

The main distinguishing features of RecallAI include:

- Document processing for multiple file formats
- Semantic search using vector embeddings
- AI-powered response generation
- Responsive web interface with dark mode support
- Citation of sources in responses
- Shell scripts for easy deployment and management

## Architecture

The system follows a layered architecture:

```
┌────────────────────┐
│     Web Frontend   │
└─────────┬──────────┘
          ↓
┌────────────────────┐
│   Flask API Layer  │
└─────────┬──────────┘
          ↓
┌──────────────────────────────────────┐
│               Core RAG               │
├───────────┬─────────────┬────────────┤
│ Document  │  Indexing & │ Language   │
│ Processing│  Retrieval  │ Model      │
└───────────┴─────────────┴────────────┘
          ↓             ↑
┌─────────┴─────────────┴────────────┐
│           Storage Layer            │
├───────────┬─────────────┬──────────┤
│  Uploads  │Vector Store │ Session  │
│  Directory│             │ Data     │
└───────────┴─────────────┴──────────┘
```

### Key Components:

1. **Flask Application (`app.py`)**: The main entry point that initializes all components and provides API endpoints.
2. **Document Loader (`rag/document_loader.py`)**: Handles processing of various document types.
3. **Document Indexer (`rag/indexing.py`)**: Manages vector embeddings and similarity search.
4. **Language Model (`rag/language_model.py`)**: Interfaces with Google's Gemini API.
5. **Web Interface (`templates/index.html`, `static/js/app.js`)**: Provides the user interface.
6. **Deployment Scripts**: Shell scripts for running and managing the application.

## RAG Implementation

RecallAI implements the Retrieval-Augmented Generation (RAG) pattern, which combines information retrieval with text generation to produce accurate, contextually relevant responses.

### RAG Workflow:

1. **Document Processing**:
   - Documents are loaded from various sources (text files, PDFs, Wikipedia)
   - Text is extracted and chunked into manageable segments
   - Each chunk is processed to remove irrelevant content

2. **Indexing**:
   - Text chunks are converted into vector embeddings using SentenceTransformers
   - Embeddings are stored in an in-memory vector store (with options for FAISS)
   - Metadata (source, page numbers, etc.) is preserved for citations

3. **Retrieval**:
   - User queries are converted to the same vector space
   - Similarity search identifies the most relevant document chunks
   - Top-k results are retrieved based on similarity scores

4. **Generation**:
   - Retrieved document chunks are assembled into a context
   - A prompt is created combining the user query and context
   - The LLM (Gemini) generates a response based on the prompt
   - Citations are added to the response referencing source documents

## Data Flow

The following diagram illustrates the data flow through the system when a user asks a question:

```
User Query → Vector Embedding → Similarity Search → Top-k Documents
                                                         ↓
User ← Response + Citations ← LLM Generation ← Context + Query Prompt
```

In more detail:

1. User submits a question through the web interface
2. Query is sent to the `/chat` endpoint
3. Query is converted to a vector embedding
4. Vector DB performs similarity search to find relevant documents
5. Top documents are retrieved and formatted as context
6. Context and query are combined into a prompt for the LLM
7. LLM generates a response based on the provided context
8. Response is formatted with citations and returned to the user

## Component Details

### Document Processing

The document processing component (`rag/document_loader.py`) handles the ingestion of different document types:

```python
def load_pdf(self, path: str) -> List[Dict[str, Any]]:
    """Load a PDF document and split it into chunks."""
    # Extract text from PDF
    # Split text into chunks
    # Return chunks with metadata
```

Key features include:
- PDF processing with `pdfplumber`
- Text file loading with chunking
- Wikipedia article retrieval using the Wikipedia API
- Text splitting using RecursiveCharacterTextSplitter
- Metadata preservation for source tracking

### Indexing and Retrieval

The indexing component (`rag/indexing.py`) manages the vector database:

```python
def add_documents(self, documents: List[Dict[str, Any]]) -> None:
    """Add documents to the index."""
    # Create embeddings for documents
    # Add to vector store
    # Update metadata mapping
```

Key features include:
- Vector embedding generation using SentenceTransformers
- In-memory vector storage with NumPy/FAISS
- Similarity search with cosine similarity
- Persistence through saving/loading vector indices
- Batched processing for large document sets

### Language Model Integration

The language model component (`rag/language_model.py`) interfaces with Google's Gemini API:

```python
def generate_response(self, query: str, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate a response using the language model."""
    # Create a prompt with context from documents
    # Call the Gemini API
    # Process and return the response
```

Key features include:
- Integration with Google's Gemini API
- Context-aware prompt construction
- Fallback mechanisms for API failures
- Source citation in responses
- Temperature and max token controls

### API Layer

The Flask application provides several API endpoints:

- `/chat`: Send a query and get a response
- `/load`: Load documents from various sources
- `/search`: Directly search the document index
- `/upload-text` and `/upload-pdf`: Upload files
- `/history`: Get conversation history

Each endpoint handles input validation, error handling, and proper response formatting.

### Frontend

The web interface consists of:

- HTML templates (`templates/index.html`)
- CSS styles (`static/css/custom.css`)
- JavaScript functionality (`static/js/app.js`)

Key frontend features include:
- Responsive design with Bootstrap 5
- Dark mode support with theme persistence
- Tab-based interface for chat, uploads, and Wikipedia
- Real-time typing indicators
- Message copying and formatting
- File drag-and-drop uploads
- Browser notifications for responses

## Security Considerations

The current implementation has several security aspects to consider:

1. **Input Validation**: All API endpoints validate input data to prevent injection attacks
2. **File Upload Security**: 
   - Uses `secure_filename` to sanitize uploaded filenames
   - Generates unique filenames to prevent overwriting
   - Restricts allowed file types
3. **Environment Variables**: Sensitive configuration is stored in environment variables
4. **Session Management**: Flask sessions for maintaining conversation history
5. **Areas for Improvement**:
   - Add authentication for API access
   - Implement rate limiting
   - Add CSRF protection
   - Consider content security policies

## Deployment Options

RecallAI provides several deployment options through shell scripts:

1. **Standard Deployment** (`run_app.sh`):
   - Handles port conflicts automatically
   - Creates necessary directories
   - Activates virtual environment if available
   - Starts the application with proper logging

2. **Alternative Port Deployment** (`run_alt_port.sh`):
   - Allows specifying a custom port
   - Useful for running multiple instances
   - Includes the same safeguards as the standard script

3. **Debug Mode** (`run_debug.sh`):
   - Runs the application with console output
   - Useful for development and troubleshooting

4. **Application Management**:
   - `stop_app.sh` for gracefully stopping the application
   - `clean_logs.sh` for managing log files

## Performance Optimization

Several optimizations are implemented to ensure good performance:

1. **Vector Search**:
   - Efficient similarity calculations
   - Option to use FAISS for larger datasets
   - Batched processing of documents

2. **Document Processing**:
   - Chunking to limit context size
   - Metadata optimization to reduce memory usage
   - Caching of embeddings when possible

3. **API Optimizations**:
   - Resource cleanup after requests
   - Efficient session handling
   - Proper error handling to prevent crashes

4. **Frontend Optimizations**:
   - Asynchronous API calls
   - Efficient DOM updates
   - Dark mode implementation without flicker

## Known Limitations

The current implementation has several known limitations:

1. **Vector Store**: In-memory vector store may not scale well for very large document collections
2. **PDF Processing**: Complex PDFs with tables, images, or unusual formatting may not be processed optimally
3. **Language Model**: Depends on external API which may have rate limits or costs
4. **Authentication**: No built-in user authentication system
5. **Concurrent Users**: Not optimized for high concurrent usage

## Future Enhancements

Planned improvements include:

1. **Vector Database**: Integration with persistent vector databases like Pinecone, Qdrant, or Weaviate
2. **Multi-User Support**: User accounts and personalized document collections
3. **Advanced Document Processing**: Better handling of tables, images, and complex PDFs
4. **Evaluation Framework**: Automated testing of response quality
5. **Fine-Tuning**: Options for fine-tuning the language model on specific domains
6. **Streaming Responses**: Implementing streaming for faster perceived performance
7. **Integration Options**: API clients, webhooks, and integrations with other tools

---

This technical documentation provides a comprehensive overview of the RecallAI system. For more specific details, refer to the source code and API documentation. 