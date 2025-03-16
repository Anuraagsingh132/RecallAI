import os
import json
import google.generativeai as genai
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LanguageModel:
    """Class for generating responses using an LLM."""
    
    def __init__(self):
        """Initialize the language model."""
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        
        # Check if API key is available
        self.is_available = self.api_key is not None and self.api_key != ""
        
        # Configure the Gemini model if API key is available
        if self.is_available:
            genai.configure(api_key=self.api_key)
    
    def generate_response(self, query: str, documents: List[Dict[str, Any]], max_tokens: int = 500) -> Dict[str, Any]:
        """
        Generate a response using the language model.
        
        Args:
            query: User query
            documents: List of retrieved documents with text and metadata
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Dictionary with response text and metadata
        """
        if not self.is_available:
            # Fallback to a simple response if API key is not available
            return self._generate_simple_response(query, documents)
        
        # Create the prompt with context
        prompt = self._create_prompt(query, documents)
        
        try:
            # Initialize the Gemini model
            model = genai.GenerativeModel(self.model)
            
            # Generate response
            response = model.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": max_tokens,
                    "temperature": 0.7,
                }
            )
            
            generated_text = response.text
            
            return {
                "response": generated_text,
                "model": self.model,
                "using_llm": True
            }
            
        except Exception as e:
            # Fallback to simple response on error
            print(f"Error generating response with Gemini: {str(e)}")
            return self._generate_simple_response(query, documents)
    
    def _create_prompt(self, query: str, documents: List[Dict[str, Any]]) -> str:
        """
        Create a prompt for the language model.
        
        Args:
            query: User query
            documents: List of retrieved documents
            
        Returns:
            Formatted prompt string
        """
        prompt = f"You are a helpful assistant that answers questions based on the provided context.\n\n"
        prompt += f"Answer the following question: '{query}'\n\n"
        prompt += "Use the following context to inform your answer:\n\n"
        
        # Add document contents to the prompt
        for i, doc in enumerate(documents):
            source = doc.get("metadata", {}).get("source", "Unknown")
            prompt += f"Document {i+1} (Source: {source}):\n{doc['text']}\n\n"
        
        prompt += f"Based on the provided context, please answer the question: '{query}'\n"
        prompt += "If the context doesn't contain the answer, please say so. Cite the sources used."
        
        return prompt
    
    def _generate_simple_response(self, query: str, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a simple response without using an LLM.
        
        Args:
            query: User query
            documents: List of retrieved documents
            
        Returns:
            Dictionary with response text and metadata
        """
        if not documents:
            return {
                "response": f"I don't have specific information to answer your question: '{query}'",
                "using_llm": False
            }
        
        # Create a simple response based on the first document
        response = f"I found some information that might help with your question: '{query}'\n\n"
        
        # Add information from the first document
        doc = documents[0]
        response += doc["text"][:300] + "...\n\n"
        
        # Add source attribution
        source = doc.get("metadata", {}).get("source", "Unknown")
        response += f"Source: {source}"
        
        return {
            "response": response,
            "using_llm": False
        } 