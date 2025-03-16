#!/bin/bash
#
# Script to prepare RecallAI for deployment to Render
#

# Terminal colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}  RecallAI - Render Deployment Prep${NC}"
echo -e "${BLUE}=========================================${NC}"

# Check for git repository
if [ ! -d ".git" ]; then
    echo -e "${YELLOW}Warning: Git repository not detected. Initializing...${NC}"
    git init
    echo -e "${GREEN}Git repository initialized.${NC}"
fi

# Check for requirements.txt
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}Error: requirements.txt not found. Please create this file first.${NC}"
    exit 1
else
    # Check if gunicorn is in requirements.txt
    if ! grep -q "gunicorn" requirements.txt; then
        echo -e "${YELLOW}Adding gunicorn to requirements.txt...${NC}"
        echo "gunicorn==20.1.0" >> requirements.txt
        echo -e "${GREEN}Added gunicorn to requirements.txt${NC}"
    else
        echo -e "${GREEN}gunicorn already in requirements.txt${NC}"
    fi
fi

# Create render.yaml if it doesn't exist
if [ ! -f "render.yaml" ]; then
    echo -e "${YELLOW}Creating render.yaml...${NC}"
    cat > render.yaml << EOL
services:
  - type: web
    name: recallai
    env: python
    region: oregon
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn --bind 0.0.0.0:$PORT app:app
    envVars:
      - key: FLASK_APP
        value: app.py
      - key: FLASK_ENV
        value: production
      - key: DEBUG
        value: "0"
      - key: VECTOR_STORE_PATH
        value: /var/data/vector_store
      - key: UPLOADS_PATH
        value: /var/data/uploads
      - key: GOOGLE_API_KEY
        sync: false
      - key: FLASK_SECRET_KEY
        generateValue: true
      - key: PORT
        fromService:
          type: web
          name: recallai
          property: port
    disk:
      name: data
      mountPath: /var/data
      sizeGB: 1
EOL
    echo -e "${GREEN}Created render.yaml${NC}"
else
    echo -e "${GREEN}render.yaml already exists${NC}"
fi

# Create Procfile if it doesn't exist
if [ ! -f "Procfile" ]; then
    echo -e "${YELLOW}Creating Procfile...${NC}"
    echo "web: gunicorn app:app" > Procfile
    echo -e "${GREEN}Created Procfile${NC}"
else
    echo -e "${GREEN}Procfile already exists${NC}"
fi

# Create .env.example if it doesn't exist
if [ ! -f ".env.example" ]; then
    echo -e "${YELLOW}Creating .env.example...${NC}"
    cat > .env.example << EOL
# Flask configuration
FLASK_APP=app.py
FLASK_ENV=production  # Use 'development' for development environments
DEBUG=0               # Set to 1 to enable debug mode

# Server configuration
PORT=8080

# Security settings
FLASK_SECRET_KEY=replace_with_secure_random_string

# Vector store and upload paths
VECTOR_STORE_PATH=./data/vector_store
UPLOADS_PATH=./data/uploads

# Google API settings for Gemini model
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_MODEL=gemini-2.0-flash

# Additional settings for production
SECURE_COOKIES=True
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
EOL
    echo -e "${GREEN}Created .env.example${NC}"
else
    echo -e "${GREEN}Found .env.example${NC}"
fi

# Create directories for local testing
echo -e "${YELLOW}Creating necessary directories...${NC}"
mkdir -p data/vector_store data/uploads
echo -e "${GREEN}Created directories${NC}"

# Show instructions
echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}Preparation complete!${NC}"
echo -e "${GREEN}To deploy to Render:${NC}"
echo -e "${YELLOW}1. Push your code to a Git repository (GitHub, GitLab, etc.)${NC}"
echo -e "${YELLOW}2. Log in to your Render dashboard at https://dashboard.render.com${NC}"
echo -e "${YELLOW}3. Click 'New' and select 'Blueprint'${NC}"
echo -e "${YELLOW}4. Connect your repository and follow the prompts${NC}"
echo -e "${YELLOW}5. Alternatively, use 'New Web Service' option and configure manually${NC}"
echo -e "${GREEN}==========================================${NC}" 