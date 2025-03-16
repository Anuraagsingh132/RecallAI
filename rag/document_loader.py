import os
import pdfplumber
import wikipedia
from typing import List, Dict, Union, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter

class DocumentLoader:
    """Class for loading documents from various sources."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize the DocumentLoader.
        
        Args:
            chunk_size: Size of text chunks to split documents into
            chunk_overlap: Overlap between consecutive chunks
        """
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len
        )
    
    def load_pdf(self, file_path: str) -> List[Dict[str, str]]:
        """
        Load text from a PDF file.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            List of document chunks with text and metadata
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n\n"
        
        # Create metadata for the source
        metadata = {"source": file_path, "type": "pdf"}
        
        return self._split_text(text, metadata)
    
    def load_text_file(self, file_path: str) -> List[Dict[str, str]]:
        """
        Load text from a plain text file.
        
        Args:
            file_path: Path to the text file
            
        Returns:
            List of document chunks with text and metadata
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Text file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        
        metadata = {"source": file_path, "type": "text"}
        
        return self._split_text(text, metadata)
    
    def load_wikipedia(self, query: str) -> List[Dict[str, str]]:
        """
        Load text from Wikipedia.
        
        Args:
            query: Search query for Wikipedia
            
        Returns:
            List of document chunks with text and metadata
        """
        # Search Wikipedia
        search_results = wikipedia.search(query, results=1)
        if not search_results:
            return []
        
        # Get the page content
        try:
            page = wikipedia.page(search_results[0], auto_suggest=False)
            content = page.content
            url = page.url
            title = page.title
        except (wikipedia.exceptions.DisambiguationError, wikipedia.exceptions.PageError) as e:
            return []
        
        metadata = {"source": url, "title": title, "type": "wikipedia"}
        
        return self._split_text(content, metadata)
    
    def _split_text(self, text: str, metadata: Dict[str, str]) -> List[Dict[str, str]]:
        """
        Split text into chunks.
        
        Args:
            text: Text to split
            metadata: Metadata for the text
            
        Returns:
            List of document chunks with text and metadata
        """
        chunks = self.text_splitter.create_documents([text], [metadata])
        return [
            {
                "text": chunk.page_content,
                "metadata": chunk.metadata
            }
            for chunk in chunks
        ] 