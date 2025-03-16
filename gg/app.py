import os
import json
import time
import uuid
from flask import Flask, request, jsonify, session, render_template, send_from_directory
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

# Import RAG components
from rag.document_loader import DocumentLoader
from rag.indexing import DocumentIndexer
from rag.language_model import LanguageModel

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder='static')
app.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(24).hex())

# Initialize RAG components
document_loader = DocumentLoader()
document_indexer = DocumentIndexer()
language_model = LanguageModel()

# Get vector store path from environment
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./data/vector_store")
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "./data/uploads")

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Try to load existing vector store
document_indexer.load(VECTOR_DB_PATH)

@app.route("/", methods=["GET"])
def index():
    """Route for the home page."""
    return render_template("index.html")

@app.route('/static/<path:path>')
def send_static(path):
    """Route for serving static files."""
    return send_from_directory('static', path)

@app.route("/api", methods=["GET"])
def api_info():
    """Route for API information."""
    return jsonify({
        "status": "success",
        "message": "RecallAI API is running",
        "endpoints": [
            {"path": "/load", "method": "POST", "description": "Load documents into the system"},
            {"path": "/chat", "method": "POST", "description": "Chat with the bot"},
            {"path": "/search", "method": "POST", "description": "Search for relevant documents"},
            {"path": "/history", "method": "GET", "description": "Get conversation history"}
        ]
    })

@app.route("/upload-text", methods=["POST"])
def upload_text():
    """Route for uploading text files."""
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part"}), 400
        
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"status": "error", "message": "No file selected"}), 400
        
    if file:
        filename = secure_filename(file.filename)
        # Add unique identifier to prevent overwriting
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(file_path)
        
        return jsonify({
            "status": "success",
            "message": "File uploaded successfully",
            "path": file_path
        })

@app.route("/upload-pdf", methods=["POST"])
def upload_pdf():
    """Route for uploading PDF files."""
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part"}), 400
        
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"status": "error", "message": "No file selected"}), 400
        
    if file and file.filename.endswith('.pdf'):
        filename = secure_filename(file.filename)
        # Add unique identifier to prevent overwriting
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(file_path)
        
        return jsonify({
            "status": "success",
            "message": "PDF uploaded successfully",
            "path": file_path
        })
    
    return jsonify({"status": "error", "message": "Invalid file format"}), 400

@app.route("/load", methods=["POST"])
def load_document():
    """Route for loading documents into the system."""
    data = request.json
    
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400
        
    source_type = data.get("source")
    
    if source_type == "pdf":
        path = data.get("path")
        if not path:
            return jsonify({"status": "error", "message": "No path provided"}), 400
            
        try:
            # Load PDF
            documents = document_loader.load_pdf(path)
            
            # Add documents to index
            document_indexer.add_documents(documents)
            
            # Save the updated index
            document_indexer.save(VECTOR_DB_PATH)
            
            return jsonify({
                "status": "success", 
                "message": f"Loaded {len(documents)} document chunks from PDF",
                "document_count": len(documents)
            })
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
            
    elif source_type == "text":
        path = data.get("path")
        if not path:
            return jsonify({"status": "error", "message": "No path provided"}), 400
            
        try:
            # Load text file
            documents = document_loader.load_text_file(path)
            
            # Add documents to index
            document_indexer.add_documents(documents)
            
            # Save the updated index
            document_indexer.save(VECTOR_DB_PATH)
            
            return jsonify({
                "status": "success", 
                "message": f"Loaded {len(documents)} document chunks from text file",
                "document_count": len(documents)
            })
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
            
    elif source_type == "wikipedia":
        query = data.get("query")
        if not query:
            return jsonify({"status": "error", "message": "No query provided"}), 400
            
        try:
            # Load from Wikipedia
            documents = document_loader.load_wikipedia(query)
            
            if not documents:
                return jsonify({
                    "status": "error", 
                    "message": f"No Wikipedia content found for query: {query}"
                }), 404
                
            # Add documents to index
            document_indexer.add_documents(documents)
            
            # Save the updated index
            document_indexer.save(VECTOR_DB_PATH)
            
            return jsonify({
                "status": "success", 
                "message": f"Loaded {len(documents)} document chunks from Wikipedia",
                "document_count": len(documents)
            })
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
            
    else:
        return jsonify({
            "status": "error", 
            "message": f"Unsupported source type: {source_type}. Supported types are: pdf, text, wikipedia"
        }), 400

@app.route("/search", methods=["POST"])
def search():
    """Route for searching documents."""
    data = request.json
    
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400
        
    query = data.get("query")
    top_k = data.get("top_k", 5)
    
    if not query:
        return jsonify({"status": "error", "message": "No query provided"}), 400
        
    try:
        # Search for relevant documents
        results = document_indexer.search(query, top_k=top_k)
        
        if not results:
            return jsonify({
                "status": "warning",
                "message": "No relevant documents found",
                "results": []
            })
            
        # Format results
        formatted_results = []
        for result in results:
            formatted_result = {
                "text": result["text"],
                "metadata": result["metadata"],
                "similarity": float(result["similarity"])
            }
            formatted_results.append(formatted_result)
            
        return jsonify({
            "status": "success",
            "message": f"Found {len(results)} relevant documents",
            "results": formatted_results
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

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

@app.route("/history", methods=["GET"])
def get_history():
    """Route for getting conversation history."""
    history = session.get('history', [])
    return jsonify({
        "status": "success",
        "history": history
    })

@app.route("/clear-history", methods=["POST"])
def clear_history():
    """Route for clearing conversation history."""
    session['history'] = []
    session.modified = True
    return jsonify({
        "status": "success",
        "message": "Conversation history cleared"
    })

if __name__ == "__main__":
    debug = os.getenv("DEBUG", "0") == "1"
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, debug=debug) 