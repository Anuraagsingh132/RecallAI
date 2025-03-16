# RecallAI Implementation Guide

This document provides a detailed explanation of how RecallAI works from an implementation perspective, with code examples highlighting key functionality.

## Table of Contents
1. [Core Components Overview](#core-components-overview)
2. [Document Processing Implementation](#document-processing-implementation)
3. [Vector Indexing Implementation](#vector-indexing-implementation)
4. [Language Model Integration](#language-model-integration)
5. [API Implementation](#api-implementation)
6. [Frontend Implementation](#frontend-implementation)
7. [Deployment Implementation](#deployment-implementation)
8. [Common Development Tasks](#common-development-tasks)

## Core Components Overview

RecallAI is built around several key Python modules that work together to provide RAG functionality:

```python
# Main app initialization in app.py
# Initialize RAG components
document_loader = DocumentLoader()
document_indexer = DocumentIndexer()
language_model = LanguageModel()

# Get vector store path from environment
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./data/vector_store")
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "./data/uploads")

# Try to load existing vector store
document_indexer.load(VECTOR_DB_PATH)
```

The application follows a modular design where each component has specific responsibilities:

1. `DocumentLoader`: Handles loading and processing documents from different sources
2. `DocumentIndexer`: Manages the vector database for document storage and retrieval
3. `LanguageModel`: Interfaces with the Gemini API for text generation

## Document Processing Implementation

### Loading Documents

RecallAI can load documents from multiple sources:

```python
# From rag/document_loader.py
class DocumentLoader:
    def load_pdf(self, path: str) -> List[Dict[str, Any]]:
        """Load a PDF document and split it into chunks."""
        documents = []
        try:
            # Open the PDF file
            with pdfplumber.open(path) as pdf:
                text = ""
                metadata = {"source": path, "type": "pdf"}
                
                # Extract text from each page
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        page_metadata = metadata.copy()
                        page_metadata["page"] = i + 1
                        text += f"\n\n{page_text}"
                
                # Split text into chunks
                chunks = self._split_text(text)
                
                # Create document objects
                for i, chunk in enumerate(chunks):
                    chunk_metadata = metadata.copy()
                    chunk_metadata["chunk"] = i
                    documents.append({
                        "text": chunk,
                        "metadata": chunk_metadata
                    })
                
        except Exception as e:
            print(f"Error loading PDF: {e}")
        
        return documents
```

### Text Chunking

Text chunking is a critical part of the RAG process:

```python
def _split_text(self, text: str) -> List[str]:
    """Split text into manageable chunks."""
    # Use RecursiveCharacterTextSplitter for intelligent splitting
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,            # Target chunk size
        chunk_overlap=200,          # Overlap to maintain context
        separators=["\n\n", "\n", " ", ""]  # Try these separators in order
    )
    
    return splitter.split_text(text)
```

### Loading from Wikipedia

RecallAI can also load content directly from Wikipedia:

```python
def load_wikipedia(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
    """Load content from Wikipedia based on a query."""
    documents = []
    try:
        # Search Wikipedia
        search_results = wikipedia.search(query, results=max_results)
        
        # Process each result
        for title in search_results:
            try:
                # Get page content
                page = wikipedia.page(title)
                content = page.content
                url = page.url
                
                # Base metadata
                metadata = {
                    "source": f"Wikipedia: {title}",
                    "url": url,
                    "title": title,
                    "type": "wikipedia"
                }
                
                # Split content into chunks
                chunks = self._split_text(content)
                
                # Create document objects
                for i, chunk in enumerate(chunks):
                    chunk_metadata = metadata.copy()
                    chunk_metadata["chunk"] = i
                    documents.append({
                        "text": chunk,
                        "metadata": chunk_metadata
                    })
                    
            except (wikipedia.exceptions.DisambiguationError, 
                    wikipedia.exceptions.PageError) as e:
                print(f"Wikipedia error for {title}: {e}")
                continue
    except Exception as e:
        print(f"Error loading from Wikipedia: {e}")
    
    return documents
```

## Vector Indexing Implementation

### Creating Embeddings

The `DocumentIndexer` class handles the creation and management of vector embeddings:

```python
# From rag/indexing.py
class DocumentIndexer:
    def __init__(self):
        """Initialize the document indexer."""
        # Initialize the embedding model
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.documents = []
        self.embeddings = None
        self.metadata = []
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Add documents to the index."""
        if not documents:
            return
            
        # Print progress info
        print(f"Adding {len(documents)} documents to index...")
        
        # Process documents in batches to avoid memory issues
        batch_size = 32
        num_batches = (len(documents) + batch_size - 1) // batch_size
        
        # Show progress bar
        for i in tqdm(range(num_batches), desc="Batches", unit="batch"):
            start_idx = i * batch_size
            end_idx = min(start_idx + batch_size, len(documents))
            batch = documents[start_idx:end_idx]
            
            # Extract text from the batch
            texts = [doc["text"] for doc in batch]
            
            # Generate embeddings for the batch
            batch_embeddings = self.embedding_model.encode(texts)
            
            # Store the documents, embeddings, and metadata
            for j, doc in enumerate(batch):
                self.documents.append(doc["text"])
                self.metadata.append(doc["metadata"])
                
                # Initialize embeddings array if needed
                if self.embeddings is None:
                    self.embeddings = np.zeros((0, batch_embeddings[0].shape[0]))
                
                # Add the new embedding
                self.embeddings = np.vstack([self.embeddings, batch_embeddings[j]])
        
        print(f"Added {len(documents)} documents to index. Total: {len(self.documents)}")
```

### Searching for Relevant Documents

When a user asks a question, the system searches for relevant documents using vector similarity:

```python
def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Search for documents similar to the query."""
    if not self.embeddings.shape[0]:
        return []
        
    # Generate embedding for the query
    query_embedding = self.embedding_model.encode(query)
    
    # Calculate cosine similarity
    similarities = cosine_similarity(
        query_embedding.reshape(1, -1), 
        self.embeddings
    )[0]
    
    # Get indices of top_k most similar documents
    top_indices = np.argsort(similarities)[::-1][:top_k]
    
    # Prepare results
    results = []
    for idx in top_indices:
        if similarities[idx] > 0.2:  # Similarity threshold
            results.append({
                "text": self.documents[idx],
                "metadata": self.metadata[idx],
                "similarity": similarities[idx]
            })
    
    return results
```

### Persistence

RecallAI saves and loads the vector database to maintain document state between runs:

```python
def save(self, directory: str) -> None:
    """Save the index to disk."""
    os.makedirs(directory, exist_ok=True)
    
    # Save documents
    with open(os.path.join(directory, "documents.pkl"), "wb") as f:
        pickle.dump(self.documents, f)
    
    # Save metadata
    with open(os.path.join(directory, "metadata.pkl"), "wb") as f:
        pickle.dump(self.metadata, f)
    
    # Save embeddings
    np.save(os.path.join(directory, "embeddings.npy"), self.embeddings)
    
    print(f"Index saved to {directory}")

def load(self, directory: str) -> bool:
    """Load the index from disk."""
    if not os.path.exists(directory):
        print(f"Index directory {directory} does not exist")
        return False
    
    try:
        # Load documents
        with open(os.path.join(directory, "documents.pkl"), "rb") as f:
            self.documents = pickle.load(f)
        
        # Load metadata
        with open(os.path.join(directory, "metadata.pkl"), "rb") as f:
            self.metadata = pickle.load(f)
        
        # Load embeddings
        self.embeddings = np.load(os.path.join(directory, "embeddings.npy"))
        
        print(f"Loaded index with {len(self.documents)} documents")
        return True
    except Exception as e:
        print(f"Error loading index: {e}")
        return False
```

## Language Model Integration

The `LanguageModel` class handles interactions with Google's Gemini API:

```python
# From rag/language_model.py
class LanguageModel:
    """Class for generating responses using an LLM (Google Gemini)."""
    
    def __init__(self):
        """Initialize the language model."""
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        
        # Initialize Gemini if API key is available
        if self.api_key:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.genai = genai
            print(f"Initialized Gemini with model: {self.model}")
        else:
            self.genai = None
            print("No API key found for Gemini, will use simple response generation")
    
    def generate_response(self, query: str, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a response using the language model."""
        # Check if we have documents or should use a fallback
        if not documents:
            return self._generate_fallback_response(query)
        
        if not self.genai or not self.api_key:
            return self._generate_simple_response(query, documents)
        
        try:
            # Prepare context from documents
            context = self._prepare_context(documents)
            
            # Create prompt
            prompt = f"""Question: {query}
            
Context information:
{context}

Based on the context information provided, please answer the question. If the 
answer is not contained in the context information, say "I don't have enough 
information to answer that question" and suggest what information might help.
"""
            
            # Generate response using Gemini
            model = self.genai.GenerativeModel(self.model)
            response = model.generate_content(prompt)
            
            return {
                "response": response.text,
                "using_llm": True,
                "model": self.model
            }
            
        except Exception as e:
            print(f"Error generating response with Gemini: {e}")
            # Fall back to simple response
            return self._generate_simple_response(query, documents)
```

## API Implementation

The Flask application provides the API layer that coordinates all components:

```python
# From app.py
@app.route("/chat", methods=["POST"])
def chat():
    """Route for chatting with the bot."""
    data = request.json
    
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400
        
    query = data.get("query")
    
    if not query:
        return jsonify({"status": "error", "message": "No query provided"}), 400
    
    # Initialize session history if not exists
    if 'history' not in session:
        session['history'] = []
        
    try:
        # Search for relevant documents
        documents = document_indexer.search(query, top_k=3)
        
        # Extract sources for the response
        sources = []
        for doc in documents:
            metadata = doc.get("metadata", {})
            source = {
                "source": metadata.get("source", "Unknown"),
                "similarity": float(doc.get("similarity", 0))
            }
            if "title" in metadata:
                source["title"] = metadata["title"]
            sources.append(source)
        
        # Generate response using the language model
        response_data = language_model.generate_response(query, documents)
        
        # Store in conversation history
        history_entry = {
            "query": query,
            "response": response_data["response"],
            "sources": sources,
            "timestamp": json.dumps({"$date": {"$numberLong": str(int(time.time() * 1000))}})
        }
        
        # Limit history size
        session['history'] = session['history'][-9:] + [history_entry]  # Keep last 10 entries
        session.modified = True
        
        return jsonify({
            "status": "success",
            "response": response_data["response"],
            "using_llm": response_data.get("using_llm", False),
            "model": response_data.get("model", "simple"),
            "sources": sources
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
```

## Frontend Implementation

The frontend uses vanilla JavaScript to interact with the backend:

```javascript
// From static/js/app.js (simplified)
function sendMessage() {
    const userInput = document.getElementById('userInput');
    const message = userInput.value.trim();
    
    if (message === '') return;
    
    // Clear input
    userInput.value = '';
    
    // Add user message to chat
    addMessageToChat('user', message);
    
    // Show typing indicator
    window.showTypingIndicator();
    
    // Send request to API
    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: message }),
    })
    .then(response => response.json())
    .then(data => {
        // Hide typing indicator
        window.removeTypingIndicator();
        
        if (data.status === 'success') {
            // Add bot response to chat
            addMessageToChat('bot', data.response, data.sources, data.model);
        } else {
            // Show error message
            addMessageToChat('bot', `Error: ${data.message}`);
        }
    })
    .catch(error => {
        window.removeTypingIndicator();
        addMessageToChat('bot', `Error: ${error.message}`);
    });
}
```

### Message Rendering

The frontend renders messages with source citations:

```javascript
function addMessageToChat(role, message, sources = null, model = null) {
    const chatBox = document.getElementById('chatBox');
    const messageDiv = document.createElement('div');
    messageDiv.classList.add(role === 'user' ? 'user-message' : 'bot-message');
    
    // Create content div
    const contentDiv = document.createElement('div');
    contentDiv.classList.add('message-content');
    
    // Format message with markdown
    const formattedMessage = markdownToHtml(message);
    contentDiv.innerHTML = formattedMessage;
    messageDiv.appendChild(contentDiv);
    
    // Add sources if available
    if (sources && sources.length > 0) {
        const sourcesElement = document.createElement('div');
        sourcesElement.classList.add('source-citation');
        sourcesElement.innerHTML = '<strong><i class="fas fa-book me-1"></i> Sources:</strong><br>';
        
        sources.forEach(source => {
            const sourceText = source.title ? 
                `${source.title} (${source.source})` : 
                `${source.source}`;
            sourcesElement.innerHTML += `<i class="fas fa-angle-right me-1"></i> ${sourceText}<br>`;
        });
        
        messageDiv.appendChild(sourcesElement);
    }
    
    // Add copy button to message
    if (window.addCopyButton) {
        window.addCopyButton(messageDiv);
    }
    
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
    
    // Send browser notification if supported
    if (window.sendNotification) {
        window.sendNotification(message);
    }
}
```

## Deployment Implementation

RecallAI includes several shell scripts for deployment and management:

### Main Deployment Script

```bash
# From run_app.sh
#!/bin/bash
#
# RecallAI Main Application Script
# This script starts the RecallAI application with proper configuration
# and handles common issues like port conflicts.
#

# Terminal colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}  RecallAI - Startup Script${NC}"
echo -e "${BLUE}=========================================${NC}"

# Kill any existing Flask processes
echo -e "${YELLOW}Stopping any existing Flask applications...${NC}"
pkill -f "python.*app.py" || true
sleep 1

# Function to check if a port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        return 1
    else
        return 0
    fi
}

# Try ports in sequence
DEFAULT_PORT=8080
port=$DEFAULT_PORT
MAX_PORT=8085

while ! check_port $port && [ $port -le $MAX_PORT ]; do
    echo -e "${YELLOW}Port $port is in use. Trying next port...${NC}"
    port=$((port + 1))
done

if [ $port -gt $MAX_PORT ]; then
    echo -e "${RED}Error: Could not find an available port in range $DEFAULT_PORT-$MAX_PORT${NC}"
    echo -e "${RED}Please close some applications and try again.${NC}"
    exit 1
fi

echo -e "${GREEN}Using port: $port${NC}"

# Create necessary directories
echo -e "${YELLOW}Creating necessary directories...${NC}"
mkdir -p data/vector_store data/uploads logs

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source venv/bin/activate 2>/dev/null || true
elif [ -d "venv_rag" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source venv_rag/bin/activate 2>/dev/null || true
fi

# Set environment variables
export FLASK_APP=app.py
export DEBUG=1
export PORT=$port

# Start the application with logging to file
LOG_FILE="logs/flask_$(date +%Y%m%d_%H%M%S).log"
echo -e "${GREEN}Starting application on port $port with logging to $LOG_FILE...${NC}"
python3 app.py > "$LOG_FILE" 2>&1 &

# Get the PID of the Flask application
PID=$!
sleep 2

# Check if the process is still running
if ps -p $PID > /dev/null; then
    echo -e "${GREEN}==========================================${NC}"
    echo -e "${GREEN}Application started successfully!${NC}"
    echo -e "${GREEN}Access the application at: http://localhost:$port${NC}"
    echo -e "${GREEN}Process ID: $PID${NC}"
    echo -e "${GREEN}Log file: $LOG_FILE${NC}"
    echo -e "${GREEN}View logs with: tail -f $LOG_FILE${NC}"
    echo -e "${GREEN}Stop the application with: ./stop_app.sh${NC}"
    echo -e "${GREEN}==========================================${NC}"
else
    echo -e "${RED}Error: Application failed to start. Check logs for details:${NC}"
    echo -e "${RED}tail -f $LOG_FILE${NC}"
    exit 1
fi
```

## Common Development Tasks

### Adding a New Document Source

To add a new document source type (e.g., Google Docs):

1. Add a new method to `DocumentLoader`:

```python
def load_google_doc(self, doc_id: str) -> List[Dict[str, Any]]:
    """Load a document from Google Docs."""
    documents = []
    
    # Import Google Docs API client
    from googleapiclient.discovery import build
    from google.oauth2 import service_account
    
    # Set up credentials and API client
    SCOPES = ['https://www.googleapis.com/auth/documents.readonly']
    SERVICE_ACCOUNT_FILE = 'credentials.json'
    
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('docs', 'v1', credentials=credentials)
    
    # Get document content
    doc = service.documents().get(documentId=doc_id).execute()
    doc_content = doc.get('body').get('content')
    text = self._extract_text_from_doc_content(doc_content)
    
    # Process as usual
    metadata = {
        "source": f"Google Doc: {doc.get('title')}",
        "doc_id": doc_id,
        "type": "google_doc"
    }
    
    # Split and create documents
    chunks = self._split_text(text)
    for i, chunk in enumerate(chunks):
        chunk_metadata = metadata.copy()
        chunk_metadata["chunk"] = i
        documents.append({
            "text": chunk,
            "metadata": chunk_metadata
        })
    
    return documents
```

2. Add a new endpoint to `app.py`:

```python
@app.route("/load-google-doc", methods=["POST"])
def load_google_doc():
    """Route for loading documents from Google Docs."""
    data = request.json
    
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400
        
    doc_id = data.get("doc_id")
    
    if not doc_id:
        return jsonify({"status": "error", "message": "No doc_id provided"}), 400
        
    try:
        # Load from Google Docs
        documents = document_loader.load_google_doc(doc_id)
        
        if not documents:
            return jsonify({
                "status": "error", 
                "message": f"No content found for Google Doc ID: {doc_id}"
            }), 404
            
        # Add documents to index
        document_indexer.add_documents(documents)
        
        # Save the updated index
        document_indexer.save(VECTOR_DB_PATH)
        
        return jsonify({
            "status": "success", 
            "message": f"Loaded {len(documents)} document chunks from Google Doc",
            "document_count": len(documents)
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
```

3. Update the frontend to include the new source option:

```html
<div class="mb-3">
    <label for="googleDocId" class="form-label">Google Doc ID</label>
    <div class="input-group">
        <input type="text" class="form-control" id="googleDocId" placeholder="Enter Google Doc ID">
        <button class="btn btn-primary" id="loadGoogleDocButton">
            <i class="fas fa-cloud-download-alt me-2"></i>Load
        </button>
    </div>
    <div class="form-text">Enter the ID of a Google Doc you want to load.</div>
</div>
```

```javascript
// Add event listener for Google Doc loading
document.getElementById('loadGoogleDocButton').addEventListener('click', function() {
    const docId = document.getElementById('googleDocId').value.trim();
    if (docId === '') {
        showAlert('Please enter a valid Google Doc ID', 'warning');
        return;
    }
    
    // Show loading state
    this.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading...';
    this.disabled = true;
    
    // Send request to load the document
    fetch('/load-google-doc', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ doc_id: docId }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showAlert(`Successfully loaded ${data.document_count} document chunks from Google Doc`, 'success');
        } else {
            showAlert(`Error: ${data.message}`, 'danger');
        }
    })
    .catch(error => {
        showAlert(`Error: ${error.message}`, 'danger');
    })
    .finally(() => {
        // Reset button state
        this.innerHTML = '<i class="fas fa-cloud-download-alt me-2"></i>Load';
        this.disabled = false;
    });
});
```

### Deploying with Docker

RecallAI can be containerized for easier deployment:

1. Create a `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/vector_store data/uploads logs

# Expose port
EXPOSE 8080

# Set environment variables
ENV FLASK_APP=app.py
ENV DEBUG=0
ENV PORT=8080

# Run the application
CMD ["python", "app.py"]
```

2. Create a `docker-compose.yml` for easier management:

```yaml
version: '3'

services:
  recallai:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    env_file:
      - .env
    restart: unless-stopped
```

3. Run with:

```bash
docker-compose up -d
```

---

This implementation guide provides a detailed look at the code that makes RecallAI work. For further details, refer to the source code and the API documentation. 