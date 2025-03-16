# RecallAI Installation Guide

This guide provides detailed instructions for installing and configuring RecallAI on your system. Follow these steps to set up your own instance of this powerful RAG chatbot application.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation Options](#installation-options)
3. [Standard Installation](#standard-installation)
4. [Docker Installation](#docker-installation)
5. [Configuration](#configuration)
6. [Upgrading](#upgrading)
7. [Uninstallation](#uninstallation)

## Prerequisites

Before installing RecallAI, ensure your system meets the following requirements:

### Hardware Requirements

- **CPU**: Multi-core processor (4+ cores recommended for smooth performance)
- **RAM**: Minimum 4GB (8GB+ recommended, especially for larger document collections)
- **Disk Space**: At least 2GB for the application and dependencies, plus additional space for documents and vector store
- **Internet Connection**: Required for downloading dependencies and accessing the Google Gemini API

### Software Requirements

- **Operating System**: 
  - Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+)
  - macOS 10.15+
  - Windows 10/11 with WSL2 (recommended) or PowerShell
- **Python**: Version 3.8-3.11
- **Package Manager**: pip (included with Python)
- **Optional**: Docker and Docker Compose (for container-based installation)

### Required Credentials

- **Google API Key**: Required for the Gemini API (used for text generation)
  - Sign up at [Google AI Studio](https://aistudio.google.com/)
  - Create an API key under your account

## Installation Options

RecallAI can be installed in several ways:

1. **Standard Installation**: Traditional installation directly on your system
2. **Docker Installation**: Containerized installation using Docker
3. **Development Setup**: For contributors who want to modify the codebase

Choose the method that best suits your needs and technical expertise.

## Standard Installation

### Step 1: Clone the Repository

```bash
# Create a directory for the application
mkdir -p ~/recallai
cd ~/recallai

# Clone the repository
git clone https://github.com/yourusername/recallai.git .
```

### Step 2: Set Up a Virtual Environment

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
# Install the required packages
pip install -r requirements.txt
```

This might take a few minutes as it installs all the necessary libraries.

### Step 4: Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your settings
nano .env
```

At minimum, update the following variables:
- `GOOGLE_API_KEY`: Your Google API key for the Gemini model
- `FLASK_SECRET_KEY`: A random string for Flask session security (generate one with `openssl rand -hex 24`)

### Step 5: Create Required Directories

```bash
# Create necessary directories
mkdir -p data/vector_store data/uploads logs
```

### Step 6: Make Scripts Executable

```bash
# Make the shell scripts executable
chmod +x *.sh
```

### Step 7: Start the Application

```bash
# Start RecallAI
./run_app.sh
```

The application should now be running at http://localhost:8080

## Docker Installation

Docker provides an isolated environment for running RecallAI.

### Step 1: Clone the Repository

```bash
# Create a directory for the application
mkdir -p ~/recallai
cd ~/recallai

# Clone the repository
git clone https://github.com/yourusername/recallai.git .
```

### Step 2: Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your settings
nano .env
```

At minimum, update:
- `GOOGLE_API_KEY`: Your Google API key for the Gemini model
- `FLASK_SECRET_KEY`: A random string for Flask session security

### Step 3: Run with Docker Compose

```bash
# Make the deployment script executable
chmod +x docker_deploy.sh

# Run the deployment script
./docker_deploy.sh
```

The application should now be running at http://localhost:8080

### Alternative: Manual Docker Setup

If you prefer to run Docker commands manually:

```bash
# Build the Docker image
docker build -t recallai .

# Create necessary directories
mkdir -p data/vector_store data/uploads logs

# Run the container
docker run -d \
  --name recallai \
  -p 8080:8080 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  --env-file .env \
  --restart unless-stopped \
  recallai
```

## Configuration

### Core Configuration Options

Edit the `.env` file to configure the application:

```
# Flask settings
FLASK_APP=app.py
FLASK_ENV=production  # Use 'development' for development mode
PORT=8080
DEBUG=0               # Set to 1 for debug mode

# Google Gemini settings
GOOGLE_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-1.5-flash  # Or another Gemini model version

# Security settings
FLASK_SECRET_KEY=your_secret_key_here
SECURE_COOKIES=True
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True

# Vector store settings
VECTOR_STORE_PATH=./data/vector_store
UPLOADS_PATH=./data/uploads
```

### Advanced Configuration

For advanced configuration, you may need to modify specific files:

- **Embedding Model**: To change the embedding model, edit `rag/indexing.py` and update the `SentenceTransformer` model name
- **PDF Processing**: Adjust PDF processing parameters in `rag/document_loader.py`
- **Chunk Size**: Modify text chunking parameters in `rag/document_loader.py` to adjust the chunk size and overlap

### Server Configuration

To run RecallAI behind a reverse proxy like Nginx:

1. Create an Nginx configuration in `/etc/nginx/sites-available/recallai`:

```nginx
server {
    listen 80;
    server_name your.domain.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

2. Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/recallai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

3. Consider adding SSL with Let's Encrypt:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your.domain.com
```

## Upgrading

To upgrade RecallAI to a newer version:

### Standard Installation

```bash
# Go to the application directory
cd ~/recallai

# Stop the current instance
./stop_app.sh

# Pull the latest changes
git pull

# Activate the virtual environment
source venv/bin/activate

# Update dependencies
pip install -r requirements.txt

# Start the application again
./run_app.sh
```

### Docker Installation

```bash
# Go to the application directory
cd ~/recallai

# Pull the latest changes
git pull

# Stop the current container
docker-compose down

# Rebuild and start the updated container
docker-compose up -d --build
```

## Uninstallation

### Standard Installation

```bash
# Go to the application directory
cd ~/recallai

# Stop the application
./stop_app.sh

# Deactivate the virtual environment
deactivate

# Remove the application directory
cd ..
rm -rf recallai
```

### Docker Installation

```bash
# Go to the application directory
cd ~/recallai

# Stop and remove the container
docker-compose down

# Remove the application directory
cd ..
rm -rf recallai

# Optionally, remove the Docker image
docker rmi recallai
```

---

Congratulations! You have successfully installed RecallAI. For more information on using the application, please refer to the [User Guide](./USER_GUIDE.md). 