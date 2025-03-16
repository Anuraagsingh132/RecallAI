#!/bin/bash

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p data/vector_store

# Create .env file from example if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "Please edit the .env file with your configuration."
fi

# Run tests
echo "Running tests..."
python3 test_indexing.py

echo "Setup complete! You can now run the application with:"
echo "source venv/bin/activate"
echo "export FLASK_APP=app.py"
echo "export FLASK_ENV=development"
echo "python -m flask run" 