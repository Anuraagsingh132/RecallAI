# 🤖 RecallAI

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)
![Google Gemini](https://img.shields.io/badge/Google-Gemini-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

A modern Retrieval-Augmented Generation (RAG) chatbot with a clean web interface, built with Flask and powered by Google's Gemini.

<p align="center">
  <img src="static/images/bot-icon.png" alt="RecallAI Logo" width="120">
</p>

## ✨ Features

- 📄 **Document Processing**: Upload and process text files, PDFs, and load Wikipedia articles
- 🔍 **Semantic Search**: Find relevant information using vector search
- 💬 **AI-Powered Chat**: Generate natural responses using Google's Gemini model
- 🌗 **Dark Mode**: Toggle between light and dark themes for better readability
- 🚀 **Easy Setup**: Simple installation with minimal dependencies
- 📱 **Responsive Design**: Works well on desktop and mobile devices

## 🛠️ Tech Stack

- **Backend**: Python, Flask
- **AI**: Google Gemini API
- **Vector DB**: In-memory vector store with numpy/FAISS
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Embeddings**: SentenceTransformers

## 📋 Prerequisites

Before you begin, ensure you have:

- Python 3.8 or higher
- pip package manager
- [Optional] Google API key for Gemini model access

## 🚀 Installation

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd rag-chatbot
```

### Step 2: Set Up Virtual Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate it
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your Google API key
nano .env
```

### Step 5: Run the Setup Script

```bash
# Make the script executable
chmod +x setup.sh

# Run it to create necessary directories
./setup.sh
```

## 🖥️ Usage

### Running the Application

```bash
# Start the application on port 8080 (recommended)
./run_app.sh
```

Then open your browser and navigate to: http://localhost:8080

### Available Scripts

- `run_app.sh` - Main application script (recommended)
- `run_debug.sh` - Runs the app in debug mode with additional logging

### Using the Web Interface

1. **Chat Tab**: Ask questions about your documents
2. **Upload Tab**: Add your own documents (text or PDF)
3. **Wikipedia Tab**: Search and load Wikipedia articles

### Dark Mode

Toggle between light and dark mode by clicking the moon/sun icon in the top right corner.

## 🔌 API Endpoints

The chatbot provides the following API endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat` | POST | Send a query and get a response |
| `/load` | POST | Load documents from various sources |
| `/search` | POST | Directly search the document index |
| `/upload-text` | POST | Upload text files |
| `/upload-pdf` | POST | Upload PDF files |
| `/history` | GET | Get chat history |

For detailed API documentation, see [API_DOCS.md](./docs/API_DOCS.md).

## 📁 Project Structure

```
.
├── app.py                 # Main Flask application
├── run_app.sh             # Application startup script
├── requirements.txt       # Python dependencies
├── docs/                  # Documentation files
├── rag/                   # Core RAG implementation
│   ├── document_loader.py # Document processing
│   ├── indexing.py        # Vector indexing and search
│   ├── language_model.py  # LLM integration
│   ├── retriever.py       # Document retrieval logic
│   └── generator.py       # Response generation
├── static/                # Frontend assets
│   ├── css/               # Stylesheets
│   ├── js/                # JavaScript files
│   └── images/            # Images and icons
├── templates/             # HTML templates
├── data/                  # Data directory
│   ├── uploads/           # User uploaded files
│   ├── vector_store/      # Vector database files
│   └── samples/           # Sample documents
└── tests/                 # Test suite
    ├── test_api.py        # API tests
    ├── test_indexing.py   # Index tests
    └── ...
```