# Deploying RecallAI on Render

This guide provides step-by-step instructions for deploying the RecallAI application on Render.com, a cloud platform that makes it easy to deploy web applications.

## Prerequisites

Before you begin, make sure you have:

1. A [Render account](https://render.com/) (you can sign up with GitHub or email)
2. Your RecallAI codebase in a Git repository (GitHub, GitLab, or Bitbucket)
3. A Google API key for Gemini (for the language model)

## Step 1: Prepare Your Repository

Ensure your RecallAI codebase has the following files properly configured:

1. **requirements.txt**: Lists all Python dependencies
2. **app.py**: The main Flask application file
3. **.env.example**: Template for environment variables

If you're starting from a fresh clone of the RecallAI repository, these files should already be present.

## Step 2: Create a render.yaml File

Create a `render.yaml` file in the root of your repository to define the deployment configuration:

```yaml
services:
  - type: web
    name: recallai
    env: python
    region: oregon  # Choose the region closest to your users
    plan: free  # Or choose a paid plan for more resources
    branch: main  # Or your preferred branch
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn --bind 0.0.0.0:$PORT app:app
    envVars:
      - key: FLASK_APP
        value: app.py
      - key: FLASK_ENV
        value: production
      - key: DEBUG
        value: 0
      - key: VECTOR_STORE_PATH
        value: /var/data/vector_store
      - key: UPLOADS_PATH
        value: /var/data/uploads
      - key: GOOGLE_API_KEY
        sync: false  # This will prompt you to enter it manually
      - key: FLASK_SECRET_KEY
        generateValue: true  # Automatically generates a secure random value
      - key: PORT
        fromService:
          type: web
          name: recallai
          property: port
    disk:
      name: data
      mountPath: /var/data
      sizeGB: 1  # Adjust based on your needs
```

## Step 3: Add gunicorn to Requirements

Make sure `gunicorn` is included in your `requirements.txt` file:

```
# Add this line to requirements.txt if it's not already there
gunicorn>=20.1.0
```

## Step 4: Update Data Paths in Your Code

Modify your code to use the persistent disk storage on Render. Update the following in your `app.py`:

```python
# Adjust the default paths to use the Render disk mount locations
VECTOR_DB_PATH = os.getenv("VECTOR_STORE_PATH", "./data/vector_store")
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "./data/uploads")
```

## Step 5: Deploy to Render

There are two ways to deploy to Render:

### Option 1: Deploy with render.yaml (Blueprint)

1. Push your changes with the render.yaml file to your Git repository
2. Log in to your Render dashboard
3. Click "New" and select "Blueprint"
4. Select your repository
5. Click "Apply Blueprint"
6. Enter any required environment variables when prompted

### Option 2: Manual Web Service Setup

If you prefer to configure your service manually:

1. Log in to your Render dashboard
2. Click "New" and select "Web Service"
3. Connect your Git repository
4. Give your service a name (e.g., "recallai")
5. Select the branch to deploy
6. Select "Python" as the runtime
7. Set the build command: `pip install -r requirements.txt`
8. Set the start command: `gunicorn --bind 0.0.0.0:$PORT app:app`
9. Click "Create Web Service"

## Step 6: Configure Environment Variables

If you used Option 2 (manual setup), you'll need to set environment variables:

1. After creating your web service, go to the "Environment" tab
2. Add the following environment variables:
   - `FLASK_APP`: `app.py`
   - `FLASK_ENV`: `production`
   - `DEBUG`: `0`
   - `GOOGLE_API_KEY`: Your Google Gemini API key
   - `FLASK_SECRET_KEY`: Generate a random string (e.g., using `openssl rand -hex 24`)
   - `VECTOR_STORE_PATH`: `/var/data/vector_store`
   - `UPLOADS_PATH`: `/var/data/uploads`

## Step 7: Set Up Disk Storage

To add persistent storage for the vector database and uploaded files:

1. Go to your web service in the Render dashboard
2. Click on the "Disk" tab
3. Click "Create Disk"
4. Set the mount path to `/var/data`
5. Choose an appropriate size (start with 1GB and increase if needed)
6. Click "Save"

## Step 8: Monitor Deployment

1. Render will automatically build and deploy your application
2. Monitor the build logs for any errors
3. Once deployed, you'll see a URL where your application is available (e.g., `https://recallai.onrender.com`)

## Step 9: First-Time Setup

After deployment:

1. Access your application using the provided URL
2. Create the necessary directories if they don't exist automatically:
   - This should happen automatically via your application code
3. Upload initial documents to build your knowledge base

## Troubleshooting

**Issue**: Application crashes during startup
- Check that all dependencies are included in requirements.txt
- Verify environment variables are correctly set
- Review logs in the Render dashboard

**Issue**: Vector store not persisting
- Ensure the disk is properly mounted
- Check that the paths in environment variables match the code

**Issue**: Memory errors
- Upgrade to a higher-tier plan on Render
- Optimize your code to use less memory

**Issue**: Slow responses
- The free tier on Render has limited resources and can be slow
- Consider upgrading to a paid plan for better performance
- Optimize your vector search and document processing

## Scaling Up

As your needs grow:

1. **Upgrade your plan**: Move to a paid plan for more resources
2. **Increase disk size**: If you're storing many documents
3. **Add a database**: For larger installations, consider using a dedicated database service
4. **Use Render private services**: For components that don't need to be publicly accessible

## Conclusion

Your RecallAI application should now be running on Render with persistent storage for your vector database and uploaded files. You can access it via the URL provided in your Render dashboard.

Remember that the free tier on Render has limitations, including:
- Limited compute resources
- Spinning down after periods of inactivity (may cause slow initial responses)
- Limited disk space

For production use, consider upgrading to a paid plan for better performance and reliability. 