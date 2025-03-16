# RecallAI User Guide

This guide provides detailed instructions on how to use the RecallAI application effectively. RecallAI is a powerful chatbot that uses Retrieval-Augmented Generation (RAG) to provide accurate answers based on your documents.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Understanding the Interface](#understanding-the-interface)
3. [Adding Documents](#adding-documents)
4. [Asking Questions](#asking-questions)
5. [Understanding Responses](#understanding-responses)
6. [Advanced Features](#advanced-features)
7. [Troubleshooting](#troubleshooting)
8. [Tips and Best Practices](#tips-and-best-practices)

## Getting Started

### Accessing RecallAI

1. Make sure RecallAI is running (see [Installation Guide](./INSTALLATION.md) if you haven't set it up yet)
2. Open your web browser and navigate to:
   - Local installation: `http://localhost:8080`
   - Or the URL provided by your administrator if using a hosted version

### Browser Requirements

RecallAI works best with modern browsers. We recommend:

- Chrome (version 90+)
- Firefox (version 88+)
- Edge (version 90+)
- Safari (version 14+)

### First-time Setup

When you first access RecallAI, you'll see the main interface with an empty chat and navigation tabs. Before asking questions, you'll need to add some documents to the system.

## Understanding the Interface

The RecallAI interface consists of several key components:

### Main Navigation

The interface has three main tabs:

- **Chat**: The main interaction area where you ask questions and view responses
- **Upload**: Where you can upload text files and PDFs
- **Wikipedia**: Where you can import content from Wikipedia

### Chat Tab

The chat tab includes:

- Chat history display showing your conversation
- Message input box at the bottom
- Send button to submit your questions

### Upload Tab

The upload tab has two sections:

- **Text Files**: Upload plain text files (`.txt`)
- **PDF Files**: Upload PDF documents (`.pdf`)

### Wikipedia Tab

This tab allows you to:

- Enter search terms
- Import Wikipedia articles directly into the system

### Theme Toggle

In the top-right corner, you'll find a theme toggle button that allows you to switch between light and dark modes for better readability.

## Adding Documents

Before RecallAI can answer questions, you need to add documents to its knowledge base. You have three options:

### 1. Uploading Text Files

1. Navigate to the **Upload** tab
2. In the **Text Files** section, click "Choose File" or drag and drop a text file
3. Once the file is selected, click "Upload"
4. After successful upload, click "Load into RecallAI"
5. Wait for the confirmation message that indicates the file has been processed

### 2. Uploading PDF Documents

1. Navigate to the **Upload** tab
2. In the **PDF Files** section, click "Choose File" or drag and drop a PDF
3. Once the file is selected, click "Upload"
4. After successful upload, click "Load into RecallAI"
5. Wait for the confirmation message that indicates the file has been processed
   - Note: PDF processing might take longer depending on the file size and complexity

### 3. Importing from Wikipedia

1. Navigate to the **Wikipedia** tab
2. Enter a search term in the search box
3. Click "Load from Wikipedia"
4. The system will search Wikipedia and import relevant articles
5. Wait for the confirmation message that indicates the articles have been processed

### Checking Document Status

After loading documents, you'll see a confirmation message indicating:

- How many document chunks were loaded
- The total number of documents in the system

This information helps you track what content is available for the chatbot to reference.

## Asking Questions

Once you've added documents, you can start asking questions:

1. Navigate to the **Chat** tab
2. Type your question in the input box at the bottom
3. Press Enter or click the Send button
4. Wait for RecallAI to process your question and generate a response

### Question Tips

For best results:

- Ask specific questions rather than vague ones
- Provide context if relevant
- One question at a time works better than multiple questions
- If asking about specific documents, mention them by name

## Understanding Responses

RecallAI responses include several components:

### Answer Text

The main response to your question, generated based on relevant documents in the system.

### Source Citations

Below each response, you'll see a "Sources" section listing:

- The documents used to generate the response
- For Wikipedia articles, the title and source
- For uploaded files, the filename

### Confidence Indicators

Some responses include confidence indicators:

- Strong matches: The system found highly relevant information
- Partial matches: The system found somewhat relevant information
- Uncertain responses: The system couldn't find strongly relevant information

### Response Format

Responses are formatted with:

- Paragraphs for general explanations
- Bullet points for lists
- Numbered lists for sequences or steps
- Code formatting for technical content when relevant

## Advanced Features

RecallAI includes several advanced features to enhance your experience:

### Dark Mode

Toggle between light and dark modes by clicking the sun/moon icon in the top-right corner. Your preference will be saved for future sessions.

### Copy to Clipboard

Each bot response includes a copy button (visible on hover) that allows you to copy the entire response to your clipboard with a single click.

### Conversation History

Your conversation history is saved within your browser session. You can:

- Scroll up to view previous exchanges
- Start a new session by refreshing the page if you want to clear history

### Browser Notifications

If enabled and supported by your browser, RecallAI can send desktop notifications when responses are ready. This is useful if you're working in another tab or window.

## Troubleshooting

### Common Issues

**No response or slow response:**
- Check if the server is running
- Large documents may take longer to process
- Complex questions might require more processing time

**"I don't have enough information" responses:**
- The system couldn't find relevant information in the loaded documents
- Try rephrasing your question
- Add more relevant documents to the system

**Upload failures:**
- Check file format (must be `.txt` or `.pdf`)
- Ensure file size is under the limit (typically 10MB)
- Try a different browser if problems persist

**PDF content not recognized correctly:**
- Some PDFs with complex formatting may not extract text properly
- Try converting to a simpler PDF format
- For scanned PDFs, ensure they have OCR applied

### Getting Help

If you encounter issues:

1. Check the server logs for error messages
2. Consult the [Troubleshooting](./TROUBLESHOOTING.md) guide for more specific solutions
3. Contact your system administrator if using a managed instance

## Tips and Best Practices

### Document Preparation

For best results:

- Break large documents into smaller, focused files
- Use clear, descriptive filenames
- Ensure text is clean and well-formatted
- For PDFs, use searchable PDFs rather than scanned images

### Question Strategies

To get the most accurate answers:

- Start with simple, specific questions
- If answers lack detail, try follow-up questions
- Use terminology that matches your documents
- Reference specific sections or documents if you know where information is located

### System Performance

To maintain good performance:

- Don't upload duplicate documents
- Remove outdated documents when they're no longer needed
- For large document collections, consider grouping related documents
- If the system becomes slow, restart the application

---

This user guide provides comprehensive instructions for using RecallAI effectively. For more technical details, please refer to the [Technical Documentation](./TECHNICAL_DETAILS.md). 